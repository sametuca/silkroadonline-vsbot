import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import pyautogui
import pydirectinput
import time
import os
import json
import random
import keyboard
import ctypes
from ctypes import wintypes
from PIL import Image
import cv2
import numpy as np

# Optimize pydirectinput pause for games
pydirectinput.PAUSE = 0

# LANGUAGE SUPPORT
LANGUAGES = {
    "TR": {
        "title": "Silkroad Vision Bot | Otomatik Av",
        "skill_interval": "Skill Aralığı:",
        "mob_interval": "Canavar Arası Bekleme:",
        "skill_keys": "Skill Tuşları:",
        "target_monsters": "Aranacak Canavarlar:",
        "input_method": "Input Yöntemi:",
        "keypress_only": "☑ Sadece Tuş Vuruşu Modu",
        "set_hunt_region": "📍 Hunt Region Seç (Template Tespiti)",
        "template_threshold": "Template Hassasiyet Eşiği:",
        "threshold_hint": "(düşük=hassas, yüksek=katı)",
        "start": "▶️ BAŞLAT",
        "stop": "⏹️ DUR",
        "log": "📝 Log",
        "press_q": "Botu durdurmak için 'Q' tuşuna basın",
        "draw_region": "🎯 Hunt Region Çiz",
        "draw_instructions": "Talimatlar:",
        "draw_step1": "1. Aşağıdaki OK butonuna tıkla",
        "draw_step2": "2. Oyun ekranında farenle bir dikdörtgen çiz",
        "draw_step3": "3. Fare düğmesini bırakarak seçimi onayla",
        "draw_step4": "4. Çizdiğin alan hunt region olacak",
        "ok_start": "OK - Seçimi Başlat",
        "cancel": "İptal",
        "hunt_region_set": "✅ Hunt region ayarlandı: X={}, Y={}, W={}, H={}",
        "click_points": "   {} adet tıklama noktası oluşturuldu",
        "region_small": "❌ Bölge çok küçük! Daha büyük bir alan seç.",
        "selection_cancelled": "❌ Seçim iptal edildi.",
        "error_empty_skills": "❌ HATA: Skill tuşları boş olamaz!",
        "error_hunt_not_set": "❌ HATA: Hunt region ayarlanmamış!",
        "error_click_button": "   Önce 'Hunt Region Seç' butonuna tıkla",
        "error_no_templates": "❌ HATA: Canavar template'i yüklenmedi!",
        "error_add_png": "   monsters/ klasörüne PNG dosyaları ekle",
        "running": "✅ ÇALIŞIYOR",
        "stopped": "⏹️ DURDURULDU",
        "line_separator": "=" * 50,
    },
    "EN": {
        "title": "Silkroad Vision Bot | Auto Hunter",
        "skill_interval": "Skill Interval:",
        "mob_interval": "Mob Interval:",
        "skill_keys": "Skill Keys:",
        "target_monsters": "Target Monsters:",
        "input_method": "Input Method:",
        "keypress_only": "☑ Keypress Only Mode",
        "set_hunt_region": "📍 Set Hunt Region (Template Detection)",
        "template_threshold": "Template Threshold:",
        "threshold_hint": "(low=sensitive, high=strict)",
        "start": "▶️ START",
        "stop": "⏹️ STOP",
        "log": "📝 Log",
        "press_q": "Press 'Q' to stop the bot",
        "draw_region": "🎯 Draw Hunt Region",
        "draw_instructions": "Instructions:",
        "draw_step1": "1. Click OK button below",
        "draw_step2": "2. Click and drag on your game screen to draw a rectangle",
        "draw_step3": "3. Release mouse button to confirm selection",
        "draw_step4": "4. The area you draw will be the hunt region",
        "ok_start": "OK - Start Selection",
        "cancel": "Cancel",
        "hunt_region_set": "✅ Hunt region set: X={}, Y={}, W={}, H={}",
        "click_points": "   Generated {} click points in the region",
        "region_small": "❌ Region too small! Please select a larger area.",
        "selection_cancelled": "❌ Selection cancelled.",
        "error_empty_skills": "❌ ERROR: Skill keys cannot be empty!",
        "error_hunt_not_set": "❌ ERROR: Hunt region not set!",
        "error_click_button": "   Click 'Set Hunt Region' button first",
        "error_no_templates": "❌ ERROR: No monster templates loaded!",
        "error_add_png": "   Add PNG files to monsters/ folder",
        "running": "✅ RUNNING",
        "stopped": "⏹️ STOPPED",
        "line_separator": "=" * 50,
    }
}

# Load/Set language
import json
LANG_FILE = "language.json"

def get_language():
    """Get saved language or show selection dialog."""
    if os.path.exists(LANG_FILE):
        try:
            with open(LANG_FILE, 'r') as f:
                data = json.load(f)
                return data.get('language', 'EN')
        except:
            return 'EN'
    else:
        # Default to EN if dialog fails
        return 'EN'

def save_language(lang):
    """Save selected language."""
    try:
        with open(LANG_FILE, 'w') as f:
            json.dump({'language': lang}, f)
    except:
        pass

CURRENT_LANGUAGE = get_language()

