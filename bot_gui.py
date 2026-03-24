import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import sys
import subprocess
import threading
import pyautogui
import pydirectinput
import time
import os
import json
import webbrowser
import keyboard
import ctypes
from ctypes import wintypes
from PIL import Image, ImageTk
import cv2
import numpy as np

# Optimize pydirectinput pause for games
pydirectinput.PAUSE = 0

# Help tab: YouTube watch URL video ID only (the part after v=)
HELP_YOUTUBE_VIDEO_ID = ""

# LANGUAGE SUPPORT
LANGUAGES = {
    "TR": {
        "title": "Silkroad Vision Bot | Otomatik Av",
        "skill_interval": "Skill Aralığı:",
        "mob_interval": "Canavar Arası Bekleme:",
        "skill_keys": "Skill Tuşları:",
        "skill_keys_hint": "(1–8: işaretlenenler sırayla basılır)",
        "target_monsters": "Aranacak Canavarlar:",
        "auto_tab_toggle": "☑ Auto TAB Aktif",
        "auto_tab_interval": "Auto TAB Aralığı:",
        "input_method": "Input Yöntemi:",
        "keypress_only": "☑ Sadece Tuş Vuruşu Modu",
        "select_game_window": "Oyun penceresini seç",
        "set_hunt_region": "Manuel alan çiz (dikdörtgen)",
        "window_pick_title": "Pencere seç",
        "window_pick_hint": "Listeden oyun penceresini seç (client alanı = tarama bölgesi).",
        "window_refresh": "Yenile",
        "window_selected": "✅ Pencere: {} | Client: X={}, Y={}, W={}, H={}",
        "window_invalid": "❌ Seçili pencere artık geçerli değil (kapanmış olabilir).",
        "window_pick_none": "❌ Listeden bir satır seç.",
        "window_capture_printwindow_hint": (
            "   Görüntü doğrudan oyun penceresinden alınır; bot üstte olsa bile oyun içeriği okunur (Windows PrintWindow)."
        ),
        "window_capture_fallback_once": (
            "⚠️ Pencere yakalama siyah/boş döndü — geçici olarak ekran kopyası kullanılıyor. "
            "Botu kenara alın veya kenarlıksız tam ekran deneyin (bazı DirectX istemcileri PrintWindow desteklemez)."
        ),
        "status_mode_template_png": "Tespit: PNG şablon (monsters/)",
        "reclick_lockout": "Aynı bölgeye tekrar tıklama kilidi:",
        "reclick_hint": "(sn; skill sonrası zemine tıklayıp yürümeyi azaltır)",
        "click_certainty": "Hedef tıklama kesinliği:",
        "click_certainty_hint": "(yukarı çıktıkça bot daha seçici olur; boş alana tıklama azalır)",
        "skip_reclick_log": "⏭️ Aynı bölge — ek hedef tıklaması yok (skill devam)",
        "detect_log_skip_click": " | tıklama yok (aynı bölge kilidi)",
        "start": "BAŞLAT",
        "stop": "DUR",
        "log": "Log",
        "status_panel_title": "Durum",
        "press_q": "Botu durdurmak için Ctrl+Q tuşlarına basın",
        "draw_region": "Hunt Region Çiz",
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
        "error_hunt_not_set": "❌ HATA: Tarama alanı yok — pencere seç veya manuel alan çiz.",
        "error_click_button": "   'Oyun penceresini seç' veya 'Manuel alan çiz' kullan",
        "error_no_templates": "❌ HATA: Canavar template'i yüklenmedi!",
        "error_add_png": "   monsters/ klasörüne PNG dosyaları ekle",
        "save_monster_template": "Canavar şablonu kaydet → monsters/",
        "tpl_wizard_title": "Canavar şablonu kaydet",
        "tpl_wizard_hint": "Görüntü üzerinde sürükleyerek hedefi kırpın; şablon adını yazıp kaydedin.",
        "tpl_monster_name": "Şablon adı (dosya adı):",
        "tpl_save_btn": "Kaydet",
        "tpl_capture_fail": "Önce oyun penceresi seç veya hunt alanı çiz.",
        "tpl_saved": "✅ Kaydedildi: monsters/{}.png",
        "tpl_name_bad": "❌ Geçerli bir ad gir (ör: Mangyang veya Earth_Ghost).",
        "tpl_crop_small": "❌ Seçilen alan çok küçük.",
        "tpl_overwrite": "'{}' zaten var. Üzerine yazılsın mı?",
        "running": "✅ ÇALIŞIYOR",
        "stopped": "⏹️ DURDURULDU",
        "line_separator": "=" * 50,
        "wf_quick_start": "Sıra: ① Tarama alanı → ② İsim / şablon → ③ Skill’ler → ▶ Başlat",
        "ui_tab_status": "Durum",
        "ui_tab_scan": "Tarama",
        "ui_tab_monsters": "Canavar",
        "ui_tab_combat": "Savaş",
        "ui_tab_extra": "Ek ayarlar",
        "ui_tab_log": "Log",
        "ui_tab_help": "Yardım",
        "help_title": "Kolay kullanım videosu",
        "help_intro": "Botun kurulumu ve kullanımı için YouTube’daki adım adım videoyu aşağıdaki düğmeyle tarayıcıda açabilirsiniz.",
        "help_open_youtube": "YouTube’da izle",
        "help_no_video": "Henüz video tanımlı değil. bot_gui.py içinde HELP_YOUTUBE_VIDEO_ID sabitine, izleme adresindeki v= sonrası gelen video kimliğini yazın.",
        "wf_step1_title": "1 · Oyun ve tarama alanı",
        "wf_step1_hint": (
            "Oyun penceresi (kolay) veya «Manuel alan çiz»: bot yalnız bu dikdörtgende arar. "
            "İmleç yanlış yere gidiyorsa manuel alan deneyin — görüntü ve tıklama aynı ekran karesinden hesaplanır; "
            "pencere modundaki PrintWindow / ölçek kayması olmaz. Çizerken bot penceresini kenara alın."
        ),
        "wf_step2_title": "2 · Canavar ismi ve şablon",
        "wf_step2_hint": (
            "① «Canavar şablonu kaydet» ile hedefi kırpıp monsters/ klasörüne kaydedin. "
            "② Aşağıya şablon dosya adlarıyla uyumlu isimleri yazın (virgülle birden fazla) — hangi PNG’lerin aranacağını belirler."
        ),
        "wf_step3_title": "3 · Savaş (skill’ler)",
        "wf_step3_hint": "Tuş sırası ve gecikmeler. «Sadece tuş» açıksa hedef seçilmez.",
        "wf_step4_title": "4 · Ek ayarlar",
        "wf_step4_hint": "TAB, tekrar tıklama kilidi ve giriş yöntemi.",
        "status_modes_title": "Anlık mod özeti",
        "status_zerk_check": "☑ Zerk modu (oyunda açıksa işaretle — bot ekrandan algılamaz)",
        "status_bot_running": "Bot: çalışıyor",
        "status_bot_idle": "Bot: durdu",
        "status_hunt_window": "Tarama · pencere",
        "status_hunt_manual": "Tarama · manuel alan",
        "status_hunt_none": "Tarama · ayarlanmadı",
        "status_mode_keypress": "Sadece tuş",
        "status_mode_auto_tab": "Auto TAB",
        "status_zerk_line_on": "Zerk: AÇIK",
        "status_zerk_line_off": "Zerk: kapalı",
        "status_input": "Giriş",
        "status_click_certainty": "Tıklama kesinliği min skor",
        "buff_mode_toggle": "☑ Buff modu (F2 → seçili 1-8 → F1, saldırı çubuğuna dön)",
        "buff_keys": "Buff tuş sırası:",
        "buff_keys_hint": "(1-8: işaretlenenler soldan sağa sırayla basılır)",
        "buff_interval": "Buff yenileme aralığı:",
        "buff_interval_hint": "(saniye; süre dolunca tekrar F2 + skill)",
        "buff_cast_gap": "F2 çubuğunda tuşlar arası bekleme (sn):",
        "buff_cast_gap_hint": "(1’e bastıktan sonra animasyon bitene kadar bekle; skill aralığından ayrı)",
        "buff_slot_times": "İsteğe bağlı — her slot için sn (1→8, virgülle):",
        "buff_slot_times_hint": "Örn: 2,1.5,3,1,1,1,1,1 — boşsa yukarıdaki tek süre her aralıkta kullanılır.",
        "buff_repeat_12": "☑ Sıra bitince 1 ve 2’ye bir kez daha bas (isteğe bağlı; tuş aralığından bağımsız)",
        "status_buff_line": "Buff: her {} | F2 tuş ara: ~{} sn",
        "status_buff_off": "Buff: kapalı",
        "log_buff_cycle": "✨ Buff döngüsü: F2 → {}{} → F1",
        "error_empty_buff_skills": "❌ HATA: Buff modu açıkken en az 1 buff tuşu seçmelisin (1-8).",
        "language_label": "Dil:",
        "language_restart_title": "Dil değişikliği",
        "language_restart_confirm": (
            "Arayüzün güncellenmesi için uygulama yeniden başlatılacak. Devam edilsin mi?"
        ),
    },
    "EN": {
        "title": "Silkroad Vision Bot | Auto Hunter",
        "skill_interval": "Skill Interval:",
        "mob_interval": "Mob Interval:",
        "skill_keys": "Skill Keys:",
        "target_monsters": "Target Monsters:",
        "auto_tab_toggle": "☑ Auto TAB Enabled",
        "auto_tab_interval": "Auto TAB Interval:",
        "input_method": "Input Method:",
        "keypress_only": "☑ Keypress Only Mode",
        "select_game_window": "Select game window",
        "set_hunt_region": "Draw region manually (rectangle)",
        "window_pick_title": "Pick window",
        "window_pick_hint": "Choose your game window (client area = scan region).",
        "window_refresh": "Refresh",
        "window_selected": "✅ Window: {} | Client: X={}, Y={}, W={}, H={}",
        "window_invalid": "❌ Selected window is no longer valid (closed?).",
        "window_pick_none": "❌ Select a row in the list.",
        "window_capture_printwindow_hint": (
            "   Capture reads the game window directly; the bot GUI on top does not block pixels (Windows PrintWindow)."
        ),
        "window_capture_fallback_once": (
            "⚠️ Window capture was black/empty — using screen grab for now. "
            "Move this app aside or try borderless fullscreen (some DirectX clients break PrintWindow)."
        ),
        "status_mode_template_png": "Detect: PNG templates (monsters/)",
        "reclick_lockout": "Same-spot click lockout:",
        "reclick_hint": "(sec; reduces move-to-ground clicks after skills)",
        "click_certainty": "Target click certainty:",
        "click_certainty_hint": "(higher = stricter; reduces empty-area clicks)",
        "skip_reclick_log": "⏭️ Same area — no extra target click (skills continue)",
        "detect_log_skip_click": " | click skipped (same-area lockout)",
        "start": "START",
        "stop": "STOP",
        "log": "Log",
        "status_panel_title": "Status",
        "press_q": "Press Ctrl+Q to stop the bot",
        "draw_region": "Draw Hunt Region",
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
        "error_hunt_not_set": "❌ ERROR: No scan area — select a window or draw a region.",
        "error_click_button": "   Use 'Select game window' or 'Draw region manually'",
        "error_no_templates": "❌ ERROR: No monster templates loaded!",
        "error_add_png": "   Add PNG files to monsters/ folder",
        "save_monster_template": "Save monster template → monsters/",
        "tpl_wizard_title": "Save monster template",
        "tpl_wizard_hint": "Drag on the image to crop the target, enter a template name, then save.",
        "tpl_monster_name": "Template name (filename):",
        "tpl_save_btn": "Save",
        "tpl_capture_fail": "Select game window or draw hunt region first.",
        "tpl_saved": "✅ Saved: monsters/{}.png",
        "tpl_name_bad": "❌ Enter a valid name (e.g. Mangyang or Earth_Ghost).",
        "tpl_crop_small": "❌ Crop area is too small.",
        "tpl_overwrite": "'{}' already exists. Overwrite?",
        "running": "✅ RUNNING",
        "stopped": "⏹️ STOPPED",
        "line_separator": "=" * 50,
        "wf_quick_start": "Order: ① Scan area → ② Names / template → ③ Skills → ▶ Start",
        "ui_tab_status": "Status",
        "ui_tab_scan": "Scan",
        "ui_tab_monsters": "Monsters",
        "ui_tab_combat": "Combat",
        "ui_tab_extra": "Extras",
        "ui_tab_log": "Log",
        "ui_tab_help": "Help",
        "help_title": "Quick start video",
        "help_intro": "Open the step-by-step tutorial on YouTube in your browser using the button below.",
        "help_open_youtube": "Watch on YouTube",
        "help_no_video": "No video is configured yet. Set HELP_YOUTUBE_VIDEO_ID in bot_gui.py to your YouTube video ID (the part after v= in the watch URL).",
        "wf_step1_title": "1 · Game & scan area",
        "wf_step1_hint": (
            "Game window (easiest) or «Draw region manually»: the bot only searches that rectangle. "
            "If clicks land in the wrong place, try manual region — capture and clicks use the same screen crop, "
            "avoiding PrintWindow / scaling mismatch from window capture. Move the bot aside while drawing."
        ),
        "wf_step2_title": "2 · Monster names & template",
        "wf_step2_hint": (
            "① Use «Save monster template» to crop the target and save it under monsters/. "
            "② Type names that match your PNG filenames below (comma-separated) — they select which templates to scan for."
        ),
        "wf_step3_title": "3 · Combat (skills)",
        "wf_step3_hint": "Skill keys and delays. Keypress-only skips targeting.",
        "wf_step4_title": "4 · Extra options",
        "wf_step4_hint": "TAB, click lockout, and input method.",
        "status_modes_title": "Live mode summary",
        "status_zerk_check": "☑ Zerk mode (check if active in-game — not auto-detected)",
        "status_bot_running": "Bot: running",
        "status_bot_idle": "Bot: stopped",
        "status_hunt_window": "Scan · window",
        "status_hunt_manual": "Scan · manual rect",
        "status_hunt_none": "Scan · not set",
        "status_mode_keypress": "Keypress only",
        "status_mode_auto_tab": "Auto TAB",
        "status_zerk_line_on": "Zerk: ON",
        "status_zerk_line_off": "Zerk: off",
        "status_input": "Input",
        "status_click_certainty": "Click certainty min score",
        "buff_mode_toggle": "☑ Buff mode (F2 → selected 1-8 → F1, back to attack bar)",
        "buff_keys": "Buff key order:",
        "buff_keys_hint": "(1-8: checked slots are pressed left-to-right)",
        "buff_interval": "Buff refresh interval:",
        "buff_interval_hint": "(seconds; F2 + skills again when due)",
        "buff_cast_gap": "Delay between F2 bar keys (sec):",
        "buff_cast_gap_hint": "(wait for cast animation; independent from attack skill interval)",
        "buff_slot_times": "Optional per-slot delays in sec (1->8, comma):",
        "buff_slot_times_hint": "Ex: 2,1.5,3,1,1,1,1,1 - empty uses uniform delay above.",
        "buff_repeat_12": "☑ Press 1 and 2 again after buff row",
        "status_buff_line": "Buff: every {} | F2 key gap: ~{} s",
        "status_buff_off": "Buff: off",
        "log_buff_cycle": "✨ Buff cycle: F2 → {}{} → F1",
        "error_empty_buff_skills": "❌ ERROR: Enable at least 1 buff key (1-8) when buff mode is on.",
        "language_label": "Language:",
        "language_restart_title": "Change language",
        "language_restart_confirm": (
            "The application will restart to update the interface. Continue?"
        ),
    }
}

