"""CustomTkinter front-end.

The whole flow is: pick the game (auto), press START. With no target yet the
bot first looks at the screen, shows the monster names it found and asks
"hit these?". Everything else (training, recording, detector mode) lives
under "Gelişmiş" so the default screen stays simple.
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
import cv2
from PIL import Image

from . import CONTACT_EMAIL, GITHUB_URL, REPO_URL, __author__, __version__, detect, winutil
from .capture import ScreenGrabber
from .config import Config
from .engine import ADMIN_HINT, BotEngine, State
from .paths import app_dir
from .recorder import Recorder, RecorderThread, sprite_box

GAME_HINTS = ("silkroad", "destiny", "online", "sro")
PREVIEW_W = 520
HOTKEY = "f9"
MODE_LABELS = {"auto": "Otomatik", "ocr": "Sadece OCR", "model": "Sadece model"}
ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
EPOCH_DONE = re.compile(r"(\d+/\d+)\s.*\s100%")
GRAY = {"fg_color": "gray30", "hover_color": "gray40"}
RED = {"fg_color": "#b03030", "hover_color": "#c04040"}


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.title("Silkroad Vision Bot")
        self.geometry("1000x680")
        self.minsize(920, 620)

        self.cfg = Config.load()
        self.engine = None
        self.recorder = Recorder()
        self.rec_thread = None
        self.windows = {}
        self.events = queue.Queue()
        self.latest = None
        self._last_preview = 0.0
        self._searching = False

        self._build()
        self._refresh_windows()
        self._render_targets()
        self._register_hotkey()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(100, self._poll)

    # -- layout ----------------------------------------------------------
    def _build(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        side = ctk.CTkFrame(self, width=340)
        side.grid(row=0, column=0, sticky="ns", padx=(12, 6), pady=12)
        side.grid_propagate(False)

        # Bottom widgets first so they keep their space.
        self.start_btn = ctk.CTkButton(side, text=f"BAŞLAT ({HOTKEY.upper()})", height=52,
                                       font=("", 17, "bold"), command=self._toggle)
        self.start_btn.pack(fill="x", padx=14, pady=(6, 14), side="bottom")
        self._start_colors = (self.start_btn.cget("fg_color"), self.start_btn.cget("hover_color"))
        self.status = ctk.CTkLabel(side, text=State.IDLE.value, anchor="w")
        self.status.pack(fill="x", padx=16, side="bottom")

        self.admin_box = ctk.CTkFrame(side, fg_color="#5a2a2a")
        ctk.CTkLabel(self.admin_box, text="Oyun yönetici olarak çalışıyor.\nBot tuş gönderebilmek için de\nyönetici olmalı.",
                     justify="left", anchor="w").pack(fill="x", padx=10, pady=(8, 4))
        ctk.CTkButton(self.admin_box, text="Yönetici olarak yeniden başlat", command=self._relaunch_admin,
                      fg_color="#c04040", hover_color="#d05050").pack(fill="x", padx=10, pady=(0, 8))

        ctk.CTkLabel(side, text="Oyun penceresi", anchor="w", font=("", 13, "bold")).pack(fill="x", padx=14, pady=(14, 4))
        row = ctk.CTkFrame(side, fg_color="transparent")
        row.pack(fill="x", padx=14)
        self.window_menu = ctk.CTkOptionMenu(row, values=["-"], command=self._on_window)
        self.window_menu.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(row, text="⟳", width=34, command=self._refresh_windows).pack(side="left", padx=(6, 0))
        self.admin_anchor = ctk.CTkFrame(side, fg_color="transparent", height=0)
        self.admin_anchor.pack(fill="x")

        ctk.CTkLabel(side, text="Hedef canavar", anchor="w", font=("", 13, "bold")).pack(fill="x", padx=14, pady=(16, 4))
        self.target_label = ctk.CTkLabel(side, text="", anchor="w", justify="left", wraplength=300,
                                         fg_color="gray20", corner_radius=6)
        self.target_label.pack(fill="x", padx=14, ipady=8)
        self.search_btn = ctk.CTkButton(side, text="🔍  Canavar ara", command=lambda: self._search(False))
        self.search_btn.pack(fill="x", padx=14, pady=(6, 0))

        ctk.CTkLabel(side, text="Tuşlar", anchor="w", font=("", 13, "bold")).pack(fill="x", padx=14, pady=(16, 4))
        self.attack_entry = self._labeled_entry(side, "Saldırı tuşları (virgülle: 1,2,3)", ",".join(self.cfg.attack_keys))
        self.loot_entry = self._labeled_entry(side, "Loot tuşu (boş bırakırsan kapalı)", self.cfg.loot_key)

        self.roam_switch = ctk.CTkSwitch(side, text="Canavar yoksa gezinerek ara")
        if self.cfg.roam:
            self.roam_switch.select()
        self.roam_switch.pack(anchor="w", padx=14, pady=(4, 0))

        self.adv_switch = ctk.CTkSwitch(side, text="Gelişmiş", command=self._toggle_advanced)
        self.adv_switch.pack(anchor="w", padx=14, pady=(10, 0))
        self.adv = ctk.CTkFrame(side, fg_color="transparent")
        self._build_advanced(self.adv)

        main = ctk.CTkFrame(self)
        main.grid(row=0, column=1, sticky="nsew", padx=(6, 12), pady=12)
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(2, weight=1)
        bar = ctk.CTkFrame(main, fg_color="transparent")
        bar.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 4))
        ctk.CTkLabel(bar, text="Canlı önizleme", font=("", 14, "bold")).pack(side="left")
        ctk.CTkButton(bar, text="Hakkında", width=80, command=self._about, **GRAY).pack(side="right")
        ctk.CTkButton(bar, text="Test taraması", width=110, command=self._test_scan, **GRAY).pack(side="right", padx=(0, 6))
        self.preview = ctk.CTkLabel(main, text="Başlat'a basınca bot ekranı burada gösterir.",
                                    fg_color="gray14", corner_radius=6, height=300)
        self.preview.grid(row=1, column=0, sticky="ew", padx=12, pady=4)
        self.log = ctk.CTkTextbox(main, state="disabled")
        self.log.grid(row=2, column=0, sticky="nsew", padx=12, pady=(4, 12))

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

    def _labeled_entry(self, parent, label, value):
        ctk.CTkLabel(parent, text=label, anchor="w", text_color="gray70").pack(fill="x", padx=14)
        entry = ctk.CTkEntry(parent)
        entry.insert(0, value)
        entry.pack(fill="x", padx=14, pady=(0, 6))
        return entry

    # -- game window + admin ---------------------------------------------
    def _refresh_windows(self):
        found = winutil.enumerate_top_level_windows()
        self.windows = {title: hwnd for hwnd, title, _ in found}
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
            self.admin_box.pack(fill="x", padx=14, pady=(10, 0), after=self.admin_anchor)
        else:
            self.admin_box.pack_forget()

    def _relaunch_admin(self):
        self._apply_inputs()
        if winutil.relaunch_as_admin():
            self._shutdown()
        else:
            self._log("Yönetici olarak yeniden başlatılamadı (UAC penceresi reddedilmiş olabilir).")

    # -- targets ---------------------------------------------------------
    def _render_targets(self):
        if self.cfg.monsters:
            self.target_label.configure(text="  " + ",  ".join(self.cfg.monsters))
            self.search_btn.configure(text="🔍  Yeniden ara", **GRAY)
        else:
            self.target_label.configure(text="  Henüz seçilmedi: 'Canavar ara'ya bas\n  ya da doğrudan BAŞLAT'a bas.")
            self.search_btn.configure(text="🔍  Canavar ara", fg_color=self._start_colors[0],
                                      hover_color=self._start_colors[1])

    def _search(self, then_start):
        """Look at the screen once, then ask which of the found names to hit."""
        if self._searching:
            return
        hwnd = self._hwnd()
        if not hwnd:
            self._log("Önce oyun penceresini seç.")
            return
        self._searching = True
        self.search_btn.configure(state="disabled", text="Aranıyor...")
        self._log("Ekran taranıyor...")
        threading.Thread(target=self._search_worker, args=(hwnd, then_start), daemon=True).start()

    def _search_worker(self, hwnd, then_start):
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
            self.events.put(("targets", (groups, frames[0] if frames else None, then_start)))
        except Exception as exc:
            self.events.put(("log", f"Arama hatası: {exc}"))
            self.events.put(("targets", ([], None, False)))
        finally:
            grabber.close()

    def _show_targets_dialog(self, groups, frame, then_start):
        self._searching = False
        self.search_btn.configure(state="normal")
        self._render_targets()
        self.lift()
        if frame is not None:
            self._show(frame, [], extra_boxes=[b for g in groups for b in g.boxes])

        win = ctk.CTkToplevel(self)
        win.title("Canavarlar bulundu" if groups else "Canavar bulunamadı")
        win.geometry("400x%d" % (200 + 34 * len(groups)))
        win.attributes("-topmost", True)
        win.transient(self)

        if not groups:
            ctk.CTkLabel(win, wraplength=360, justify="left",
                         text="Ekranda canavar ismi okunamadı.\n\nKarakterini canavarların yakınına götür, "
                              "oyun penceresinin üstünün açık olduğundan emin ol ve tekrar ara.").pack(padx=20, pady=20)
            row = ctk.CTkFrame(win, fg_color="transparent")
            row.pack(side="bottom", fill="x", padx=20, pady=16)
            ctk.CTkButton(row, text="Tekrar ara", command=lambda: (win.destroy(), self._search(then_start))).pack(
                side="left", expand=True, fill="x", padx=(0, 6))
            ctk.CTkButton(row, text="Kapat", command=win.destroy, **GRAY).pack(side="left", expand=True, fill="x")
            return

        ctk.CTkLabel(win, text="Ekranda şunları buldum.\nBu canavarlara mı vuracağım?",
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
            if not chosen:
                self._log("Hiçbir canavar seçilmedi.")
                return
            self.cfg.monsters = chosen
            self.cfg.save()
            self._render_targets()
            self._log("Hedef: " + ", ".join(chosen))
            if then_start:
                self._start()

        row = ctk.CTkFrame(win, fg_color="transparent")
        row.pack(side="bottom", fill="x", padx=20, pady=16)
        ctk.CTkButton(row, text="Evet, bunlara vur", command=accept).pack(side="left", expand=True, fill="x", padx=(0, 6))
        ctk.CTkButton(row, text="Hayır", command=win.destroy, **GRAY).pack(side="left", expand=True, fill="x")

    # -- scanning / preview ---------------------------------------------
    def _grab_once(self):
        hwnd = self._hwnd()
        rect = hwnd and winutil.get_window_client_rect_on_screen(hwnd)
        if not rect:
            self._log("Önce oyun penceresini seç.")
            return None
        grabber = ScreenGrabber()
        try:
            return grabber.grab_bgr(rect)
        finally:
            grabber.close()

    def _test_scan(self):
        if not self.cfg.monsters:
            self._log("Önce hedef seç ('Canavar ara').")
            return
        frame = self._grab_once()
        if frame is not None:
            dets = detect.detect(frame, self.cfg)
            self._show(frame, dets)
            self._log(f"Test taraması ({detect.active_mode(self.cfg).upper()}): {len(dets)} canavar bulundu.")

    def _show(self, frame, dets, extra_boxes=()):
        img = frame.copy()
        for x, y, w, h in extra_boxes:
            cv2.rectangle(img, (x - 2, y - 2), (x + w + 2, y + h + 2), (0, 255, 0), 2)
        for d in dets:
            x, y, w, h = d.box
            cv2.rectangle(img, (x - 2, y - 2), (x + w + 2, y + h + 2), (0, 255, 0), 2)
            cv2.circle(img, d.click, 5, (0, 0, 255), -1)
            if self.recorder.enabled and d.source == "ocr":
                sx, sy, sw, sh = sprite_box(d, frame.shape)
                cv2.rectangle(img, (sx, sy), (sx + sw, sy + sh), (255, 160, 0), 1)
        scale = PREVIEW_W / img.shape[1]
        img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
        pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        photo = ctk.CTkImage(pil, size=pil.size)
        self.preview.configure(image=photo, text="", height=pil.size[1])
        self.preview.image = photo

    # -- run control -----------------------------------------------------
    def _apply_inputs(self):
        self.cfg.attack_keys = [k.strip() for k in self.attack_entry.get().split(",") if k.strip()]
        self.cfg.loot_key = self.loot_entry.get().strip()
        self.cfg.roam = bool(self.roam_switch.get())
        self.cfg.save()

    def _toggle(self):
        if self.engine and self.engine.is_alive():
            self.engine.stop()
            return
        if not self._hwnd():
            self._log("Önce oyun penceresini seç.")
            return
        if self._needs_admin():
            self._update_admin_banner()
            if messagebox.askyesno("Yönetici yetkisi gerekli", ADMIN_HINT + "\n\nŞimdi yönetici olarak yeniden başlatayım mı?"):
                self._relaunch_admin()
            return
        if not self.cfg.monsters:
            self._search(then_start=True)  # no target yet: look, ask, then go
            return
        self._start()

    def _start(self):
        hwnd = self._hwnd()
        if not hwnd or (self.engine and self.engine.is_alive()):
            return
        self._apply_inputs()
        if not self.cfg.attack_keys:
            self._log("Uyarı: saldırı tuşu girilmedi, bot sadece canavara tıklayacak.")
        self.engine = BotEngine(
            self.cfg, hwnd,
            on_log=lambda m: self.events.put(("log", m)),
            on_state=lambda s: self.events.put(("state", s)),
            on_frame=lambda f, d: setattr(self, "latest", (f, d)),
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
        ctk.CTkLabel(win, text="Silkroad Vision Bot", font=("", 20, "bold")).pack(pady=(22, 0))
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
                self._log("Önce hedef seç; etiketler canavar isminden üretilir.")
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
                    on_log=lambda m: self.events.put(("log", m)),
                    on_frame=lambda f, d: setattr(self, "latest", (f, d)))
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
                self._show_targets_dialog(*payload)
            elif kind == "train_done":
                self.train_btn.configure(state="normal", text="Modeli eğit")
            elif kind == "toggle":
                self._toggle()
        if self.latest and time.time() - self._last_preview > 0.4:
            self._last_preview = time.time()
            frame, dets = self.latest
            self.latest = None
            self._show(frame, dets)
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
