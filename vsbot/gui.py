"""Tkinter GUI: a 4-step wizard (Window -> Monsters -> Keys -> Start).

The hunt region is just the selected game window's client area - no
separate "draw a box" step for it. Advanced knobs (detection mode, HP bar,
buffs, thresholds) live in a collapsed panel on the last page so the
default path stays short.
"""

import os
import threading
import time
import tkinter as tk
import tkinter.font as tkfont
from tkinter import messagebox, simpledialog, ttk

import sv_ttk

from . import color_detect, ocr, tesseract_installer, winutil
from .bot_engine import BotConfig, BotEngine
from .detection import base_monster_name, load_monster_templates, sanitize_template_basename
from .i18n import Translator, get_language, save_language
from .paths import data_path
from .reference_match import ReferenceMatcher
from .region_select import pick_screen_point, select_screen_region

MONSTERS_DIR = data_path("monsters")

STEP_KEYS = ["step1_title", "step2_title", "step3_title", "step4_title"]
PAGE_WINDOW, PAGE_MONSTERS, PAGE_KEYS, PAGE_START = range(4)

ACCENT = "#3b82f6"
ACCENT_DIM = "#93a3b8"
# sv_ttk's dark theme doesn't reach plain tk widgets (Text/Listbox aren't
# ttk) - theme those by hand so they don't show up as a jarring bright
# white box in the middle of an otherwise dark window.
DARK_WIDGET_BG = "#202020"
DARK_WIDGET_FG = "#e8e8e8"


def _enlarge_default_fonts(root):
    """sv_ttk's flat dark theme still inherits Tk's tiny 9pt default fonts -
    bump every named default font up so the whole app reads comfortably at
    a glance instead of looking like a dense old-school Windows dialog."""
    for name, size, weight in (
        ("TkDefaultFont", 11, "normal"), ("TkTextFont", 11, "normal"),
        ("TkHeadingFont", 12, "bold"), ("TkMenuFont", 11, "normal"),
        ("TkFixedFont", 11, "normal"),
    ):
        try:
            f = tkfont.nametofont(name)
            f.configure(size=size, weight=weight)
        except tk.TclError:
            pass


def _configure_custom_styles():
    style = ttk.Style()
    style.configure("TLabelframe", padding=14)
    style.configure("TLabelframe.Label", font=("Segoe UI", 11, "bold"))
    style.configure("TButton", padding=(14, 8))
    style.configure("Nav.TButton", padding=(22, 14), font=("Segoe UI", 12, "bold"))
    style.configure("Big.Accent.TButton", padding=(22, 14), font=("Segoe UI", 12, "bold"))
    style.configure("StepCurrent.TLabel", font=("Segoe UI", 12, "bold"), foreground=ACCENT)
    style.configure("StepDone.TLabel", font=("Segoe UI", 11), foreground="#4ade80")
    style.configure("StepTodo.TLabel", font=("Segoe UI", 11), foreground=ACCENT_DIM)
    style.configure("Hint.TLabel", font=("Segoe UI", 10), foreground=ACCENT_DIM)
    style.configure("Title.TLabel", font=("Segoe UI", 16, "bold"))


