"""CustomTkinter front-end.

First start: pick a language. Then a short three-step wizard (game window ->
monster name -> keys), prefilled from the last run. After "Finish" the
dashboard shows a summary, the START button and the log. Training, recording
and the detector mode live under "Advanced" so the default screens stay simple.
The language can be changed at any time; the window is rebuilt in place.
"""

import queue
import re
import subprocess
import sys
import threading
import time
import tkinter as tk
import webbrowser

import customtkinter as ctk

from . import CONTACT_EMAIL, GITHUB_URL, REPO_URL, __author__, __version__, detect, i18n, theme, winutil
from .capture import ScreenGrabber
from .config import Config
from .engine import BotEngine, State
from .i18n import LANGUAGES, t
from .overlay import Overlay, OverlayState
from .paths import app_dir
from .recorder import Recorder, RecorderThread

APP_TITLE = "Silkroad Vision Bot"
GAME_HINTS = ("silkroad", "destiny", "online", "sro")
HOTKEY = "f5"
ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
EPOCH_DONE = re.compile(r"(\d+/\d+)\s.*\s100%")
GRAY, RED = theme.GRAY, theme.RED
STEP_KEYS = ("step_game", "step_monster", "step_keys")


def mode_labels():
    return {"auto": t("mode_auto"), "ocr": t("mode_ocr"), "model": t("mode_model")}


