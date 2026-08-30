"""Tkinter GUI wiring capture, detection, profiles and the engine together."""

import os
import time
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

from . import color_detect, ocr, profiles, winutil
from .bot_engine import BotConfig, BotEngine
from .detection import load_monster_templates, sanitize_template_basename
from .i18n import Translator, get_language, save_language
from .paths import data_path
from .region_select import pick_screen_point, select_screen_region

MONSTERS_DIR = data_path("monsters")


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

        lang = get_language()
        if lang is None:
            dlg = LanguageDialog(root)
            root.wait_window(dlg)
            lang = dlg.choice or "EN"
            save_language(lang)
        self.t = Translator(lang)

        self.root.title(self.t("app_title"))
        self.root.geometry("660x880")
        self.root.minsize(600, 760)

        self.hunt_region = None
        self.selected_hwnd = None
        self.selected_window_title = None

        self.config = BotConfig(monsters_dir=MONSTERS_DIR)
        self.engine = BotEngine(self.config, log_fn=self._log_threadsafe)

        os.makedirs(MONSTERS_DIR, exist_ok=True)
        self._build_ui()
        self._refresh_template_count()
        self._refresh_profile_list()
        self._register_stop_hotkey()
        self._tick_status()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_ui(self):
        outer_container = ttk.Frame(self.root)
        outer_container.pack(fill="both", expand=True)

        canvas = tk.Canvas(outer_container, highlightthickness=0)
        vscroll = ttk.Scrollbar(outer_container, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vscroll.set)
        canvas.pack(side="left", fill="both", expand=True)
        vscroll.pack(side="right", fill="y")

        outer = ttk.Frame(canvas, padding=10)
        canvas.create_window((0, 0), window=outer, anchor="nw")
        outer.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # -- profiles ---------------------------------------------------------
        prof_frame = ttk.LabelFrame(outer, text=self.t("profiles"), padding=8)
        prof_frame.pack(fill="x", pady=4)
        self.profile_var = tk.StringVar()
        self.profile_combo = ttk.Combobox(prof_frame, textvariable=self.profile_var, state="readonly", width=24)
        self.profile_combo.pack(side="left")
        ttk.Button(prof_frame, text=self.t("load_profile"), command=self._load_profile).pack(side="left", padx=4)
        ttk.Button(prof_frame, text=self.t("save_profile"), command=self._save_profile).pack(side="left", padx=4)
        ttk.Button(prof_frame, text=self.t("delete_profile"), command=self._delete_profile).pack(side="left", padx=4)

        # -- window / region ------------------------------------------------
        win_frame = ttk.LabelFrame(outer, text=self.t("window"), padding=8)
        win_frame.pack(fill="x", pady=4)
        ttk.Button(win_frame, text=self.t("select_window"), command=self._select_window).pack(side="left")
        self.window_label = ttk.Label(win_frame, text=self.t("no_window_selected"))
        self.window_label.pack(side="left", padx=10)

        region_frame = ttk.LabelFrame(outer, text=self.t("hunt_region"), padding=8)
        region_frame.pack(fill="x", pady=4)
        ttk.Button(region_frame, text=self.t("set_hunt_region"), command=self._set_hunt_region).pack(side="left")
        self.region_label = ttk.Label(region_frame, text=self.t("region_not_set"))
        self.region_label.pack(side="left", padx=10)

        # -- detection mode ----------------------------------------------------
        det_frame = ttk.LabelFrame(outer, text=self.t("detection_mode"), padding=8)
        det_frame.pack(fill="x", pady=4)
        self.mode_labels = {
            "hybrid": self.t("mode_hybrid"), "color": self.t("mode_color"),
            "template": self.t("mode_template"), "ocr": self.t("mode_ocr"),
        }
        self.mode_var = tk.StringVar(value=self.mode_labels["hybrid"])
        ttk.Combobox(det_frame, textvariable=self.mode_var, state="readonly",
                     values=list(self.mode_labels.values()), width=36).pack(side="left")
        if not ocr.is_available():
            ttk.Label(det_frame, text=self.t("ocr_unavailable"), foreground="#888").pack(side="left", padx=8)

        color_frame = ttk.Frame(det_frame)
        color_frame.pack(fill="x", pady=(6, 0))
        ttk.Button(color_frame, text=self.t("calibrate_color"), command=self._calibrate_color).pack(side="left")
        self.color_label = ttk.Label(color_frame, text=self._hsv_text(self.config.nameplate_hsv))
        self.color_label.pack(side="left", padx=10)

        # -- templates -------------------------------------------------------
        tpl_frame = ttk.LabelFrame(outer, text=self.t("monster_templates"), padding=8)
        tpl_frame.pack(fill="x", pady=4)
        ttk.Button(tpl_frame, text=self.t("add_template"), command=self._add_template).pack(side="left")
        self.template_count_label = ttk.Label(tpl_frame, text="")
        self.template_count_label.pack(side="left", padx=10)

        ttk.Label(outer, text=self.t("target_monsters")).pack(anchor="w", pady=(8, 0))
        self.target_monsters_var = tk.StringVar()
        ttk.Entry(outer, textvariable=self.target_monsters_var).pack(fill="x")

        # -- mode toggles -----------------------------------------------------
        toggles = ttk.Frame(outer)
        toggles.pack(fill="x", pady=6)
        self.keypress_only_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(toggles, text=self.t("keypress_only"), variable=self.keypress_only_var).pack(anchor="w")
        self.auto_tab_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(toggles, text=self.t("auto_tab"), variable=self.auto_tab_var).pack(anchor="w")

        # -- keys / timings ----------------------------------------------------
        keys_frame = ttk.LabelFrame(outer, text=self.t("settings"), padding=8)
        keys_frame.pack(fill="x", pady=4)

        ttk.Label(keys_frame, text=self.t("skill_keys")).grid(row=0, column=0, sticky="w")
        self.skill_keys_var = tk.StringVar(value="1,2,3,4")
        ttk.Entry(keys_frame, textvariable=self.skill_keys_var, width=20).grid(row=0, column=1, sticky="ew", padx=6)

        ttk.Label(keys_frame, text=self.t("loot_key")).grid(row=1, column=0, sticky="w")
        self.loot_key_var = tk.StringVar(value="")
        ttk.Entry(keys_frame, textvariable=self.loot_key_var, width=20).grid(row=1, column=1, sticky="ew", padx=6)

        self.skill_interval_var = self._add_slider(keys_frame, 2, self.t("skill_interval"), 0.05, 1.0, 0.15)
        self.mob_interval_var = self._add_slider(keys_frame, 3, self.t("mob_interval"), 0.1, 2.0, 0.2)
        self.auto_tab_interval_var = self._add_slider(keys_frame, 4, self.t("auto_tab_interval"), 0.5, 10.0, 3.0)
        self.threshold_var = self._add_slider(keys_frame, 5, self.t("template_threshold"), 0.10, 0.90, 0.40)
        self.reclick_var = self._add_slider(keys_frame, 6, self.t("reclick_lockout"), 0.0, 8.0, 2.5)
        keys_frame.columnconfigure(1, weight=1)

        ttk.Label(keys_frame, text=self.t("input_method")).grid(row=7, column=0, sticky="w", pady=(6, 0))
        self.input_method_var = tk.StringVar(value="auto")
        ttk.Combobox(keys_frame, textvariable=self.input_method_var, state="readonly",
                     values=["auto", "sendinput", "pydirectinput", "keyboard"]).grid(
            row=7, column=1, sticky="ew", padx=6, pady=(6, 0))

        # -- HP bar --------------------------------------------------------------
        hp_frame = ttk.LabelFrame(outer, text=self.t("hp_bar"), padding=8)
        hp_frame.pack(fill="x", pady=4)
        hp_btns = ttk.Frame(hp_frame)
        hp_btns.pack(fill="x")
        ttk.Button(hp_btns, text=self.t("set_hp_bar"), command=self._set_hp_bar).pack(side="left")
        ttk.Button(hp_btns, text=self.t("clear"), command=self._clear_hp_bar).pack(side="left", padx=4)
        self.hp_bar_label = ttk.Label(hp_frame, text=self.t("hp_bar_not_set"))
        self.hp_bar_label.pack(anchor="w", pady=(4, 0))

        # -- buffs -----------------------------------------------------------
        buff_frame = ttk.LabelFrame(outer, text=self.t("buffs"), padding=8)
        buff_frame.pack(fill="x", pady=4)
        self.buffs_enabled_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(buff_frame, text=self.t("enable_buffs"), variable=self.buffs_enabled_var).grid(
            row=0, column=0, columnspan=2, sticky="w")
        ttk.Label(buff_frame, text=self.t("buff_keys")).grid(row=1, column=0, sticky="w")
        self.buff_keys_var = tk.StringVar(value="")
        ttk.Entry(buff_frame, textvariable=self.buff_keys_var).grid(row=1, column=1, sticky="ew", padx=6)
        self.buff_interval_var = self._add_slider(buff_frame, 2, self.t("buff_interval"), 5.0, 600.0, 60.0)
        buff_frame.columnconfigure(1, weight=1)

        # -- controls --------------------------------------------------------
        controls = ttk.Frame(outer)
        controls.pack(fill="x", pady=8)
        self.start_btn = ttk.Button(controls, text=self.t("start"), command=self._start)
        self.start_btn.pack(side="left")
        self.stop_btn = ttk.Button(controls, text=self.t("stop"), command=self._stop, state="disabled")
        self.stop_btn.pack(side="left", padx=6)

        status_frame = ttk.Frame(outer)
        status_frame.pack(fill="x")
        self.status_label = ttk.Label(status_frame, text=self.t("status_idle"), font=("Segoe UI", 10, "bold"))
        self.status_label.pack(side="left")
        self.kills_label = ttk.Label(status_frame, text=self.t("kills", n=0))
        self.kills_label.pack(side="left", padx=12)
        self.runtime_label = ttk.Label(status_frame, text=self.t("runtime", t="0:00"))
        self.runtime_label.pack(side="left", padx=12)

        ttk.Label(outer, text=self.t("hotkey_hint"), foreground="#888").pack(anchor="w", pady=(0, 4))

        # -- log ---------------------------------------------------------------
        log_frame = ttk.LabelFrame(outer, text=self.t("log"), padding=4)
        log_frame.pack(fill="both", expand=True, pady=4)
        self.log_text = tk.Text(log_frame, height=10, state="disabled", wrap="word")
        self.log_text.pack(fill="both", expand=True, side="left")
        scroll = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scroll.pack(side="right", fill="y")
        self.log_text.configure(yscrollcommand=scroll.set)

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
    # window / region / templates
    # ------------------------------------------------------------------
    def _select_window(self):
        windows = winutil.enumerate_top_level_windows()
        if not windows:
            messagebox.showinfo(self.t("select_window"), "No windows found.")
            return

        picker = tk.Toplevel(self.root)
        picker.title(self.t("select_window"))
        picker.geometry("420x360")
        listbox = tk.Listbox(picker)
        listbox.pack(fill="both", expand=True, padx=8, pady=8)
        for _hwnd, title, _rect in windows:
            listbox.insert("end", title)

        def confirm():
            sel = listbox.curselection()
            if not sel:
                return
            hwnd, title, _rect = windows[sel[0]]
            self.selected_hwnd = hwnd
            self.selected_window_title = title
            self.window_label.configure(text=title)
            picker.destroy()

        ttk.Button(picker, text="OK", command=confirm).pack(pady=(0, 8))

    def _bring_selected_window_front(self):
        if self.selected_hwnd is not None:
            winutil.bring_window_to_front(self.selected_hwnd)
            time.sleep(0.2)

    def _set_hunt_region(self):
        self._bring_selected_window_front()
        rect = select_screen_region(self.root, self.t("drag_to_select"))
        if rect is None:
            return
        self.hunt_region = rect
        self.config.hunt_region = rect
        left, top, right, bottom = rect
        self.region_label.configure(text=self.t("region_set", w=right - left, h=bottom - top, x=left, y=top))

    def _add_template(self):
        self._bring_selected_window_front()
        rect = select_screen_region(self.root, self.t("template_wizard_hint"))
        if rect is None:
            return

        name = simpledialog.askstring(self.t("add_template"), self.t("template_name_prompt"), parent=self.root)
        if not name:
            return
        filename = sanitize_template_basename(name) + ".png"
        path = os.path.join(MONSTERS_DIR, filename)

        try:
            img = winutil.grab_screen(rect)
            os.makedirs(MONSTERS_DIR, exist_ok=True)
            img.save(path)
        except Exception as exc:
            messagebox.showerror(self.t("add_template"), str(exc))
            return

        self._log(f"📸 Template saved: {filename}")
        self._refresh_template_count()

    def _refresh_template_count(self):
        templates = load_monster_templates(MONSTERS_DIR)
        self.template_count_label.configure(text=self.t("templates_loaded", n=len(templates)))

    # ------------------------------------------------------------------
    # color / HP bar calibration
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
            messagebox.showwarning(self.t("set_hp_bar"), self.t("err_no_region"))
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

    # ------------------------------------------------------------------
    # profiles
    # ------------------------------------------------------------------
    def _refresh_profile_list(self):
        names = profiles.list_profiles()
        self.profile_combo.configure(values=names)

    def _profile_dict(self):
        return {
            "hunt_region": list(self.hunt_region) if self.hunt_region else None,
            "selected_window_title": self.selected_window_title,
            "detection_mode": self._mode_key(),
            "nameplate_hsv": [list(self.config.nameplate_hsv[0]), list(self.config.nameplate_hsv[1])],
            "target_monsters": self.target_monsters_var.get(),
            "keypress_only": self.keypress_only_var.get(),
            "auto_tab": self.auto_tab_var.get(),
            "auto_tab_interval": self.auto_tab_interval_var.get(),
            "skill_keys": self.skill_keys_var.get(),
            "loot_key": self.loot_key_var.get(),
            "skill_interval": self.skill_interval_var.get(),
            "mob_interval": self.mob_interval_var.get(),
            "threshold": self.threshold_var.get(),
            "reclick": self.reclick_var.get(),
            "input_method": self.input_method_var.get(),
            "hp_bar_rect": list(self.config.hp_bar_rect) if self.config.hp_bar_rect else None,
            "buffs_enabled": self.buffs_enabled_var.get(),
            "buff_keys": self.buff_keys_var.get(),
            "buff_interval": self.buff_interval_var.get(),
        }

    def _mode_key(self):
        label = self.mode_var.get()
        for key, text in self.mode_labels.items():
            if text == label:
                return key
        return "hybrid"

    def _save_profile(self):
        name = self.profile_var.get().strip() or simpledialog.askstring(
            self.t("save_profile"), self.t("profile_name_prompt"), parent=self.root)
        if not name:
            return
        saved = profiles.save_profile(name, self._profile_dict())
        self.profile_var.set(saved)
        self._refresh_profile_list()
        self._log("💾 " + self.t("profile_saved", name=saved))

    def _load_profile(self):
        name = self.profile_var.get().strip()
        if not name:
            messagebox.showwarning(self.t("load_profile"), self.t("no_profile_selected"))
            return
        try:
            data = profiles.load_profile(name)
        except (FileNotFoundError, OSError) as exc:
            messagebox.showerror(self.t("load_profile"), str(exc))
            return

        if data.get("hunt_region"):
            self.hunt_region = tuple(data["hunt_region"])
            self.config.hunt_region = self.hunt_region
            left, top, right, bottom = self.hunt_region
            self.region_label.configure(text=self.t("region_set", w=right - left, h=bottom - top, x=left, y=top))

        mode_key = data.get("detection_mode", "hybrid")
        self.mode_var.set(self.mode_labels.get(mode_key, self.mode_labels["hybrid"]))

        if data.get("nameplate_hsv"):
            lo, hi = data["nameplate_hsv"]
            self.config.nameplate_hsv = (tuple(lo), tuple(hi))
            self.color_label.configure(text=self._hsv_text(self.config.nameplate_hsv))

        self.target_monsters_var.set(data.get("target_monsters", ""))
        self.keypress_only_var.set(data.get("keypress_only", False))
        self.auto_tab_var.set(data.get("auto_tab", False))
        self.auto_tab_interval_var.set(data.get("auto_tab_interval", 3.0))
        self.skill_keys_var.set(data.get("skill_keys", "1,2,3,4"))
        self.loot_key_var.set(data.get("loot_key", ""))
        self.skill_interval_var.set(data.get("skill_interval", 0.15))
        self.mob_interval_var.set(data.get("mob_interval", 0.2))
        self.threshold_var.set(data.get("threshold", 0.40))
        self.reclick_var.set(data.get("reclick", 2.5))
        self.input_method_var.set(data.get("input_method", "auto"))

        hp_rect = data.get("hp_bar_rect")
        self.config.hp_bar_rect = tuple(hp_rect) if hp_rect else None
        self.hp_bar_label.configure(
            text=(self.t("hp_bar_set") + f": {self.config.hp_bar_rect}") if hp_rect else self.t("hp_bar_not_set"))

        self.buffs_enabled_var.set(data.get("buffs_enabled", False))
        self.buff_keys_var.set(data.get("buff_keys", ""))
        self.buff_interval_var.set(data.get("buff_interval", 60.0))

        self._log("📂 " + self.t("profile_loaded", name=name))

    def _delete_profile(self):
        name = self.profile_var.get().strip()
        if not name:
            messagebox.showwarning(self.t("delete_profile"), self.t("no_profile_selected"))
            return
        profiles.delete_profile(name)
        self.profile_var.set("")
        self._refresh_profile_list()
        self._log("🗑 " + self.t("profile_deleted", name=name))

    # ------------------------------------------------------------------
    # config / engine control
    # ------------------------------------------------------------------
    def _collect_config(self):
        c = self.config
        c.hunt_region = self.hunt_region
        c.detection_mode = self._mode_key()
        c.target_monsters = [
            s.strip().lower() for s in self.target_monsters_var.get().split(",") if s.strip()
        ]
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