class LanguageDialog(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Language / Dil")
        self.resizable(False, False)
        self.choice = None
        self.attributes("-topmost", True)
        self.grab_set()

        frame = ttk.Frame(self, padding=24)
        frame.pack()
        ttk.Label(frame, text="Select Language / Dil Seçin", font=("Segoe UI", 12, "bold")).pack(pady=(0, 16))

        btns = ttk.Frame(frame)
        btns.pack()
        ttk.Button(btns, text="🇬🇧 English", width=16, command=lambda: self._pick("EN")).pack(side="left", padx=6)
        ttk.Button(btns, text="🇹🇷 Türkçe", width=16, command=lambda: self._pick("TR")).pack(side="left", padx=6)

        self.protocol("WM_DELETE_WINDOW", lambda: self._pick("EN"))

    def _pick(self, lang):
        self.choice = lang
        self.destroy()


class BotGUI:
    def __init__(self, root):
        winutil.try_set_process_dpi_aware()
        self.root = root

        sv_ttk.set_theme("dark")
        _enlarge_default_fonts(root)
        _configure_custom_styles()

        lang = get_language()
        if lang is None:
            dlg = LanguageDialog(root)
            root.wait_window(dlg)
            lang = dlg.choice or "EN"
            save_language(lang)
        self.t = Translator(lang)

        self.root.title(self.t("app_title"))
        self.root.geometry("720x840")
        self.root.minsize(660, 700)

        self.hunt_region = None
        self.selected_hwnd = None
        self.selected_window_title = None
        self.monsters = []  # [{"name": str, "path": str}] added via the wizard this session

        self.mode_labels = {
            "hybrid": self.t("mode_hybrid"), "color": self.t("mode_color"),
            "template": self.t("mode_template"), "ocr": self.t("mode_ocr"),
        }

        self.config = BotConfig(monsters_dir=MONSTERS_DIR)
        self.engine = BotEngine(self.config, log_fn=self._log_threadsafe)
        self.reference_matcher = ReferenceMatcher()
        self.engine.reference_matcher = self.reference_matcher

        os.makedirs(MONSTERS_DIR, exist_ok=True)
        self.current_page = PAGE_WINDOW
        self._build_ui()
        self._load_existing_monsters()
        self._register_stop_hotkey()
        self._tick_status()
        self._show_page(PAGE_WINDOW)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_ui(self):
        root_frame = ttk.Frame(self.root, padding=20)
        root_frame.pack(fill="both", expand=True)

        # -- step indicator ----------------------------------------------------
        step_bar = ttk.Frame(root_frame)
        step_bar.pack(fill="x", pady=(0, 20))
        self.step_labels = []
        step_glyphs = ["①", "②", "③", "④"]
        for i, key in enumerate(STEP_KEYS):
            lbl = ttk.Label(step_bar, text=f"{step_glyphs[i]} {self.t(key)}")
            lbl.pack(side="left")
            self.step_labels.append(lbl)
            if i < len(STEP_KEYS) - 1:
                ttk.Label(step_bar, text="   ", style="Hint.TLabel").pack(side="left")

        # -- page container ------------------------------------------------
        # Sized to its content, not the window - otherwise short pages
        # (step 1, 2, 4) leave a huge empty gap before the nav buttons.
        # The leftover room goes to the log below instead, which is
        # actually useful to see more of.
        self.page_container = ttk.Frame(root_frame)
        self.page_container.pack(fill="x")

        self.page_frames = [ttk.Frame(self.page_container) for _ in range(4)]
        self._build_page_window(self.page_frames[PAGE_WINDOW])
        self._build_page_monsters(self.page_frames[PAGE_MONSTERS])
        self._build_page_keys(self.page_frames[PAGE_KEYS])
        self._build_page_start(self.page_frames[PAGE_START])

        # -- navigation ---------------------------------------------------------
        nav = ttk.Frame(root_frame)
        nav.pack(fill="x", pady=(16, 6))
        self.back_btn = ttk.Button(nav, text=self.t("back"), command=self._go_back, style="Nav.TButton")
        self.back_btn.pack(side="left")
        self.next_btn = ttk.Button(nav, text=self.t("next"), command=self._go_next, style="Big.Accent.TButton")
        self.next_btn.pack(side="right")

        ttk.Label(root_frame, text=self.t("hotkey_hint"), style="Hint.TLabel").pack(anchor="w", pady=(0, 4))

        # -- log (always visible) ------------------------------------------
        log_frame = ttk.LabelFrame(root_frame, text=self.t("log"), padding=4)
        log_frame.pack(fill="x", pady=4)
        self.log_text = tk.Text(log_frame, height=5, state="disabled", wrap="word",
                                 bg=DARK_WIDGET_BG, fg=DARK_WIDGET_FG, insertbackground=DARK_WIDGET_FG,
                                 selectbackground=ACCENT, relief="flat", borderwidth=0, font=("Segoe UI", 10))
        self.log_text.pack(fill="both", expand=True, side="left")
        scroll = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scroll.pack(side="right", fill="y")
        self.log_text.configure(yscrollcommand=scroll.set)

    # -- page 1: window ----------------------------------------------------------
    def _build_page_window(self, parent):
        ttk.Label(parent, text=self.t("step1_help"), wraplength=640, justify="left").pack(anchor="w", pady=(0, 16))
        ttk.Button(parent, text=self.t("select_window"), command=self._select_window,
                   style="Nav.TButton").pack(anchor="w")
        self.window_label = ttk.Label(parent, text=self.t("no_window_selected"), font=("Segoe UI", 12, "bold"))
        self.window_label.pack(anchor="w", pady=(12, 0))

        ttk.Separator(parent).pack(fill="x", pady=20)
        self.keypress_only_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(parent, text=self.t("keypress_only"), variable=self.keypress_only_var).pack(anchor="w")

    # -- page 2: monsters --------------------------------------------------------
    def _build_page_monsters(self, parent):
        ttk.Label(parent, text=self.t("step2_help"), wraplength=640, justify="left").pack(anchor="w", pady=(0, 16))
        ttk.Button(parent, text=self.t("add_monster"), command=self._add_monster,
                   style="Nav.TButton").pack(anchor="w")

        list_frame = ttk.Frame(parent)
        list_frame.pack(fill="both", expand=True, pady=(14, 0))
        self.monster_listbox = tk.Listbox(list_frame, height=8, font=("Segoe UI", 11),
                                           bg=DARK_WIDGET_BG, fg=DARK_WIDGET_FG,
                                           selectbackground=ACCENT, relief="flat", borderwidth=0,
                                           highlightthickness=0)
        self.monster_listbox.pack(side="left", fill="both", expand=True)
        mscroll = ttk.Scrollbar(list_frame, command=self.monster_listbox.yview)
        mscroll.pack(side="right", fill="y")
        self.monster_listbox.configure(yscrollcommand=mscroll.set)

        ttk.Button(parent, text=self.t("remove_monster"), command=self._remove_selected_monster).pack(
            anchor="w", pady=(6, 0))
        self.monster_count_label = ttk.Label(parent, text=self.t("no_monsters_added"))
        self.monster_count_label.pack(anchor="w", pady=(6, 0))

    # -- page 3: keys -------------------------------------------------------------
    def _build_page_keys(self, parent):
        ttk.Label(parent, text=self.t("step3_help"), wraplength=640, justify="left").pack(anchor="w", pady=(0, 16))
        self.skill_keys_var = tk.StringVar(value="1,2,3,4")
        ttk.Entry(parent, textvariable=self.skill_keys_var, font=("Segoe UI", 13), width=30).pack(anchor="w")

        interval_frame = ttk.Frame(parent)
        interval_frame.pack(fill="x", pady=(20, 0))
        self.mob_interval_var = self._add_slider(interval_frame, 0, self.t("mob_interval"), 0.1, 2.0, 0.2)
        interval_frame.columnconfigure(1, weight=1)

    # -- page 4: start + advanced -------------------------------------------------
    def _build_page_start(self, parent):
        self.summary_label = ttk.Label(parent, text="", justify="left", style="Hint.TLabel")
        self.summary_label.pack(anchor="w", pady=(0, 10))

        controls = ttk.Frame(parent)
        controls.pack(fill="x", pady=4)
        self.start_btn = ttk.Button(controls, text=self.t("start"), command=self._start, style="Big.Accent.TButton")
        self.start_btn.pack(side="left")
        self.stop_btn = ttk.Button(controls, text=self.t("stop"), command=self._stop, state="disabled",
                                    style="Nav.TButton")
        self.stop_btn.pack(side="left", padx=8)

        status_frame = ttk.Frame(parent)
        status_frame.pack(fill="x", pady=4)
        self.status_label = ttk.Label(status_frame, text=self.t("status_idle"), font=("Segoe UI", 12, "bold"))
        self.status_label.pack(side="left")
        self.kills_label = ttk.Label(status_frame, text=self.t("kills", n=0))
        self.kills_label.pack(side="left", padx=12)
        self.runtime_label = ttk.Label(status_frame, text=self.t("runtime", t="0:00"))
        self.runtime_label.pack(side="left", padx=12)

        self.advanced_visible = tk.BooleanVar(value=False)
        adv_toggle = ttk.Checkbutton(parent, text=self.t("advanced_settings"), variable=self.advanced_visible,
                                      command=self._toggle_advanced, style="Toolbutton")
        adv_toggle.pack(anchor="w", pady=(14, 4))

        # Advanced settings can get tall (detection + keys + HP
        # bar + buffs) - give this section its own bounded, scrollable area
        # instead of letting it push the nav/log off the bottom of the
        # window with no way to reach them.
        self.advanced_frame = ttk.Frame(parent)
        adv_canvas = tk.Canvas(self.advanced_frame, height=320, highlightthickness=0,
                                bg=DARK_WIDGET_BG, bd=0)
        adv_scroll = ttk.Scrollbar(self.advanced_frame, orient="vertical", command=adv_canvas.yview)
        adv_canvas.configure(yscrollcommand=adv_scroll.set)
        adv_canvas.pack(side="left", fill="both", expand=True)
        adv_scroll.pack(side="right", fill="y")

        adv_inner = ttk.Frame(adv_canvas)
        adv_window = adv_canvas.create_window((0, 0), window=adv_inner, anchor="nw")
        adv_inner.bind("<Configure>", lambda _e: adv_canvas.configure(scrollregion=adv_canvas.bbox("all")))
        adv_canvas.bind("<Configure>", lambda e: adv_canvas.itemconfig(adv_window, width=e.width))
        adv_canvas.bind("<Enter>", lambda _e: adv_canvas.bind_all(
            "<MouseWheel>", lambda ev: adv_canvas.yview_scroll(int(-1 * (ev.delta / 120)), "units")))
        adv_canvas.bind("<Leave>", lambda _e: adv_canvas.unbind_all("<MouseWheel>"))

        self._build_advanced_panel(adv_inner)
        # not packed initially - _toggle_advanced() handles visibility

    def _build_advanced_panel(self, parent):
        det_frame = ttk.LabelFrame(parent, text=self.t("detection_mode"), padding=8)
        det_frame.pack(fill="x", pady=4)
        self.mode_var = tk.StringVar(value=self.mode_labels["color"])
        ttk.Combobox(det_frame, textvariable=self.mode_var, state="readonly",
                     values=list(self.mode_labels.values()), width=36).pack(anchor="w")

        ocr_row = ttk.Frame(det_frame)
        ocr_row.pack(fill="x", pady=(6, 0))
        self.ocr_status_var = tk.StringVar()
        ttk.Label(ocr_row, textvariable=self.ocr_status_var, style="Hint.TLabel",
                  wraplength=340, justify="left").pack(side="left")
        self.install_tesseract_btn = ttk.Button(
            ocr_row, text=self.t("install_tesseract"), command=self._install_tesseract)
        self._refresh_ocr_status()

        color_frame = ttk.Frame(det_frame)
        color_frame.pack(fill="x", pady=(6, 0))
        ttk.Button(color_frame, text=self.t("calibrate_color"), command=self._calibrate_color).pack(side="left")
        self.color_label = ttk.Label(color_frame, text=self._hsv_text(self.config.nameplate_hsv))
        self.color_label.pack(side="left", padx=10)

        ttk.Label(parent, text=self.t("target_monsters")).pack(anchor="w", pady=(8, 0))
        self.target_monsters_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.target_monsters_var).pack(fill="x")

        toggles = ttk.Frame(parent)
        toggles.pack(fill="x", pady=6)
        self.auto_tab_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(toggles, text=self.t("auto_tab"), variable=self.auto_tab_var).pack(anchor="w")

        keys_frame = ttk.LabelFrame(parent, text=self.t("settings"), padding=8)
        keys_frame.pack(fill="x", pady=4)
        ttk.Label(keys_frame, text=self.t("loot_key")).grid(row=0, column=0, sticky="w")
        self.loot_key_var = tk.StringVar(value="")
        ttk.Entry(keys_frame, textvariable=self.loot_key_var, width=20).grid(row=0, column=1, sticky="ew", padx=6)

        # (mob_interval - "wait between monsters" - lives on the Keys wizard
        # page since it's the one timing knob most people actually want to
        # tune; the rest stay here for people who want finer control.)
        self.skill_interval_var = self._add_slider(keys_frame, 1, self.t("skill_interval"), 0.05, 1.0, 0.15)
        self.auto_tab_interval_var = self._add_slider(keys_frame, 2, self.t("auto_tab_interval"), 0.5, 10.0, 3.0)
        self.threshold_var = self._add_slider(keys_frame, 3, self.t("template_threshold"), 0.10, 0.90, 0.40)
        self.reclick_var = self._add_slider(keys_frame, 4, self.t("reclick_lockout"), 0.0, 8.0, 2.5)
        keys_frame.columnconfigure(1, weight=1)

        ttk.Label(keys_frame, text=self.t("input_method")).grid(row=5, column=0, sticky="w", pady=(6, 0))
        self.input_method_var = tk.StringVar(value="auto")
        ttk.Combobox(keys_frame, textvariable=self.input_method_var, state="readonly",
                     values=["auto", "sendinput", "pydirectinput", "keyboard"]).grid(
            row=5, column=1, sticky="ew", padx=6, pady=(6, 0))

        hp_frame = ttk.LabelFrame(parent, text=self.t("hp_bar"), padding=8)
        hp_frame.pack(fill="x", pady=4)
        hp_btns = ttk.Frame(hp_frame)
        hp_btns.pack(fill="x")
        ttk.Button(hp_btns, text=self.t("set_hp_bar"), command=self._set_hp_bar).pack(side="left")
        ttk.Button(hp_btns, text=self.t("clear"), command=self._clear_hp_bar).pack(side="left", padx=4)
        self.hp_bar_label = ttk.Label(hp_frame, text=self.t("hp_bar_not_set"))
        self.hp_bar_label.pack(anchor="w", pady=(4, 0))

        buff_frame = ttk.LabelFrame(parent, text=self.t("buffs"), padding=8)
        buff_frame.pack(fill="x", pady=4)
        self.buffs_enabled_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(buff_frame, text=self.t("enable_buffs"), variable=self.buffs_enabled_var).grid(
            row=0, column=0, columnspan=2, sticky="w")
        ttk.Label(buff_frame, text=self.t("buff_keys")).grid(row=1, column=0, sticky="w")
        self.buff_keys_var = tk.StringVar(value="")
        ttk.Entry(buff_frame, textvariable=self.buff_keys_var).grid(row=1, column=1, sticky="ew", padx=6)
        self.buff_interval_var = self._add_slider(buff_frame, 2, self.t("buff_interval"), 5.0, 600.0, 60.0)
        buff_frame.columnconfigure(1, weight=1)

    def _toggle_advanced(self):
        if self.advanced_visible.get():
            self.advanced_frame.pack(fill="both", expand=True)
        else:
            self.advanced_frame.pack_forget()

    def _add_slider(self, parent, row, label, lo, hi, default):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=2)
        var = tk.DoubleVar(value=default)
        value_label = ttk.Label(parent, text=f"{default:.2f}", width=6)

        def on_change(_evt=None):
            value_label.configure(text=f"{var.get():.2f}")

        scale = ttk.Scale(parent, from_=lo, to=hi, variable=var, orient="horizontal", command=on_change)
        scale.grid(row=row, column=1, sticky="ew", padx=6, pady=2)
        value_label.grid(row=row, column=2, sticky="w")
        return var

    @staticmethod
    def _hsv_text(hsv_range):
        (h0, s0, v0), (h1, s1, v1) = hsv_range
        return f"H{h0}-{h1} S{s0}-{s1} V{v0}-{v1}"

    # ------------------------------------------------------------------
    # wizard navigation
    # ------------------------------------------------------------------
    def _show_page(self, index):
        for frame in self.page_frames:
            frame.pack_forget()
        self.page_frames[index].pack(fill="x")
        self.current_page = index

        for i, lbl in enumerate(self.step_labels):
            if i == index:
                lbl.configure(style="StepCurrent.TLabel")
            elif i < index:
                lbl.configure(style="StepDone.TLabel")
            else:
                lbl.configure(style="StepTodo.TLabel")

        self.back_btn.configure(state=("disabled" if index == PAGE_WINDOW else "normal"))
        if index == PAGE_START:
            self.next_btn.pack_forget()
            self._update_summary()
        else:
            self.next_btn.pack(side="right")

    def _skip_monsters(self):
        return self.keypress_only_var.get()

    def _go_next(self):
        if self.current_page == PAGE_WINDOW:
            if self.selected_hwnd is None:
                messagebox.showwarning(self.t("next"), self.t("err_no_window"))
                return
            self._show_page(PAGE_KEYS if self._skip_monsters() else PAGE_MONSTERS)
            return

        if self.current_page == PAGE_MONSTERS:
            if not self.monsters:
                messagebox.showwarning(self.t("next"), self.t("err_no_monsters"))
                return
            self._show_page(PAGE_KEYS)
            return

        if self.current_page == PAGE_KEYS:
            if not self.skill_keys_var.get().strip():
                messagebox.showwarning(self.t("next"), self.t("err_no_keys"))
                return
            self._show_page(PAGE_START)
            return

    def _go_back(self):
        if self.current_page == PAGE_KEYS:
            self._show_page(PAGE_WINDOW if self._skip_monsters() else PAGE_MONSTERS)
            return
        if self.current_page == PAGE_START:
            self._show_page(PAGE_KEYS)
            return
        if self.current_page > PAGE_WINDOW:
            self._show_page(self.current_page - 1)

    def _update_summary(self):
        window_txt = self.selected_window_title or "-"
        monsters_txt = ", ".join(m["name"] for m in self.monsters) if self.monsters else "-"
        keys_txt = self.skill_keys_var.get()

        lines = [
            self.t("summary_window", v=window_txt),
            self.t("summary_monsters", v=monsters_txt),
            self.t("summary_keys", v=keys_txt),
            "",
            self.t("ready_to_start"),
        ]
        self.summary_label.configure(text="\n".join(lines))

    # ------------------------------------------------------------------
    # window / region
    # ------------------------------------------------------------------
    def _select_window(self):
        windows = winutil.enumerate_top_level_windows()
        if not windows:
            messagebox.showinfo(self.t("select_window"), "No windows found.")
            return

        picker = tk.Toplevel(self.root)
        picker.title(self.t("select_window"))
        picker.geometry("460x400")
        listbox = tk.Listbox(picker, font=("Segoe UI", 11), bg=DARK_WIDGET_BG, fg=DARK_WIDGET_FG,
                              selectbackground=ACCENT, relief="flat", borderwidth=0, highlightthickness=0)
        listbox.pack(fill="both", expand=True, padx=10, pady=10)
        for _hwnd, title, _rect in windows:
            listbox.insert("end", title)

        def confirm():
            sel = listbox.curselection()
            if not sel:
                return
            hwnd, title, fallback_rect = windows[sel[0]]
            self.selected_hwnd = hwnd
            self.selected_window_title = title
            # Hunt region = the window's own client area - no separate
            # "draw a box" step; falls back to the outer window rect if the
            # client-area lookup fails for some reason.
            self.hunt_region = winutil.get_window_client_rect_on_screen(hwnd) or fallback_rect
            self.config.hunt_region = self.hunt_region
            self.window_label.configure(text=title)
            picker.destroy()

        listbox.bind("<Double-Button-1>", lambda _e: confirm())
        ttk.Button(picker, text="OK", command=confirm, style="Nav.TButton").pack(pady=(0, 10))

    def _bring_selected_window_front(self):
        if self.selected_hwnd is not None:
            winutil.bring_window_to_front(self.selected_hwnd)
            time.sleep(0.2)

    # ------------------------------------------------------------------
    # monsters (color calibration only - no template file)
    # ------------------------------------------------------------------
    def _add_monster(self):
        """One box → two independent detection signals, no template file:

        1. Color calibration (HSV) - fast, primary signal.
        2. ORB reference (reference_match.py) - a completely different,
           color-blind signal (local gradient patterns) that bot_engine
           falls back to whenever color finds nothing that cycle. Doesn't
           need a good crop the way color does; even a so-so one usually
           yields enough keypoints to be useful.

        Both come from the exact same drag - no extra step, no separate
        "training" action.
        """
        self._bring_selected_window_front()
        rect = select_screen_region(self.root, self.t("template_wizard_hint"))
        if rect is None:
            return

        name = simpledialog.askstring(self.t("add_monster"), self.t("template_name_prompt"), parent=self.root)
        if not name:
            return
        base = sanitize_template_basename(name)

        try:
            img = winutil.grab_screen(rect)
        except Exception as exc:
            messagebox.showerror(self.t("add_monster"), str(exc))
            return

        status = "none"
        try:
            import numpy as np
            bgr = np.array(img)[:, :, ::-1]

            hsv_range = color_detect.dominant_text_hsv(bgr)
            if hsv_range is not None:
                self.config.nameplate_hsv = hsv_range
                if hasattr(self, "color_label"):
                    self.color_label.configure(text=self._hsv_text(hsv_range))
                # sanity check: does the range we just derived even find
                # its own source crop again? If not, this is visibly
                # flagged right away instead of the user discovering it
                # during live hunting.
                status = "ok" if color_detect.find_candidates(bgr, hsv_range) else "weak"

            orb_ok = self.reference_matcher.add(base, bgr)
            self._log(("🧩 " if orb_ok else "🧩⚠ ") + self.t("orb_added" if orb_ok else "orb_too_plain", name=base))
        except Exception:
            pass  # calibration failing shouldn't block adding the name

        self._register_monster(base, None, status=status)

    _STATUS_ICON = {"ok": "✅", "weak": "⚠", "none": "⚠"}
    _STATUS_COLOR = {"ok": "#4ade80", "weak": "#facc15", "none": "#f87171"}

    def _register_monster(self, name, path, status=None):
        if any(m["name"] == name for m in self.monsters):
            return
        self.monsters.append({"name": name, "path": path, "status": status})
        icon = self._STATUS_ICON.get(status, "")
        self.monster_listbox.insert("end", f"{icon} {name}".strip())
        if status in self._STATUS_COLOR:
            self.monster_listbox.itemconfig(self.monster_listbox.size() - 1, fg=self._STATUS_COLOR[status])
        self._sync_target_monsters()
        self.monster_count_label.configure(text=self.t("monsters_added", n=len(self.monsters)))
        status_key = {"ok": "color_calibration_ok", "weak": "color_calibration_weak",
                      "none": "color_calibration_none"}.get(status)
        if status_key:
            self._log(f"{icon} {name} - {self.t(status_key)}")

    def _remove_selected_monster(self):
        sel = self.monster_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        removed_name = self.monsters[idx]["name"]
        del self.monsters[idx]
        self.monster_listbox.delete(idx)
        self.reference_matcher.remove(removed_name)
        self._sync_target_monsters()
        text = self.t("monsters_added", n=len(self.monsters)) if self.monsters else self.t("no_monsters_added")
        self.monster_count_label.configure(text=text)

    def _sync_target_monsters(self):
        if hasattr(self, "target_monsters_var"):
            self.target_monsters_var.set(",".join(m["name"] for m in self.monsters))

    def _load_existing_monsters(self):
        """Pre-fill step 3 with templates already on disk from a previous run.

        Variant files (wolf__v2.png, wolf__v3.png, ...) collapse into one
        "wolf" list entry, same as they do for matching.
        """
        for tpl in load_monster_templates(MONSTERS_DIR):
            name = base_monster_name(tpl.name)
            self._register_monster(name, tpl.path)
            try:
                import cv2
                self.reference_matcher.add(name, cv2.cvtColor(tpl.gray, cv2.COLOR_GRAY2BGR))
            except Exception:
                pass  # ORB backfill is a bonus - color calibration still needs a fresh capture either way

    # ------------------------------------------------------------------
    # OCR engine status / installer
    # ------------------------------------------------------------------
    def _refresh_ocr_status(self):
        engine = ocr.engine_name()
        if engine == "tesseract":
            self.ocr_status_var.set(self.t("ocr_engine_tesseract"))
            self.install_tesseract_btn.pack_forget()
        elif engine == "easyocr":
            self.ocr_status_var.set(self.t("ocr_engine_easyocr"))
            self.install_tesseract_btn.pack_forget()
        else:
            self.ocr_status_var.set(self.t("ocr_unavailable"))
            self.install_tesseract_btn.pack(side="left", padx=4)

    def _install_tesseract(self):
        if not messagebox.askyesno(self.t("install_tesseract"), self.t("install_tesseract_confirm")):
            return
        self.install_tesseract_btn.configure(state="disabled")
        self._log("⬇ " + self.t("install_tesseract_starting"))

        def worker():
            ok = tesseract_installer.download_and_install(progress_cb=self._log_threadsafe)
            self.root.after(0, self._on_tesseract_install_done, ok)

        threading.Thread(target=worker, daemon=True).start()

    def _on_tesseract_install_done(self, ok):
        self.install_tesseract_btn.configure(state="normal")
        ocr.reset_cache()
        self._refresh_ocr_status()
        if ok and ocr.engine_name() == "tesseract":
            self._log("✅ " + self.t("install_tesseract_success"))
        else:
            self._log("❌ " + self.t("install_tesseract_failed"))

    # ------------------------------------------------------------------
    # color / HP bar calibration (advanced)
    # ------------------------------------------------------------------
    def _calibrate_color(self):
        self._bring_selected_window_front()
        point = pick_screen_point(self.root, self.t("calibrate_hint"))
        if point is None:
            return
        x, y = point
        try:
            sample_rect = (x - 3, y - 3, x + 4, y + 4)
            img = winutil.grab_screen(sample_rect)
            import numpy as np
            bgr = np.array(img)[:, :, ::-1]  # RGB -> BGR
            hsv_range = color_detect.sample_hsv_at(bgr, 3, 3)
        except Exception as exc:
            messagebox.showerror(self.t("calibrate_color"), str(exc))
            return

        self.config.nameplate_hsv = hsv_range
        self.color_label.configure(text=self._hsv_text(hsv_range))
        self._log("🎨 " + self.t("color_calibrated") + f": {self._hsv_text(hsv_range)}")

    def _set_hp_bar(self):
        if self.hunt_region is None:
            messagebox.showwarning(self.t("set_hp_bar"), self.t("err_no_window"))
            return
        self._bring_selected_window_front()
        rect = select_screen_region(self.root, self.t("hp_bar_hint"))
        if rect is None:
            return
        left, top, _r, _b = self.hunt_region
        x0, y0, x1, y1 = rect
        relative = (x0 - left, y0 - top, x1 - x0, y1 - y0)
        self.config.hp_bar_rect = relative
        self.hp_bar_label.configure(text=self.t("hp_bar_set") + f": {relative}")
        self._log("❤ " + self.t("hp_bar_set"))

    def _clear_hp_bar(self):
        self.config.hp_bar_rect = None
        self.hp_bar_label.configure(text=self.t("hp_bar_not_set"))

    def _mode_key(self):
        label = self.mode_var.get()
        for key, text in self.mode_labels.items():
            if text == label:
                return key
        return "color"

    # ------------------------------------------------------------------
    # config / engine control
    # ------------------------------------------------------------------
    def _collect_config(self):
        c = self.config
        c.hunt_region = self.hunt_region
        c.game_hwnd = self.selected_hwnd
        c.detection_mode = self._mode_key()
        typed_targets = [s.strip().lower() for s in self.target_monsters_var.get().split(",") if s.strip()]
        c.target_monsters = typed_targets or [m["name"].lower() for m in self.monsters]
        c.keypress_only = self.keypress_only_var.get()
        c.auto_tab = self.auto_tab_var.get()
        c.auto_tab_interval = self.auto_tab_interval_var.get()
        c.skill_keys = [s.strip() for s in self.skill_keys_var.get().split(",") if s.strip()]
        c.loot_key = self.loot_key_var.get().strip() or None
        c.skill_interval = self.skill_interval_var.get()
        c.mob_interval = self.mob_interval_var.get()
        c.template_threshold = self.threshold_var.get()
        c.reclick_lockout = self.reclick_var.get()
        c.input_method = self.input_method_var.get()
        c.buffs_enabled = self.buffs_enabled_var.get()
        c.buff_keys = [s.strip() for s in self.buff_keys_var.get().split(",") if s.strip()]
        c.buff_interval = self.buff_interval_var.get()
        return c

    def _start(self):
        self._collect_config()

        if self.selected_hwnd is None:
            messagebox.showwarning(self.t("start"), self.t("err_no_window"))
            return

        if not self.config.keypress_only and self.config.hunt_region is None:
            messagebox.showwarning(self.t("start"), self.t("err_no_region"))
            return

        if not self.config.keypress_only and self.config.detection_mode == "template":
            templates = load_monster_templates(MONSTERS_DIR)
            if not templates:
                messagebox.showwarning(self.t("start"), self.t("err_no_templates"))
                return

        self._bring_selected_window_front()

        self.engine.start()
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.status_label.configure(text=self.t("status_running"))
        self._log("▶ " + self.t("status_running") + f" [{self.config.detection_mode}]")

    def _stop(self):
        self.engine.stop()
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.status_label.configure(text=self.t("status_stopped"))
        self._log("⏹ " + self.t("status_stopped"))

    def _register_stop_hotkey(self):
        try:
            import keyboard
            keyboard.add_hotkey("q", self._on_hotkey_stop)
            keyboard.add_hotkey("ctrl+b", self._on_hotkey_start)
            keyboard.add_hotkey("ctrl+d", self._on_hotkey_stop)
        except Exception:
            pass  # keyboard lib may need admin rights; Start/Stop buttons still work

    def _on_hotkey_start(self):
        if not self.engine.running:
            self.root.after(0, self._start)

    def _on_hotkey_stop(self):
        if self.engine.running:
            self.root.after(0, self._stop)

    def _tick_status(self):
        if self.engine.running:
            elapsed = int(self.engine.elapsed_seconds())
            self.runtime_label.configure(text=self.t("runtime", t=f"{elapsed // 60}:{elapsed % 60:02d}"))
            self.kills_label.configure(text=self.t("kills", n=self.engine.kills))
        else:
            if self.stop_btn["state"] == "normal":
                self._stop()
        self.root.after(500, self._tick_status)

    # ------------------------------------------------------------------
    # logging
    # ------------------------------------------------------------------
    def _log(self, message):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"{time.strftime('%H:%M:%S')}  {message}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _log_threadsafe(self, message):
        self.root.after(0, lambda: self._log(message))
