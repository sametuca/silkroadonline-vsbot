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

# Optimize pydirectinput pause for games
pydirectinput.PAUSE = 0

# Monster images folder
MONSTERS_FOLDER = 'monsters'

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
        self.confidence = 0.78
        self.skill_delay = 0.15
        self.mob_delay = 0.2
        self.skills = ['1', '2', '3', '4']
        self.static_mode = False  # Static mode (no mouse movement)
        
        # Hunt mode: "images" or "region"
        self.hunt_mode = "images"  # Default to image detection
        self.hunt_region = None  # Hunt region (x, y, width, height)
        self.click_points = []  # Pre-calculated click points in region
        self.current_click_index = 0  # Current point index
        
        self.power_bar_enabled = False  # Power bar detection
        self.power_bar_check_interval = 17.0  # Bar check interval (seconds)
        self.power_bar_mode = "filtered"  # "filtered" or "always"
        self.power_bar_only_for = ""  # Use power bar only for these mobs (keywords)
        self.last_power_bar_check = 0
        self.power_bar_uses = 0  # How many times TAB pressed
        
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
        
        self.time_label = ttk.Label(status_frame, text="Running Time: 00:00:00", font=("Arial", 10))
        self.time_label.grid(row=3, column=0, pady=2)
        
        # Settings panel
        settings_frame = ttk.LabelFrame(main_frame, text="⚙️ Settings", padding="10")
        settings_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Confidence setting
        ttk.Label(settings_frame, text="Detection Confidence:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.confidence_var = tk.DoubleVar(value=0.78)
        confidence_slider = ttk.Scale(settings_frame, from_=0.5, to=0.95, variable=self.confidence_var, 
                                     orient=tk.HORIZONTAL, length=200, command=self.update_confidence)
        confidence_slider.grid(row=0, column=1, padx=5)
        self.confidence_value_label = ttk.Label(settings_frame, text="0.78")
        self.confidence_value_label.grid(row=0, column=2)
        
        # Skill delay setting
        ttk.Label(settings_frame, text="Skill Interval (sec):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.skill_delay_var = tk.DoubleVar(value=0.15)
        skill_delay_slider = ttk.Scale(settings_frame, from_=0.1, to=1.0, variable=self.skill_delay_var,
                                      orient=tk.HORIZONTAL, length=200, command=self.update_skill_delay)
        skill_delay_slider.grid(row=1, column=1, padx=5)
        self.skill_delay_label = ttk.Label(settings_frame, text="0.15")
        self.skill_delay_label.grid(row=1, column=2)
        
        # Mob delay setting
        ttk.Label(settings_frame, text="Mob Interval (sec):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.mob_delay_var = tk.DoubleVar(value=0.2)
        mob_delay_slider = ttk.Scale(settings_frame, from_=0.1, to=2.0, variable=self.mob_delay_var,
                                    orient=tk.HORIZONTAL, length=200, command=self.update_mob_delay)
        mob_delay_slider.grid(row=2, column=1, padx=5)
        self.mob_delay_label = ttk.Label(settings_frame, text="0.20")
        self.mob_delay_label.grid(row=2, column=2)
        
        # Skill keys
        ttk.Label(settings_frame, text="Skill Keys:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.skills_entry = ttk.Entry(settings_frame, width=15)
        self.skills_entry.insert(0, "1,2,3,4")
        self.skills_entry.grid(row=3, column=1, padx=5, sticky=tk.W)
        ttk.Label(settings_frame, text="(comma separated)").grid(row=3, column=2, sticky=tk.W)
        
        # Static mode (No mouse movement)
        self.static_mode_var = tk.BooleanVar(value=False)
        static_check = ttk.Checkbutton(settings_frame, text="⛔ Static Mode (No mouse movement)", 
                                      variable=self.static_mode_var, command=self.toggle_static_mode)
        static_check.grid(row=4, column=0, columnspan=3, sticky=tk.W, pady=5)
        
        # Hunt Mode Selection
        ttk.Label(settings_frame, text="Hunt Mode:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.hunt_mode_var = tk.StringVar(value="images")
        hunt_mode_frame = ttk.Frame(settings_frame)
        hunt_mode_frame.grid(row=5, column=1, columnspan=2, sticky=tk.W, pady=5)
        
        ttk.Radiobutton(hunt_mode_frame, text="📸 Image Detection", 
                       variable=self.hunt_mode_var, value="images").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(hunt_mode_frame, text="🎯 Region Mode", 
                       variable=self.hunt_mode_var, value="region").pack(side=tk.LEFT, padx=5)
        
        # Set Hunt Region button
        self.set_hunt_region_button = ttk.Button(settings_frame, text="📍 Set Hunt Region (for Region Mode)", 
                                                 command=self.set_hunt_region)
        self.set_hunt_region_button.grid(row=6, column=0, columnspan=3, pady=5)
        
        # Monster names for region mode
        ttk.Label(settings_frame, text="Monster Names:").grid(row=7, column=0, sticky=tk.W, pady=5)
        self.region_monsters_entry = ttk.Entry(settings_frame, width=25)
        self.region_monsters_entry.insert(0, "shakram, edimmu")
        self.region_monsters_entry.grid(row=7, column=1, padx=5, sticky=tk.W)
        ttk.Label(settings_frame, text="(for region mode)").grid(row=7, column=2, sticky=tk.W)
        
        # Power Bar detection
        self.power_bar_var = tk.BooleanVar(value=False)
        power_bar_check = ttk.Checkbutton(settings_frame, text="⚡ Power Bar Detection (TAB key)", 
                                         variable=self.power_bar_var, command=self.toggle_power_bar)
        power_bar_check.grid(row=8, column=0, columnspan=3, sticky=tk.W, pady=5)
        
        # Power bar check interval
        ttk.Label(settings_frame, text="Bar Check Interval (sec):").grid(row=9, column=0, sticky=tk.W, pady=5)
        self.bar_check_var = tk.DoubleVar(value=17.0)
        bar_check_slider = ttk.Scale(settings_frame, from_=5.0, to=30.0, variable=self.bar_check_var,
                                    orient=tk.HORIZONTAL, length=200, command=self.update_bar_interval)
        bar_check_slider.grid(row=9, column=1, padx=5)
        self.bar_check_label = ttk.Label(settings_frame, text="17.0")
        self.bar_check_label.grid(row=9, column=2)
        
        # Power bar mode selection
        ttk.Label(settings_frame, text="Power Bar Mode:").grid(row=10, column=0, sticky=tk.W, pady=5)
        self.power_bar_mode_var = tk.StringVar(value="filtered")
        mode_frame = ttk.Frame(settings_frame)
        mode_frame.grid(row=10, column=1, columnspan=2, sticky=tk.W, pady=5)
        
        ttk.Radiobutton(mode_frame, text="Only for specific mobs", 
                       variable=self.power_bar_mode_var, value="filtered").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(mode_frame, text="Always when full", 
                       variable=self.power_bar_mode_var, value="always").pack(side=tk.LEFT, padx=5)
        
        # Power bar filter (only shown when filtered mode)
        ttk.Label(settings_frame, text="Filter Keywords:").grid(row=11, column=0, sticky=tk.W, pady=5)
        self.power_bar_filter_entry = ttk.Entry(settings_frame, width=20)
        self.power_bar_filter_entry.insert(0, "giant")
        self.power_bar_filter_entry.grid(row=11, column=1, padx=5, sticky=tk.W)
        ttk.Label(settings_frame, text="(for filtered mode)").grid(row=11, column=2, sticky=tk.W)
        
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
        
    def update_confidence(self, value):
        self.confidence = float(value)
        self.confidence_value_label.config(text=f"{self.confidence:.2f}")
        
    def update_skill_delay(self, value):
        self.skill_delay = float(value)
        self.skill_delay_label.config(text=f"{self.skill_delay:.2f}")
        
    def update_mob_delay(self, value):
        self.mob_delay = float(value)
        self.mob_delay_label.config(text=f"{self.mob_delay:.2f}")
        
    def update_bar_interval(self, value):
        self.power_bar_check_interval = float(value)
        self.bar_check_label.config(text=f"{self.power_bar_check_interval:.1f}")
        
    def toggle_static_mode(self):
        self.static_mode = self.static_mode_var.get()
        if self.static_mode:
            self.log("⛔ Static Mode ON - Mouse movement DISABLED")
        else:
            self.log("➡️ Static Mode OFF - Mouse movement ENABLED")
    
    def set_hunt_region(self):
        """Let user select a hunt region by drawing on screen."""
        self.log("📍 Hunt Region Selection")
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
            power_mode = self.power_bar_mode_var.get()
            if power_mode == "filtered":
                power_filter = self.power_bar_filter_entry.get().strip()
                self.log(f"⚡ Power Bar: ON - Filtered mode (keywords: '{power_filter}')")
            else:
                self.log("⚡ Power Bar: ON - Always mode (all mobs)")
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
        
        # Get hunt mode
        hunt_mode = self.hunt_mode_var.get()
        
        # Check requirements based on mode
        if hunt_mode == "images":
            monster_images = self.get_monster_images()
            if not monster_images:
                self.log(f"❌ ERROR: No images found in '{MONSTERS_FOLDER}' folder!")
                self.log("   Either add monster images OR switch to Region Mode")
                return
        else:  # region mode
            monster_images = []
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
            
            # Check if at least one monster image exists (with smart matching)
            monster_names = [name.strip().lower() for name in monster_names_input.split(',')]
            
            # Get all available monster files for smart matching
            available_monsters = {}
            if os.path.exists(MONSTERS_FOLDER):
                for file in os.listdir(MONSTERS_FOLDER):
                    if file.endswith('.png'):
                        base_name = file[:-4]  # Remove .png
                        normalized = base_name.lower().replace(' ', '').replace('-', '').replace('_', '')
                        available_monsters[normalized] = file
            
            found_any = False
            matched_files = []
            for monster_name in monster_names:
                # Try direct match first
                monster_file = os.path.join(MONSTERS_FOLDER, f"{monster_name}.png")
                if os.path.exists(monster_file):
                    found_any = True
                    matched_files.append(f"{monster_name}.png")
                else:
                    # Try normalized matching
                    normalized_input = monster_name.replace(' ', '').replace('-', '').replace('_', '')
                    if normalized_input in available_monsters:
                        found_any = True
                        matched_files.append(f"{available_monsters[normalized_input]} (matched from '{monster_name}')")
            
            if not found_any:
                self.log("❌ ERROR: No monster images found!")
                self.log(f"   Make sure images exist in '{MONSTERS_FOLDER}' folder")
                self.log(f"   You entered: {', '.join(monster_names)}")
                self.log(f"   Available files: {', '.join([f for f in os.listdir(MONSTERS_FOLDER) if f.endswith('.png')])}")
                return
            else:
                self.log(f"✅ Matched {len(matched_files)} monster(s):")
                for mf in matched_files:
                    self.log(f"   - {mf}")
        
        self.bot_running = True
        self.total_kills = 0
        self.start_time = time.time()
        
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_label.config(text="✅ RUNNING", foreground="green")
        
        self.log("=" * 60)
        self.log("🚀 BOT STARTED!")
        
        # Log hunt mode info
        if hunt_mode == "images":
            self.log(f"📸 Mode: IMAGE DETECTION")
            self.log(f"📁 {len(monster_images)} different monsters loaded:")
            for img in monster_images:
                self.log(f"   - {os.path.basename(img)}")
        else:
            self.log(f"🎯 Mode: REGION MODE")
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
            power_mode = self.power_bar_mode_var.get()
            if power_mode == "filtered":
                power_filter = self.power_bar_filter_entry.get().strip()
                self.log(f"⚡ Power Bar: ON - Filtered mode (keywords: '{power_filter}')")
            else:
                self.log(f"⚡ Power Bar: ON - Always mode (all mobs)")
            self.log(f"   Check interval: {self.power_bar_check_interval}s")
            if bar_images:
                self.log(f"   ✅ {len(bar_images)} bar image(s) loaded")
        self.log("=" * 60)
        
        # Start bot thread
        self.bot_thread = threading.Thread(target=self.bot_loop, args=(monster_images,), daemon=True)
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
            
    def get_monster_images(self):
        valid_extensions = ('.png', '.jpg', '.jpeg')
        images = []
        
        if not os.path.exists(MONSTERS_FOLDER):
            os.makedirs(MONSTERS_FOLDER)
            return images
            
        for filename in os.listdir(MONSTERS_FOLDER):
            if filename.lower().endswith(valid_extensions):
                images.append(os.path.join(MONSTERS_FOLDER, filename))
                
        return images
        
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
        """Check if power bar is full and press TAB if conditions are met."""
        # Get current mode
        power_bar_mode = self.power_bar_mode_var.get()
        
        # Check if power bar should be used for this mob
        if power_bar_mode == "filtered":
            power_bar_filter = self.power_bar_filter_entry.get().strip().lower()
            
            if power_bar_filter:
                # If filter is set, check if current mob name contains any filter keyword
                mob_name_lower = current_mob_name.lower()
                filter_keywords = [kw.strip() for kw in power_bar_filter.split(',')]
                
                # Check if any keyword matches
                if not any(keyword in mob_name_lower for keyword in filter_keywords):
                    # This mob is not in the filter list, skip power bar
                    self.log(f"   ⏭️ [{current_mob_name}] - Skipping power bar (not giant)")
                    return
                else:
                    self.log(f"   ✓ [{current_mob_name}] matches filter, checking power bar...")
        else:
            # Always mode - use for all mobs
            self.log(f"   ⚡ [ALWAYS MODE] Checking power bar for [{current_mob_name}]...")
        
        current_time = time.time()
        
        # Skip if check interval hasn't passed
        if current_time - self.last_power_bar_check < self.power_bar_check_interval:
            time_remaining = self.power_bar_check_interval - (current_time - self.last_power_bar_check)
            self.log(f"   ⏳ Power bar cooldown: {time_remaining:.1f}s remaining")
            return
            
        self.last_power_bar_check = current_time
        
        bar_images = self.get_power_bar_images()
        if not bar_images:
            self.log(f"   ⚠️ No power bar image found in '{POWER_BAR_FOLDER}' folder!")
            return
        
        self.log(f"   🔍 Searching for power bar on screen...")
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
                    self.log(f"⚡ POWER ACTIVATED for [{current_mob_name}]! (#{self.power_bar_uses})")
                    
                    # Wait 10 seconds after using power (for bar to refill)
                    self.last_power_bar_check = current_time + 10
                    return
            except Exception as e:
                self.log(f"   ⚠️ Error detecting power bar: {e}")
                continue
        
        # Bar not found
        self.log(f"   ❌ Power bar not detected on screen (bar may not be full yet)")
        
    def find_any_monster(self, images):
        """Find any monster on screen from the list and return the closest one to screen center."""
        screen_width, screen_height = pyautogui.size()
        screen_center_x = screen_width // 2
        screen_center_y = screen_height // 2
        
        all_found_mobs = []  # List of (distance, center_point, mob_name)
        
        # Check all monster types
        for img_path in images:
            try:
                # Find all matches for this monster type
                locations = list(pyautogui.locateAllOnScreen(img_path, confidence=self.confidence, grayscale=False))
                
                if locations:
                    mob_name = os.path.basename(img_path)
                    # Add all found instances to list with their distance from screen center
                    for loc in locations:
                        center = pyautogui.center(loc)
                        # Calculate distance from screen center (Euclidean distance)
                        distance = ((center.x - screen_center_x) ** 2 + (center.y - screen_center_y) ** 2) ** 0.5
                        all_found_mobs.append((distance, center, mob_name))
            except:
                continue
        
        # If any mobs found, return the closest one
        if all_found_mobs:
            # Sort by distance (closest first)
            all_found_mobs.sort(key=lambda x: x[0])
            closest_distance, closest_center, closest_name = all_found_mobs[0]
            return closest_center, closest_name
        
        return None, None
        
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
            
    def bot_loop(self, monster_images):
        time.sleep(2)  # Initial delay
        hunt_mode = self.hunt_mode_var.get()
        
        while self.bot_running:
            # Check if Q key is pressed
            if keyboard.is_pressed('q'):
                self.root.after(0, self.stop_bot)
                break
                
            try:
                if hunt_mode == "region":
                    # Region mode: Search for specific monsters in the defined region
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
                    
                    # Get all available monster files for smart matching
                    available_monsters = {}
                    if os.path.exists(MONSTERS_FOLDER):
                        for file in os.listdir(MONSTERS_FOLDER):
                            if file.endswith('.png'):
                                # Store both original and normalized versions
                                base_name = file[:-4]  # Remove .png
                                normalized = base_name.lower().replace(' ', '').replace('-', '').replace('_', '')
                                available_monsters[normalized] = file
                    
                    # Search for each monster in the region
                    found_monster = False
                    for monster_name in monster_names:
                        # Try direct match first
                        monster_file = os.path.join(MONSTERS_FOLDER, f"{monster_name}.png")
                        
                        # If direct match doesn't exist, try normalized matching
                        if not os.path.exists(monster_file):
                            normalized_input = monster_name.replace(' ', '').replace('-', '').replace('_', '')
                            if normalized_input in available_monsters:
                                monster_file = os.path.join(MONSTERS_FOLDER, available_monsters[normalized_input])
                                self.log(f"💡 Matched '{monster_name}' to '{available_monsters[normalized_input]}'")
                            else:
                                continue
                        
                        try:
                            # Search only within the hunt region
                            location = pyautogui.locateOnScreen(monster_file, confidence=self.confidence, 
                                                               region=self.hunt_region)
                            
                            if location is not None:
                                found_monster = True
                                center_x, center_y = pyautogui.center(location)
                                
                                self.total_kills += 1
                                self.root.after(0, lambda: self.kills_label.config(
                                    text=f"Mobs Killed: {self.total_kills}"))
                                
                                self.log(f"🎯 [Region] Found {monster_name} at ({center_x}, {center_y})")
                                
                                # Power bar check
                                if self.power_bar_enabled:
                                    self.check_power_bar(monster_name)
                                
                                # Mouse movement and click (only if static mode is off)
                                if not self.static_mode:
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
                                break  # Found a monster, restart the search
                        
                        except Exception as e:
                            continue
                    
                    if not found_monster:
                        # No monsters found in region, wait a bit
                        time.sleep(0.5)
                    
                else:
                    # Image detection mode (original behavior)
                    location, found_name = self.find_any_monster(monster_images)
                    if location is not None:
                        self.total_kills += 1
                        self.root.after(0, lambda: self.kills_label.config(
                            text=f"Mobs Killed: {self.total_kills}"))
                        
                        self.log(f"🎯 [{found_name}] found! Attacking...")
                        
                        # Power bar check for this specific mob (if enabled)
                        if self.power_bar_enabled:
                            self.check_power_bar(found_name)
                        
                        # Mouse movement and click (only if static mode is off)
                        if not self.static_mode:
                            offset_x = location.x + random.randint(-3, 3)
                            offset_y = location.y + random.randint(-3, 3)
                            pyautogui.moveTo(offset_x, offset_y, duration=0.08)  # Slight animated movement
                            pydirectinput.click()
                            time.sleep(0.1)  # Wait for target selection
                        
                        # Press skills
                        skill_log = "   Skills: "
                        for skill in self.skills:
                            self.press_key(skill)
                            skill_log += f"{skill} "
                            time.sleep(self.skill_delay)
                        
                        self.log(skill_log + "✓")
                        time.sleep(self.mob_delay)
                    
            except Exception as e:
                self.log(f"⚠️ Error: {e}")
                time.sleep(1)

def main():
    root = tk.Tk()
    app = BotGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