# Load/Set language
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


class _BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD),
        ("biWidth", wintypes.LONG),
        ("biHeight", wintypes.LONG),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", wintypes.LONG),
        ("biYPelsPerMeter", wintypes.LONG),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
    ]


class _BITMAPINFO(ctypes.Structure):
    _fields_ = [("bmiHeader", _BITMAPINFOHEADER)]


PW_CLIENTONLY = 0x00000001
PW_RENDERFULLCONTENT = 0x00000002
DIB_RGB_COLORS = 0


def _capture_hwnd_client_pil(hwnd):
    """
    Capture HWND client area via PrintWindow into a PIL RGB image.
    Unlike screen grabs, overlapping windows (e.g. this bot) do not cover the game pixels.
    Some DirectX clients may return black; caller may fall back to screen capture.
    """
    try:
        hwnd = int(hwnd)
        u = ctypes.windll.user32
        g = ctypes.windll.gdi32
        if not u.IsWindow(hwnd) or u.IsIconic(hwnd):
            return None
        rect = wintypes.RECT()
        if not u.GetClientRect(hwnd, ctypes.byref(rect)):
            return None
        w = int(rect.right - rect.left)
        h = int(rect.bottom - rect.top)
        if w < 8 or h < 8:
            return None
        hdc = u.GetDC(hwnd)
        if not hdc:
            return None
        hdc_mem = None
        hbmp = None
        try:
            hdc_mem = g.CreateCompatibleDC(hdc)
            if not hdc_mem:
                return None
            hbmp = g.CreateCompatibleBitmap(hdc, w, h)
            if not hbmp:
                return None
            g.SelectObject(hdc_mem, hbmp)
            ok = int(
                u.PrintWindow(hwnd, hdc_mem, PW_CLIENTONLY | PW_RENDERFULLCONTENT)
            )
            if not ok:
                ok = int(u.PrintWindow(hwnd, hdc_mem, PW_CLIENTONLY))
            if not ok:
                return None
            bmi = _BITMAPINFO()
            bmi.bmiHeader.biSize = ctypes.sizeof(_BITMAPINFOHEADER)
            bmi.bmiHeader.biWidth = w
            bmi.bmiHeader.biHeight = -h
            bmi.bmiHeader.biPlanes = 1
            bmi.bmiHeader.biBitCount = 32
            buf = (ctypes.c_ubyte * (w * h * 4))()
            lines = int(
                g.GetDIBits(
                    hdc_mem,
                    hbmp,
                    0,
                    h,
                    ctypes.byref(buf),
                    ctypes.byref(bmi),
                    DIB_RGB_COLORS,
                )
            )
            if lines == 0:
                return None
            arr = np.frombuffer(buf, dtype=np.uint8).reshape((h, w, 4))
            rgb = cv2.cvtColor(arr, cv2.COLOR_BGRA2RGB)
            return Image.fromarray(rgb)
        finally:
            if hbmp:
                g.DeleteObject(hbmp)
            if hdc_mem:
                g.DeleteDC(hdc_mem)
            u.ReleaseDC(hwnd, hdc)
    except Exception:
        return None


def _try_set_process_dpi_aware():
    """Align GDI capture / client rect with mouse coordinates on scaled Windows desktops."""
    try:
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    except Exception:
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass


def _client_area_screen_rect(hwnd):
    """Return (x, y, w, h) in screen pixels for HWND client area, or None."""
    try:
        hwnd = int(hwnd)
        u = ctypes.windll.user32
        if not u.IsWindow(hwnd):
            return None
        if u.IsIconic(hwnd):
            return None
        rect = wintypes.RECT()
        if not u.GetClientRect(hwnd, ctypes.byref(rect)):
            return None
        pt = wintypes.POINT(0, 0)
        if not u.ClientToScreen(hwnd, ctypes.byref(pt)):
            return None
        w = rect.right - rect.left
        h = rect.bottom - rect.top
        if w < 80 or h < 80:
            return None
        return (int(pt.x), int(pt.y), int(w), int(h))
    except Exception:
        return None