def parse_names(text):
    """'Mangyang, Cave Bat' -> ['Mangyang', 'Cave Bat'] (case-insensitive de-duplication)."""
    seen, names = set(), []
    for part in text.split(","):
        name = " ".join(part.split())
        if name and name.lower() not in seen:
            seen.add(name.lower())
            names.append(name)
    return names


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        theme.apply()
        self.withdraw()  # stay hidden until built and centred, so the window never flashes at a corner
        self.title(APP_TITLE)
        self.configure(fg_color=theme.BG)
        theme.set_icon(self)
        self.minsize(920, 620)

        self.cfg = Config.load()
        i18n.set_language(self.cfg.language or "tr")
        self.engine = None
        self.recorder = Recorder()
        self.rec_thread = None
        self.overlay = Overlay(self)
        self.ostate = OverlayState()
        self.windows = {}
        self.events = queue.Queue()
        self._searching = False
        self.step = 0
        self.view = "lang" if not self.cfg.language else "wizard"
        self.frames = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._build_all()
        self._show_view(self.view)
        self._register_hotkey()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(100, self._poll)
        self._center(self, 1000, 680)  # start in the middle of the screen
        self.deiconify()

    # ======================================================================
    # Building and switching views
    # ======================================================================
    def _build_all(self):
        for frame in self.frames:
            frame.destroy()
        self.langpage = ctk.CTkFrame(self, fg_color="transparent")
        self.wizard = ctk.CTkFrame(self, fg_color="transparent")
        self.dashboard = ctk.CTkFrame(self, fg_color="transparent")
        self.frames = [self.langpage, self.wizard, self.dashboard]
        self._build_language_page()
        self._build_wizard()
        self._build_dashboard()
        self._refresh_windows()
        self._render_summary()
        self._refresh_run_button()

    def _show_view(self, view):
        self.view = view
        for name, frame in (("lang", self.langpage), ("wizard", self.wizard), ("dash", self.dashboard)):
            frame.grid(row=0, column=0, sticky="nsew") if name == view else frame.grid_remove()
        if view == "wizard":
            self._goto_step(self.step)

    def _snapshot_inputs(self):
        """Keep what the user typed so a rebuild (language switch) loses nothing."""
        if hasattr(self, "monster_entry") and self.monster_entry.winfo_exists():
            names = parse_names(self.monster_entry.get())
            if names:
                self.cfg.monsters = names
            self._apply_inputs()

    def _set_language(self, code):
        if code == i18n.get_language() and self.cfg.language == code:
            return
        self._snapshot_inputs()
        self.cfg.language = code
        i18n.set_language(code)
        self.cfg.save()
        view = self.view if self.view != "lang" else "wizard"
        self._build_all()
        self._show_view(view)

    def _language_menu(self, parent):
        names = list(LANGUAGES.values())
        menu = ctk.CTkOptionMenu(parent, values=names, width=110, height=28,
                                 command=lambda label: self._set_language(
                                     next(k for k, v in LANGUAGES.items() if v == label)))
        menu.set(LANGUAGES[i18n.get_language()])
        return menu

    # ======================================================================
    # Language page (first start)
    # ======================================================================
    def _build_language_page(self):
        self.langpage.grid_columnconfigure(0, weight=1)
        self.langpage.grid_rowconfigure(0, weight=1)
        card = ctk.CTkFrame(self.langpage, width=460, height=420, **theme.CARD_STYLE)
        card.grid(row=0, column=0)
        card.pack_propagate(False)  # children are packed: keep the card at its fixed size
        ctk.CTkLabel(card, text="", image=theme.app_icon(96)).pack(pady=(30, 6))
        ctk.CTkLabel(card, text=APP_TITLE, font=("", 24, "bold")).pack()
        ctk.CTkLabel(card, text=t("lang_title"), font=("", 16, "bold")).pack(pady=(16, 2))
        ctk.CTkLabel(card, text="Programı hangi dilde kullanmak istersin?\nWhich language do you want to use?",
                     text_color=theme.MUTED, justify="center").pack()
        for code, label in LANGUAGES.items():
            ctk.CTkButton(card, text=label, height=46, width=260, font=("", 15, "bold"), corner_radius=theme.RADIUS_PILL,
                          command=lambda c=code: self._choose_language(c)).pack(pady=(14, 0))

    def _choose_language(self, code):
        self.cfg.language = code
        i18n.set_language(code)
        self.cfg.save()
        self._build_all()
        self._show_view("wizard")

    # ======================================================================
    # Wizard
    # ======================================================================
    def _build_wizard(self):
        self.wizard.grid_columnconfigure(0, weight=1)
        self.wizard.grid_rowconfigure(0, weight=1)

        card = ctk.CTkFrame(self.wizard, width=560, height=620, **theme.CARD_STYLE)
        card.grid(row=0, column=0)
        card.pack_propagate(False)  # children are packed: keep the card at its fixed size

        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", padx=16, pady=(12, 0))
        self._language_menu(top).pack(side="right")

        ctk.CTkLabel(card, text="", image=theme.app_icon(72)).pack(pady=(2, 6))
        ctk.CTkLabel(card, text=APP_TITLE, font=("", 24, "bold")).pack()
        ctk.CTkLabel(card, text=t("wizard_subtitle"), text_color=theme.MUTED).pack()

        self.step_labels = []
        bar = ctk.CTkFrame(card, fg_color="transparent")
        bar.pack(pady=(16, 6))
        for i, key in enumerate(STEP_KEYS):
            label = ctk.CTkLabel(bar, text=f"{i + 1}  {t(key)}", width=110, corner_radius=14, height=28)
            label.pack(side="left", padx=4)
            self.step_labels.append(label)

        self.pages = ctk.CTkFrame(card, fg_color="transparent")
        self.pages.pack(fill="both", expand=True, padx=34, pady=(10, 0))
        self.page_frames = []
        for build in (self._build_page_window, self._build_page_monster, self._build_page_keys):
            page = ctk.CTkFrame(self.pages, fg_color="transparent")
            self.page_frames.append(page)
            build(page)

        nav = ctk.CTkFrame(card, fg_color="transparent")
        nav.pack(fill="x", padx=34, pady=(8, 26), side="bottom")
        self.back_btn = ctk.CTkButton(nav, text=t("back"), width=110, height=38, corner_radius=theme.RADIUS_PILL,
                                      command=lambda: self._goto_step(self.step - 1), **GRAY)
        self.back_btn.pack(side="left")
        self.next_btn = ctk.CTkButton(nav, text=t("next"), width=150, height=38, corner_radius=theme.RADIUS_PILL, command=self._next_step)
        self.next_btn.pack(side="right")
        self.wizard_error = ctk.CTkLabel(card, text="", text_color=theme.ERROR_TEXT, wraplength=480)
        self.wizard_error.pack(side="bottom")

    def _heading(self, parent, title, hint):
        ctk.CTkLabel(parent, text=title, font=("", 17, "bold"), anchor="w").pack(fill="x", pady=(8, 2))
        ctk.CTkLabel(parent, text=hint, text_color=theme.MUTED, anchor="w", justify="left", wraplength=480).pack(fill="x")

    def _build_page_window(self, page):
        self._heading(page, t("win_title"), t("win_hint"))
        row = ctk.CTkFrame(page, fg_color="transparent")
        row.pack(fill="x", pady=(16, 0))
        self.window_menu = ctk.CTkOptionMenu(row, values=["-"], command=self._on_window, height=36)
        self.window_menu.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(row, text="⟳", width=42, height=36, command=self._refresh_windows).pack(side="left", padx=(8, 0))

    def _build_page_monster(self, page):
        self._heading(page, t("mon_title"), t("mon_hint"))
        self.monster_entry = ctk.CTkEntry(page, height=40, font=("", 15), placeholder_text=t("mon_placeholder"))
        self.monster_entry.insert(0, ", ".join(self.cfg.monsters))
        self.monster_entry.pack(fill="x", pady=(16, 0))
        self.monster_entry.bind("<Return>", lambda _e: self._next_step())
        self.search_btn = ctk.CTkButton(page, text=t("mon_read_btn"), command=self._search, **GRAY)
        self.search_btn.pack(fill="x", pady=(10, 0))
        ctk.CTkLabel(page, anchor="w", justify="left", text_color=theme.MUTED, wraplength=480,
                     text=t("mon_note")).pack(fill="x", pady=(12, 0))

    def _build_page_keys(self, page):
        self._heading(page, t("keys_title"), t("keys_hint"))
        self.attack_entry = self._labeled_entry(page, t("keys_attack"), ",".join(self.cfg.attack_keys))
        self.speed_label = ctk.CTkLabel(page, text="", anchor="w", justify="left", text_color=theme.MUTED, wraplength=480)
        self.speed_label.pack(fill="x", pady=(14, 0))
        self.speed_slider = ctk.CTkSlider(page, from_=0.2, to=1.2, number_of_steps=10, command=self._on_speed)
        self.speed_slider.set(self.cfg.attack_interval)
        self.speed_slider.pack(fill="x")
        self._on_speed(self.cfg.attack_interval)
        self.roam_switch = ctk.CTkSwitch(page, text=t("roam_switch"))
        if self.cfg.roam:
            self.roam_switch.select()
        self.roam_switch.pack(anchor="w", pady=(14, 0))
        self.radius_label = ctk.CTkLabel(page, text="", anchor="w", justify="left", text_color=theme.MUTED, wraplength=480)
        self.radius_label.pack(fill="x", pady=(10, 0))
        self.radius_slider = ctk.CTkSlider(page, from_=2, to=12, number_of_steps=10, command=self._on_radius)
        self.radius_slider.set(self.cfg.roam_radius)
        self.radius_slider.pack(fill="x")
        self._on_radius(self.cfg.roam_radius)

    def _on_speed(self, value):
        self.speed_label.configure(text=t("speed_text", s=f"{value:.1f}"))

    def _on_radius(self, value):
        self.radius_label.configure(text=t("radius_text", n=int(round(value))))

    def _labeled_entry(self, parent, label, value):
        ctk.CTkLabel(parent, text=label, anchor="w", text_color=theme.MUTED).pack(fill="x", pady=(14, 0))
        entry = ctk.CTkEntry(parent, height=36)
        entry.insert(0, value)
        entry.pack(fill="x")
        return entry

    def _goto_step(self, index):
        self.step = max(0, min(len(self.page_frames) - 1, index))
        self.dashboard.grid_remove()
        self.langpage.grid_remove()
        self.wizard.grid(row=0, column=0, sticky="nsew")
        self.view = "wizard"
        for i, page in enumerate(self.page_frames):
            if i == self.step:
                page.pack(fill="both", expand=True)
            else:
                page.pack_forget()
        for i, label in enumerate(self.step_labels):
            if i == self.step:
                label.configure(fg_color=theme.ACCENT, text_color="white")
            elif i < self.step:
                label.configure(fg_color=theme.SUCCESS_SOFT, text_color=theme.SUCCESS_TEXT)
            else:
                label.configure(fg_color=theme.FIELD, text_color=theme.MUTED)
        self.back_btn.configure(state="normal" if self.step else "disabled")
        self.next_btn.configure(text=t("finish") if self.step == len(self.page_frames) - 1 else t("next"))
        self.wizard_error.configure(text="")
        if self.step == 1:
            self.monster_entry.focus_set()

    def _next_step(self):
        error = self._validate_step(self.step)
        if error:
            self.wizard_error.configure(text=error)
            return
        if self.step == len(self.page_frames) - 1:
            self._finish_wizard()
        else:
            self._goto_step(self.step + 1)

    def _validate_step(self, step):
        if step == 0 and not self._hwnd():
            return t("err_no_window")
        if step == 1 and not parse_names(self.monster_entry.get()):
            return t("err_no_monster")
        return ""

    def _finish_wizard(self):
        self.cfg.monsters = parse_names(self.monster_entry.get())
        self._apply_inputs()
        self._render_summary()
        self._show_view("dash")
        self._log(t("ready_log"))

    # ======================================================================
    # Dashboard
    # ======================================================================
    def _build_dashboard(self):
        self.dashboard.grid_columnconfigure(1, weight=1)
        self.dashboard.grid_rowconfigure(0, weight=1)

        side = ctk.CTkFrame(self.dashboard, width=340, **theme.CARD_STYLE)
        side.grid(row=0, column=0, sticky="ns", padx=(12, 6), pady=12)
        side.grid_propagate(False)

        # Bottom widgets first so they keep their space.
        self.start_btn = ctk.CTkButton(side, text=f"{t('start')} ({HOTKEY.upper()})", height=54,
                                       font=("", 17, "bold"), corner_radius=theme.RADIUS_PILL, command=self._toggle)
        self.start_btn.pack(fill="x", padx=14, pady=(6, 14), side="bottom")
        self._start_colors = (self.start_btn.cget("fg_color"), self.start_btn.cget("hover_color"))
        self.status = ctk.CTkLabel(side, text=t("state_idle"), anchor="w")
        self.status.pack(fill="x", padx=16, side="bottom")

        head = ctk.CTkFrame(side, fg_color="transparent")
        head.pack(fill="x", padx=14, pady=(16, 0))
        ctk.CTkLabel(head, text="", image=theme.app_icon(40)).pack(side="left")
        ctk.CTkLabel(head, text=APP_TITLE, font=("", 16, "bold")).pack(side="left", padx=(10, 0))

        ctk.CTkLabel(side, text=t("settings_title"), anchor="w", font=("", 14, "bold")).pack(fill="x", padx=14, pady=(18, 6))
        self.summary = ctk.CTkLabel(side, text="", anchor="w", justify="left", wraplength=300,
                                    fg_color=theme.INSET, corner_radius=theme.RADIUS_CONTROL)
        self.summary.pack(fill="x", padx=14, ipady=10)
        ctk.CTkButton(side, text=t("change_settings"), command=lambda: self._goto_step(0), **GRAY).pack(
            fill="x", padx=14, pady=(8, 0))

        self.overlay_switch = ctk.CTkSwitch(side, text=t("overlay_switch"), command=self._on_overlay_switch)
        if self.cfg.overlay:
            self.overlay_switch.select()
        self.overlay_switch.pack(anchor="w", padx=14, pady=(14, 0))

        self.adv_switch = ctk.CTkSwitch(side, text=t("advanced"), command=self._toggle_advanced)
        self.adv_switch.pack(anchor="w", padx=14, pady=(10, 0))
        self.adv = ctk.CTkFrame(side, fg_color="transparent")
        self._build_advanced(self.adv)

        main = ctk.CTkFrame(self.dashboard, **theme.CARD_STYLE)
        main.grid(row=0, column=1, sticky="nsew", padx=(6, 12), pady=12)
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(1, weight=1)
        bar = ctk.CTkFrame(main, fg_color="transparent")
        bar.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 4))
        ctk.CTkLabel(bar, text=t("log_title"), font=("", 14, "bold")).pack(side="left")
        ctk.CTkButton(bar, text=t("about_btn"), width=80, command=self._about, **GRAY).pack(side="right")
        self._language_menu(bar).pack(side="right", padx=(0, 6))
        ctk.CTkButton(bar, text=t("test_scan"), width=110, command=self._test_scan, **GRAY).pack(side="right", padx=(0, 6))
        self.log = ctk.CTkTextbox(main, state="disabled", font=("Consolas", 12))
        self.log.grid(row=1, column=0, sticky="nsew", padx=12, pady=(4, 12))

    def _build_advanced(self, parent):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=(6, 0))
        ctk.CTkLabel(row, text=t("detector"), text_color=theme.MUTED).pack(side="left")
        labels = mode_labels()
        self.mode_menu = ctk.CTkOptionMenu(row, values=list(labels.values()), command=self._on_mode, width=140)
        self.mode_menu.set(labels.get(self.cfg.detector, labels["auto"]))
        self.mode_menu.pack(side="right")
        self.rec_btn = ctk.CTkButton(parent, text=t("rec_stop") if self.recorder.enabled else t("rec_start"),
                                     command=self._toggle_record, **(RED if self.recorder.enabled else GRAY))
        self.rec_btn.pack(fill="x", padx=14, pady=(6, 0))
        self.rec_label = ctk.CTkLabel(parent, text="", anchor="w", text_color=theme.MUTED)
        self.rec_label.pack(fill="x", padx=16)
        self.train_btn = ctk.CTkButton(parent, text=t("train"), command=self._train, **GRAY)
        self.train_btn.pack(fill="x", padx=14, pady=(6, 0))
        self._update_rec_label()

    def _toggle_advanced(self):
        if self.adv_switch.get():
            self.adv.pack(fill="x", after=self.adv_switch)
        else:
            self.adv.pack_forget()

    def _render_summary(self):
        keys = ", ".join(self.cfg.attack_keys) or t("none")
        roam = t("sum_roam_on", n=int(self.cfg.roam_radius)) if self.cfg.roam else t("off")
        lines = [
            f"{t('sum_game')}:  {self.window_menu.get().strip()}",
            f"{t('sum_target')}:  {', '.join(self.cfg.monsters) or '-'}",
            f"{t('sum_attack')}:  {keys}",
            f"{t('sum_roam')}:  {roam}",
        ]
        self.summary.configure(text="\n".join("  " + ln for ln in lines))

    def _refresh_run_button(self):
        if self.engine and self.engine.is_alive():
            self.start_btn.configure(text=f"{t('stop')} ({HOTKEY.upper()})", **RED)
        else:
            fg, hover = self._start_colors
            self.start_btn.configure(text=f"{t('start')} ({HOTKEY.upper()})", fg_color=fg, hover_color=hover)

    # -- game window -------------------------------------------------------
    def _refresh_windows(self):
        found = winutil.enumerate_top_level_windows()
        # Never offer this program's own window as "the game" (its title contains "Silkroad").
        self.windows = {title: hwnd for hwnd, title, _ in found if title.strip() != APP_TITLE}
        titles = list(self.windows) or ["-"]
        self.window_menu.configure(values=titles)
        pick = next((x for x in titles if x == self.cfg.window_title), None) or \
            next((x for x in titles if any(h in x.lower() for h in GAME_HINTS)), titles[0])
        self.window_menu.set(pick)
        self._on_window(pick)

    def _on_window(self, title):
        self.cfg.window_title = title
        name = winutil.character_name_from_title(title)
        if name:
            self.cfg.player_name = name

    def _hwnd(self):
        return self.windows.get(self.window_menu.get())

    # -- reading the name from the screen (optional helper) ----------------
    def _search(self):
        """Look at the screen once and offer the names found, to avoid typos."""
        if self._searching:
            return
        hwnd = self._hwnd()
        if not hwnd:
            self.wizard_error.configure(text=t("err_no_window"))
            return
        self._searching = True
        self.search_btn.configure(state="disabled", text=t("mon_searching"))
        threading.Thread(target=self._search_worker, args=(hwnd,), daemon=True).start()

    def _search_worker(self, hwnd):
        grabber = ScreenGrabber()
        try:
            winutil.bring_window_to_front(hwnd)  # the capture reads screen pixels: nothing may cover the game
            time.sleep(0.4)
            rect = winutil.get_window_client_rect_on_screen(hwnd)
            frames = []
            for _ in range(3):
                frame = grabber.grab_bgr(rect) if rect else None
                if frame is not None:
                    frames.append(frame)
                time.sleep(0.25)
            groups = detect.find_targets(frames, self.cfg, self.cfg.player_name) if frames else []
            self.events.put(("targets", groups))
        except Exception as exc:
            self.events.put(("log", t("scan_error", err=exc)))
            self.events.put(("targets", []))
        finally:
            grabber.close()

    def _show_targets_dialog(self, groups):
        self._searching = False
        if self.search_btn.winfo_exists():
            self.search_btn.configure(state="normal", text=t("mon_read_btn"))
        self.lift()
        win = ctk.CTkToplevel(self)
        win.title(t("found_title") if groups else t("notfound_title"))
        win.attributes("-topmost", True)
        win.transient(self)
        theme.set_icon(win)

        row = ctk.CTkFrame(win, fg_color="transparent")
        row.pack(side="bottom", fill="x", padx=20, pady=16)
        if not groups:
            ctk.CTkLabel(win, wraplength=360, justify="left", text=t("notfound_text")).pack(padx=20, pady=20)
            ctk.CTkButton(row, text=t("retry"), command=lambda: (win.destroy(), self._search())).pack(
                side="left", expand=True, fill="x", padx=(0, 6))
            ctk.CTkButton(row, text=t("close"), command=win.destroy, **GRAY).pack(side="left", expand=True, fill="x")
            self._center(win, 400, 220)
            return

        ctk.CTkLabel(win, text=t("found_header"), font=("", 14, "bold"), justify="left").pack(anchor="w", padx=20, pady=(16, 8))
        checks = []
        for i, g in enumerate(groups):
            var = tk.BooleanVar(value=(i == 0))  # only the most frequent name by default: others may be players
            ctk.CTkCheckBox(win, text=t("found_count", name=g.name, n=g.count), variable=var).pack(anchor="w", padx=24, pady=3)
            checks.append((g.name, var))
        if len(groups) > 1:
            ctk.CTkLabel(win, text=t("found_others"), text_color=theme.MUTED, wraplength=360, justify="left").pack(
                anchor="w", padx=24, pady=(4, 0))

        def accept():
            chosen = [name for name, var in checks if var.get()]
            win.destroy()
            if chosen:
                self.monster_entry.delete(0, "end")
                self.monster_entry.insert(0, ", ".join(chosen))

        ctk.CTkButton(row, text=t("use_this"), command=accept).pack(side="left", expand=True, fill="x", padx=(0, 6))
        ctk.CTkButton(row, text=t("cancel"), command=win.destroy, **GRAY).pack(side="left", expand=True, fill="x")
        self._center(win, 400, 210 + 34 * len(groups))

    # -- test scan ----------------------------------------------------------
    def _grab_once(self):
        hwnd = self._hwnd()
        rect = hwnd and winutil.get_window_client_rect_on_screen(hwnd)
        if not rect:
            self._log(t("scan_window_missing"))
            return None
        grabber = ScreenGrabber()
        try:
            return grabber.grab_bgr(rect)
        finally:
            grabber.close()

    def _test_scan(self):
        """Look once, attack nothing, and report what the bot recognises."""
        if not self.cfg.monsters:
            self._log(t("scan_need_target"))
            return
        frame = self._grab_once()
        if frame is None:
            return
        dets = detect.detect(frame, self.cfg)
        self.ostate.update_scan(frame.shape, dets)
        self.ostate.flash(3.0)
        mode = detect.active_mode(self.cfg).upper()
        if dets:
            names = ", ".join(sorted({d.name for d in dets}))
            self._log(t("scan_found", mode=mode, n=len(dets), names=names))
        else:
            self._log(t("scan_none", mode=mode))

    # -- run control -----------------------------------------------------
    def _apply_inputs(self):
        self.cfg.attack_keys = [k.strip() for k in self.attack_entry.get().split(",") if k.strip()]
        self.cfg.roam = bool(self.roam_switch.get())
        self.cfg.roam_radius = float(round(self.radius_slider.get()))
        self.cfg.attack_interval = round(float(self.speed_slider.get()), 1)
        self.cfg.overlay = bool(self.overlay_switch.get()) if hasattr(self, "overlay_switch") else self.cfg.overlay
        self.cfg.save()

    def _toggle(self):
        if self.engine and self.engine.is_alive():
            self.engine.stop()
            return
        hwnd = self._hwnd()
        if not hwnd or not winutil.is_window_valid(hwnd):
            self._log(t("scan_window_missing"))
            return
        if not self.cfg.monsters:
            self._goto_step(1)
            return
        self._start(hwnd)

    def _start(self, hwnd):
        if self.engine and self.engine.is_alive():
            return
        self._apply_inputs()
        if not self.cfg.attack_keys:
            self._log(t("no_attack_keys"))
        self.engine = BotEngine(
            self.cfg, hwnd,
            on_log=lambda m: self.events.put(("log", m)),
            on_state=lambda s: self.events.put(("state", s)),
            on_frame=lambda f, d: self.ostate.update_scan(f.shape, d),
            on_roam=self.ostate.update_roam,
            recorder=self.recorder,
        )
        self.engine.start()
        self._refresh_run_button()

    def _register_hotkey(self):
        try:
            import keyboard
            keyboard.add_hotkey(HOTKEY, lambda: self.events.put(("toggle", None)))
        except Exception:
            self._log(t("hotkey_failed"))

    # -- on-screen markers -----------------------------------------------
    def _on_overlay_switch(self):
        self.cfg.overlay = bool(self.overlay_switch.get())
        self.cfg.save()
        if not self.cfg.overlay:
            self.overlay.hide()

    def _update_overlay(self):
        """Draw boxes over the game while the bot works (or briefly after a test scan)."""
        hwnd = self._hwnd()
        running = bool(self.engine and self.engine.is_alive())
        flashing = time.time() < self.ostate.flash_until
        # Never while recording: the boxes would end up in the saved training frames.
        if not self.cfg.overlay or self.recorder.enabled or not hwnd or not (running or flashing):
            self.overlay.hide()
            return
        rect = winutil.get_window_client_rect_on_screen(hwnd)
        visible = winutil.is_window_valid(hwnd) and not winutil.is_minimized(hwnd)
        # While the bot runs the game is in front; if the user switched to another app, stay out of the way.
        if not rect or not visible or (not flashing and not winutil.is_foreground(hwnd)):
            self.overlay.hide()
            return
        target = self.engine.target_pos if running else None
        self.overlay.draw(rect, self.ostate.shapes(target))

    # -- dialogs ---------------------------------------------------------------
    def _center(self, win, width, height):
        """Open a dialog in the middle of the screen (width/height in unscaled px, like geometry())."""
        win.geometry(f"{width}x{height}")
        win.update()  # create the real window so its outer frame (title bar, borders) can be measured
        rect = winutil.window_rect(win.winfo_id())
        if rect:
            outer_w, outer_h = rect[2] - rect[0], rect[3] - rect[1]
        else:
            outer_w, outer_h = win.winfo_width(), win.winfo_height()
        x = max(0, (win.winfo_screenwidth() - outer_w) // 2)
        y = max(0, (win.winfo_screenheight() - outer_h) // 2)
        win.geometry(f"+{x}+{y}")

    def _about(self):
        win = ctk.CTkToplevel(self)
        win.title(t("about_title"))
        win.attributes("-topmost", True)
        win.transient(self)
        theme.set_icon(win)
        ctk.CTkLabel(win, text="", image=theme.app_icon(96)).pack(pady=(22, 0))
        ctk.CTkLabel(win, text=APP_TITLE, font=("", 20, "bold")).pack(pady=(8, 0))
        ctk.CTkLabel(win, text=t("about_version", v=__version__), text_color=theme.MUTED).pack()
        ctk.CTkLabel(win, text=t("about_desc"), justify="center", wraplength=360).pack(pady=(12, 0))
        ctk.CTkLabel(win, text=t("about_dev", name=__author__), font=("", 13, "bold")).pack(pady=(14, 6))
        for text, url in (("GitHub: sametuca", GITHUB_URL), (CONTACT_EMAIL, "mailto:" + CONTACT_EMAIL),
                          (t("about_project"), REPO_URL)):
            ctk.CTkButton(win, text=text, width=220, command=lambda u=url: webbrowser.open(u), **GRAY).pack(pady=3)
        ctk.CTkLabel(win, text=t("about_license"), text_color=theme.MUTED).pack(pady=(10, 0))
        self._center(win, 420, 450)

    # -- advanced: detector mode, recording, training ---------------------
    def _on_mode(self, label):
        self.cfg.detector = next(k for k, v in mode_labels().items() if v == label)
        self.cfg.save()

    def _toggle_record(self):
        if self.recorder.enabled:
            self.recorder.enabled = False
            self.rec_btn.configure(text=t("rec_start"), **GRAY)
            self._log(t("rec_stopped_log", n=self.recorder.saved))
        else:
            if not self.cfg.monsters:
                self._log(t("rec_need_target"))
                return
            hwnd = self._hwnd()
            if not hwnd:
                self._log(t("scan_window_missing"))
                return
            self.recorder.enabled = True
            self.rec_btn.configure(text=t("rec_stop"), **RED)
            if self.engine and self.engine.is_alive():
                self._log(t("rec_while_hunting"))
            else:
                self.rec_thread = RecorderThread(
                    self.cfg, hwnd, self.recorder,
                    on_log=lambda m: self.events.put(("log", m)))
                self.rec_thread.start()
        self._update_rec_label()

    def _update_rec_label(self):
        self.rec_label.configure(text=t("rec_count", n=self.recorder.saved))

    def _train(self):
        if getattr(sys, "frozen", False):
            self._log(t("train_frozen"))
            return
        if self.recorder.saved < 10:
            self._log(t("train_more_frames", n=self.recorder.saved))
            return
        self.train_btn.configure(state="disabled", text=t("training"))
        self._log(t("train_started"))
        threading.Thread(target=self._train_worker, daemon=True).start()

    def _train_worker(self):
        put = lambda m: self.events.put(("log", m))  # noqa: E731
        try:
            proc = subprocess.Popen([sys.executable, "-m", "srbot.train"], cwd=app_dir(),
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            buf = b""
            while True:
                chunk = proc.stdout.read1(4096)
                if not chunk:
                    break
                buf += chunk
                *lines, buf = re.split(rb"[\r\n]", buf)
                for raw in lines:
                    text = ANSI.sub("", raw.decode("utf-8", "replace")).strip()
                    m = EPOCH_DONE.search(text)
                    if m:
                        put(f"Epoch {m.group(1)}")
                    elif text.startswith(("Veri:", "Model hazır")) or "SystemExit" in text:
                        put(text)
            code = proc.wait()
            put(t("train_done") if code == 0 else t("train_failed", code=code))
        except Exception as exc:
            put(t("train_error", err=exc))
        finally:
            self.events.put(("train_done", None))

    # -- event loop ------------------------------------------------------
    def _poll(self):
        while not self.events.empty():
            kind, payload = self.events.get()
            if kind == "log":
                self._log(payload)
            elif kind == "state":
                self.status.configure(text=t("state_" + payload.name.lower()))
                if payload is State.IDLE:
                    self._refresh_run_button()
            elif kind == "targets":
                self._show_targets_dialog(payload)
            elif kind == "train_done":
                self.train_btn.configure(state="normal", text=t("train"))
            elif kind == "toggle":
                if self.view == "dash":  # the hotkey only drives the dashboard, not the wizard
                    self._toggle()
        self._update_rec_label()
        self._update_overlay()
        self.after(100, self._poll)

    def _log(self, message):
        self.log.configure(state="normal")
        self.log.insert("end", f"[{time.strftime('%H:%M:%S')}] {message}\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _shutdown(self):
        if self.engine:
            self.engine.stop()
        self.recorder.enabled = False
        self.overlay.close()
        self.destroy()

    def _on_close(self):
        self._apply_inputs()
        self._shutdown()
