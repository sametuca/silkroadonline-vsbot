"""CustomTkinter front-end.

Start-up is a short three-step wizard (game window -> monster name -> keys),
prefilled from the last run. After "Bitir" the dashboard shows a summary,
the START button and the log. Training, recording and the
detector mode live under "Gelişmiş" so the default screens stay simple.
"""

import queue
import re
import subprocess
import sys
import threading
import time
import tkinter as tk
import webbrowser
from tkinter import messagebox

import customtkinter as ctk

from . import CONTACT_EMAIL, GITHUB_URL, REPO_URL, __author__, __version__, detect, winutil
from .capture import ScreenGrabber
from .config import Config
from .engine import ADMIN_HINT, BotEngine, State
from .paths import app_dir
from .recorder import Recorder, RecorderThread

APP_TITLE = "Silkroad Vision Bot"
GAME_HINTS = ("silkroad", "destiny", "online", "sro")
HOTKEY = "f9"
MODE_LABELS = {"auto": "Otomatik", "ocr": "Sadece OCR", "model": "Sadece model"}
ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
EPOCH_DONE = re.compile(r"(\d+/\d+)\s.*\s100%")
GRAY = {"fg_color": "gray30", "hover_color": "gray40"}
RED = {"fg_color": "#b03030", "hover_color": "#c04040"}
STEP_TITLES = ("Oyun", "Canavar", "Tuşlar")


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
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.title(APP_TITLE)
        self.geometry("1000x680")
        self.minsize(920, 620)

        self.cfg = Config.load()
        self.engine = None
        self.recorder = Recorder()
        self.rec_thread = None
        self.windows = {}
        self.events = queue.Queue()
        self._searching = False
        self.step = 0

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.wizard = ctk.CTkFrame(self, fg_color="transparent")
        self.dashboard = ctk.CTkFrame(self, fg_color="transparent")
        self._build_wizard()
        self._build_dashboard()
        self._refresh_windows()
        self._goto_step(0)
        self._register_hotkey()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(100, self._poll)

    # ======================================================================
    # Wizard
    # ======================================================================
    def _build_wizard(self):
        self.wizard.grid(row=0, column=0, sticky="nsew")
        self.wizard.grid_columnconfigure(0, weight=1)
        self.wizard.grid_rowconfigure(0, weight=1)

        card = ctk.CTkFrame(self.wizard, width=560, height=520)
        card.grid(row=0, column=0)
        card.grid_propagate(False)

        ctk.CTkLabel(card, text=APP_TITLE, font=("", 24, "bold")).pack(pady=(26, 2))
        ctk.CTkLabel(card, text="Birkaç adımda hazırla", text_color="gray70").pack()

        self.step_labels = []
        bar = ctk.CTkFrame(card, fg_color="transparent")
        bar.pack(pady=(16, 6))
        for i, title in enumerate(STEP_TITLES):
            label = ctk.CTkLabel(bar, text=f"{i + 1}  {title}", width=110, corner_radius=14, height=28)
            label.pack(side="left", padx=4)
            self.step_labels.append(label)

        self.pages = ctk.CTkFrame(card, fg_color="transparent")
        self.pages.pack(fill="both", expand=True, padx=34, pady=(10, 0))
        self._build_page_window(self._new_page())
        self._build_page_monster(self._new_page())
        self._build_page_keys(self._new_page())

        nav = ctk.CTkFrame(card, fg_color="transparent")
        nav.pack(fill="x", padx=34, pady=(8, 26), side="bottom")
        self.back_btn = ctk.CTkButton(nav, text="Geri", width=110, command=lambda: self._goto_step(self.step - 1), **GRAY)
        self.back_btn.pack(side="left")
        self.next_btn = ctk.CTkButton(nav, text="İleri", width=150, command=self._next_step)
        self.next_btn.pack(side="right")
        self.wizard_error = ctk.CTkLabel(card, text="", text_color="#e07070", wraplength=480)
        self.wizard_error.pack(side="bottom")

    def _new_page(self):
        page = ctk.CTkFrame(self.pages, fg_color="transparent")
        self.page_frames = getattr(self, "page_frames", [])
        self.page_frames.append(page)
        return page

    def _heading(self, parent, title, hint):
        ctk.CTkLabel(parent, text=title, font=("", 17, "bold"), anchor="w").pack(fill="x", pady=(8, 2))
        ctk.CTkLabel(parent, text=hint, text_color="gray70", anchor="w", justify="left", wraplength=480).pack(fill="x")

    def _build_page_window(self, page):
        self._heading(page, "Oyun penceresini seç",
                      "Oyunu pencere modunda aç. Pencere listede yoksa oyunu açıp ⟳ düğmesine bas.")
        row = ctk.CTkFrame(page, fg_color="transparent")
        row.pack(fill="x", pady=(16, 0))
        self.window_menu = ctk.CTkOptionMenu(row, values=["-"], command=self._on_window, height=36)
        self.window_menu.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(row, text="⟳", width=42, height=36, command=self._refresh_windows).pack(side="left", padx=(8, 0))
        self.admin_box = ctk.CTkFrame(page, fg_color="#5a2a2a")
        ctk.CTkLabel(self.admin_box, justify="left", anchor="w",
                     text="Oyun yönetici olarak çalışıyor. Bot tuş gönderebilmek için\nde yönetici olmalı.").pack(
            fill="x", padx=12, pady=(10, 4))
        ctk.CTkButton(self.admin_box, text="Yönetici olarak yeniden başlat", command=self._relaunch_admin,
                      fg_color="#c04040", hover_color="#d05050").pack(fill="x", padx=12, pady=(0, 10))

    def _build_page_monster(self, page):
        self._heading(page, "Hangi canavara vuracağız?",
                      "Oyunda canavarın üstünde yazan adı birebir aynı yaz (büyük/küçük harf fark etmez). "
                      "Birden fazla canavar için virgülle ayır.")
        self.monster_entry = ctk.CTkEntry(page, height=40, font=("", 15), placeholder_text="Örn: Mangyang")
        self.monster_entry.insert(0, ", ".join(self.cfg.monsters))
        self.monster_entry.pack(fill="x", pady=(16, 0))
        self.monster_entry.bind("<Return>", lambda _e: self._next_step())
        self.search_btn = ctk.CTkButton(page, text="🔍  Adı ekrandan oku (isteğe bağlı)", command=self._search, **GRAY)
        self.search_btn.pack(fill="x", pady=(10, 0))
        ctk.CTkLabel(page, anchor="w", justify="left", text_color="gray60", wraplength=480,
                     text="Normal, şampiyon ve dev canavarlar aynı adı taşır, bu yüzden tek ad hepsini kapsar.").pack(
            fill="x", pady=(12, 0))

    def _build_page_keys(self, page):
        self._heading(page, "Tuşlar ve seçenekler",
                      "Skill çubuğundaki tuşları gir. Birden fazlası sırayla basılır (örn. 1,2,3).")
        self.attack_entry = self._labeled_entry(page, "Saldırı tuşları", ",".join(self.cfg.attack_keys))
        self.loot_entry = self._labeled_entry(page, "Loot tuşu (boş bırakırsan kapalı)", self.cfg.loot_key)
        self.roam_switch = ctk.CTkSwitch(page, text="Canavar yoksa gezinerek ara")
        if self.cfg.roam:
            self.roam_switch.select()
        self.roam_switch.pack(anchor="w", pady=(14, 0))
        self.radius_label = ctk.CTkLabel(page, text="", anchor="w", text_color="gray70")
        self.radius_label.pack(fill="x", pady=(10, 0))
        self.radius_slider = ctk.CTkSlider(page, from_=2, to=12, number_of_steps=10, command=self._on_radius)
        self.radius_slider.set(self.cfg.roam_radius)
        self.radius_slider.pack(fill="x")
        self._on_radius(self.cfg.roam_radius)

    def _on_radius(self, value):
        self.radius_label.configure(
            text=f"Kasılma alanı: başladığın yerden en fazla {int(round(value))} adım uzağa gider "
                 "(canavarı gördükçe merkez kayar)")

    def _labeled_entry(self, parent, label, value):
        ctk.CTkLabel(parent, text=label, anchor="w", text_color="gray70").pack(fill="x", pady=(14, 0))
        entry = ctk.CTkEntry(parent, height=36)
        entry.insert(0, value)
        entry.pack(fill="x")
        return entry

    def _goto_step(self, index):
        self.step = max(0, min(len(self.page_frames) - 1, index))
        self.dashboard.grid_remove()
        self.wizard.grid()
        for i, page in enumerate(self.page_frames):
            if i == self.step:
                page.pack(fill="both", expand=True)
            else:
                page.pack_forget()
        for i, label in enumerate(self.step_labels):
            if i == self.step:
                label.configure(fg_color="#1f6aa5", text_color="white")
            elif i < self.step:
                label.configure(fg_color="#2b5a3a", text_color="white")
            else:
                label.configure(fg_color="gray25", text_color="gray70")
        self.back_btn.configure(state="normal" if self.step else "disabled")
        self.next_btn.configure(text="Bitir" if self.step == len(self.page_frames) - 1 else "İleri")
        self.wizard_error.configure(text="")
        if self.step == 0:
            self._update_admin_banner()
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
            return "Önce oyun penceresini seç. Oyun açık değilse aç ve ⟳ düğmesine bas."
        if step == 1 and not parse_names(self.monster_entry.get()):
            return "Canavarın adını yaz (oyunda üstünde göründüğü gibi)."
        return ""

    def _finish_wizard(self):
        self.cfg.monsters = parse_names(self.monster_entry.get())
        self._apply_inputs()
        self._render_summary()
        self.wizard.grid_remove()
        self.dashboard.grid()
        self._log("Hazır. BAŞLAT'a basınca bot oyun penceresini öne alıp avlanmaya başlar.")

    # ======================================================================
    # Dashboard
    # ======================================================================
    def _build_dashboard(self):
        self.dashboard.grid(row=0, column=0, sticky="nsew")
        self.dashboard.grid_columnconfigure(1, weight=1)
        self.dashboard.grid_rowconfigure(0, weight=1)

        side = ctk.CTkFrame(self.dashboard, width=340)
        side.grid(row=0, column=0, sticky="ns", padx=(12, 6), pady=12)
        side.grid_propagate(False)

        # Bottom widgets first so they keep their space.
        self.start_btn = ctk.CTkButton(side, text=f"BAŞLAT ({HOTKEY.upper()})", height=52,
                                       font=("", 17, "bold"), command=self._toggle)
        self.start_btn.pack(fill="x", padx=14, pady=(6, 14), side="bottom")
        self._start_colors = (self.start_btn.cget("fg_color"), self.start_btn.cget("hover_color"))
        self.status = ctk.CTkLabel(side, text=State.IDLE.value, anchor="w")
        self.status.pack(fill="x", padx=16, side="bottom")

        ctk.CTkLabel(side, text="Hazırlanan ayarlar", anchor="w", font=("", 14, "bold")).pack(fill="x", padx=14, pady=(16, 6))
        self.summary = ctk.CTkLabel(side, text="", anchor="w", justify="left", wraplength=300,
                                    fg_color="gray20", corner_radius=6)
        self.summary.pack(fill="x", padx=14, ipady=10)
        ctk.CTkButton(side, text="⚙  Ayarları değiştir", command=lambda: self._goto_step(0), **GRAY).pack(
            fill="x", padx=14, pady=(8, 0))

        self.adv_switch = ctk.CTkSwitch(side, text="Gelişmiş", command=self._toggle_advanced)
        self.adv_switch.pack(anchor="w", padx=14, pady=(18, 0))
        self.adv = ctk.CTkFrame(side, fg_color="transparent")
        self._build_advanced(self.adv)

        main = ctk.CTkFrame(self.dashboard)
        main.grid(row=0, column=1, sticky="nsew", padx=(6, 12), pady=12)
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(1, weight=1)
        bar = ctk.CTkFrame(main, fg_color="transparent")
        bar.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 4))
        ctk.CTkLabel(bar, text="Günlük", font=("", 14, "bold")).pack(side="left")
        ctk.CTkButton(bar, text="Hakkında", width=80, command=self._about, **GRAY).pack(side="right")
        ctk.CTkButton(bar, text="Test taraması", width=110, command=self._test_scan, **GRAY).pack(side="right", padx=(0, 6))
        self.log = ctk.CTkTextbox(main, state="disabled")
        self.log.grid(row=1, column=0, sticky="nsew", padx=12, pady=(4, 12))

    def _build_advanced(self, parent):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=(6, 0))
        ctk.CTkLabel(row, text="Tespit:", text_color="gray70").pack(side="left")
        self.mode_menu = ctk.CTkOptionMenu(row, values=list(MODE_LABELS.values()), command=self._on_mode, width=140)
        self.mode_menu.set(MODE_LABELS.get(self.cfg.detector, MODE_LABELS["auto"]))
        self.mode_menu.pack(side="right")
        self.rec_btn = ctk.CTkButton(parent, text="Eğitim verisi topla", command=self._toggle_record, **GRAY)
        self.rec_btn.pack(fill="x", padx=14, pady=(6, 0))
        self.rec_label = ctk.CTkLabel(parent, text="", anchor="w", text_color="gray70")
        self.rec_label.pack(fill="x", padx=16)
        self.train_btn = ctk.CTkButton(parent, text="Modeli eğit", command=self._train, **GRAY)
        self.train_btn.pack(fill="x", padx=14, pady=(6, 0))
        self._update_rec_label()

    def _toggle_advanced(self):
        if self.adv_switch.get():
            self.adv.pack(fill="x", after=self.adv_switch)
        else:
            self.adv.pack_forget()

    def _render_summary(self):
        keys = ", ".join(self.cfg.attack_keys) or "yok"
        lines = [
            f"Oyun:  {self.window_menu.get().strip()}",
            f"Hedef:  {', '.join(self.cfg.monsters) or '-'}",
            f"Saldırı tuşları:  {keys}",
            f"Loot tuşu:  {self.cfg.loot_key or 'kapalı'}",
            f"Gezinme:  {'radara göre, ' + str(int(self.cfg.roam_radius)) + ' adım alan' if self.cfg.roam else 'kapalı'}",
        ]
        self.summary.configure(text="\n".join("  " + ln for ln in lines))

    # -- game window + admin ---------------------------------------------
    def _refresh_windows(self):
        found = winutil.enumerate_top_level_windows()
        # Never offer this program's own window as "the game" (its title contains "Silkroad").
        self.windows = {title: hwnd for hwnd, title, _ in found if title.strip() != APP_TITLE}
        titles = list(self.windows) or ["-"]
        self.window_menu.configure(values=titles)
        pick = next((t for t in titles if t == self.cfg.window_title), None) or \
            next((t for t in titles if any(h in t.lower() for h in GAME_HINTS)), titles[0])
        self.window_menu.set(pick)
        self._on_window(pick)

    def _on_window(self, title):
        self.cfg.window_title = title
        name = winutil.character_name_from_title(title)
        if name:
            self.cfg.player_name = name
        self._update_admin_banner()

    def _hwnd(self):
        return self.windows.get(self.window_menu.get())

    def _needs_admin(self):
        hwnd = self._hwnd()
        return bool(hwnd) and winutil.needs_admin_for(hwnd)

    def _update_admin_banner(self):
        if self._needs_admin():
            self.admin_box.pack(fill="x", pady=(16, 0))
        else:
            self.admin_box.pack_forget()

    def _relaunch_admin(self):
        self._apply_inputs()
        if winutil.relaunch_as_admin():
            self._shutdown()
        else:
            self._log("Yönetici olarak yeniden başlatılamadı (UAC penceresi reddedilmiş olabilir).")

    # -- reading the name from the screen (optional helper) ----------------
    def _search(self):
        """Look at the screen once and offer the names found, to avoid typos."""
        if self._searching:
            return
        hwnd = self._hwnd()
        if not hwnd:
            self.wizard_error.configure(text="Önce oyun penceresini seç.")
            return
        self._searching = True
        self.search_btn.configure(state="disabled", text="Aranıyor...")
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
            self.events.put(("log", f"Arama hatası: {exc}"))
            self.events.put(("targets", []))
        finally:
            grabber.close()

    def _show_targets_dialog(self, groups):
        self._searching = False
        self.search_btn.configure(state="normal", text="🔍  Adı ekrandan oku (isteğe bağlı)")
        self.lift()
        win = ctk.CTkToplevel(self)
        win.title("Canavarlar bulundu" if groups else "Canavar bulunamadı")
        win.geometry("400x%d" % (210 + 34 * len(groups)))
        win.attributes("-topmost", True)
        win.transient(self)

        row = ctk.CTkFrame(win, fg_color="transparent")
        row.pack(side="bottom", fill="x", padx=20, pady=16)
        if not groups:
            ctk.CTkLabel(win, wraplength=360, justify="left",
                         text="Ekranda canavar ismi okunamadı.\n\nKarakterini canavarların yakınına götür, oyun "
                              "penceresinin üstünün açık olduğundan emin ol ya da adı elle yaz.").pack(padx=20, pady=20)
            ctk.CTkButton(row, text="Tekrar ara", command=lambda: (win.destroy(), self._search())).pack(
                side="left", expand=True, fill="x", padx=(0, 6))
            ctk.CTkButton(row, text="Kapat", command=win.destroy, **GRAY).pack(side="left", expand=True, fill="x")
            return

        ctk.CTkLabel(win, text="Ekranda şunları buldum.\nHangisine vuracağız?",
                     font=("", 14, "bold"), justify="left").pack(anchor="w", padx=20, pady=(16, 8))
        checks = []
        for i, g in enumerate(groups):
            var = tk.BooleanVar(value=(i == 0))  # only the most frequent name by default: others may be players
            ctk.CTkCheckBox(win, text=f"{g.name}  ({g.count} adet)", variable=var).pack(anchor="w", padx=24, pady=3)
            checks.append((g.name, var))
        if len(groups) > 1:
            ctk.CTkLabel(win, text="Diğerleri başka oyuncu veya NPC olabilir, bu yüzden işaretsiz.",
                         text_color="gray70", wraplength=360, justify="left").pack(anchor="w", padx=24, pady=(4, 0))

        def accept():
            chosen = [name for name, var in checks if var.get()]
            win.destroy()
            if chosen:
                self.monster_entry.delete(0, "end")
                self.monster_entry.insert(0, ", ".join(chosen))

        ctk.CTkButton(row, text="Bunu kullan", command=accept).pack(side="left", expand=True, fill="x", padx=(0, 6))
        ctk.CTkButton(row, text="İptal", command=win.destroy, **GRAY).pack(side="left", expand=True, fill="x")

    # -- test scan ----------------------------------------------------------
    def _grab_once(self):
        hwnd = self._hwnd()
        rect = hwnd and winutil.get_window_client_rect_on_screen(hwnd)
        if not rect:
            self._log("Oyun penceresi bulunamadı. 'Ayarları değiştir' ile yeniden seç.")
            return None
        grabber = ScreenGrabber()
        try:
            return grabber.grab_bgr(rect)
        finally:
            grabber.close()

    def _test_scan(self):
        """Look once, attack nothing, and report what the bot recognises."""
        if not self.cfg.monsters:
            self._log("Önce hedef canavarı gir ('Ayarları değiştir').")
            return
        frame = self._grab_once()
        if frame is None:
            return
        dets = detect.detect(frame, self.cfg)
        mode = detect.active_mode(self.cfg).upper()
        if dets:
            names = ", ".join(sorted({d.name for d in dets}))
            self._log(f"Test taraması ({mode}): {len(dets)} canavar bulundu ({names}).")
        else:
            self._log(f"Test taraması ({mode}): hedef canavar görünmüyor. Oyun penceresinin üstü açık mı, ad doğru mu?")

    # -- run control -----------------------------------------------------
    def _apply_inputs(self):
        self.cfg.attack_keys = [k.strip() for k in self.attack_entry.get().split(",") if k.strip()]
        self.cfg.loot_key = self.loot_entry.get().strip()
        self.cfg.roam = bool(self.roam_switch.get())
        self.cfg.roam_radius = float(round(self.radius_slider.get()))
        self.cfg.save()

    def _toggle(self):
        if self.engine and self.engine.is_alive():
            self.engine.stop()
            return
        hwnd = self._hwnd()
        if not hwnd or not winutil.is_window_valid(hwnd):
            self._log("Oyun penceresi bulunamadı. 'Ayarları değiştir' ile yeniden seç.")
            return
        if self._needs_admin():
            if messagebox.askyesno("Yönetici yetkisi gerekli", ADMIN_HINT + "\n\nŞimdi yönetici olarak yeniden başlatayım mı?"):
                self._relaunch_admin()
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
            self._log("Uyarı: saldırı tuşu girilmedi, bot sadece canavara tıklayacak.")
        self.engine = BotEngine(
            self.cfg, hwnd,
            on_log=lambda m: self.events.put(("log", m)),
            on_state=lambda s: self.events.put(("state", s)),
            recorder=self.recorder,
        )
        self.engine.start()
        self.start_btn.configure(text=f"DURDUR ({HOTKEY.upper()})", **RED)

    def _register_hotkey(self):
        try:
            import keyboard
            keyboard.add_hotkey(HOTKEY, lambda: self.events.put(("toggle", None)))
        except Exception:
            self._log("Global kısayol kurulamadı; düğmeyi kullan.")

    def _about(self):
        win = ctk.CTkToplevel(self)
        win.title("Hakkında")
        win.geometry("380x330")
        win.attributes("-topmost", True)
        win.transient(self)
        ctk.CTkLabel(win, text=APP_TITLE, font=("", 20, "bold")).pack(pady=(22, 0))
        ctk.CTkLabel(win, text=f"Sürüm {__version__}", text_color="gray70").pack()
        ctk.CTkLabel(win, text="Ekrandaki canavarları isim etiketinden tanıyan,\nbellek okumayan açık kaynaklı av botu.",
                     justify="center").pack(pady=(12, 0))
        ctk.CTkLabel(win, text=f"Geliştirici: {__author__}", font=("", 13, "bold")).pack(pady=(14, 6))
        for text, url in (("GitHub: sametuca", GITHUB_URL), (CONTACT_EMAIL, "mailto:" + CONTACT_EMAIL),
                          ("Proje sayfası", REPO_URL)):
            ctk.CTkButton(win, text=text, width=220, command=lambda u=url: webbrowser.open(u), **GRAY).pack(pady=3)
        ctk.CTkLabel(win, text="MIT Lisansı", text_color="gray60").pack(pady=(10, 0))

    # -- advanced: detector mode, recording, training ---------------------
    def _on_mode(self, label):
        self.cfg.detector = next(k for k, v in MODE_LABELS.items() if v == label)
        self.cfg.save()

    def _toggle_record(self):
        if self.recorder.enabled:
            self.recorder.enabled = False
            self.rec_btn.configure(text="Eğitim verisi topla", **GRAY)
            self._log(f"Veri toplama durdu. Veri setinde {self.recorder.saved} kare var.")
        else:
            if not self.cfg.monsters:
                self._log("Önce hedef canavarı gir; etiketler canavar isminden üretilir.")
                return
            hwnd = self._hwnd()
            if not hwnd:
                self._log("Önce oyun penceresini seç.")
                return
            self.recorder.enabled = True
            self.rec_btn.configure(text="Veri toplamayı durdur", **RED)
            if self.engine and self.engine.is_alive():
                self._log("Bot avlanırken kareler kaydedilecek.")
            else:
                self.rec_thread = RecorderThread(
                    self.cfg, hwnd, self.recorder,
                    on_log=lambda m: self.events.put(("log", m)))
                self.rec_thread.start()
        self._update_rec_label()

    def _update_rec_label(self):
        self.rec_label.configure(text=f"Kayıtlı kare: {self.recorder.saved}")

    def _train(self):
        if getattr(sys, "frozen", False):
            self._log("Eğitim exe içinden yapılamaz: kaynak koddan 'python -m srbot.train' çalıştır.")
            return
        if self.recorder.saved < 10:
            self._log(f"Eğitim için daha fazla kare gerek (şu an {self.recorder.saved}, öneri 100+).")
            return
        self.train_btn.configure(state="disabled", text="Eğitiliyor...")
        self._log("Eğitim başladı (CPU'da dakikalar sürebilir). Bu sırada botu başlatma.")
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
            put("Eğitim bitti, model kullanıma hazır." if code == 0 else
                f"Eğitim başarısız (kod {code}). Ayrıntı için terminalde 'python -m srbot.train' çalıştır.")
        except Exception as exc:
            put(f"Eğitim başlatılamadı: {exc}")
        finally:
            self.events.put(("train_done", None))

    # -- event loop ------------------------------------------------------
    def _poll(self):
        while not self.events.empty():
            kind, payload = self.events.get()
            if kind == "log":
                self._log(payload)
            elif kind == "state":
                self.status.configure(text=payload.value)
                if payload is State.IDLE:
                    fg, hover = self._start_colors
                    self.start_btn.configure(text=f"BAŞLAT ({HOTKEY.upper()})", fg_color=fg, hover_color=hover)
            elif kind == "targets":
                self._show_targets_dialog(payload)
            elif kind == "train_done":
                self.train_btn.configure(state="normal", text="Modeli eğit")
            elif kind == "toggle":
                if self.dashboard.winfo_ismapped():  # the hotkey only drives the dashboard, not the wizard
                    self._toggle()
        self._update_rec_label()
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
        self.destroy()

    def _on_close(self):
        self._apply_inputs()
        self._shutdown()
