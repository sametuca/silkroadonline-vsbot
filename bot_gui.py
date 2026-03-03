import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import pyautogui
import pydirectinput
import time
import os
import random
import keyboard
import ctypes
from ctypes import wintypes
import pytesseract
from PIL import Image
import cv2
import numpy as np
import subprocess
import winreg
import shutil

# Tesseract Auto-Detection Function
def find_tesseract():
    """Automatically find Tesseract installation on Windows."""
    if os.name != 'nt':
        return None
    
    # Method 1: Check Windows Registry
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Tesseract-OCR")
        install_path = winreg.QueryValueEx(key, "InstallDir")[0]
        winreg.CloseKey(key)
        tesseract_path = os.path.join(install_path, "tesseract.exe")
        if os.path.exists(tesseract_path):
            print(f"✅ Tesseract found via Registry: {tesseract_path}")
            return tesseract_path
    except:
        pass
    
    # Method 2: Check PATH environment variable
    tesseract_in_path = shutil.which("tesseract")
    if tesseract_in_path:
        print(f"✅ Tesseract found in PATH: {tesseract_in_path}")
        return tesseract_in_path
    
    # Method 3: Use 'where' command to find tesseract
    try:
        result = subprocess.run(['where', 'tesseract'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and result.stdout.strip():
            tesseract_path = result.stdout.strip().split('\n')[0]
            if os.path.exists(tesseract_path):
                print(f"✅ Tesseract found via 'where' command: {tesseract_path}")
                return tesseract_path
    except:
        pass
    
    # Method 4: Check common installation locations
    possible_paths = [
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
        r'C:\Tesseract-OCR\tesseract.exe',
        os.path.expandvars(r'%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe'),
        os.path.expandvars(r'%LOCALAPPDATA%\Tesseract-OCR\tesseract.exe'),
        os.path.expandvars(r'%APPDATA%\Tesseract-OCR\tesseract.exe'),
        os.path.expandvars(r'%ProgramW6432%\Tesseract-OCR\tesseract.exe'),
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            print(f"✅ Tesseract found: {path}")
            return path
    
    print("⚠️ Tesseract not found automatically. Please install it or add to PATH.")
    return None

# Configure Tesseract path automatically
tesseract_path = find_tesseract()
if tesseract_path:
    pytesseract.pytesseract.tesseract_cmd = tesseract_path
else:
    print("❌ Tesseract OCR not found! OCR features will not work.")
    print("   Install from: https://github.com/UB-Mannheim/tesseract/wiki")

# Optimize pydirectinput pause for games
pydirectinput.PAUSE = 0

# Power bar images folder
POWER_BAR_FOLDER = 'power_bar'

# Windows API constants for SendInput
KEYEVENTF_KEYDOWN = 0x0000
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008
KEYEVENTF_EXTENDEDKEY = 0x0001

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
        ("dwExtraInfo", ctypes.POINTER(wintypes.ULONG))
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
        self.root.title("Silkroad Vision Bot | Auto Hunter")
        self.root.geometry("650x900")
        self.root.resizable(True, True)
        self.root.minsize(600, 700)  # Minimum window size
        
        # Bot status
        self.bot_running = False
        self.bot_thread = None
        self.skill_delay = 0.15
        self.mob_delay = 0.2
        self.skills = ['1', '2', '3', '4']
        
        # Hunt region for OCR-based detection
        self.hunt_region = None  # Hunt region (x, y, width, height)
        self.click_points = []  # Pre-calculated click points in region
        self.current_click_index = 0  # Current point index
        
        self.power_bar_enabled = False  # Power bar detection
        self.power_bar_check_interval = 17.0  # Bar check interval (seconds)
        self.last_power_bar_check = 0
        self.power_bar_uses = 0  # How many times TAB pressed
        
        # Auto TAB on Giant detection
        self.auto_tab_on_giant = False  # Auto press TAB when "Giant" text is detected
        self.giant_tab_cooldown = 15.0  # Cooldown between TAB presses for Giant
        self.last_giant_tab = 0  # Last time TAB was pressed for Giant
        self.giant_tab_count = 0  # How many times TAB pressed for Giant
        
        # Statistics
        self.total_kills = 0
        self.start_time = None
        
        self.setup_ui()
        
    def setup_ui(self):
        # Create canvas and scrollbar for scrollable content
        canvas = tk.Canvas(self.root)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Enable mousewheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Main frame (now inside scrollable_frame)
        main_frame = ttk.Frame(scrollable_frame, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="🎮 SILKROAD VISION BOT", font=("Arial", 20, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=10)
        
        # Status panel
        status_frame = ttk.LabelFrame(main_frame, text="📊 Status", padding="10")
        status_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.status_label = ttk.Label(status_frame, text="⭕ STOPPED", font=("Arial", 12, "bold"), foreground="red")
        self.status_label.grid(row=0, column=0, pady=5)
        
        self.kills_label = ttk.Label(status_frame, text="Mobs Killed: 0", font=("Arial", 10))
        self.kills_label.grid(row=1, column=0, pady=2)
        
        self.power_bar_label = ttk.Label(status_frame, text="⚡ Power Used: 0", font=("Arial", 10))
        self.power_bar_label.grid(row=2, column=0, pady=2)
        
        self.giant_tab_label = ttk.Label(status_frame, text="🔥 Giant TABs: 0", font=("Arial", 10))
        self.giant_tab_label.grid(row=3, column=0, pady=2)
        
        self.time_label = ttk.Label(status_frame, text="Running Time: 00:00:00", font=("Arial", 10))
        self.time_label.grid(row=4, column=0, pady=2)
        
        # Settings panel
        settings_frame = ttk.LabelFrame(main_frame, text="⚙️ Settings", padding="10")
        settings_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Skill delay setting
        ttk.Label(settings_frame, text="Skill Interval (sec):").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.skill_delay_var = tk.DoubleVar(value=0.15)
        skill_delay_slider = ttk.Scale(settings_frame, from_=0.1, to=1.0, variable=self.skill_delay_var,
                                      orient=tk.HORIZONTAL, length=200, command=self.update_skill_delay)
        skill_delay_slider.grid(row=0, column=1, padx=5)
        self.skill_delay_label = ttk.Label(settings_frame, text="0.15")
        self.skill_delay_label.grid(row=0, column=2)
        
        # Mob delay setting
        ttk.Label(settings_frame, text="Mob Interval (sec):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.mob_delay_var = tk.DoubleVar(value=0.2)
        mob_delay_slider = ttk.Scale(settings_frame, from_=0.1, to=2.0, variable=self.mob_delay_var,
                                    orient=tk.HORIZONTAL, length=200, command=self.update_mob_delay)
        mob_delay_slider.grid(row=1, column=1, padx=5)
        self.mob_delay_label = ttk.Label(settings_frame, text="0.20")
        self.mob_delay_label.grid(row=1, column=2)
        
        # Skill keys
        ttk.Label(settings_frame, text="Skill Keys:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.skills_entry = ttk.Entry(settings_frame, width=15)
        self.skills_entry.insert(0, "1,2,3,4")
        self.skills_entry.grid(row=2, column=1, padx=5, sticky=tk.W)
        ttk.Label(settings_frame, text="(comma separated)").grid(row=2, column=2, sticky=tk.W)
        
        # Set Hunt Region button
        self.set_hunt_region_button = ttk.Button(settings_frame, text="📍 Set Hunt Region (OCR-based Detection)", 
                                                 command=self.set_hunt_region)
        self.set_hunt_region_button.grid(row=3, column=0, columnspan=3, pady=10)
        
        # Monster names
        ttk.Label(settings_frame, text="Monster Names:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.region_monsters_entry = ttk.Entry(settings_frame, width=25)
        self.region_monsters_entry.insert(0, "shakram, edimmu")
        self.region_monsters_entry.grid(row=4, column=1, padx=5, sticky=tk.W)
        ttk.Label(settings_frame, text="(comma separated)").grid(row=4, column=2, sticky=tk.W)
        
        # Power Bar detection
        self.power_bar_var = tk.BooleanVar(value=False)
        power_bar_check = ttk.Checkbutton(settings_frame, text="⚡ Power Bar Detection (TAB key)", 
                                         variable=self.power_bar_var, command=self.toggle_power_bar)
        power_bar_check.grid(row=5, column=0, columnspan=3, sticky=tk.W, pady=10)
        
        # Power bar check interval
        ttk.Label(settings_frame, text="Bar Check Interval (sec):").grid(row=6, column=0, sticky=tk.W, pady=5)
        self.bar_check_var = tk.DoubleVar(value=17.0)
        bar_check_slider = ttk.Scale(settings_frame, from_=5.0, to=30.0, variable=self.bar_check_var,
                                    orient=tk.HORIZONTAL, length=200, command=self.update_bar_interval)
        bar_check_slider.grid(row=6, column=1, padx=5)
        self.bar_check_label = ttk.Label(settings_frame, text="17.0")
        self.bar_check_label.grid(row=6, column=2)
        
        # Auto TAB on Giant detection (OCR-based)
        self.auto_tab_giant_var = tk.BooleanVar(value=False)
        auto_tab_giant_check = ttk.Checkbutton(settings_frame, text="🔥 Auto TAB when 'Giant' detected (OCR)", 
                                               variable=self.auto_tab_giant_var, command=self.toggle_auto_tab_giant)
        auto_tab_giant_check.grid(row=7, column=0, columnspan=3, sticky=tk.W, pady=10)
        
        # Giant TAB cooldown
        ttk.Label(settings_frame, text="Giant TAB Cooldown (sec):").grid(row=8, column=0, sticky=tk.W, pady=5)
        self.giant_tab_cooldown_var = tk.DoubleVar(value=15.0)
        giant_cooldown_slider = ttk.Scale(settings_frame, from_=5.0, to=30.0, variable=self.giant_tab_cooldown_var,
                                         orient=tk.HORIZONTAL, length=200, command=self.update_giant_cooldown)
        giant_cooldown_slider.grid(row=8, column=1, padx=5)
        self.giant_cooldown_label = ttk.Label(settings_frame, text="15.0")
        self.giant_cooldown_label.grid(row=8, column=2)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=15)
        
        self.start_button = ttk.Button(button_frame, text="▶️ START", command=self.start_bot, width=15)
        self.start_button.grid(row=0, column=0, padx=5)
        
        self.stop_button = ttk.Button(button_frame, text="⏹️ STOP", command=self.stop_bot, 
                                     width=15, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=1, padx=5)
        
        # Log panel
        log_frame = ttk.LabelFrame(main_frame, text="📝 Log", padding="5")
        log_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=70, 
                                                  font=("Consolas", 9), state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Info
        info_label = ttk.Label(main_frame, text="Press 'Q' to stop the bot", 
                              font=("Arial", 8), foreground="gray")
        info_label.grid(row=5, column=0, columnspan=2, pady=5)
        
    def update_skill_delay(self, value):
        self.skill_delay = float(value)
        self.skill_delay_label.config(text=f"{self.skill_delay:.2f}")
        
    def update_mob_delay(self, value):
        self.mob_delay = float(value)
        self.mob_delay_label.config(text=f"{self.mob_delay:.2f}")
        
    def update_bar_interval(self, value):
        self.power_bar_check_interval = float(value)
        self.bar_check_label.config(text=f"{self.power_bar_check_interval:.1f}")
    
    def update_giant_cooldown(self, value):
        self.giant_tab_cooldown = float(value)
        self.giant_cooldown_label.config(text=f"{self.giant_tab_cooldown:.1f}")
    
    def toggle_auto_tab_giant(self):
        self.auto_tab_on_giant = self.auto_tab_giant_var.get()
        if self.auto_tab_on_giant:
            self.log("🔥 Auto TAB on Giant: ON")
            self.log(f"   TAB will be pressed when 'Giant' text is detected")
            self.log(f"   Cooldown: {self.giant_tab_cooldown:.1f}s between TABs")
        else:
            self.log("❌ Auto TAB on Giant: OFF")
    
    def set_hunt_region(self):
        """Let user select a hunt region by drawing on screen."""
        self.log("📍 Hunt Region Selection (OCR-based Detection)")
        self.log("   1. Click OK on the dialog")
        self.log("   2. Click and drag to draw a rectangle on your game")
        self.log("   3. Release mouse to confirm")
        
        # Create instruction dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Hunt Region")
        dialog.geometry("450x200")
        dialog.transient(self.root)
        
        ttk.Label(dialog, text="🎯 Draw Hunt Region", font=("Arial", 14, "bold")).pack(pady=10)
        ttk.Label(dialog, text="Instructions:", font=("Arial", 10, "bold")).pack(pady=5)
        ttk.Label(dialog, text="1. Click OK button below", font=("Arial", 9)).pack()
        ttk.Label(dialog, text="2. Click and drag on your game screen to draw a rectangle", font=("Arial", 9)).pack()
        ttk.Label(dialog, text="3. Release mouse button to confirm selection", font=("Arial", 9)).pack()
        ttk.Label(dialog, text="4. The area you draw will be the hunt region", font=("Arial", 9)).pack(pady=5)
        
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
                    
                    self.log(f"✅ Hunt region set: X={x}, Y={y}, W={w}, H={h}")
                    self.log(f"   Generated {len(self.click_points)} click points in the region")
                else:
                    self.log("❌ Region too small! Please select a larger area.")
            else:
                self.log("❌ Selection cancelled.")
        
        ttk.Button(dialog, text="OK - Start Selection", command=start_selection).pack(pady=15)
        ttk.Button(dialog, text="Cancel", command=lambda: [dialog.destroy(), self.log("❌ Region selection cancelled")]).pack()
            
    def toggle_power_bar(self):
        self.power_bar_enabled = self.power_bar_var.get()
        if self.power_bar_enabled:
            self.log("⚡ Power Bar: ON")
            # Check if power bar image exists
            bar_images = self.get_power_bar_images()
            if not bar_images:
                self.log(f"⚠️ WARNING: 'bar_full.png' not found in '{POWER_BAR_FOLDER}' folder!")
            else:
                self.log(f"✅ Bar image loaded: {os.path.basename(bar_images[0])}")
        else:
            self.log("⚡ Power Bar Detection OFF")
        
    def log(self, message):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        
    def start_bot(self):
        # Get skill keys
        skills_text = self.skills_entry.get().strip()
        self.skills = [s.strip() for s in skills_text.split(',') if s.strip()]
        
        if not self.skills:
            self.log("❌ ERROR: Skill keys cannot be empty!")
            return
        
        # Check hunt region
        if not self.hunt_region:
            self.log("❌ ERROR: Hunt region not set!")
            self.log("   Click 'Set Hunt Region' button first")
            return
        
        # Check if monster names are provided
        monster_names_input = self.region_monsters_entry.get().strip()
        if not monster_names_input:
            self.log("❌ ERROR: No monster names specified!")
            self.log("   Enter monster names in the 'Monster Names' field (comma separated)")
            return
        
        # Log that we're using OCR mode
        monster_names = [name.strip() for name in monster_names_input.split(',')]
        self.log(f"✅ OCR-based detection (no images needed!)")
        self.log(f"   Hunting: {', '.join(monster_names)}")
        
        self.bot_running = True
        self.total_kills = 0
        self.start_time = time.time()
        
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_label.config(text="✅ RUNNING", foreground="green")
        
        self.log("=" * 60)
        self.log("🚀 BOT STARTED!")
        
        # Log hunt info
        x, y, w, h = self.hunt_region
        self.log(f"📍 Hunt Region: X={x}, Y={y}, W={w}, H={h}")
        monster_names_input = self.region_monsters_entry.get().strip()
        monster_names = [name.strip() for name in monster_names_input.split(',')]
        self.log(f"🎯 Hunting: {', '.join(monster_names)}")
        self.log(f"🎯 Skill keys: {', '.join(self.skills)}")
        self.log(f"⚙️ Skill interval: {self.skill_delay}s")
        self.log(f"⚙️ Mob interval: {self.mob_delay}s")
        if self.power_bar_enabled:
            bar_images = self.get_power_bar_images()
            self.log(f"⚡ Power Bar: ON")
            self.log(f"   Check interval: {self.power_bar_check_interval}s")
            if bar_images:
                self.log(f"   ✅ {len(bar_images)} bar image(s) loaded")
        if self.auto_tab_on_giant:
            self.log(f"🔥 Auto TAB on Giant: ON")
            self.log(f"   Cooldown: {self.giant_tab_cooldown:.1f}s between TABs")
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
        self.status_label.config(text="⭕ STOPPED", foreground="red")
        self.log("🛑 Bot stopped!")
        
    def update_timer(self):
        if self.bot_running and self.start_time:
            elapsed = int(time.time() - self.start_time)
            hours = elapsed // 3600
            minutes = (elapsed % 3600) // 60
            seconds = elapsed % 60
            self.time_label.config(text=f"Running Time: {hours:02d}:{minutes:02d}:{seconds:02d}")
            self.root.after(1000, self.update_timer)
            
    def get_power_bar_images(self):
        """Load power bar images."""
        valid_extensions = ('.png', '.jpg', '.jpeg')
        images = []
        
        if not os.path.exists(POWER_BAR_FOLDER):
            os.makedirs(POWER_BAR_FOLDER)
            return images
            
        for filename in os.listdir(POWER_BAR_FOLDER):
            if filename.lower().endswith(valid_extensions):
                images.append(os.path.join(POWER_BAR_FOLDER, filename))
                
        return images
        
    def check_power_bar(self, current_mob_name=""):
        """Check if power bar is full and press TAB."""
        current_time = time.time()
        
        # Skip if check interval hasn't passed
        if current_time - self.last_power_bar_check < self.power_bar_check_interval:
            time_remaining = self.power_bar_check_interval - (current_time - self.last_power_bar_check)
            return
            
        self.last_power_bar_check = current_time
        
        bar_images = self.get_power_bar_images()
        if not bar_images:
            return
        
        for img_path in bar_images:
            try:
                # Search for bar (lower confidence, lighting may vary)
                location = pyautogui.locateOnScreen(img_path, confidence=0.70, grayscale=False)
                
                if location is not None:
                    # Bar found! Press TAB
                    self.power_bar_uses += 1
                    self.root.after(0, lambda: self.power_bar_label.config(
                        text=f"⚡ Power Used: {self.power_bar_uses}"))
                    
                    keyboard.press_and_release('tab')
                    self.log(f"⚡ POWER ACTIVATED! (#{self.power_bar_uses})")
                    
                    # Wait 10 seconds after using power (for bar to refill)
                    self.last_power_bar_check = current_time + 10
                    return
            except Exception as e:
                continue
    
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
        
    def press_key(self, key):
        """Press a key using multiple methods for better compatibility."""
        try:
            # Method 1: Try pydirectinput (best for games)
            pydirectinput.press(key)
            time.sleep(0.01)
        except Exception as e:
            # Method 2: Fallback to keyboard library
            try:
                keyboard.press_and_release(key)
                time.sleep(0.01)
            except:
                pass
            
    def bot_loop(self):
        time.sleep(2)  # Initial delay
        
        while self.bot_running:
            # Check if Q key is pressed
            if keyboard.is_pressed('q'):
                self.root.after(0, self.stop_bot)
                break
                
            try:
                # OCR-based monster detection
                if not self.hunt_region:
                    self.log("❌ Hunt region not set! Click 'Set Hunt Region' button.")
                    time.sleep(3)
                    continue
                
                # Get monster names from user input
                monster_names_input = self.region_monsters_entry.get()
                if not monster_names_input.strip():
                    self.log("❌ No monster names specified! Enter monster names (comma separated).")
                    time.sleep(3)
                    continue
                
                monster_names = [name.strip().lower() for name in monster_names_input.split(',')]
                    
                # Take screenshot of the region
                x, y, w, h = self.hunt_region
                screenshot = pyautogui.screenshot(region=(x, y, w, h))
                    
                # Convert to OpenCV format for better OCR
                img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                
                # Apply thresholding for better text detection
                _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
                
                # Use Tesseract to get text with bounding boxes
                try:
                    ocr_data = pytesseract.image_to_data(thresh, output_type=pytesseract.Output.DICT, 
                                                         config='--psm 6')
                    
                    # Check for "Giant" text and auto TAB if enabled
                    if self.auto_tab_on_giant:
                        current_time = time.time()
                        # Check cooldown
                        if current_time - self.last_giant_tab >= self.giant_tab_cooldown:
                            # Search for "Giant" in all OCR text
                            for text in ocr_data['text']:
                                if text.strip() and 'giant' in text.lower():
                                    # Giant detected! Press TAB
                                    self.giant_tab_count += 1
                                    self.last_giant_tab = current_time
                                    self.root.after(0, lambda: self.giant_tab_label.config(
                                        text=f"🔥 Giant TABs: {self.giant_tab_count}"))
                                    
                                    keyboard.press_and_release('tab')
                                    self.log(f"🔥 GIANT DETECTED! Auto TAB pressed (#{self.giant_tab_count})")
                                    break  # Only press once per scan
                        
                    # Search for monster names in OCR results
                    found_monster = False
                    for i, text in enumerate(ocr_data['text']):
                        if not text.strip():
                            continue
                        
                        text_lower = text.lower()
                            
                        # Check if any monster name matches
                        for monster_name in monster_names:
                            # Flexible matching: check if monster name is in the text or vice versa
                            if monster_name in text_lower or text_lower in monster_name:
                                # Also check similarity for partial matches
                                if len(text_lower) >= 3 and (monster_name in text_lower or 
                                                              text_lower in monster_name or
                                                              self.text_similarity(monster_name, text_lower) > 0.6):
                                    found_monster = True
                                    
                                    # Get bounding box coordinates
                                    box_x = ocr_data['left'][i]
                                    box_y = ocr_data['top'][i]
                                    box_w = ocr_data['width'][i]
                                    box_h = ocr_data['height'][i]
                                    
                                    # Calculate center in screen coordinates
                                    center_x = x + box_x + box_w // 2
                                    center_y = y + box_y + box_h // 2
                                    
                                    self.total_kills += 1
                                    self.root.after(0, lambda: self.kills_label.config(
                                        text=f"Mobs Killed: {self.total_kills}"))
                                    
                                    self.log(f"🎯 [OCR] Found '{text}' (matched: {monster_name}) at ({center_x}, {center_y})")
                                    
                                    # Power bar check
                                    if self.power_bar_enabled:
                                        self.check_power_bar(monster_name)
                                    
                                    # Mouse movement and click
                                    offset_x = center_x + random.randint(-5, 5)
                                    offset_y = center_y + random.randint(-5, 5)
                                    pyautogui.moveTo(offset_x, offset_y, duration=0.08)
                                    pydirectinput.click()
                                    time.sleep(0.1)
                                    
                                    # Press skills
                                    skill_log = "   Skills: "
                                    for skill in self.skills:
                                        self.press_key(skill)
                                        skill_log += f"{skill} "
                                        time.sleep(self.skill_delay)
                                    
                                    self.log(skill_log + "✓")
                                    time.sleep(self.mob_delay)
                                    break
                        
                        if found_monster:
                            break
                    
                    if not found_monster:
                        # No monsters found, wait a bit
                        time.sleep(0.5)
                
                except Exception as e:
                    error_msg = str(e)
                    if "tesseract" in error_msg.lower():
                        self.log(f"⚠️ OCR Error: Tesseract not installed!")
                        self.log(f"   Run 'install_tesseract.bat' to install Tesseract OCR")
                        self.log(f"   Or download from: https://github.com/UB-Mannheim/tesseract/wiki")
                    else:
                        self.log(f"⚠️ OCR Error: {error_msg}")
                    time.sleep(3)
                
            except Exception as e:
                self.log(f"⚠️ Error: {e}")
                time.sleep(1)

def main():
    root = tk.Tk()
    app = BotGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