def _enumerate_top_level_windows(min_w=200, min_h=200):
    """List (hwnd, title) for visible top-level windows, rough size filter."""
    u = ctypes.windll.user32
    out = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def _cb(hwnd, _lp):
        if not u.IsWindowVisible(hwnd):
            return True
        ln = u.GetWindowTextLengthW(hwnd)
        if ln <= 0:
            return True
        buf = ctypes.create_unicode_buffer(ln + 1)
        u.GetWindowTextW(hwnd, buf, ln + 1)
        title = buf.value.strip()
        if not title:
            return True
        r = wintypes.RECT()
        if not u.GetWindowRect(hwnd, ctypes.byref(r)):
            return True
        ww = r.right - r.left
        hh = r.bottom - r.top
        if ww < min_w or hh < min_h:
            return True
        out.append((hwnd, title))
        return True

    u.EnumWindows(_cb, 0)
    out.sort(key=lambda t: t[1].lower())
    return out


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
        self.root.resizable(True, True)
        self.root.minsize(900, 720)
        self._apply_initial_window_geometry(1120, 1040)
        self.root.bind_all("<Control-q>", self._on_hotkey_stop)
        self.root.bind_all("<Control-Q>", self._on_hotkey_stop)

        # Bot status
        self.bot_running = False
        self.bot_thread = None
        self.skill_delay = 0.03
        self.mob_delay = 0.018
        self.skills = ['1', '2', '3', '4']
        self.buff_mode = False
        self.buff_interval_s = 30 * 60
        self.buff_repeat_12 = False
        self.buff_keys = ["1", "2", "3", "4", "5"]
        self._buff_slot_delays = [1.2, 1.2, 1.2, 1.2, 1.2]
        self._buff_cast_gap_default = 1.2
        self._last_buff_time = 0.0
        self.keypress_only_mode = False  # Start in template detection mode by default
        self.input_method = "auto"  # auto, sendinput, pydirectinput, keyboard
        self.target_monster_names = []

        # Auto TAB system
        self.auto_tab_enabled = True
        self.auto_tab_interval = 15  # seconds
        self.last_auto_tab_time = 0
        
        # Hunt region (manual rect or game window client area)
        self.hunt_region = None  # (x, y, width, height) screen coords
        self.hunt_source = "none"  # "window" | "manual" | "none"
        self.hunt_window_hwnd = None
        self.hunt_window_title = ""
        self.click_points = []  # Pre-calculated click points in region
        self.current_click_index = 0  # Current point index
        
        self.monster_templates = {}  # {monster_name: {color, gray, width, height}}
        self.template_threshold = 0.16  # template match minimum score
        self.min_click_confidence = 0.66  # hard floor before we allow target clicks
        self.min_confidence_gap = 0.035  # top-vs-runner-up gap to avoid ambiguous matches
        self.template_debug = True  # Show all match scores for debugging
        self.template_scales = [0.80, 0.90, 1.00, 1.10, 1.20]
        self.template_scales_advanced = [0.76, 0.84, 0.92, 1.00, 1.08, 1.16, 1.24]
        self.advanced_vision_match = True
        self._clahe = None  # lazy: cv2.createCLAHE
        self.no_detection_count = 0
        self.last_no_detection_log_time = 0
        # After a click, ignore same monster near same hunt-relative spot (dead body / nameplate linger).
        # Too long = visible pause while the template still matches the corpse; too short = double-tap dead mob.
        self.target_click_cooldown = 1.05
        self.target_position_tolerance = 72  # Pixel tolerance for "same target"
        self.reclick_lockout_s = 2.5  # Screen: block another ground click near last hit for this long
        self.reclick_screen_tolerance_px = 128  # Pixels (screen) — same "spot" radius
        self._no_reclick_screen_until = 0.0
        self._last_attack_click_screen = None  # (sx, sy) last successful target click
        self._last_skip_click_log = 0.0
        self.recent_target_clicks = []
        self.last_cooldown_log_time = 0
        self.template_loc_agreement_px = 38
        self._last_window_invalid_log = 0.0
        self._printwindow_fallback_logged = False
        
        # Statistics
        self.start_time = None
        self._gui_photo_refs = []
        self._icon_cache = {}

        self.setup_ui()

    def _apply_initial_window_geometry(self, width, height):
        """Set default size and center on the primary monitor."""
        try:
            sw = int(self.root.winfo_screenwidth())
            sh = int(self.root.winfo_screenheight())
            x = max(0, (sw - width) // 2)
            y = max(0, (sh - height) // 2)
            self.root.geometry(f"{width}x{height}+{x}+{y}")
        except tk.TclError:
            self.root.geometry(f"{width}x{height}")

    def show_language_selection(self):
        """Show language selection dialog on first launch."""
        d_bg = "#f4f6fa"
        d_panel = "#ffffff"
        d_accent = "#b45309"
        d_border = "#e2e8f0"
        dialog = tk.Toplevel(self.root)
        dialog.title("Language Selection / Dil Seçimi")
        dialog.geometry("380x220")
        dialog.configure(bg=d_bg)
        dialog.transient(self.root)
        dialog.grab_set()

        outer = tk.Frame(dialog, bg=d_border, padx=1, pady=1)
        outer.pack(fill=tk.BOTH, expand=True, padx=14, pady=14)
        box = tk.Frame(outer, bg=d_panel, padx=22, pady=20)
        box.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            box,
            text="Select Language / Dil Seç",
            font=("Segoe UI", 13, "bold"),
            fg=d_accent,
            bg=d_panel,
        ).pack(pady=(0, 6))
        tk.Label(
            box,
            text="Silkroad Vision Bot",
            font=("Segoe UI", 9),
            fg="#64748b",
            bg=d_panel,
        ).pack(pady=(0, 14))

        def select_lang(lang):
            save_language(lang)
            global CURRENT_LANGUAGE
            CURRENT_LANGUAGE = lang
            dialog.destroy()

        def _btn(parent, text, cmd):
            b = tk.Button(
                parent,
                text=text,
                command=cmd,
                font=("Segoe UI", 10, "bold"),
                fg="#ffffff",
                bg=d_accent,
                activebackground="#d97706",
                activeforeground="#ffffff",
                relief=tk.FLAT,
                padx=16,
                pady=10,
                cursor="hand2",
                width=22,
            )
            b.pack(pady=5)
            return b

        _btn(box, "🇹🇷 Türkçe", lambda: select_lang("TR"))
        _btn(box, "🇬🇧 English", lambda: select_lang("EN"))

        self.root.wait_window(dialog)

    def _on_ui_language_change(self, event=None):
        sel = self.lang_var.get()
        if sel not in LANGUAGES:
            self.lang_var.set(CURRENT_LANGUAGE)
            return
        if sel == CURRENT_LANGUAGE:
            return
        if not messagebox.askyesno(
            parent=self.root,
            title=tr("language_restart_title"),
            message=tr("language_restart_confirm"),
        ):
            self.lang_var.set(CURRENT_LANGUAGE)
            return
        prev = CURRENT_LANGUAGE
        save_language(sel)
        try:
            subprocess.Popen([sys.executable, *sys.argv])
        except Exception:
            save_language(prev)
            self.lang_var.set(prev)
            messagebox.showerror(
                parent=self.root,
                title="Error",
                message="Could not restart. Please close and open the app manually.",
            )
            return
        self.root.destroy()

    def _help_youtube_watch_url(self):
        vid = (HELP_YOUTUBE_VIDEO_ID or "").strip()
        if not vid:
            return ""
        return f"https://www.youtube.com/watch?v={vid}"

    def _open_help_youtube(self):
        url = self._help_youtube_watch_url()
        if url:
            webbrowser.open(url)

    def _load_help_youtube_thumbnail_async(self):
        vid = (HELP_YOUTUBE_VIDEO_ID or "").strip()
        if not vid:
            return

        def worker():
            try:
                req = urllib.request.Request(
                    f"https://img.youtube.com/vi/{vid}/hqdefault.jpg",
                    headers={"User-Agent": "Mozilla/5.0"},
                )
                with urllib.request.urlopen(req, timeout=12) as resp:
                    data = resp.read()
            except Exception:
                return
            self.root.after(0, lambda d=data: self._apply_help_youtube_thumb(d))

        threading.Thread(target=worker, daemon=True).start()

    def _apply_help_youtube_thumb(self, jpeg_bytes):
        if not jpeg_bytes:
            return
        try:
            im = Image.open(io.BytesIO(jpeg_bytes))
            im = im.convert("RGB")
            max_w = 720
            w, h = im.size
            if w > max_w and w > 0:
                r = max_w / float(w)
                im = im.resize(
                    (max(1, int(w * r)), max(1, int(h * r))),
                    Image.Resampling.LANCZOS,
                )
            self._help_thumb_photo = ImageTk.PhotoImage(im)
        except Exception:
            return
        lbl = getattr(self, "_help_thumb_label", None)
        if lbl is None:
            return
        lbl.configure(image=self._help_thumb_photo)
        lbl.pack(anchor=tk.W, pady=(8, 6))

    def _load_header_logo_asset(self, max_height=118):
        """Load Silkroad Online logo from assets/ for the header; keep aspect ratio."""
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "sro_logo.png")
        if not os.path.isfile(path):
            return None
        try:
            im = Image.open(path)
            if im.mode not in ("RGBA", "RGB"):
                im = im.convert("RGBA")
            w, h = im.size
            if h > max_height and h > 0:
                r = max_height / float(h)
                im = im.resize(
                    (max(1, int(w * r)), max(1, int(h * r))),
                    Image.Resampling.LANCZOS,
                )
            return ImageTk.PhotoImage(im)
        except Exception:
            return None

    def _get_action_icon(self, name, size=18, recolor_rgb=None):
        """Load assets/icons/{name}.png, resize, optional monochrome tint. Cached."""
        key = (name, int(size), recolor_rgb)
        if key in self._icon_cache:
            return self._icon_cache[key]
        path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "assets", "icons", f"{name}.png"
        )
        if not os.path.isfile(path):
            self._icon_cache[key] = None
            return None
        try:
            im = Image.open(path).convert("RGBA")
            im = im.resize((size, size), Image.Resampling.LANCZOS)
            if recolor_rgb:
                arr = np.asarray(im, dtype=np.uint8).copy()
                mask = arr[:, :, 3] > 8
                arr[mask, 0] = recolor_rgb[0]
                arr[mask, 1] = recolor_rgb[1]
                arr[mask, 2] = recolor_rgb[2]
                im = Image.fromarray(arr, mode="RGBA")
            ph = ImageTk.PhotoImage(im)
            self._gui_photo_refs.append(ph)
            self._icon_cache[key] = ph
            return ph
        except Exception:
            self._icon_cache[key] = None
            return None

    def _btn_icon_opts(self, name, size=18, recolor_rgb=None):
        img = self._get_action_icon(name, size, recolor_rgb)
        if img:
            return {"image": img, "compound": tk.LEFT}
        return {}

    def setup_ui(self):
        style = ttk.Style()
        style.theme_use("clam")

        # Light mode — clean paper, warm amber + teal accents
        bg_canvas = "#e2e8f0"
        bg_panel = "#ffffff"
        bg_inset = "#f8fafc"
        fg_color = "#1e293b"
        fg_muted = "#64748b"
        accent_gold = "#b45309"
        accent_jade = "#0d9488"
        border_line = "#cbd5e1"
        btn_hover = "#e2e8f0"
        danger_bg = "#fee2e2"
        danger_fg = "#991b1b"
        ico_slate = (30, 41, 59)
        ico_white = (255, 255, 255)
        ico_danger = (153, 27, 27)

        self.root.configure(bg=bg_canvas)

        style.configure("TFrame", background=bg_panel)
        style.configure("TLabel", background=bg_panel, foreground=fg_color)
        style.configure(
            "TLabelframe",
            background=bg_panel,
            foreground=fg_color,
            borderwidth=1,
            relief="solid",
            bordercolor=border_line,
        )
        style.configure(
            "TLabelframe.Label",
            background=bg_panel,
            foreground=accent_gold,
            font=("Segoe UI", 10, "bold"),
        )
        style.configure(
            "TButton",
            font=("Segoe UI", 9),
            padding=(14, 8),
            background=bg_inset,
            foreground=fg_color,
            borderwidth=1,
            bordercolor=border_line,
            focuscolor="none",
        )
        style.map(
            "TButton",
            background=[("active", btn_hover), ("disabled", bg_inset)],
            foreground=[("disabled", fg_muted)],
        )
        style.configure(
            "Accent.TButton",
            font=("Segoe UI", 10, "bold"),
            padding=(18, 10),
            background="#d97706",
            foreground="#ffffff",
            borderwidth=0,
            focuscolor="none",
        )
        style.map(
            "Accent.TButton",
            background=[("active", "#ea580c"), ("disabled", "#cbd5e1")],
            foreground=[("disabled", "#94a3b8")],
        )
        style.configure(
            "Danger.TButton",
            font=("Segoe UI", 10, "bold"),
            padding=(18, 10),
            background=danger_bg,
            foreground=danger_fg,
            borderwidth=1,
            bordercolor="#fecaca",
            focuscolor="none",
        )
        style.map(
            "Danger.TButton",
            background=[("active", "#fecaca"), ("disabled", bg_inset)],
            foreground=[("disabled", fg_muted)],
        )
        style.configure(
            "Title.TLabel",
            font=("Segoe UI", 22, "bold"),
            foreground=accent_gold,
            background=bg_panel,
        )
        style.configure(
            "Subtitle.TLabel",
            font=("Segoe UI", 11),
            foreground=accent_jade,
            background=bg_panel,
        )
        style.configure(
            "Info.TLabel",
            font=("Segoe UI", 8),
            foreground=fg_muted,
            background=bg_panel,
        )
        style.configure(
            "TCheckbutton",
            background=bg_panel,
            foreground=fg_color,
            focuscolor="none",
        )
        style.map("TCheckbutton", background=[("active", bg_panel)])
        style.configure(
            "TEntry",
            fieldbackground=bg_inset,
            foreground=fg_color,
            insertcolor=accent_jade,
            bordercolor=border_line,
        )
        style.configure(
            "TCombobox",
            fieldbackground=bg_inset,
            foreground=fg_color,
            insertcolor=fg_color,
            bordercolor=border_line,
            arrowcolor=accent_gold,
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", bg_inset)],
            selectbackground=[("readonly", bg_inset)],
        )
        style.configure(
            "Horizontal.TScale",
            background=bg_panel,
            troughcolor=bg_inset,
            bordercolor=border_line,
        )
        style.configure(
            "Vertical.TScrollbar",
            background=bg_inset,
            troughcolor=bg_canvas,
            bordercolor=bg_canvas,
            arrowcolor=bg_inset,
        )
        style.configure("TSeparator", background=border_line)
        style.configure("TNotebook", background=bg_panel, borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            background=bg_inset,
            foreground=fg_color,
            padding=(12, 6),
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", bg_panel)],
            expand=[("selected", [1, 1, 1, 0])],
        )

        main_bg = tk.Canvas(self.root, bg=bg_canvas, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=main_bg.yview)
        scrollable_frame = ttk.Frame(main_bg)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: main_bg.configure(scrollregion=main_bg.bbox("all")),
        )
        _scroll_win = main_bg.create_window((0, 0), window=scrollable_frame, anchor="nw")

        def _sync_scroll_width(event):
            main_bg.itemconfig(_scroll_win, width=max(1, event.width))

        main_bg.bind("<Configure>", _sync_scroll_width)
        main_bg.configure(yscrollcommand=scrollbar.set)

        main_bg.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def _on_mousewheel(event):
            main_bg.yview_scroll(int(-1 * (event.delta / 120)), "units")

        main_bg.bind_all("<MouseWheel>", _on_mousewheel)

        scrollable_frame.columnconfigure(0, weight=1)

        main_frame = ttk.Frame(scrollable_frame, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=2)

        wrap_tab = 820

        # HEADER (language + logo + credits)
        header_wrap = ttk.Frame(main_frame)
        header_wrap.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 14))
        header_frame = tk.Frame(header_wrap, bg=bg_panel, padx=12)
        header_frame.pack(fill=tk.X, pady=(14, 10))

        lang_row = tk.Frame(header_frame, bg=bg_panel)
        lang_row.pack(fill=tk.X, pady=(0, 6))
        lang_inner = tk.Frame(lang_row, bg=bg_panel)
        lang_inner.pack(side=tk.RIGHT)
        ttk.Label(lang_inner, text=tr("language_label"), style="Info.TLabel").pack(
            side=tk.LEFT, padx=(0, 6)
        )
        self.lang_var = tk.StringVar(value=CURRENT_LANGUAGE)
        lang_cb = ttk.Combobox(
            lang_inner,
            textvariable=self.lang_var,
            values=["TR", "EN"],
            state="readonly",
            width=5,
        )
        lang_cb.pack(side=tk.LEFT)
        lang_cb.bind("<<ComboboxSelected>>", self._on_ui_language_change)

        self._header_logo_photo = self._load_header_logo_asset(max_height=120)
        if self._header_logo_photo:
            tk.Label(
                header_frame,
                image=self._header_logo_photo,
                bg=bg_panel,
                bd=0,
                highlightthickness=0,
            ).pack(pady=(0, 4))
        else:
            ttk.Label(header_frame, text="SILKROAD VISION BOT", style="Title.TLabel").pack()

        ttk.Label(
            header_frame,
            text="◆  Auto Hunter  ·  Template · Vision  ◆",
            style="Subtitle.TLabel",
        ).pack(pady=(6, 2))
        github_frame = ttk.Frame(header_frame)
        github_frame.pack(pady=(2, 0))
        ttk.Label(github_frame, text="Developed by: Samet UCA", style="Info.TLabel").pack()
        ttk.Label(
            github_frame,
            text="github.com/SametUCA",
            style="Info.TLabel",
            foreground=accent_jade,
            cursor="hand2",
        ).pack()
        _email_lbl = ttk.Label(
            github_frame,
            text="sametuca@hotmail.com",
            style="Info.TLabel",
            foreground=accent_jade,
            cursor="hand2",
        )
        _email_lbl.pack()
        _email_lbl.bind(
            "<Button-1>",
            lambda _e: webbrowser.open("mailto:sametuca@hotmail.com"),
        )

        # Shared toggles (status panel + steps need same BooleanVars)
        self.zerk_mode_var = tk.BooleanVar(value=False)
        self.keypress_only_var = tk.BooleanVar(value=False)
        self.auto_tab_enabled_var = tk.BooleanVar(value=True)

        # ============ TABBED SETTINGS ============
        self.main_notebook = ttk.Notebook(main_frame)
        self.main_notebook.grid(
            row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(6, 0)
        )

        tab_status = ttk.Frame(self.main_notebook, padding=10)
        tab_scan = ttk.Frame(self.main_notebook, padding=10)
        tab_monsters = ttk.Frame(self.main_notebook, padding=10)
        tab_combat = ttk.Frame(self.main_notebook, padding=10)
        tab_extra = ttk.Frame(self.main_notebook, padding=10)
        tab_log = ttk.Frame(self.main_notebook, padding=10)
        tab_help = ttk.Frame(self.main_notebook, padding=10)

        self.main_notebook.add(tab_status, text=tr("ui_tab_status"))
        self.main_notebook.add(tab_scan, text=tr("ui_tab_scan"))
        self.main_notebook.add(tab_monsters, text=tr("ui_tab_monsters"))
        self.main_notebook.add(tab_combat, text=tr("ui_tab_combat"))
        self.main_notebook.add(tab_extra, text=tr("ui_tab_extra"))
        self.main_notebook.add(tab_log, text=tr("ui_tab_log"))
        self.main_notebook.add(tab_help, text=tr("ui_tab_help"))

        log_frame = ttk.LabelFrame(tab_log, text=tr("log"), padding="12")
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=16,
            width=92,
            font=("Consolas", 10),
            bg="#f8fafc",
            fg="#0f172a",
            insertbackground=accent_jade,
            selectbackground="#ccfbf1",
            selectforeground=fg_color,
            relief=tk.FLAT,
            borderwidth=0,
            highlightthickness=1,
            highlightbackground=border_line,
            highlightcolor=accent_jade,
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        help_frame = ttk.LabelFrame(tab_help, text=tr("help_title"), padding="12")
        help_frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(
            help_frame,
            text=tr("help_intro"),
            wraplength=wrap_tab,
            justify=tk.LEFT,
        ).pack(anchor=tk.W, pady=(0, 8))
        _help_vid = (HELP_YOUTUBE_VIDEO_ID or "").strip()
        open_btn = ttk.Button(
            help_frame,
            text=tr("help_open_youtube"),
            command=self._open_help_youtube,
        )
        open_btn.pack(anchor=tk.W, pady=(0, 4))
        if not _help_vid:
            open_btn.state(["disabled"])
            ttk.Label(
                help_frame,
                text=tr("help_no_video"),
                wraplength=wrap_tab,
                justify=tk.LEFT,
            ).pack(anchor=tk.W, pady=(8, 0))
        else:
            self._help_thumb_label = tk.Label(help_frame, cursor="hand2", bd=0)
            self._help_thumb_label.bind("<Button-1>", lambda e: self._open_help_youtube())
            self._help_thumb_photo = None
            self._load_help_youtube_thumbnail_async()

        # ============ STATUS PANEL ============
        status_frame = ttk.LabelFrame(tab_status, text=tr("status_panel_title"), padding="14")
        status_frame.pack(fill=tk.BOTH, expand=True)
        status_inner = ttk.Frame(status_frame)
        status_inner.pack(fill=tk.BOTH, expand=True)

        top_status = ttk.Frame(status_inner)
        top_status.pack(fill=tk.X, pady=(0, 6))
        self.status_label = ttk.Label(
            top_status,
            text="⭕ " + tr("stopped"),
            font=("Segoe UI", 13, "bold"),
            foreground="#dc2626",
        )
        self.status_label.pack(side=tk.LEFT, anchor=tk.W)
        self.time_label = ttk.Label(
            top_status,
            text="Running Time: 00:00:00",
            font=("Segoe UI", 10),
            foreground=fg_muted,
        )
        self.time_label.pack(side=tk.RIGHT, anchor=tk.E, padx=(12, 0))

        ttk.Separator(status_inner, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=8)

        ttk.Label(
            status_inner,
            text=tr("status_modes_title"),
            font=("Segoe UI", 10, "bold"),
            foreground=accent_gold,
        ).pack(anchor=tk.W)
        self.status_modes_detail = tk.Text(
            status_inner,
            height=4,
            font=("Consolas", 9),
            bg="#f8fafc",
            fg=fg_color,
            insertwidth=0,
            relief="flat",
            borderwidth=0,
            highlightthickness=1,
            highlightbackground=border_line,
            highlightcolor=accent_jade,
            padx=8,
            pady=8,
            wrap=tk.WORD,
            cursor="arrow",
            takefocus=False,
        )
        for _tag, _opts in (
            ("sm_ok", {"foreground": "#047857"}),
            ("sm_err", {"foreground": "#b91c1c"}),
            ("sm_zerk_on", {"foreground": "#b45309"}),
            ("sm_muted", {"foreground": "#64748b"}),
            ("sm_feat", {"foreground": "#0369a1"}),
            ("sm_debug", {"foreground": "#6d28d9"}),
            ("sm_info", {"foreground": "#475569"}),
        ):
            self.status_modes_detail.tag_configure(_tag, **_opts)
        self.status_modes_detail.pack(anchor=tk.W, fill=tk.X, pady=(4, 8))

        zerk_row = ttk.Frame(status_inner)
        zerk_row.pack(fill=tk.X, pady=(0, 6))
        ttk.Checkbutton(
            zerk_row,
            text=tr("status_zerk_check"),
            variable=self.zerk_mode_var,
            command=self.refresh_status_modes,
        ).pack(anchor=tk.W)

        ttk.Separator(status_inner, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=8)
        ttk.Label(
            status_inner,
            text=tr("wf_quick_start"),
            style="Info.TLabel",
            font=("Segoe UI", 9),
            wraplength=wrap_tab,
        ).pack(anchor=tk.W, pady=(0, 2))

        # ============ STEP 1 — Scan area ============
        step1 = ttk.LabelFrame(tab_scan, text=tr("wf_step1_title"), padding="12")
        step1.pack(fill=tk.X, expand=False)
        step1.columnconfigure(1, weight=1)
        ttk.Label(step1, text=tr("wf_step1_hint"), style="Info.TLabel", wraplength=wrap_tab).grid(
            row=0, column=0, columnspan=3, sticky=tk.W, pady=(0, 8)
        )
        hunt_btn_frame = ttk.Frame(step1)
        hunt_btn_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=2)
        hunt_btn_frame.columnconfigure(0, weight=1)
        hunt_btn_frame.columnconfigure(1, weight=1)
        self.select_window_button = ttk.Button(
            hunt_btn_frame,
            text=tr("select_game_window"),
            command=self.select_game_window,
            **self._btn_icon_opts("window", 18, ico_slate),
        )
        self.select_window_button.grid(row=0, column=0, padx=(0, 4), sticky="ew")
        self.set_hunt_region_button = ttk.Button(
            hunt_btn_frame,
            text=tr("set_hunt_region"),
            command=self.set_hunt_region,
            **self._btn_icon_opts("region", 18, ico_slate),
        )
        self.set_hunt_region_button.grid(row=0, column=1, padx=(4, 0), sticky="ew")

        # ============ STEP 2 — Names & template ============
        step2 = ttk.LabelFrame(tab_monsters, text=tr("wf_step2_title"), padding="12")
        step2.pack(fill=tk.BOTH, expand=True)
        step2.columnconfigure(1, weight=1)
        ttk.Label(step2, text=tr("wf_step2_hint"), style="Info.TLabel", wraplength=wrap_tab).grid(
            row=0, column=0, columnspan=3, sticky=tk.W, pady=(0, 8)
        )
        self.save_template_button = ttk.Button(
            step2,
            text=tr("save_monster_template"),
            command=self.open_monster_template_wizard,
            **self._btn_icon_opts("template", 18, ico_slate),
        )
        self.save_template_button.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(0, 10))
        ttk.Label(step2, text=tr("target_monsters")).grid(row=2, column=0, sticky=tk.W, pady=6)
        self.target_monsters_entry = ttk.Entry(step2, width=28)
        self.target_monsters_entry.insert(0, "Earth Ghost")
        self.target_monsters_entry.grid(row=2, column=1, padx=8, sticky="ew")
        ttk.Label(step2, text="(name1,name2)", style="Info.TLabel").grid(row=2, column=2, sticky=tk.W, padx=5)

        # ============ STEP 3 — Skills ============
        step3 = ttk.LabelFrame(tab_combat, text=tr("wf_step3_title"), padding="12")
        step3.pack(fill=tk.BOTH, expand=True)
        step3.columnconfigure(1, weight=1)
        ttk.Label(step3, text=tr("wf_step3_hint"), style="Info.TLabel", wraplength=wrap_tab).grid(
            row=0, column=0, columnspan=3, sticky=tk.W, pady=(0, 8)
        )
        keypress_only_check = ttk.Checkbutton(
            step3,
            text=tr("keypress_only"),
            variable=self.keypress_only_var,
            command=self.toggle_keypress_only_mode,
        )
        keypress_only_check.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(0, 6))
        ttk.Label(step3, text=tr("skill_keys")).grid(row=2, column=0, sticky=tk.W, pady=6)
        self.skill_bar_slot_keys = ("1", "2", "3", "4", "5", "6", "7", "8")
        self.skill_slot_vars = [tk.BooleanVar(value=(i < 4)) for i in range(8)]
        skill_box_frame = ttk.Frame(step3)
        skill_box_frame.grid(row=2, column=1, padx=8, sticky="w")
        for idx, key in enumerate(self.skill_bar_slot_keys):
            ttk.Checkbutton(
                skill_box_frame,
                text=key,
                variable=self.skill_slot_vars[idx],
            ).grid(row=0, column=idx, padx=(0, 4))
        ttk.Label(step3, text=tr("skill_keys_hint"), style="Info.TLabel").grid(
            row=2, column=2, sticky=tk.W, padx=5
        )
        ttk.Label(step3, text=tr("skill_interval")).grid(row=3, column=0, sticky=tk.W, pady=6)
        self.skill_delay_var = tk.DoubleVar(value=0.03)
        skill_delay_slider = ttk.Scale(
            step3,
            from_=0.0,
            to=1.0,
            variable=self.skill_delay_var,
            orient=tk.HORIZONTAL,
            length=200,
            command=self.update_skill_delay,
        )
        skill_delay_slider.grid(row=3, column=1, padx=8, sticky="ew")
        self.skill_delay_label = ttk.Label(step3, text="0.03 s", width=8)
        self.skill_delay_label.grid(row=3, column=2, padx=5)
        ttk.Label(step3, text=tr("mob_interval")).grid(row=4, column=0, sticky=tk.W, pady=6)
        self.mob_delay_var = tk.DoubleVar(value=0.018)
        mob_delay_slider = ttk.Scale(
            step3,
            from_=0.0,
            to=2.0,
            variable=self.mob_delay_var,
            orient=tk.HORIZONTAL,
            length=200,
            command=self.update_mob_delay,
        )
        mob_delay_slider.grid(row=4, column=1, padx=8, sticky="ew")
        self.mob_delay_label = ttk.Label(step3, text="0.02 s", width=8)
        self.mob_delay_label.grid(row=4, column=2, padx=5)
        self.update_skill_delay(self.skill_delay_var.get())
        self.update_mob_delay(self.mob_delay_var.get())

        self.buff_mode_var = tk.BooleanVar(value=False)
        buff_mode_check = ttk.Checkbutton(
            step3,
            text=tr("buff_mode_toggle"),
            variable=self.buff_mode_var,
            command=self.refresh_status_modes,
        )
        buff_mode_check.grid(row=5, column=0, columnspan=3, sticky=tk.W, pady=(8, 4))
        ttk.Label(step3, text=tr("buff_keys")).grid(row=6, column=0, sticky=tk.W, pady=6)
        self.buff_bar_slot_keys = ("1", "2", "3", "4", "5", "6", "7", "8")
        self.buff_slot_vars = [tk.BooleanVar(value=(i < 5)) for i in range(8)]
        buff_box_frame = ttk.Frame(step3)
        buff_box_frame.grid(row=6, column=1, padx=8, sticky="w")
        for idx, key in enumerate(self.buff_bar_slot_keys):
            ttk.Checkbutton(
                buff_box_frame,
                text=key,
                variable=self.buff_slot_vars[idx],
                command=self.refresh_status_modes,
            ).grid(row=0, column=idx, padx=(0, 4))
        ttk.Label(step3, text=tr("buff_keys_hint"), style="Info.TLabel").grid(
            row=6, column=2, sticky=tk.W, padx=5
        )

        ttk.Label(step3, text=tr("buff_interval")).grid(row=7, column=0, sticky=tk.W, pady=6)
        self.buff_interval_var = tk.DoubleVar(value=1800.0)
        buff_interval_slider = ttk.Scale(
            step3,
            from_=1,
            to=5400,
            variable=self.buff_interval_var,
            orient=tk.HORIZONTAL,
            length=200,
            command=self.update_buff_interval,
        )
        buff_interval_slider.grid(row=7, column=1, padx=8, sticky="ew")
        self.buff_interval_label = ttk.Label(step3, text="30 dk 0 sn", width=12)
        self.buff_interval_label.grid(row=7, column=2, padx=5)
        ttk.Label(step3, text=tr("buff_interval_hint"), style="Info.TLabel").grid(
            row=8, column=0, columnspan=3, sticky=tk.W, pady=(0, 4)
        )
        ttk.Label(step3, text=tr("buff_cast_gap")).grid(row=9, column=0, sticky=tk.W, pady=6)
        self.buff_cast_gap_var = tk.DoubleVar(value=1.2)
        buff_cast_gap_slider = ttk.Scale(
            step3,
            from_=0.2,
            to=12.0,
            variable=self.buff_cast_gap_var,
            orient=tk.HORIZONTAL,
            length=200,
            command=self.update_buff_cast_gap,
        )
        buff_cast_gap_slider.grid(row=9, column=1, padx=8, sticky="ew")
        self.buff_cast_gap_label = ttk.Label(step3, text="1.2 s", width=10)
        self.buff_cast_gap_label.grid(row=9, column=2, padx=5)
        ttk.Label(step3, text=tr("buff_cast_gap_hint"), style="Info.TLabel").grid(
            row=10, column=0, columnspan=3, sticky=tk.W, pady=(0, 2)
        )
        ttk.Label(step3, text=tr("buff_slot_times"), style="Info.TLabel").grid(
            row=11, column=0, columnspan=3, sticky=tk.W, pady=(6, 0)
        )
        self.buff_slot_delays_entry = ttk.Entry(step3, width=36)
        self.buff_slot_delays_entry.grid(row=12, column=0, columnspan=3, sticky=tk.W, pady=2)
        ttk.Label(step3, text=tr("buff_slot_times_hint"), style="Info.TLabel").grid(
            row=13, column=0, columnspan=3, sticky=tk.W, pady=(0, 4)
        )
        self.buff_repeat_12_var = tk.BooleanVar(value=True)
        buff_repeat_check = ttk.Checkbutton(
            step3,
            text=tr("buff_repeat_12"),
            variable=self.buff_repeat_12_var,
            command=self.refresh_status_modes,
        )
        buff_repeat_check.grid(row=14, column=0, columnspan=3, sticky=tk.W, pady=2)
        self.update_buff_interval(str(self.buff_interval_var.get()))
        self.update_buff_cast_gap(str(self.buff_cast_gap_var.get()))
        self.buff_slot_delays_entry.bind("<KeyRelease>", lambda _e: self.refresh_status_modes())

        # ============ STEP 4 — Extras ============
        step4 = ttk.LabelFrame(tab_extra, text=tr("wf_step4_title"), padding="12")
        step4.pack(fill=tk.BOTH, expand=True)
        step4.columnconfigure(1, weight=1)
        ttk.Label(step4, text=tr("wf_step4_hint"), style="Info.TLabel", wraplength=wrap_tab).grid(
            row=0, column=0, columnspan=3, sticky=tk.W, pady=(0, 8)
        )
        ttk.Label(step4, text=tr("input_method")).grid(row=1, column=0, sticky=tk.W, pady=6)
        self.input_method_var = tk.StringVar(value="Auto (Recommended)")
        self.input_method_combo = ttk.Combobox(
            step4,
            textvariable=self.input_method_var,
            state="readonly",
            width=30,
            values=[
                "Auto (Recommended)",
                "SendInput (Scan Code)",
                "PyDirectInput",
                "Keyboard Library",
            ],
        )
        self.input_method_combo.grid(row=1, column=1, columnspan=2, sticky="ew", padx=8)
        self.input_method_combo.bind("<<ComboboxSelected>>", self.update_input_method)
        auto_tab_check = ttk.Checkbutton(
            step4,
            text=tr("auto_tab_toggle"),
            variable=self.auto_tab_enabled_var,
            command=self.toggle_auto_tab,
        )
        auto_tab_check.grid(row=2, column=0, columnspan=3, sticky=tk.W, pady=6)
        ttk.Label(step4, text=tr("auto_tab_interval")).grid(row=3, column=0, sticky=tk.W, pady=6)
        self.auto_tab_interval_var = tk.DoubleVar(value=15)
        auto_tab_slider = ttk.Scale(
            step4,
            from_=5,
            to=60,
            variable=self.auto_tab_interval_var,
            orient=tk.HORIZONTAL,
            length=200,
            command=self.update_auto_tab_interval,
        )
        auto_tab_slider.grid(row=3, column=1, padx=8, sticky="ew")
        self.auto_tab_interval_label = ttk.Label(step4, text="15 sn", width=8)
        self.auto_tab_interval_label.grid(row=3, column=2, padx=5)
        ttk.Label(step4, text=tr("reclick_lockout")).grid(row=4, column=0, sticky=tk.W, pady=6)
        self.reclick_lockout_var = tk.DoubleVar(value=2.5)
        reclick_slider = ttk.Scale(
            step4,
            from_=0.0,
            to=12.0,
            variable=self.reclick_lockout_var,
            orient=tk.HORIZONTAL,
            length=200,
            command=self.update_reclick_lockout,
        )
        reclick_slider.grid(row=4, column=1, padx=8, sticky="ew")
        self.reclick_lockout_label = ttk.Label(step4, text="2.5 sn", width=8)
        self.reclick_lockout_label.grid(row=4, column=2, padx=5)
        ttk.Label(step4, text=tr("reclick_hint"), style="Info.TLabel").grid(
            row=5, column=0, columnspan=3, sticky=tk.W, pady=(0, 4)
        )

        ttk.Label(step4, text=tr("click_certainty")).grid(row=6, column=0, sticky=tk.W, pady=6)
        self.min_click_confidence_var = tk.DoubleVar(value=float(self.min_click_confidence))
        certainty_slider = ttk.Scale(
            step4,
            from_=0.16,
            to=0.85,
            variable=self.min_click_confidence_var,
            orient=tk.HORIZONTAL,
            length=200,
            command=self.update_min_click_confidence,
        )
        certainty_slider.grid(row=6, column=1, padx=8, sticky="ew")
        self.min_click_confidence_label = ttk.Label(step4, text=f"{self.min_click_confidence:.2f}", width=8)
        self.min_click_confidence_label.grid(row=6, column=2, padx=5)
        ttk.Label(step4, text=tr("click_certainty_hint"), style="Info.TLabel").grid(
            row=7, column=0, columnspan=3, sticky=tk.W, pady=(0, 4)
        )

        # ============ BUTTONS ============
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(14, 8))

        self.start_button = ttk.Button(
            button_frame,
            text=tr("start"),
            command=self.start_bot,
            width=22,
            style="Accent.TButton",
            **self._btn_icon_opts("start", 20, ico_white),
        )
        self.start_button.pack(side="left", padx=8)

        self.stop_button = ttk.Button(
            button_frame,
            text=tr("stop"),
            command=self.stop_bot,
            width=22,
            state=tk.DISABLED,
            style="Danger.TButton",
            **self._btn_icon_opts("stop", 20, ico_danger),
        )
        self.stop_button.pack(side="left", padx=8)

        # ============ FOOTER ============
        footer_frame = ttk.Frame(main_frame)
        footer_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(12, 4))
        ttk.Label(
            footer_frame,
            text=tr("press_q") + "  ·  © 2026 Samet UCA",
            style="Info.TLabel",
        ).pack()

        self.refresh_status_modes()

    def refresh_status_modes(self):
        """Update Status panel summary (zerk + hunt + toggles)."""
        if not hasattr(self, "status_modes_detail"):
            return
        t = self.status_modes_detail
        t.configure(state=tk.NORMAL)
        t.delete("1.0", tk.END)

        def add_line(text, tag=None):
            if tag:
                t.insert(tk.END, text + "\n", tag)
            else:
                t.insert(tk.END, text + "\n")

        if getattr(self, "bot_running", False):
            add_line("● " + tr("status_bot_running"), "sm_ok")
        else:
            add_line("○ " + tr("status_bot_idle"), "sm_err")

        hs = getattr(self, "hunt_source", "none")
        if hs == "window":
            wt = (getattr(self, "hunt_window_title", None) or "").strip() or "—"
            if len(wt) > 42:
                wt = wt[:40] + "…"
            add_line("· " + tr("status_hunt_window") + ": " + wt, "sm_ok")
        elif hs == "manual":
            add_line("· " + tr("status_hunt_manual"), "sm_ok")
        else:
            add_line("· " + tr("status_hunt_none"), "sm_err")

        if self.zerk_mode_var.get():
            add_line("· " + tr("status_zerk_line_on"), "sm_zerk_on")
        else:
            add_line("· " + tr("status_zerk_line_off"), "sm_muted")

        if self.keypress_only_var.get():
            add_line("· " + tr("status_mode_keypress"), "sm_feat")
        else:
            add_line("· " + tr("status_mode_template_png"), "sm_feat")
        if self.auto_tab_enabled_var.get():
            add_line("· " + tr("status_mode_auto_tab"), "sm_feat")

        if hasattr(self, "input_method_var"):
            im = self.input_method_var.get()
            if im:
                add_line("· " + tr("status_input") + ": " + im, "sm_info")

        add_line(
            "· " + tr("status_click_certainty") + f": {getattr(self, 'min_click_confidence', 0.66):.2f}",
            "sm_info",
        )

        if getattr(self, "buff_mode_var", None) and self.buff_mode_var.get():
            try:
                sec = int(round(float(self.buff_interval_var.get())))
            except (tk.TclError, TypeError, ValueError):
                sec = 1800
            gap_u = 1.2
            bgv = getattr(self, "buff_cast_gap_var", None)
            if bgv is not None:
                try:
                    gap_u = float(bgv.get())
                except (tk.TclError, TypeError, ValueError):
                    gap_u = 1.2
            gap_u = max(0.2, min(12.0, gap_u))
            gap_txt = f"{gap_u:.1f}"
            ent = getattr(self, "buff_slot_delays_entry", None)
            if ent is not None and ent.get().strip():
                gap_txt = gap_txt + "*"
            add_line("· " + tr("status_buff_line").format(self._format_seconds(sec), gap_txt), "sm_ok")
        elif getattr(self, "buff_mode_var", None):
            add_line("· " + tr("status_buff_off"), "sm_muted")

        try:
            line_count = int(t.index("end-1c").split(".")[0])
        except (tk.TclError, ValueError):
            line_count = 1
        t.configure(height=min(max(line_count, 2), 24), state=tk.DISABLED)

    def update_skill_delay(self, value):
        self.skill_delay = float(value)
        self.skill_delay_label.config(text=f"{self.skill_delay:.2f}")
        
    def update_mob_delay(self, value):
        self.mob_delay = float(value)
        self.mob_delay_label.config(text=f"{self.mob_delay:.2f}")

    def update_buff_interval(self, value):
        try:
            sec = float(value)
        except (TypeError, ValueError):
            sec = 1800.0
        sec = max(1.0, min(5400.0, sec))
        self.buff_interval_label.config(text=self._format_seconds(int(round(sec))))
        self.refresh_status_modes()

    @staticmethod
    def _format_seconds(total_seconds):
        s = max(1, int(round(float(total_seconds))))
        m, sec = divmod(s, 60)
        if m <= 0:
            return f"{sec} sn"
        return f"{m} dk {sec} sn"

    def update_buff_cast_gap(self, value):
        try:
            g = float(value)
        except (TypeError, ValueError):
            try:
                g = float(self.buff_cast_gap_var.get())
            except (tk.TclError, TypeError, ValueError):
                g = 1.2
        g = max(0.2, min(12.0, g))
        self.buff_cast_gap_label.config(text=f"{g:.1f} sn")
        self.refresh_status_modes()

    @staticmethod
    def _coerce_buff_slot_delays(raw, uniform, expected_count):
        """Parse optional per-slot delays (seconds after each selected F2-bar key)."""
        n = max(1, int(expected_count))
        u = max(0.15, min(15.0, float(uniform)))
        if not (raw or "").strip():
            return [u] * n
        parts = [p.strip() for p in raw.replace(";", ",").split(",") if p.strip()]
        nums = []
        for p in parts:
            try:
                nums.append(max(0.05, float(p)))
            except ValueError:
                return [u] * n
        if len(nums) >= n:
            out = nums[:n]
        elif len(nums) > 0:
            out = nums + [nums[-1]] * (n - len(nums))
        else:
            return [u] * n
        return [min(15.0, max(0.05, x)) for x in out]

    def _parse_buff_slot_delays(self):
        try:
            u = float(self.buff_cast_gap_var.get())
        except (tk.TclError, TypeError, ValueError):
            u = 1.2
        u = max(0.2, min(12.0, u))
        raw = self.buff_slot_delays_entry.get().strip() if hasattr(self, "buff_slot_delays_entry") else ""
        return BotGUI._coerce_buff_slot_delays(raw, u, len(getattr(self, "buff_keys", [])))

    def update_reclick_lockout(self, value):
        self.reclick_lockout_s = max(0.0, float(value))
        self.reclick_lockout_label.config(text=f"{self.reclick_lockout_s:.1f} sn")

    def update_min_click_confidence(self, value):
        try:
            v = float(value)
        except (TypeError, ValueError):
            v = float(getattr(self, "min_click_confidence", 0.66))
        v = max(0.16, min(0.85, v))
        self.min_click_confidence = v
        if hasattr(self, "min_click_confidence_label"):
            self.min_click_confidence_label.config(text=f"{v:.2f}")
        self.refresh_status_modes()

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
        self.refresh_status_modes()

    def toggle_keypress_only_mode(self):
        self.keypress_only_mode = self.keypress_only_var.get()
        if self.keypress_only_mode:
            self.log("⌨️ Sadece Tuş Vuruşu Modu: ON")
            self.log("   Canavar seçimi yapılmayacak")
        else:
            self.log("🎯 Görüntü modu: ON (monsters/ PNG şablon)")
        self.refresh_status_modes()
    
    def update_auto_tab_interval(self, value):
        """Update auto TAB interval in seconds."""
        seconds = float(value)
        self.auto_tab_interval = seconds
        self.auto_tab_interval_label.config(text=f"{seconds:.0f} sn")

    def toggle_auto_tab(self):
        """Enable/disable auto TAB key presses."""
        self.auto_tab_enabled = self.auto_tab_enabled_var.get()
        if self.auto_tab_enabled:
            self.log("⚔️ Auto TAB: ON")
        else:
            self.log("⚔️ Auto TAB: OFF")
        self.refresh_status_modes()

    def _rebuild_click_points(self, x, y, w, h):
        self.click_points = []
        rows, cols = 6, 8
        for row in range(rows):
            for col in range(cols):
                px = x + (w // (cols + 1)) * (col + 1)
                py = y + (h // (rows + 1)) * (row + 1)
                self.click_points.append((px, py))

    def resolve_hunt_region(self):
        """Current scan rectangle in screen coordinates, or None."""
        if self.hunt_source == "window" and self.hunt_window_hwnd:
            return _client_area_screen_rect(self.hunt_window_hwnd)
        if self.hunt_region:
            return self.hunt_region
        return None

    def _hunt_rel_from_screenshot(self, rel_x, rel_y, screenshot, client_w, client_h):
        """Map detection coords (same space as PIL capture) to client-rect pixels for mouse."""
        try:
            sw, sh = screenshot.size
        except Exception:
            sw, sh = 0, 0
        if sw <= 0 or sh <= 0 or client_w <= 0 or client_h <= 0:
            return int(rel_x), int(rel_y)
        if sw != client_w or sh != client_h:
            if not getattr(self, "_hunt_scale_mismatch_logged", False):
                self._hunt_scale_mismatch_logged = True
                self.log(
                    f"⚙️ Görüntü {sw}×{sh} ≠ tarama {client_w}×{client_h} px — "
                    f"tıklama ölçekleniyor (DPI/ölçek uyumu)."
                )
            rel_x = rel_x * (client_w / float(sw))
            rel_y = rel_y * (client_h / float(sh))
        rx = int(round(rel_x))
        ry = int(round(rel_y))
        return max(0, min(client_w - 1, rx)), max(0, min(client_h - 1, ry))

    def _capture_hunt_screenshot_pil(self):
        """
        PIL RGB image of the hunt area.
        Window source: PrintWindow on the game HWND (other windows on top do not occlude pixels).
        Manual region: screen grab (overlapping windows still appear in the crop).
        """
        try:
            if self.hunt_source == "window" and self.hunt_window_hwnd:
                im = _capture_hwnd_client_pil(self.hunt_window_hwnd)
                if im is not None:
                    arr = np.asarray(im, dtype=np.uint8)
                    if arr.size > 0 and float(arr.mean()) > 2.5:
                        return im
                    reg = _client_area_screen_rect(self.hunt_window_hwnd)
                    if reg:
                        if not self._printwindow_fallback_logged:
                            self.log(tr("window_capture_fallback_once"))
                            self._printwindow_fallback_logged = True
                        return pyautogui.screenshot(region=reg).convert("RGB")
                    return None
                reg = _client_area_screen_rect(self.hunt_window_hwnd)
                if reg:
                    if not self._printwindow_fallback_logged:
                        self.log(tr("window_capture_fallback_once"))
                        self._printwindow_fallback_logged = True
                    return pyautogui.screenshot(region=reg).convert("RGB")
                return None
            reg = self.resolve_hunt_region()
            if not reg:
                return None
            return pyautogui.screenshot(region=reg).convert("RGB")
        except Exception:
            return None

    def select_game_window(self):
        """Pick a top-level window; hunt region = its client area (updates while playing if window moves)."""
        self._window_pick_entries = []

        bg_main = "#f4f6fa"
        bg_inset = "#ffffff"
        fg_color = "#1e293b"
        accent_teal = "#0d9488"
        border_line = "#cbd5e1"

        dialog = tk.Toplevel(self.root)
        dialog.title(tr("window_pick_title"))
        dialog.geometry("660x560")
        dialog.minsize(540, 460)
        dialog.resizable(True, True)
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(bg=bg_main)

        hint = ttk.Label(dialog, text=tr("window_pick_hint"), wraplength=600)
        hint.pack(side=tk.TOP, fill=tk.X, padx=14, pady=(14, 8))

        mid = ttk.Frame(dialog)
        mid.pack(fill=tk.BOTH, expand=True)

        action_row = ttk.Frame(mid)
        btn_row = ttk.Frame(mid)
        list_frame = ttk.Frame(mid)

        sb = ttk.Scrollbar(list_frame)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        lb = tk.Listbox(
            list_frame,
            height=8,
            yscrollcommand=sb.set,
            font=("Segoe UI", 10),
            bg=bg_inset,
            fg=fg_color,
            selectbackground=accent_teal,
            selectforeground="#ffffff",
            highlightthickness=1,
            highlightbackground=border_line,
            highlightcolor=accent_teal,
            relief=tk.FLAT,
            borderwidth=0,
        )
        lb.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.config(command=lb.yview)

        def refresh_list():
            lb.delete(0, tk.END)
            self._window_pick_entries = _enumerate_top_level_windows()
            for _hwnd, title in self._window_pick_entries:
                lb.insert(tk.END, title)

        def confirm():
            sel = lb.curselection()
            if not sel:
                self.log(tr("window_pick_none"))
                return
            hwnd, title = self._window_pick_entries[sel[0]]
            r = _client_area_screen_rect(hwnd)
            if not r:
                self.log(tr("window_invalid"))
                return
            x, y, w, h = r
            self.hunt_window_hwnd = hwnd
            self.hunt_window_title = title
            self.hunt_source = "window"
            self.hunt_region = (x, y, w, h)
            self._printwindow_fallback_logged = False
            self._rebuild_click_points(x, y, w, h)
            self.log(tr("window_selected").format(title, x, y, w, h))
            self.log(tr("click_points").format(len(self.click_points)))
            self.refresh_status_modes()
            dialog.destroy()

        def cancel_pick():
            dialog.destroy()

        dlg_ico = (30, 41, 59)
        ttk.Button(
            action_row,
            text=tr("ok_start"),
            command=confirm,
            width=20,
            **self._btn_icon_opts("ok", 16, dlg_ico),
        ).pack(side=tk.LEFT, padx=6)
        ttk.Button(
            action_row,
            text=tr("cancel"),
            command=cancel_pick,
            width=14,
            **self._btn_icon_opts("cancel", 16, dlg_ico),
        ).pack(side=tk.LEFT, padx=6)
        ttk.Button(
            btn_row,
            text=tr("window_refresh"),
            command=refresh_list,
            **self._btn_icon_opts("refresh", 16, dlg_ico),
        ).pack(side=tk.LEFT, padx=4)

        # Reserve bottom rows first so the list never covers buttons (fixes clipped OK/Cancel).
        action_row.pack(side=tk.BOTTOM, fill=tk.X, padx=14, pady=(6, 16))
        btn_row.pack(side=tk.BOTTOM, fill=tk.X, padx=14, pady=(4, 8))
        list_frame.pack(fill=tk.BOTH, expand=True, padx=14, pady=(4, 8))

        refresh_list()
        lb.bind("<Double-Button-1>", lambda _e: confirm())

    @staticmethod
    def _sanitize_template_basename(name):
        name = (name or "").strip()
        if not name:
            return None
        for c in '\\/*?:"<>|':
            name = name.replace(c, "")
        name = "_".join(name.split())
        if not name or name in (".", ".."):
            return None
        return name

    def open_monster_template_wizard(self):
        """Capture hunt area, pick crop + name, save to monsters/."""
        reg = self.resolve_hunt_region()
        if not reg:
            self.log(tr("tpl_capture_fail"))
            messagebox.showwarning(tr("tpl_wizard_title"), tr("tpl_capture_fail"), parent=self.root)
            return

        try:
            shot = self._capture_hunt_screenshot_pil()
            if shot is None:
                self.log(f"❌ Görüntü alınamadı")
                return
            pil_img = shot.convert("RGB") if hasattr(shot, "convert") else Image.fromarray(np.array(shot)).convert("RGB")
        except Exception as e:
            self.log(f"❌ Görüntü alınamadı: {e}")
            return

        world_w, world_h = pil_img.size
        max_dw, max_dh = 880, 560
        scale = min(max_dw / world_w, max_dh / world_h, 1.0)
        disp_w = max(1, int(world_w * scale))
        disp_h = max(1, int(world_h * scale))
        display_img = pil_img.resize((disp_w, disp_h), Image.Resampling.LANCZOS)

        dlg = tk.Toplevel(self.root)
        dlg.title(tr("tpl_wizard_title"))
        dlg.transient(self.root)
        dlg.grab_set()
        dlg.minsize(520, 400)

        ttk.Label(dlg, text=tr("tpl_wizard_hint"), wraplength=860).pack(pady=(10, 6), padx=12)

        body = ttk.Frame(dlg)
        body.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)

        photo = ImageTk.PhotoImage(display_img)
        canvas = tk.Canvas(body, width=disp_w, height=disp_h, highlightthickness=1, highlightbackground="#888")
        canvas.pack()
        canvas.create_image(0, 0, anchor=tk.NW, image=photo)
        dlg._tpl_photo = photo

        state = {"rect": None}
        drag = {"active": False, "x": 0, "y": 0}
        rect_draw = {"id": None}

        def draw_rect_exc(l, t, r, b):
            if rect_draw["id"] is not None:
                canvas.delete(rect_draw["id"])
                rect_draw["id"] = None
            if l is None:
                return
            x1 = int(l * scale)
            y1 = int(t * scale)
            x2 = max(x1 + 1, int(r * scale))
            y2 = max(y1 + 1, int(b * scale))
            rect_draw["id"] = canvas.create_rectangle(
                x1, y1, x2, y2, outline="#00ff00", width=2
            )

        def clamp_exc(l, t, r, b):
            l = max(0, min(world_w - 1, l))
            t = max(0, min(world_h - 1, t))
            r = max(l + 1, min(world_w, r))
            b = max(t + 1, min(world_h, b))
            return l, t, r, b

        def canvas_to_exc(cx1, cy1, cx2, cy2):
            l = int(min(cx1, cx2) / scale)
            t = int(min(cy1, cy2) / scale)
            r = int(max(cx1, cx2) / scale) + 1
            b = int(max(cy1, cy2) / scale) + 1
            return clamp_exc(l, t, r, b)

        def on_down(e):
            drag["active"] = True
            drag["x"], drag["y"] = e.x, e.y

        def on_move(e):
            if not drag["active"]:
                return
            l, t, r, b = canvas_to_exc(drag["x"], drag["y"], e.x, e.y)
            draw_rect_exc(l, t, r, b)

        def on_up(e):
            if not drag["active"]:
                return
            drag["active"] = False
            l, t, r, b = canvas_to_exc(drag["x"], drag["y"], e.x, e.y)
            state["rect"] = (l, t, r, b)
            draw_rect_exc(l, t, r, b)

        canvas.bind("<ButtonPress-1>", on_down)
        canvas.bind("<B1-Motion>", on_move)
        canvas.bind("<ButtonRelease-1>", on_up)

        bottom = ttk.Frame(dlg)
        bottom.pack(fill=tk.X, pady=10, padx=12)
        ttk.Label(bottom, text=tr("tpl_monster_name")).pack(anchor=tk.W)
        name_var = tk.StringVar(value="")
        name_entry = ttk.Entry(bottom, textvariable=name_var, width=50)
        name_entry.pack(fill=tk.X, pady=(4, 8))

        def do_save():
            base = self._sanitize_template_basename(name_var.get())
            if not base:
                messagebox.showerror(tr("tpl_wizard_title"), tr("tpl_name_bad"), parent=dlg)
                return
            if not state["rect"]:
                messagebox.showerror(tr("tpl_wizard_title"), tr("tpl_crop_small"), parent=dlg)
                return
            l, t, r, b = state["rect"]
            if (r - l) < 4 or (b - t) < 4:
                messagebox.showerror(tr("tpl_wizard_title"), tr("tpl_crop_small"), parent=dlg)
                return
            os.makedirs("monsters", exist_ok=True)
            out_path = os.path.join("monsters", base + ".png")
            if os.path.isfile(out_path):
                if not messagebox.askyesno(
                    tr("tpl_wizard_title"),
                    tr("tpl_overwrite").format(base),
                    parent=dlg,
                ):
                    return
            try:
                crop = pil_img.crop((l, t, r, b))
                crop.save(out_path, "PNG")
            except Exception as ex:
                messagebox.showerror(tr("tpl_wizard_title"), str(ex), parent=dlg)
                return
            self.log(tr("tpl_saved").format(base))
            self.load_monster_templates()
            dlg.destroy()

        row_btn = ttk.Frame(bottom)
        row_btn.pack(fill=tk.X)
        dlg_ico = (30, 41, 59)
        ttk.Button(
            row_btn,
            text=tr("tpl_save_btn"),
            command=do_save,
            **self._btn_icon_opts("save", 16, dlg_ico),
        ).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(
            row_btn,
            text=tr("cancel"),
            command=dlg.destroy,
            **self._btn_icon_opts("cancel", 16, dlg_ico),
        ).pack(side=tk.LEFT)

    def set_hunt_region(self):
        """Let user select a hunt region by drawing on screen."""
        self.log("📍 Hunt Region Selection (Template-based Detection)")
        self.log("   1. Click OK on the dialog")
        self.log("   2. Click and drag to draw a rectangle on your game")
        self.log("   3. Release mouse to confirm")
        
        # Create instruction dialog
        dialog = tk.Toplevel(self.root)
        dialog.title(tr("draw_region"))
        dialog.geometry("560x360")
        dialog.minsize(480, 300)
        dialog.resizable(True, True)
        dialog.transient(self.root)

        btn_bar = ttk.Frame(dialog)
        btn_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=14, pady=(8, 16))

        body = ttk.Frame(dialog)
        body.pack(fill=tk.BOTH, expand=True, padx=14, pady=(12, 4))

        ttk.Label(body, text=tr("draw_region"), font=("Segoe UI", 14, "bold")).pack(anchor=tk.W, pady=(0, 8))
        ttk.Label(body, text=tr("draw_instructions"), font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(0, 6))
        ttk.Label(body, text=tr("draw_step1"), font=("Segoe UI", 9)).pack(anchor=tk.W)
        ttk.Label(body, text=tr("draw_step2"), font=("Segoe UI", 9)).pack(anchor=tk.W)
        ttk.Label(body, text=tr("draw_step3"), font=("Segoe UI", 9)).pack(anchor=tk.W)
        ttk.Label(body, text=tr("draw_step4"), font=("Segoe UI", 9)).pack(anchor=tk.W, pady=(0, 4))

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
                    self.hunt_source = "manual"
                    self.hunt_window_hwnd = None
                    self.hunt_window_title = ""
                    self.hunt_region = (x, y, w, h)
                    self._rebuild_click_points(x, y, w, h)
                    self.log(tr("hunt_region_set").format(x, y, w, h))
                    self.log(tr("click_points").format(len(self.click_points)))
                    self.refresh_status_modes()
                else:
                    self.log(tr("region_small"))
            else:
                self.log(tr("selection_cancelled"))

        dlg_ico = (30, 41, 59)
        ttk.Button(
            btn_bar,
            text=tr("ok_start"),
            command=start_selection,
            width=22,
            **self._btn_icon_opts("ok", 16, dlg_ico),
        ).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(
            btn_bar,
            text=tr("cancel"),
            command=lambda: (dialog.destroy(), self.log(tr("selection_cancelled"))),
            width=14,
            **self._btn_icon_opts("cancel", 16, dlg_ico),
        ).pack(side=tk.LEFT)

    def log(self, message):
        if not hasattr(self, 'log_text'):
            return
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        
    def start_bot(self):
        # Get skill keys
        self.skills = [
            key
            for key, var in zip(self.skill_bar_slot_keys, self.skill_slot_vars)
            if var.get()
        ]
        
        if not self.skills:
            self.log(tr("error_empty_skills"))
            return

        try:
            self.skill_delay = max(0.0, float(self.skill_delay_var.get()))
        except (tk.TclError, TypeError, ValueError):
            self.skill_delay = 0.03
        try:
            self.mob_delay = max(0.0, float(self.mob_delay_var.get()))
        except (tk.TclError, TypeError, ValueError):
            self.mob_delay = 0.018

        self.keypress_only_mode = self.keypress_only_var.get()

        self.buff_mode = self.buff_mode_var.get()
        self.buff_keys = [
            key
            for key, var in zip(self.buff_bar_slot_keys, self.buff_slot_vars)
            if var.get()
        ]
        if self.buff_mode and not self.buff_keys:
            self.log(tr("error_empty_buff_skills"))
            return
        try:
            bm = float(self.buff_interval_var.get())
        except (tk.TclError, TypeError, ValueError):
            bm = 1800.0
        self.buff_interval_s = max(1.0, min(5400.0, bm))
        self.buff_repeat_12 = self.buff_repeat_12_var.get()
        self._buff_slot_delays = self._parse_buff_slot_delays()
        self._last_buff_time = time.time()
        
        self.auto_tab_enabled = self.auto_tab_enabled_var.get()
        self.last_auto_tab_time = time.time()
        self.advanced_vision_match = True
        try:
            self.min_click_confidence = max(0.16, min(0.85, float(self.min_click_confidence_var.get())))
        except (tk.TclError, TypeError, ValueError):
            self.min_click_confidence = 0.66
        try:
            self.reclick_lockout_s = max(0.0, float(self.reclick_lockout_var.get()))
        except (tk.TclError, TypeError, ValueError):
            self.reclick_lockout_s = 2.5
        self._no_reclick_screen_until = 0.0
        self._last_attack_click_screen = None
        self._last_skip_click_log = 0.0

        targets_text = self.target_monsters_entry.get().strip()
        self.target_monster_names = [name.strip() for name in targets_text.split(',') if name.strip()]
        
        if not self.keypress_only_mode:
            reg = self.resolve_hunt_region()
            if not reg:
                self.log(tr("error_hunt_not_set"))
                self.log(tr("error_click_button"))
                return

            self.load_monster_templates()

            if not self.target_monster_names and self.monster_templates:
                self.target_monster_names = list(self.monster_templates.keys())
                self.log(f"🎯 Target monsters otomatik dolduruldu: {', '.join(self.target_monster_names)}")

            if not self.target_monster_names and not self.monster_templates:
                self.log("❌ Aranacak canavar isimlerini gir (ör: mangyang,tigergirl)")
                self.log("   veya monsters/ klasorune PNG template ekle")
                return
        
        self._hunt_scale_mismatch_logged = False
        self.bot_running = True
        self.start_time = time.time()
        
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_label.config(text="✅ " + tr("running"), foreground="#059669")
        self.refresh_status_modes()
        
        self.log("=" * 60)
        self.log("🚀 BOT STARTED!")
        
        # Log run mode info
        if self.keypress_only_mode:
            self.log("⌨️ Mode: KEYPRESS ONLY")
            self.log("   Canavar seçimi yapılmadan skill döngüsü çalışacak")
        else:
            rx, ry, rw, rh = self.resolve_hunt_region() or (0, 0, 0, 0)
            self.log("🧠 Mode: PNG template detection")
            self.log(f"📍 Hunt Region: X={rx}, Y={ry}, W={rw}, H={rh}")
            if self.hunt_source == "window" and self.hunt_window_title:
                self.log(f"   🪟 Kaynak: pencere — {self.hunt_window_title}")
                self.log(tr("window_capture_printwindow_hint"))
            self.log(f"🎯 Target filter: {', '.join(self.target_monster_names)}")
            if self.monster_templates:
                self.log(f"🖼️ Şablon: {len(self.monster_templates)} PNG | eşik {self.template_threshold:.2f}")
        
        self.log(f"🎯 Skill keys: {', '.join(self.skills)}")
        self.log(f"⌨️ Input method: {self.input_method_var.get()}")
        self.log(f"⚙️ Skill interval: {self.skill_delay}s")
        self.log(f"⚙️ Mob interval: {self.mob_delay}s")
        self.log(f"⚔️ Auto TAB: {'ON' if self.auto_tab_enabled else 'OFF'}")
        self.log(f"⚔️ Auto TAB interval: {self.auto_tab_interval:.0f}s")
        self.log(f"🎚️ Click certainty min score: {self.min_click_confidence:.2f}")
        if self.buff_mode:
            ds = ", ".join(f"{x:.2f}" for x in self._buff_slot_delays)
            keys = "-".join(self.buff_keys)
            self.log(
                f"✨ Buff mode: ON | interval: {self._format_seconds(self.buff_interval_s)} | "
                f"keys: [{keys}] | F2 bar wait (s): [{ds}] | "
                f"extra 1-2: {'yes' if self.buff_repeat_12 else 'no'}"
            )
        if not self.keypress_only_mode:
            self.log(f"🖱️ Aynı bölge tıklama kilidi: {self.reclick_lockout_s:.1f}s")
        self.log("=" * 60)
        
        # Start bot thread
        self.bot_thread = threading.Thread(target=self.bot_loop, daemon=True)
        self.bot_thread.start()
        
        # Start timer
        self.update_timer()
        
    def _on_hotkey_stop(self, _event=None):
        if self.bot_running:
            self.stop_bot()

    def stop_bot(self):
        was_running = self.bot_running
        self.bot_running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_label.config(text="⭕ " + tr("stopped"), foreground="#dc2626")
        self.refresh_status_modes()
        if was_running:
            self.log("🛑 Bot stopped!")

    def update_timer(self):
        if self.bot_running and self.start_time:
            elapsed = int(time.time() - self.start_time)
            hours = elapsed // 3600
            minutes = (elapsed % 3600) // 60
            seconds = elapsed % 60
            self.time_label.config(text=f"Running Time: {hours:02d}:{minutes:02d}:{seconds:02d}")
            self.root.after(1000, self.update_timer)

    def normalize_monster_name(self, name):
        """Normalize monster/template names for robust matching."""
        if not name:
            return ""
        return ''.join(ch.lower() for ch in name if ch.isalnum())

    def cleanup_recent_target_clicks(self, now=None):
        """Keep recent target cache small and time-bounded."""
        if now is None:
            now = time.time()

        max_keep = self.target_click_cooldown + 0.5
        self.recent_target_clicks = [
            item for item in self.recent_target_clicks
            if now - item['time'] <= max_keep
        ]

    def is_recent_target_click(self, monster_name, center_x, center_y, now=None):
        """Check whether this target position was clicked recently (likely dead label linger)."""
        if now is None:
            now = time.time()

        normalized_name = self.normalize_monster_name(monster_name)
        tolerance_sq = self.target_position_tolerance * self.target_position_tolerance

        for item in self.recent_target_clicks:
            if now - item['time'] > self.target_click_cooldown:
                continue

            if item['name'] != normalized_name:
                continue

            dx = center_x - item['x']
            dy = center_y - item['y']
            if (dx * dx + dy * dy) <= tolerance_sq:
                return True

        return False

    def remember_target_click(self, monster_name, center_x, center_y, now=None):
        """Store clicked target to avoid immediate re-click loops."""
        if now is None:
            now = time.time()

        self.recent_target_clicks.append({
            'name': self.normalize_monster_name(monster_name),
            'x': center_x,
            'y': center_y,
            'time': now,
        })
        self.cleanup_recent_target_clicks(now)

    def _should_block_repeat_ground_click(self, screen_x, screen_y, now=None):
        """Block another left-click near the last target click while lockout is active (reduces walk-to-ground)."""
        if now is None:
            now = time.time()
        if now >= self._no_reclick_screen_until:
            return False
        if self._last_attack_click_screen is None:
            return False
        lx, ly = self._last_attack_click_screen
        t = self.reclick_screen_tolerance_px
        dx = screen_x - lx
        dy = screen_y - ly
        return (dx * dx + dy * dy) <= (t * t)

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
                    raw = cv2.imread(filepath, cv2.IMREAD_UNCHANGED)
                    if raw is None:
                        continue
                    mask = None
                    if raw.ndim == 3 and raw.shape[2] == 4:
                        bgr = raw[:, :, :3]
                        a = raw[:, :, 3]
                        if int(a.max()) > 0:
                            mask = np.where(a > 128, 255, 0).astype(np.uint8)
                        img = bgr
                    elif raw.ndim == 2:
                        img = cv2.cvtColor(raw, cv2.COLOR_GRAY2BGR)
                    else:
                        img = raw
                    monster_name = filename[:-4]
                    gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    h, w = gray_img.shape[:2]
                    edges = cv2.Canny(gray_img, 50, 150)
                    if mask is not None:
                        edges = cv2.bitwise_and(edges, edges, mask=mask)
                    self.monster_templates[monster_name] = {
                        'color': img,
                        'gray': gray_img,
                        'edges': edges,
                        'mask': mask,
                        'width': w,
                        'height': h,
                    }
                    tag = " + alpha" if mask is not None else ""
                    self.log(f"✅ Template yüklendi: {monster_name}{tag}")
                except Exception as e:
                    self.log(f"❌ Template yükleme hatası ({filename}): {e}")
            
            if self.monster_templates:
                self.log(f"📊 Toplam {len(self.monster_templates)} monster template yüklendi")
            else:
                self.log("⚠️ monsters/ klasöründe PNG dosyası bulunamadı!")
                
        except Exception as e:
            self.log(f"❌ Monster templates yüklenirken hata: {e}")

    def _clahe_apply(self, gray):
        if self._clahe is None:
            self._clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        return self._clahe.apply(gray)

    def _gray_match_scores(self, gray_scene, gray_tpl, mask_tpl, use_multi_metric):
        """Best gray-channel match; returns (score, top_left_xy) or (0, None)."""
        if gray_tpl.shape[0] > gray_scene.shape[0] or gray_tpl.shape[1] > gray_scene.shape[1]:
            return 0.0, None
        try:
            if use_multi_metric and mask_tpl is not None:
                corr = cv2.matchTemplate(gray_scene, gray_tpl, cv2.TM_CCORR_NORMED, mask=mask_tpl)
                ccoeff = cv2.matchTemplate(gray_scene, gray_tpl, cv2.TM_CCOEFF_NORMED)
                _, mv_corr, _, loc = cv2.minMaxLoc(corr)
                x, y = loc[0], loc[1]
                if 0 <= y < ccoeff.shape[0] and 0 <= x < ccoeff.shape[1]:
                    v_ce = float(ccoeff[y, x])
                else:
                    v_ce = 0.0
                score = 0.55 * float(mv_corr) + 0.45 * max(-1.0, min(1.0, v_ce))
                return score, loc
            if use_multi_metric and mask_tpl is None:
                ccoeff = cv2.matchTemplate(gray_scene, gray_tpl, cv2.TM_CCOEFF_NORMED)
                ccorr = cv2.matchTemplate(gray_scene, gray_tpl, cv2.TM_CCORR_NORMED)
                blended = cv2.addWeighted(ccoeff, 0.52, ccorr, 0.48, 0)
                _, score, _, loc = cv2.minMaxLoc(blended)
                return float(score), loc
            if mask_tpl is not None:
                try:
                    gray_result = cv2.matchTemplate(
                        gray_scene, gray_tpl, cv2.TM_CCORR_NORMED, mask=mask_tpl
                    )
                except Exception:
                    gray_result = cv2.matchTemplate(gray_scene, gray_tpl, cv2.TM_CCOEFF_NORMED)
            else:
                gray_result = cv2.matchTemplate(gray_scene, gray_tpl, cv2.TM_CCOEFF_NORMED)
            _, score, _, loc = cv2.minMaxLoc(gray_result)
            return float(score), loc
        except Exception:
            return 0.0, None

    def _orb_template_hit(self, scene_gray, tpl_gray, tpl_mask=None):
        """ORB + homography rough location; returns (cx, cy, conf01) or (None, None, 0)."""
        if tpl_gray.shape[0] < 22 or tpl_gray.shape[1] < 22:
            return None, None, 0.0
        try:
            orb = cv2.ORB_create(nfeatures=350, scaleFactor=1.2, edgeThreshold=10)
            kp1, d1 = orb.detectAndCompute(tpl_gray, tpl_mask)
            kp2, d2 = orb.detectAndCompute(scene_gray, None)
            if d1 is None or d2 is None or len(kp1) < 10 or len(kp2) < 16:
                return None, None, 0.0
            bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
            matches = bf.match(d1, d2)
            if len(matches) < 10:
                return None, None, 0.0
            matches = sorted(matches, key=lambda m: m.distance)
            keep = min(80, max(12, int(len(matches) * 0.65)))
            good = matches[:keep]
            src = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
            dst = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
            H, inlier_mask = cv2.findHomography(src, dst, cv2.RANSAC, 4.5, maxIters=2500)
            if H is None or inlier_mask is None:
                return None, None, 0.0
            inliers = int(inlier_mask.ravel().sum())
            if inliers < 7:
                return None, None, 0.0
            h0, w0 = tpl_gray.shape[:2]
            corners = np.float32([[0, 0], [w0, 0], [w0, h0], [0, h0]]).reshape(-1, 1, 2)
            proj = cv2.perspectiveTransform(corners, H)
            cx = float(np.mean(proj[:, 0, 0]))
            cy = float(np.mean(proj[:, 0, 1]))
            md = float(np.mean([m.distance for m in good[: max(1, inliers)]]))
            score = min(1.0, inliers / 20.0) * max(0.25, 1.0 - md / 75.0)
            return cx, cy, score
        except Exception:
            return None, None, 0.0

    def _orb_scan_templates(self, gray_work, thr):
        """When classical template pass finds nothing, try ORB per monster."""
        out = []
        if not getattr(self, "advanced_vision_match", True) or not self.monster_templates:
            return out
        orb_floor = max(0.26, min(0.72, float(thr) * 0.62))
        for monster_name, template_data in self.monster_templates.items():
            try:
                if self.target_monster_names:
                    mn = self.normalize_monster_name(monster_name)
                    allowed = False
                    for t in self.target_monster_names:
                        tn = self.normalize_monster_name(t)
                        if not tn:
                            continue
                        if tn == mn or tn in mn or mn in tn:
                            allowed = True
                            break
                    if not allowed:
                        continue
                g = template_data["gray"]
                mk = template_data.get("mask")
                tpl_g = self._clahe_apply(g)
                tw, th = tpl_g.shape[1], tpl_g.shape[0]
                cx, cy, sc = self._orb_template_hit(gray_work, tpl_g, mk)
                if cx is None or sc < orb_floor:
                    continue
                tx = int(cx - tw // 2)
                ty = int(cy - th // 2)
                tx = max(0, min(gray_work.shape[1] - tw, tx))
                ty = max(0, min(gray_work.shape[0] - th, ty))
                mapped = min(0.92, sc * 1.05)
                out.append((mapped, monster_name, tx, ty, tw, th))
            except Exception:
                continue
        return out

    def detect_monster_template(self, screenshot):
        """
        Detect monster using multi-scale template match (gray + edges), optional CLAHE,
        blended correlation metrics, and ORB assist when classical match fails.
        Returns (monster_name, confidence, center_x, center_y) or (None, 0, 0, 0)
        """
        self._detect_cooldown_blocked_only = False
        if not self.monster_templates:
            return None, 0, 0, 0

        agree_sq = self.template_loc_agreement_px * self.template_loc_agreement_px
        use_adv = getattr(self, "advanced_vision_match", True)
        scales = self.template_scales_advanced if use_adv else self.template_scales
        multi = use_adv

        try:
            img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            edge_img = cv2.Canny(gray_img, 50, 150)

            if use_adv:
                gray_work = self._clahe_apply(gray_img)
                edge_work = cv2.Canny(gray_work, 50, 150)
            else:
                gray_work = gray_img
                edge_work = edge_img

            candidates = []
            thr = float(self.template_threshold)

            for monster_name, template_data in self.monster_templates.items():
                try:
                    if self.target_monster_names:
                        mn = self.normalize_monster_name(monster_name)
                        allowed = False
                        for t in self.target_monster_names:
                            tn = self.normalize_monster_name(t)
                            if not tn:
                                continue
                            if tn == mn or tn in mn or mn in tn:
                                allowed = True
                                break
                        if not allowed:
                            continue
                    base_gray_template = template_data["gray"]
                    base_edge_template = template_data["edges"]
                    base_mask = template_data.get("mask")
                    best_local = 0.0
                    best_local_pos = None

                    for scale in scales:
                        if scale == 1.0:
                            gray_resized = base_gray_template
                            mask_template = base_mask
                        else:
                            new_w = max(8, int(base_gray_template.shape[1] * scale))
                            new_h = max(8, int(base_gray_template.shape[0] * scale))
                            gray_resized = cv2.resize(
                                base_gray_template, (new_w, new_h), interpolation=cv2.INTER_AREA
                            )
                            if base_mask is not None:
                                mask_template = cv2.resize(
                                    base_mask, (new_w, new_h), interpolation=cv2.INTER_NEAREST
                                )
                            else:
                                mask_template = None

                        if use_adv:
                            gray_template = self._clahe_apply(gray_resized)
                            edge_template = cv2.Canny(gray_template, 50, 150)
                            if mask_template is not None:
                                edge_template = cv2.bitwise_and(
                                    edge_template, edge_template, mask=mask_template
                                )
                        else:
                            gray_template = gray_resized
                            if scale == 1.0:
                                edge_template = base_edge_template
                            else:
                                edge_template = cv2.resize(
                                    base_edge_template,
                                    (gray_resized.shape[1], gray_resized.shape[0]),
                                    interpolation=cv2.INTER_AREA,
                                )

                        if (
                            gray_template.shape[0] > gray_work.shape[0]
                            or gray_template.shape[1] > gray_work.shape[1]
                        ):
                            continue

                        gray_max_val, gray_max_loc = self._gray_match_scores(
                            gray_work, gray_template, mask_template, multi
                        )
                        if gray_max_loc is None:
                            continue

                        edge_result = cv2.matchTemplate(
                            edge_work, edge_template, cv2.TM_CCOEFF_NORMED
                        )
                        _, edge_max_val, _, edge_max_loc = cv2.minMaxLoc(edge_result)

                        dx = gray_max_loc[0] - edge_max_loc[0]
                        dy = gray_max_loc[1] - edge_max_loc[1]
                        combined_score = 0.5 * (gray_max_val + edge_max_val)
                        if use_adv:
                            if (dx * dx + dy * dy) > agree_sq:
                                combined_score *= 0.58
                            if gray_max_val < 0.38 or edge_max_val < 0.28:
                                combined_score *= 0.82
                        else:
                            if (dx * dx + dy * dy) > agree_sq:
                                combined_score *= 0.52
                            if gray_max_val < 0.38 or edge_max_val < 0.28:
                                combined_score *= 0.75

                        best_loc = gray_max_loc
                        if combined_score > best_local:
                            best_local = combined_score
                            best_local_pos = (
                                best_loc[0],
                                best_loc[1],
                                gray_template.shape[1],
                                gray_template.shape[0],
                                scale,
                            )

                    if self.template_debug and best_local > 0.2:
                        self.log(
                            f"📸 {monster_name}: skor={best_local:.2f} (eşik {thr:.2f})"
                        )

                    if best_local_pos and best_local >= thr:
                        best_x, best_y, scaled_w, scaled_h, _ = best_local_pos
                        candidates.append((best_local, monster_name, best_x, best_y, scaled_w, scaled_h))

                except Exception as e:
                    self.log(f"⚠️ Template eşleştirme hatası ({monster_name}): {e}")
                    continue

            if not candidates and use_adv:
                for oc in self._orb_scan_templates(gray_work, thr):
                    candidates.append(oc)
                if candidates and self.template_debug:
                    self.log("🔭 ORB yedeği aday üretti (klasik eşleşme zayıftı)")

            if not candidates:
                self.no_detection_count += 1
                return None, 0, 0, 0

            candidates.sort(key=lambda item: item[0], reverse=True)
            now = time.time()
            self.cleanup_recent_target_clicks(now)
            skipped_recent = 0

            top_conf = float(candidates[0][0])
            # Keep detection threshold permissive for search, but require a stronger score to click.
            if top_conf < self.min_click_confidence:
                self.no_detection_count += 1
                return None, 0, 0, 0

            if len(candidates) > 1:
                second_conf = float(candidates[1][0])
                if (
                    top_conf < (self.min_click_confidence + 0.08)
                    and (top_conf - second_conf) < self.min_confidence_gap
                ):
                    if self.template_debug and now - self.last_cooldown_log_time > 1.2:
                        self.log(
                            f"⚖️ Belirsiz eşleşme atlandı: top={top_conf:.2f}, ikinci={second_conf:.2f}"
                        )
                        self.last_cooldown_log_time = now
                    self.no_detection_count += 1
                    return None, 0, 0, 0

            for confidence, monster_name, template_x, template_y, template_w, template_h in candidates:
                center_x = template_x + template_w // 2
                center_y = template_y + template_h // 2

                if self.is_recent_target_click(monster_name, center_x, center_y, now):
                    skipped_recent += 1
                    continue

                self.no_detection_count = 0
                return monster_name, confidence, center_x, center_y

            if skipped_recent > 0 and now - self.last_cooldown_log_time > 1.5:
                self.log(f"⏳ Aynı hedef tekrarlandı, {skipped_recent} eşleşme cooldown ile atlandı")
                self.last_cooldown_log_time = now

            self.no_detection_count += 1
            self._detect_cooldown_blocked_only = True
            return None, 0, 0, 0

        except Exception as e:
            self.log(f"⚠️ Detect monster hatası: {e}")
            self._detect_cooldown_blocked_only = False
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
            time.sleep(0.005)
            pydirectinput.keyUp(key)
            time.sleep(0.005)
            return True
        except Exception:
            return False

    def send_keyboard_key(self, key):
        try:
            keyboard.press_and_release(key)
            time.sleep(0.005)
            return True
        except Exception:
            return False

    def click_at(self, x, y):
        """Click at screen coordinates using game-friendly method first, then fallback."""
        xi, yi = int(round(x)), int(round(y))
        try:
            # pydirectinput often sends clicks without moving the visible cursor; games / users expect real cursor position.
            ctypes.windll.user32.SetCursorPos(xi, yi)
            time.sleep(0.007)
        except Exception:
            pass
        try:
            pydirectinput.moveTo(xi, yi)
            time.sleep(0.002)
            pydirectinput.click(x=xi, y=yi)
            return True
        except Exception:
            pass

        try:
            pyautogui.click(x=xi, y=yi)
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
            time.sleep(0.006)
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

    def _run_buff_sequence(self):
        """F2 bar: selected keys, optional 1-2 again, then F1 for attack skills."""
        keys = list(getattr(self, "buff_keys", None) or ["1", "2", "3", "4", "5"])
        seq = "-".join(keys)
        extra = " → 1-2" if self.buff_repeat_12 else ""
        self.log(tr("log_buff_cycle").format(seq, extra))
        delays = getattr(self, "_buff_slot_delays", None)
        if not delays or len(delays) != len(keys):
            delays = [max(0.15, float(self.skill_delay))] * len(keys)
        self.press_key("f2")
        time.sleep(0.35)
        for i, k in enumerate(keys):
            self.press_key(k)
            time.sleep(delays[i])
        if self.buff_repeat_12:
            rep = [k for k in ("1", "2") if k in keys]
            for k in rep:
                self.press_key(k)
                idx = keys.index(k)
                time.sleep(delays[idx])
        self.press_key("f1")
        time.sleep(max(0.08, min(0.45, delays[-1])))
            
    def bot_loop(self):
        time.sleep(0.2)

        if self.buff_mode:
            self._run_buff_sequence()
            self._last_buff_time = time.time()
        
        while self.bot_running:
            if keyboard.is_pressed("ctrl") and keyboard.is_pressed("q"):
                self.root.after(0, self.stop_bot)
                break

            if self.buff_mode and (time.time() - self._last_buff_time >= self.buff_interval_s):
                self._run_buff_sequence()
                self._last_buff_time = time.time()

            # Press TAB every fixed interval
            current_time = time.time()
            if self.auto_tab_enabled and current_time - self.last_auto_tab_time >= self.auto_tab_interval:
                self.press_key('tab')
                self.last_auto_tab_time = current_time
                self.log("⚔️ Auto TAB pressed")
                time.sleep(0.01)
            
            try:
                if self.keypress_only_mode:
                    self.run_keypress_cycle()
                    continue

                dims = self.resolve_hunt_region()
                if not dims:
                    now = time.time()
                    if now - self._last_window_invalid_log > 2.5:
                        self.log(tr("window_invalid"))
                        self._last_window_invalid_log = now
                    time.sleep(0.8)
                    continue

                self.cleanup_recent_target_clicks()

                x, y, w, h = dims
                screenshot = self._capture_hunt_screenshot_pil()
                if screenshot is None:
                    time.sleep(0.04)
                    continue

                monster_name, confidence, rel_center_x, rel_center_y = self.detect_monster_template(screenshot)
                detect_source = "TEMPLATE"

                center_x = center_y = None
                if monster_name and confidence >= self.template_threshold:
                    rel_center_x, rel_center_y = self._hunt_rel_from_screenshot(
                        rel_center_x, rel_center_y, screenshot, w, h
                    )
                    center_x = x + rel_center_x
                    center_y = y + rel_center_y

                    now_ts = time.time()
                    skip_ground_click = self._should_block_repeat_ground_click(center_x, center_y, now_ts)
                    skip_suffix = tr("detect_log_skip_click") if skip_ground_click else ""
                    self.log(
                        f"🎯 [{detect_source}] {monster_name} detected (score: {confidence:.2f}) at ({center_x}, {center_y}){skip_suffix}"
                    )
                    if skip_ground_click:
                        if now_ts - self._last_skip_click_log > 2.0:
                            self.log(tr("skip_reclick_log"))
                            self._last_skip_click_log = now_ts
                        time.sleep(0.008)
                    else:
                        if not self.click_at(center_x, center_y):
                            self.log("⚠️ Mouse click gonderilemedi")
                            time.sleep(0.07)
                            continue
                        self.remember_target_click(monster_name, rel_center_x, rel_center_y)
                        time.sleep(0.008)

                    skill_log = "   Skills: "
                    for skill in self.skills:
                        self.press_key(skill)
                        skill_log += f"{skill} "
                        time.sleep(self.skill_delay)

                    self.log(skill_log + "✓")
                    time.sleep(self.mob_delay)

                    if not skip_ground_click:
                        self._last_attack_click_screen = (center_x, center_y)
                        self._no_reclick_screen_until = time.time() + self.reclick_lockout_s

                if not (monster_name and confidence >= self.template_threshold):
                    if self.no_detection_count > 0 and self.no_detection_count % 10 == 0:
                        now = time.time()
                        if now - self.last_no_detection_log_time > 2:
                            self.log(
                                "🔍 Şablon eşleşmesi yok. monsters/ PNG, tarama alanı ve «Aranacak Canavarlar» listesini kontrol edin."
                            )
                            self.last_no_detection_log_time = now

                    # Corpse still matches template but position is on click-cooldown — scan quicker until it clears or a new mob appears.
                    delay = 0.028 if getattr(self, "_detect_cooldown_blocked_only", False) else 0.07
                    time.sleep(delay)

                continue

            except Exception as e:
                self.log(f"⚠️ Error: {e}")
                time.sleep(0.35)

def main():
    _try_set_process_dpi_aware()
    root = tk.Tk()
    app = BotGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