def tr(key):
    """Get translated string."""
    return LANGUAGES[CURRENT_LANGUAGE].get(key, key)



# Windows API constants for SendInput
KEYEVENTF_KEYDOWN = 0x0000
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008
KEYEVENTF_EXTENDEDKEY = 0x0001
INPUT_KEYBOARD = 1
ULONG_PTR = ctypes.c_ulonglong if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_ulong

# Virtual Key Codes
VK_CODES = {
    '1': 0x31, '2': 0x32, '3': 0x33, '4': 0x34, 
    '5': 0x35, '6': 0x36, '7': 0x37, '8': 0x38,
    '9': 0x39, '0': 0x30
}

# Scan Codes (Hardware level)
SCAN_CODES = {
    '1': 0x02, '2': 0x03, '3': 0x04, '4': 0x05,
    '5': 0x06, '6': 0x07, '7': 0x08, '8': 0x09,
    '9': 0x0A, '0': 0x0B
}

# Windows SendInput structures
class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR)
    ]

class INPUT(ctypes.Structure):
    class _INPUT(ctypes.Union):
        _fields_ = [("ki", KEYBDINPUT)]
    _fields_ = [
        ("type", wintypes.DWORD),
        ("union", _INPUT)
    ]

class BotGUI:
    def __init__(self, root):
        self.root = root
        
        # Show language selection on first launch
        if not os.path.exists(LANG_FILE):
            self.show_language_selection()
        
        # Now update language
        global CURRENT_LANGUAGE
        CURRENT_LANGUAGE = get_language()
        
        self.root.title(tr("title"))
        self.root.geometry("650x900")
        self.root.resizable(True, True)
        self.root.minsize(600, 700)  # Minimum window size
        
        # Bot status
        self.bot_running = False
        self.bot_thread = None
        self.skill_delay = 0.15
        self.mob_delay = 0.2
        self.skills = ['1', '2', '3', '4']
        self.keypress_only_mode = False  # Start in template detection mode by default
        self.input_method = "auto"  # auto, sendinput, pydirectinput, keyboard
        self.active_template_filter = set()  # Normalized target template names
        
        # Buff system
        self.buff_keys = ['F2']  # Default: F2 for buffs
        self.buff_interval = 1800  # 30 minutes in seconds (1800 seconds)
        self.last_buff_time = 0  # Track last buff activation time
        self.buff_enabled = True  # Enable/disable buff system

        # Auto TAB system
        self.auto_tab_interval = 15  # seconds
        self.last_auto_tab_time = 0
        
        # Hunt region for OCR-based detection
        self.hunt_region = None  # Hunt region (x, y, width, height)
        self.click_points = []  # Pre-calculated click points in region
        self.current_click_index = 0  # Current point index
        
        # Detection Mode
        self.detection_mode = "template"  # Template matching mode only
        self.monster_templates = {}  # {monster_name: cv2_image}
        self.template_threshold = 0.4  # Minimum match confidence (lowered for better detection)
        self.template_debug = True  # Show all match scores for debugging
        
        # Load monster templates from folder
        self.load_monster_templates()
        
        # Statistics
        self.total_kills = 0
        self.start_time = None
        
        self.setup_ui()
    
    def show_language_selection(self):
        """Show language selection dialog on first launch."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Language Selection / Dil Seçimi")
        dialog.geometry("350x180")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Select Language / Dil Seç", font=("Arial", 12, "bold")).pack(pady=15)
        
        def select_lang(lang):
            save_language(lang)
            global CURRENT_LANGUAGE
            CURRENT_LANGUAGE = lang
            dialog.destroy()
        
        ttk.Button(dialog, text="🇹🇷 Türkçe", command=lambda: select_lang('TR'), width=25).pack(pady=5)
        ttk.Button(dialog, text="🇬🇧 English", command=lambda: select_lang('EN'), width=25).pack(pady=5)
        
        self.root.wait_window(dialog)
        
    def setup_ui(self):
        # Configure ttk style for modern look
        style = ttk.Style()
        style.theme_use('clam')
        
        # Define color scheme (Modern Dark Blue Theme)
        bg_color = "#f0f2f5"
        fg_color = "#1a1a1a"
        accent_color = "#1e90ff"  # Dodger Blue
        hover_color = "#4169e1"
        border_color = "#e0e0e0"
        
        # Configure style
        style.configure('TFrame', background=bg_color)
        style.configure('TLabel', background=bg_color, foreground=fg_color)
        style.configure('TLabelframe', background=bg_color, foreground=fg_color, borderwidth=2)
        style.configure('TLabelframe.Label', background=bg_color, foreground=accent_color, font=("Segoe UI", 10, "bold"))
        style.configure('TButton', font=("Segoe UI", 9), padding=5)
        style.map('TButton',
                  background=[('active', hover_color)])
        style.configure('Title.TLabel', font=("Segoe UI", 24, "bold"), foreground=accent_color)
        style.configure('Subtitle.TLabel', font=("Segoe UI", 11, "bold"), foreground=accent_color)
        style.configure('Info.TLabel', font=("Segoe UI", 8), foreground="#666666")
        
        # Create canvas and scrollbar for scrollable content
        main_bg = tk.Canvas(self.root, bg=bg_color, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=main_bg.yview)
        scrollable_frame = ttk.Frame(main_bg)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: main_bg.configure(scrollregion=main_bg.bbox("all"))
        )
        
        main_bg.create_window((0, 0), window=scrollable_frame, anchor="nw")
        main_bg.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        main_bg.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Enable mousewheel scrolling
        def _on_mousewheel(event):
            main_bg.yview_scroll(int(-1*(event.delta/120)), "units")
        main_bg.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Main frame
        main_frame = ttk.Frame(scrollable_frame, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # ============ HEADER ============
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        
        title_label = ttk.Label(header_frame, text="🎮 SILKROAD VISION BOT", style='Title.TLabel')
        title_label.pack(pady=5)
        
        subtitle_label = ttk.Label(header_frame, text="Auto Hunter & Buff Manager", style='Subtitle.TLabel')
        subtitle_label.pack()
        
        sep1 = ttk.Separator(header_frame, orient='horizontal')
        sep1.pack(fill='x', pady=10)
        
        # GitHub info
        github_frame = ttk.Frame(header_frame)
        github_frame.pack(pady=5)
        ttk.Label(github_frame, text="👨‍💻 Developed by: Samet UCA", style='Info.TLabel').pack()
        ttk.Label(github_frame, text="📍 GitHub: github.com/SametUCA", style='Info.TLabel', foreground=accent_color).pack()
        
        # ============ STATUS PANEL ============
        status_frame = ttk.LabelFrame(main_frame, text="📊 Status", padding="12")
        status_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        self.status_label = ttk.Label(status_frame, text="⭕ " + tr("stopped"), font=("Segoe UI", 12, "bold"), foreground="red")
        self.status_label.pack(pady=8)
        
        stats_frame = ttk.Frame(status_frame)
        stats_frame.pack(fill='x', pady=5)
        
        self.kills_label = ttk.Label(stats_frame, text="Mobs Killed: 0", font=("Segoe UI", 10))
        self.kills_label.pack(side='left', padx=10)
        
        self.time_label = ttk.Label(stats_frame, text="Running Time: 00:00:00", font=("Segoe UI", 10))
        self.time_label.pack(side='right', padx=10)
        
        # ============ SETTINGS PANEL ============
        settings_frame = ttk.LabelFrame(main_frame, text="⚙️ Settings", padding="12")
        settings_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        # Skill delay setting
        ttk.Label(settings_frame, text=tr("skill_interval")).grid(row=0, column=0, sticky=tk.W, pady=6)
        self.skill_delay_var = tk.DoubleVar(value=0.15)
        skill_delay_slider = ttk.Scale(settings_frame, from_=0.1, to=1.0, variable=self.skill_delay_var,
                                      orient=tk.HORIZONTAL, length=200, command=self.update_skill_delay)
        skill_delay_slider.grid(row=0, column=1, padx=8, sticky='ew')
        self.skill_delay_label = ttk.Label(settings_frame, text="0.15 s", width=8)
        self.skill_delay_label.grid(row=0, column=2, padx=5)
        
        # Mob delay setting
        ttk.Label(settings_frame, text=tr("mob_interval")).grid(row=1, column=0, sticky=tk.W, pady=6)
        self.mob_delay_var = tk.DoubleVar(value=0.2)
        mob_delay_slider = ttk.Scale(settings_frame, from_=0.1, to=2.0, variable=self.mob_delay_var,
                                    orient=tk.HORIZONTAL, length=200, command=self.update_mob_delay)
        mob_delay_slider.grid(row=1, column=1, padx=8, sticky='ew')
        self.mob_delay_label = ttk.Label(settings_frame, text="0.20 s", width=8)
        self.mob_delay_label.grid(row=1, column=2, padx=5)
        
        # Skill keys
        ttk.Label(settings_frame, text=tr("skill_keys")).grid(row=2, column=0, sticky=tk.W, pady=6)
        self.skills_entry = ttk.Entry(settings_frame, width=15)
        self.skills_entry.insert(0, "1,2,3,4")
        self.skills_entry.grid(row=2, column=1, padx=8, sticky=tk.W)
        ttk.Label(settings_frame, text="(comma separated)", style='Info.TLabel').grid(row=2, column=2, sticky=tk.W, padx=5)

        # Target monsters (optional)
        ttk.Label(settings_frame, text=tr("target_monsters")).grid(row=3, column=0, sticky=tk.W, pady=6)
        self.target_monsters_entry = ttk.Entry(settings_frame, width=28)
        self.target_monsters_entry.grid(row=3, column=1, padx=8, sticky='ew')
        ttk.Label(settings_frame, text="(optional: name1,name2)", style='Info.TLabel').grid(row=3, column=2, sticky=tk.W, padx=5)

        # Keypress-only mode
        self.keypress_only_var = tk.BooleanVar(value=False)
        keypress_only_check = ttk.Checkbutton(
            settings_frame,
            text=tr("keypress_only"),
            variable=self.keypress_only_var,
            command=self.toggle_keypress_only_mode
        )
        keypress_only_check.grid(row=4, column=0, columnspan=3, sticky=tk.W, pady=8)

        # Input method selection
        ttk.Label(settings_frame, text=tr("input_method")).grid(row=5, column=0, sticky=tk.W, pady=6)
        self.input_method_var = tk.StringVar(value="Auto (Recommended)")
        self.input_method_combo = ttk.Combobox(
            settings_frame,
            textvariable=self.input_method_var,
            state="readonly",
            width=30,
            values=[
                "Auto (Recommended)",
                "SendInput (Scan Code)",
                "PyDirectInput",
                "Keyboard Library"
            ]
        )
        self.input_method_combo.grid(row=5, column=1, columnspan=2, sticky='ew', padx=8)
        self.input_method_combo.bind("<<ComboboxSelected>>", self.update_input_method)
        
        # Hunt Region button
        self.set_hunt_region_button = ttk.Button(settings_frame, text="📍 " + tr("set_hunt_region"), 
                                                 command=self.set_hunt_region)
        self.set_hunt_region_button.grid(row=6, column=0, columnspan=3, pady=10, sticky='ew', padx=8)
        
        # Template threshold
        ttk.Label(settings_frame, text=tr("template_threshold")).grid(row=7, column=0, sticky=tk.W, pady=6)
        self.template_threshold_var = tk.DoubleVar(value=0.4)
        template_threshold_slider = ttk.Scale(settings_frame, from_=0.1, to=0.9, variable=self.template_threshold_var,
                                            orient=tk.HORIZONTAL, length=200, command=self.update_template_threshold)
        template_threshold_slider.grid(row=7, column=1, padx=8, sticky='ew')
        self.template_threshold_label = ttk.Label(settings_frame, text="0.40", width=8)
        self.template_threshold_label.grid(row=7, column=2, padx=5)
        ttk.Label(settings_frame, text=tr("threshold_hint"), style='Info.TLabel').grid(row=7, column=0, columnspan=3, sticky=tk.E, pady=(0, 5))

        # ============ BUFF SYSTEM ============
        sep2 = ttk.Separator(settings_frame, orient='horizontal')
        sep2.grid(row=8, column=0, columnspan=3, sticky='ew', pady=10)
        
        # Buff Keys
        ttk.Label(settings_frame, text="⚡ Buff Keys:").grid(row=9, column=0, sticky=tk.W, pady=6)
        self.buff_keys_entry = ttk.Entry(settings_frame, width=15)
        self.buff_keys_entry.insert(0, "F2")
        self.buff_keys_entry.grid(row=9, column=1, padx=8, sticky=tk.W)
        ttk.Label(settings_frame, text="(keys for buffs)", style='Info.TLabel').grid(row=9, column=2, sticky=tk.W, padx=5)

        # Buff Interval
        ttk.Label(settings_frame, text="⏱️ Buff Interval (min):").grid(row=10, column=0, sticky=tk.W, pady=6)
        self.buff_interval_var = tk.DoubleVar(value=30)
        buff_interval_slider = ttk.Scale(settings_frame, from_=5, to=120, variable=self.buff_interval_var,
                                        orient=tk.HORIZONTAL, length=200, command=self.update_buff_interval)
        buff_interval_slider.grid(row=10, column=1, padx=8, sticky='ew')
        self.buff_interval_label = ttk.Label(settings_frame, text="30 min", width=8)
        self.buff_interval_label.grid(row=10, column=2, padx=5)

        # Buff enabled checkbox
        self.buff_enabled_var = tk.BooleanVar(value=True)
        buff_enabled_check = ttk.Checkbutton(
            settings_frame,
            text="⚡ Buff Sistemini Aktif Et",
            variable=self.buff_enabled_var,
            command=self.toggle_buff_system
        )
        buff_enabled_check.grid(row=11, column=0, columnspan=3, sticky=tk.W, pady=8)

        # Configure grid weight for better layout
        settings_frame.columnconfigure(1, weight=1)

        # ============ BUTTONS ============
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=15)
        
        self.start_button = ttk.Button(button_frame, text="▶️  START", command=self.start_bot, width=20)
        self.start_button.pack(side='left', padx=8)
        
        self.stop_button = ttk.Button(button_frame, text="⏹️  STOP", command=self.stop_bot, 
                                     width=20, state=tk.DISABLED)
        self.stop_button.pack(side='left', padx=8)
        
        # ============ LOG PANEL ============
        log_frame = ttk.LabelFrame(main_frame, text="📝 Log", padding="10")
        log_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=12, width=70, 
                                                  font=("Consolas", 9), bg="#1e1e1e", fg="#00ff00")
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # ============ FOOTER ============
        footer_frame = ttk.Frame(main_frame)
        footer_frame.grid(row=5, column=0, columnspan=2, pady=10)
        ttk.Label(footer_frame, text="Press 'Q' to stop | © 2026 Samet UCA", 
                  style='Info.TLabel').pack()
        
    def update_skill_delay(self, value):
        self.skill_delay = float(value)
        self.skill_delay_label.config(text=f"{self.skill_delay:.2f}")
        
    def update_mob_delay(self, value):
        self.mob_delay = float(value)
        self.mob_delay_label.config(text=f"{self.mob_delay:.2f}")
    
    def update_ocr_speed(self):
        self.ocr_speed_mode = self.ocr_speed_var.get()
        speed_names = {"fast": "⚡ Fast", "normal": "⚖️ Normal", "accurate": "🎯 Accurate"}
        self.log(f"OCR Speed: {speed_names.get(self.ocr_speed_mode, 'Unknown')}")

    def update_template_threshold(self, value):
        self.template_threshold = float(value)
        self.template_threshold_label.config(text=f"{self.template_threshold:.2f}")
        
    def update_input_method(self, event=None):
        method_text = self.input_method_var.get()
        method_map = {
            "Auto (Recommended)": "auto",
            "SendInput (Scan Code)": "sendinput",
            "PyDirectInput": "pydirectinput",
            "Keyboard Library": "keyboard"
        }
        self.input_method = method_map.get(method_text, "auto")
        self.log(f"⌨️ Input Method: {method_text}")

    def toggle_keypress_only_mode(self):
        self.keypress_only_mode = self.keypress_only_var.get()
        if self.keypress_only_mode:
            self.log("⌨️ Sadece Tuş Vuruşu Modu: ON")
            self.log("   Canavar seçimi yapılmayacak")
        else:
            self.log("🎯 Template Av Modu: ON")
            self.log("   Monsters klasöründeki template'lerden canavar seçimi yapılacak")
    
    def update_buff_interval(self, value):
        """Update buff interval in minutes and convert to seconds."""
        minutes = float(value)
        self.buff_interval = minutes * 60  # Convert to seconds
        self.buff_interval_label.config(text=f"{minutes:.0f} dk")
    
    def toggle_buff_system(self):
        """Enable/disable buff system."""
        self.buff_enabled = self.buff_enabled_var.get()
        if self.buff_enabled:
            self.log("⚡ Buff Sistemi: AÇIK")
            self.log(f"   Buff tuşları her {self.buff_interval/60:.0f} dakikada basılacak")
        else:
            self.log("⚡ Buff Sistemi: KAPALI")
    
    def set_hunt_region(self):
        """Let user select a hunt region by drawing on screen."""
        self.log("📍 Hunt Region Selection (Template-based Detection)")
        self.log("   1. Click OK on the dialog")
        self.log("   2. Click and drag to draw a rectangle on your game")
        self.log("   3. Release mouse to confirm")
        
        # Create instruction dialog
        dialog = tk.Toplevel(self.root)
        dialog.title(tr("draw_region"))
        dialog.geometry("500x280")
        dialog.transient(self.root)
        
        ttk.Label(dialog, text=tr("draw_region"), font=("Arial", 14, "bold")).pack(pady=10)
        ttk.Label(dialog, text=tr("draw_instructions"), font=("Arial", 10, "bold")).pack(pady=5)
        ttk.Label(dialog, text=tr("draw_step1"), font=("Arial", 9)).pack()
        ttk.Label(dialog, text=tr("draw_step2"), font=("Arial", 9)).pack()
        ttk.Label(dialog, text=tr("draw_step3"), font=("Arial", 9)).pack()
        ttk.Label(dialog, text=tr("draw_step4"), font=("Arial", 9)).pack(pady=5)
        
        def start_selection():
            dialog.destroy()
            self.root.withdraw()  # Hide main window
            time.sleep(0.3)
            
            # Get screen size
            screen_width, screen_height = pyautogui.size()
            
            # Variables for selection
            selection = {'start': None, 'end': None, 'done': False}
            
            # Create fullscreen transparent window for selection
            selector = tk.Toplevel()
            selector.attributes('-fullscreen', True)
            selector.attributes('-alpha', 0.3)
            selector.attributes('-topmost', True)
            selector.configure(bg='gray')
            
            canvas = tk.Canvas(selector, highlightthickness=0, bg='gray')
            canvas.pack(fill=tk.BOTH, expand=True)
            
            rect = None
            
            def on_mouse_down(event):
                selection['start'] = (event.x_root, event.y_root)
                
            def on_mouse_move(event):
                nonlocal rect
                if selection['start']:
                    if rect:
                        canvas.delete(rect)
                    x1, y1 = selection['start']
                    x2, y2 = event.x_root, event.y_root
                    # Draw rectangle on canvas (adjust for window position)
                    rect = canvas.create_rectangle(x1, y1, x2, y2, outline='red', width=3)
                    
            def on_mouse_up(event):
                selection['end'] = (event.x_root, event.y_root)
                selection['done'] = True
                selector.destroy()
                
            canvas.bind('<Button-1>', on_mouse_down)
            canvas.bind('<B1-Motion>', on_mouse_move)
            canvas.bind('<ButtonRelease-1>', on_mouse_up)
            
            # ESC to cancel
            selector.bind('<Escape>', lambda e: selector.destroy())
            
            selector.wait_window()
            
            # Show main window again
            self.root.deiconify()
            
            # Process selection
            if selection['done'] and selection['start'] and selection['end']:
                x1, y1 = selection['start']
                x2, y2 = selection['end']
                
                # Calculate region (normalize coordinates)
                x = min(x1, x2)
                y = min(y1, y2)
                w = abs(x2 - x1)
                h = abs(y2 - y1)
                
                if w > 20 and h > 20:  # Minimum size
                    self.hunt_region = (x, y, w, h)
                    
                    # Generate click points in a dense grid pattern (8x6 = 48 points)
                    self.click_points = []
                    rows = 6
                    cols = 8
                    for row in range(rows):
                        for col in range(cols):
                            px = x + (w // (cols + 1)) * (col + 1)
                            py = y + (h // (rows + 1)) * (row + 1)
                            self.click_points.append((px, py))
                    
                    self.log(tr("hunt_region_set").format(x, y, w, h))
                    self.log(tr("click_points").format(len(self.click_points)))
                else:
                    self.log(tr("region_small"))
            else:
                self.log(tr("selection_cancelled"))
        
        ttk.Button(dialog, text=tr("ok_start"), command=start_selection).pack(pady=15)
        ttk.Button(dialog, text=tr("cancel"), command=lambda: [dialog.destroy(), self.log(tr("selection_cancelled"))]).pack()

            
    
    def log(self, message):
        if not hasattr(self, 'log_text'):
            return
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        
    def start_bot(self):
        # Get skill keys
        skills_text = self.skills_entry.get().strip()
        self.skills = [s.strip() for s in skills_text.split(',') if s.strip()]
        
        if not self.skills:
            self.log(tr("error_empty_skills"))
            return
        
        # Get buff keys
        buff_keys_text = self.buff_keys_entry.get().strip()
        self.buff_keys = [s.strip() for s in buff_keys_text.split(',') if s.strip()]
        self.buff_enabled = self.buff_enabled_var.get()
        self.last_buff_time = time.time()  # Reset buff timer on start
        self.last_auto_tab_time = time.time()
        
        if not self.keypress_only_mode:
            # Check hunt region
            if not self.hunt_region:
                self.log(tr("error_hunt_not_set"))
                self.log(tr("error_click_button"))
                return

            # Template mode: check if templates are loaded
            if not self.monster_templates:
                self.log(tr("error_no_templates"))
                self.log(tr("error_add_png"))
                return

            # Optional target-monster filtering
            targets_text = self.target_monsters_entry.get().strip()
            requested_names = [name.strip() for name in targets_text.split(',') if name.strip()]
            self.active_template_filter = set()

            if requested_names:
                available_templates = {
                    self.normalize_monster_name(name): name
                    for name in self.monster_templates.keys()
                }
                missing_names = []

                for requested_name in requested_names:
                    normalized_requested = self.normalize_monster_name(requested_name)
                    if normalized_requested in available_templates:
                        self.active_template_filter.add(normalized_requested)
                    else:
                        missing_names.append(requested_name)

                if missing_names:
                    self.log(f"⚠️ Template bulunamadı: {', '.join(missing_names)}")

                if not self.active_template_filter:
                    self.log("❌ Aranacak canavar isimleri eşleşmedi! monsters/ dosya adlarını kontrol et.")
                    return
            else:
                self.active_template_filter = set()
        
        self.bot_running = True
        self.total_kills = 0
        self.start_time = time.time()
        
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_label.config(text="✅ " + tr("running"), foreground="green")
        
        self.log("=" * 60)
        self.log("🚀 BOT STARTED!")
        
        # Log run mode info
        if self.keypress_only_mode:
            self.log("⌨️ Mode: KEYPRESS ONLY")
            self.log("   Canavar seçimi yapılmadan skill döngüsü çalışacak")
        elif self.detection_mode == "template":
            x, y, w, h = self.hunt_region
            self.log(f"📸 Mode: TEMPLATE DETECTION")
            self.log(f"📍 Hunt Region: X={x}, Y={y}, W={w}, H={h}")
            self.log(f"📊 Templates loaded: {len(self.monster_templates)}")
            for monster in self.monster_templates.keys():
                self.log(f"   ▶ {monster}")
            if self.active_template_filter:
                filtered_names = [
                    name for name in self.monster_templates.keys()
                    if self.normalize_monster_name(name) in self.active_template_filter
                ]
                self.log(f"🎯 Target monsters: {', '.join(filtered_names)}")
            else:
                self.log("🎯 Target monsters: ALL")
        
        self.log(f"🎯 Skill keys: {', '.join(self.skills)}")
        self.log(f"⌨️ Input method: {self.input_method_var.get()}")
        self.log(f"⚙️ Skill interval: {self.skill_delay}s")
        self.log(f"⚙️ Mob interval: {self.mob_delay}s")
        self.log(f"🎨 Template threshold: {self.template_threshold:.2f}")
        self.log(f"⚔️ Auto TAB interval: {self.auto_tab_interval:.0f}s")
        self.log("=" * 60)
        
        # Start bot thread
        self.bot_thread = threading.Thread(target=self.bot_loop, daemon=True)
        self.bot_thread.start()
        
        # Start timer
        self.update_timer()
        
    def stop_bot(self):
        self.bot_running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_label.config(text="⭕ " + tr("stopped"), foreground="red")
        self.log("🛑 Bot stopped!")
        
    def update_timer(self):
        if self.bot_running and self.start_time:
            elapsed = int(time.time() - self.start_time)
            hours = elapsed // 3600
            minutes = (elapsed % 3600) // 60
            seconds = elapsed % 60
            self.time_label.config(text=f"Running Time: {hours:02d}:{minutes:02d}:{seconds:02d}")
            self.root.after(1000, self.update_timer)
    
    def text_similarity(self, s1, s2):
        """Calculate similarity ratio between two strings using Levenshtein distance."""
        if not s1 or not s2:
            return 0.0
        
        # Normalize strings
        s1 = s1.lower().strip()
        s2 = s2.lower().strip()
        
        if s1 == s2:
            return 1.0
        
        # Simple Levenshtein distance calculation
        if len(s1) < len(s2):
            s1, s2 = s2, s1
        
        if len(s2) == 0:
            return 0.0
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        distance = previous_row[-1]
        max_len = max(len(s1), len(s2))
        return 1.0 - (distance / max_len)

    def normalize_monster_name(self, name):
        """Normalize monster/template names for robust matching."""
        if not name:
            return ""
        return ''.join(ch.lower() for ch in name if ch.isalnum())
        
    def load_monster_templates(self):
        """Load monster template images from monsters/ folder."""
        try:
            if not os.path.exists('monsters'):
                self.log("⚠️ monsters/ klasörü bulunamadı!")
                return
            
            self.monster_templates = {}
            monster_files = [f for f in os.listdir('monsters') if f.lower().endswith('.png')]
            
            for filename in monster_files:
                filepath = os.path.join('monsters', filename)
                try:
                    img = cv2.imread(filepath, cv2.IMREAD_COLOR)
                    if img is not None:
                        # Use filename without .png as monster name
                        monster_name = filename[:-4]  # Remove .png extension
                        self.monster_templates[monster_name] = img
                        self.log(f"✅ Template yüklendi: {monster_name}")
                except Exception as e:
                    self.log(f"❌ Template yükleme hatası ({filename}): {e}")
            
            if self.monster_templates:
                self.log(f"📊 Toplam {len(self.monster_templates)} monster template yüklendi")
            else:
                self.log("⚠️ monsters/ klasöründe PNG dosyası bulunamadı!")
                
        except Exception as e:
            self.log(f"❌ Monster templates yüklenirken hata: {e}")
    
    def detect_monster_template(self, screenshot, target_filter=None):
        """
        Detect monster in screenshot using template matching.
        Returns (monster_name, confidence, x, y) or (None, 0, 0, 0)
        """
        if not self.monster_templates:
            return None, 0, 0, 0
        
        try:
            # Convert PIL image to OpenCV format
            img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            best_match = None
            best_confidence = 0
            best_x, best_y = 0, 0
            
            # Try each template
            for monster_name, template in self.monster_templates.items():
                try:
                    if target_filter:
                        normalized_name = self.normalize_monster_name(monster_name)
                        if normalized_name not in target_filter:
                            continue

                    gray_template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
                    
                    # Check template is not bigger than image
                    if gray_template.shape[0] > gray_img.shape[0] or gray_template.shape[1] > gray_img.shape[1]:
                        if self.template_debug:
                            self.log(f"⚠️ {monster_name}: Template çok büyük (template: {gray_template.shape}, img: {gray_img.shape})")
                        continue
                    
                    # Use correlation matching
                    result = cv2.matchTemplate(gray_img, gray_template, cv2.TM_CCOEFF_NORMED)
                    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                    
                    # Debug: show confidence score for all templates
                    if self.template_debug and max_val > 0.2:
                        self.log(f"📸 {monster_name}: Confidence = {max_val:.2f} (threshold: {self.template_threshold:.2f})")
                    
                    # max_val is the normalized correlation value (0-1)
                    if max_val > best_confidence and max_val >= self.template_threshold:
                        best_confidence = max_val
                        best_match = monster_name
                        best_x, best_y = max_loc
                        
                except Exception as e:
                    self.log(f"⚠️ Template eşleştirme hatası ({monster_name}): {e}")
                    continue
            
            if best_match:
                return best_match, best_confidence, best_x, best_y
            else:
                return None, 0, 0, 0
                
        except Exception as e:
            self.log(f"⚠️ Detect monster hatası: {e}")
            return None, 0, 0, 0
        
    def press_key(self, key):
        """Press a key using selected input method, with safe fallbacks."""
        method = self.input_method

        if method == "sendinput":
            if self.send_scan_code_key(key):
                return
            if self.send_pydirectinput_key(key):
                return
            self.send_keyboard_key(key)
            return

        if method == "pydirectinput":
            if self.send_pydirectinput_key(key):
                return
            if self.send_scan_code_key(key):
                return
            self.send_keyboard_key(key)
            return

        if method == "keyboard":
            if self.send_keyboard_key(key):
                return
            if self.send_scan_code_key(key):
                return
            self.send_pydirectinput_key(key)
            return

        # auto mode
        if self.send_scan_code_key(key):
            return
        if self.send_pydirectinput_key(key):
            return
        self.send_keyboard_key(key)

    def send_pydirectinput_key(self, key):
        try:
            pydirectinput.keyDown(key)
            time.sleep(0.01)
            pydirectinput.keyUp(key)
            time.sleep(0.01)
            return True
        except Exception:
            return False

    def send_keyboard_key(self, key):
        try:
            keyboard.press_and_release(key)
            time.sleep(0.01)
            return True
        except Exception:
            return False

    def send_scan_code_key(self, key):
        """Send key press with Windows SendInput using scan codes."""
        scan_code = SCAN_CODES.get(key)
        if scan_code is None:
            return False

        try:
            key_down = INPUT(type=INPUT_KEYBOARD)
            key_down.union.ki = KEYBDINPUT(
                wVk=0,
                wScan=scan_code,
                dwFlags=KEYEVENTF_SCANCODE,
                time=0,
                dwExtraInfo=0
            )

            key_up = INPUT(type=INPUT_KEYBOARD)
            key_up.union.ki = KEYBDINPUT(
                wVk=0,
                wScan=scan_code,
                dwFlags=KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP,
                time=0,
                dwExtraInfo=0
            )

            sent_down = ctypes.windll.user32.SendInput(1, ctypes.byref(key_down), ctypes.sizeof(INPUT))
            time.sleep(0.01)
            sent_up = ctypes.windll.user32.SendInput(1, ctypes.byref(key_up), ctypes.sizeof(INPUT))
            return sent_down == 1 and sent_up == 1
        except Exception:
            return False

    def run_keypress_cycle(self):
        """Run a single keypress cycle without monster detection."""
        skill_log = "⌨️ Skills: "
        for skill in self.skills:
            self.press_key(skill)
            skill_log += f"{skill} "
            time.sleep(self.skill_delay)

        self.log(skill_log + "✓")
        time.sleep(self.mob_delay)
            
    def bot_loop(self):
        time.sleep(2)  # Initial delay
        
        while self.bot_running:
            # Check if Q key is pressed
            if keyboard.is_pressed('q'):
                self.root.after(0, self.stop_bot)
                break

            # Press TAB every fixed interval
            current_time = time.time()
            if current_time - self.last_auto_tab_time >= self.auto_tab_interval:
                self.press_key('tab')
                self.last_auto_tab_time = current_time
                self.log("⚔️ Auto TAB pressed")
                time.sleep(0.1)
            
            # Check if buff should be activated (every buff_interval seconds)
            if self.buff_enabled:
                current_time = time.time()
                if current_time - self.last_buff_time >= self.buff_interval:
                    self.log(f"⚡ BUFF TIME! Basılan tuşlar: {', '.join(self.buff_keys)}")
                    for buff_key in self.buff_keys:
                        self.press_key(buff_key)
                        time.sleep(0.3)  # Small delay between buff keys
                    self.last_buff_time = current_time
                    time.sleep(1)  # Extra delay after buffs
                
            try:
                if self.keypress_only_mode:
                    self.run_keypress_cycle()
                    continue

                if self.detection_mode == "template":
                    # Template-based monster detection
                    if not self.hunt_region:
                        self.log("❌ Hunt region not set! Click 'Set Hunt Region' button.")
                        time.sleep(3)
                        continue
                    
                    if not self.monster_templates:
                        self.log("❌ Monster templates not loaded! Başlangıçta yüklemeye çalış.")
                        self.load_monster_templates()
                        time.sleep(3)
                        continue
                    
                    # Take screenshot of hunt region
                    x, y, w, h = self.hunt_region
                    screenshot = pyautogui.screenshot(region=(x, y, w, h))
                    
                    # Detect monster using template matching
                    monster_name, confidence, template_x, template_y = self.detect_monster_template(
                        screenshot,
                        self.active_template_filter
                    )
                    
                    if monster_name and confidence >= self.template_threshold:
                        # Monster found!
                        self.total_kills += 1
                        self.root.after(0, lambda: self.kills_label.config(
                            text=f"Mobs Killed: {self.total_kills}"))
                        
                        # Calculate click position (center of template in screen coordinates)
                        template = self.monster_templates[monster_name]
                        template_h, template_w = template.shape[:2]
                        center_x = x + template_x + template_w // 2
                        center_y = y + template_y + template_h // 2
                        
                        self.log(f"🎯 [TEMPLATE] {monster_name} detected (confidence: {confidence:.2f}) at ({center_x}, {center_y})")
                        
                        # Click on the monster
                        offset_x = center_x + random.randint(-5, 5)
                        offset_y = center_y + random.randint(-5, 5)
                        pyautogui.moveTo(offset_x, offset_y, duration=0.08)
                        pydirectinput.click()
                        time.sleep(0.1)
                        
                        # Execute skills
                        skill_log = "   Skills: "
                        for skill in self.skills:
                            self.press_key(skill)
                            skill_log += f"{skill} "
                            time.sleep(self.skill_delay)
                        
                        self.log(skill_log + "✓")
                        time.sleep(self.mob_delay)
                    else:
                        # No monster found, wait a bit
                        time.sleep(0.3)
                    
                    continue

            except Exception as e:
                self.log(f"⚠️ Error: {e}")
                time.sleep(1)

def main():
    root = tk.Tk()
    app = BotGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
