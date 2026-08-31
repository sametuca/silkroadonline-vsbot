"""Minimal TR/EN localization, persisted to language.json next to the app."""

import json

from .paths import data_path

_LANG_FILE = data_path("language.json")

_STRINGS = {
    "app_title": {"EN": "Silkroad Vision Bot", "TR": "Silkroad Vision Bot"},
    "select_language": {"EN": "Select Language", "TR": "Dil Seçin"},
    "settings": {"EN": "Settings", "TR": "Ayarlar"},
    "window": {"EN": "Game Window", "TR": "Oyun Penceresi"},
    "select_window": {"EN": "Select Window", "TR": "Pencere Seç"},
    "refresh": {"EN": "Refresh", "TR": "Yenile"},
    "no_window_selected": {"EN": "No window selected", "TR": "Pencere seçilmedi"},
    "target_monsters": {"EN": "Target Monsters (optional, comma separated)", "TR": "Aranacak Canavarlar (opsiyonel, virgülle)"},
    "keypress_only": {"EN": "Keypress Only Mode (no monster detection)", "TR": "Sadece Tuş Vuruşu Modu (canavar tespiti kapalı)"},
    "auto_tab": {"EN": "Auto TAB targeting", "TR": "Otomatik TAB ile hedefleme"},
    "skill_keys": {"EN": "Skill Keys (comma separated)", "TR": "Skill Tuşları (virgülle)"},
    "skill_interval": {"EN": "Skill Interval (s)", "TR": "Skill Aralığı (sn)"},
    "mob_interval": {"EN": "Mob Interval (s)", "TR": "Canavar Arası Bekleme (sn)"},
    "auto_tab_interval": {"EN": "Auto TAB Interval (s)", "TR": "Otomatik TAB Aralığı (sn)"},
    "template_threshold": {"EN": "Template Confidence Threshold", "TR": "Şablon Güven Eşiği"},
    "reclick_lockout": {"EN": "Dead-target reclick lockout (s)", "TR": "Ölü hedef tekrar tıklama engeli (sn)"},
    "input_method": {"EN": "Input Method", "TR": "Input Yöntemi"},
    "buffs": {"EN": "Buffs", "TR": "Buff'lar"},
    "enable_buffs": {"EN": "Enable buff casting", "TR": "Buff atmayı etkinleştir"},
    "buff_keys": {"EN": "Buff Keys (comma separated)", "TR": "Buff Tuşları (virgülle)"},
    "buff_interval": {"EN": "Buff Interval (s)", "TR": "Buff Aralığı (sn)"},
    "start": {"EN": "▶ Start", "TR": "▶ Başlat"},
    "stop": {"EN": "⏹ Stop", "TR": "⏹ Durdur"},
    "status_idle": {"EN": "Idle", "TR": "Boşta"},
    "status_running": {"EN": "Running", "TR": "Çalışıyor"},
    "status_stopped": {"EN": "Stopped", "TR": "Durduruldu"},
    "kills": {"EN": "Kills: {n}", "TR": "Öldürülen: {n}"},
    "runtime": {"EN": "Runtime: {t}", "TR": "Süre: {t}"},
    "log": {"EN": "Log", "TR": "Log"},
    "err_no_window": {"EN": "Select the game window first.", "TR": "Önce oyun penceresini seçin."},
    "err_no_region": {"EN": "Couldn't read that window's area - try selecting it again.",
                       "TR": "O pencerenin alanı okunamadı - tekrar seçmeyi deneyin."},
    "err_no_templates": {"EN": "No templates loaded and Keypress Only Mode is off.", "TR": "Şablon yüklenmedi ve Sadece Tuş Vuruşu Modu kapalı."},
    "hotkey_hint": {"EN": "Hotkeys (work anywhere, even while the game is focused): Ctrl+B start, Ctrl+D or Q stop.",
                    "TR": "Kısayollar (oyun penceresindeyken de çalışır): Ctrl+B başlat, Ctrl+D veya Q durdur."},
    "template_wizard_hint": {"EN": "Drag a tight box around just the monster's name text, then release.",
                              "TR": "Canavarın isim yazısının tam üzerine dar bir kutu çizin, sonra bırakın."},
    "template_name_prompt": {"EN": "Monster name (just a label, doesn't need to match the game):",
                              "TR": "Canavar adı (sadece bir etiket, oyundaki isimle aynı olmak zorunda değil):"},

    "detection_mode": {"EN": "Detection Mode", "TR": "Tespit Modu"},
    "mode_hybrid": {"EN": "Hybrid (color + shape, recommended)", "TR": "Hibrit (renk + şekil, önerilen)"},
    "mode_color": {"EN": "Color only (no templates needed)", "TR": "Sadece renk (şablon gerekmez)"},
    "mode_template": {"EN": "Template only (full-frame)", "TR": "Sadece şablon (tüm ekran)"},
    "mode_ocr": {"EN": "OCR (reads the name, needs easyocr)", "TR": "OCR (ismi okur, easyocr gerekir)"},
    "ocr_unavailable": {"EN": "No OCR engine found - OCR mode disabled (Tesseract or easyocr needed)",
                         "TR": "OCR motoru bulunamadı - OCR modu kapalı (Tesseract veya easyocr gerekir)"},
    "ocr_engine_tesseract": {"EN": "OCR: Tesseract (fast)", "TR": "OCR: Tesseract (hızlı)"},
    "ocr_engine_easyocr": {"EN": "OCR: easyocr (slower)", "TR": "OCR: easyocr (yavaş)"},
    "install_tesseract": {"EN": "🚀 Install Tesseract", "TR": "🚀 Tesseract'ı Kur"},
    "install_tesseract_confirm": {
        "EN": "This downloads the official Tesseract-OCR installer from GitHub (~50MB) and "
              "runs it silently. Windows may ask for your permission (UAC) - please allow it. Continue?",
        "TR": "Bu işlem GitHub'dan resmi Tesseract-OCR kurulum dosyasını indirir (~50MB) ve "
              "sessizce çalıştırır. Windows izin isteyebilir (UAC) - lütfen izin verin. Devam edilsin mi?"},
    "install_tesseract_starting": {"EN": "Starting Tesseract install...", "TR": "Tesseract kurulumu başlıyor..."},
    "install_tesseract_success": {"EN": "Tesseract installed - OCR confirmation is now active.",
                                   "TR": "Tesseract kuruldu - OCR doğrulama artık aktif."},
    "install_tesseract_failed": {"EN": "Install didn't complete - hybrid/color/template modes still work fine.",
                                  "TR": "Kurulum tamamlanamadı - hibrit/renk/şablon modları yine de sorunsuz çalışır."},
    "calibrate_color": {"EN": "🎨 Calibrate Nameplate Color", "TR": "🎨 İsim Etiketi Rengini Kalibre Et"},
    "calibrate_hint": {"EN": "Click once directly on a monster's name text.", "TR": "Bir canavarın isim yazısının tam üzerine bir kez tıklayın."},
    "color_calibrated": {"EN": "Nameplate color calibrated", "TR": "İsim etiketi rengi kalibre edildi"},
    "color_calibration_ok": {"EN": "color check passed ✅", "TR": "renk kontrolü başarılı ✅"},
    "color_calibration_weak": {"EN": "⚠ color didn't re-match its own crop - try a tighter box around just the name text",
                                "TR": "⚠ renk kendi kırpımını bile bulamadı - ismin tam üzerine daha dar bir kutu deneyin"},
    "color_calibration_none": {"EN": "⚠ no clear color found - try a tighter box around just the name text",
                                "TR": "⚠ net bir renk bulunamadı - ismin tam üzerine daha dar bir kutu deneyin"},
    "orb_added": {"EN": "{name}: shape reference added (backup path if color misses)",
                  "TR": "{name}: şekil referansı eklendi (renk kaçırırsa yedek yol)"},
    "orb_too_plain": {"EN": "{name}: crop too plain for a shape reference - color-only for this one",
                       "TR": "{name}: kırpım şekil referansı için fazla düz - bunun için sadece renk kullanılacak"},
    "hp_bar": {"EN": "HP Bar (optional, for reliable death detection)", "TR": "HP Bar (opsiyonel, güvenilir ölüm tespiti için)"},
    "set_hp_bar": {"EN": "❤ Set HP Bar Region", "TR": "❤ HP Bar Bölgesi Seç"},
    "hp_bar_hint": {"EN": "Drag a thin box over just the target's HP bar (top-left corner to bottom-right).",
                     "TR": "Hedefin HP barının tam üzerinde ince bir kutu seçin (sol üstten sağ alta)."},
    "hp_bar_not_set": {"EN": "Not set (using timer fallback)", "TR": "Ayarlanmadı (zamanlayıcıya düşülüyor)"},
    "hp_bar_set": {"EN": "HP bar region set", "TR": "HP bar bölgesi ayarlandı"},
    "clear": {"EN": "Clear", "TR": "Temizle"},
    "loot_key": {"EN": "Loot Key (optional)", "TR": "Loot Tuşu (opsiyonel)"},
    "step1_title": {"EN": "1. Game Window", "TR": "1. Oyun Penceresi"},
    "step2_title": {"EN": "2. Monsters", "TR": "2. Canavarlar"},
    "step3_title": {"EN": "3. Attack Keys", "TR": "3. Saldırı Tuşları"},
    "step4_title": {"EN": "4. Start", "TR": "4. Başlat"},
    "next": {"EN": "Next ▶", "TR": "İleri ▶"},
    "back": {"EN": "◀ Back", "TR": "◀ Geri"},
    "step1_help": {"EN": "Pick the game's window - its whole area becomes the hunt region automatically, "
                          "no separate step for that.",
                    "TR": "Oyun penceresini seçin - av bölgesi otomatik olarak o pencerenin tamamı olur, "
                          "ayrı bir adım gerekmez."},
    "step2_help": {"EN": "For each monster you want to hunt: drag a tight box around just its name text, "
                          "type a name. The color is calibrated from that box automatically - no template "
                          "picture needed.",
                    "TR": "Avlamak istediğiniz her canavar için: isim yazısının tam üzerine dar bir kutu çizin, "
                          "bir isim yazın. Renk o kutudan otomatik kalibre edilir - şablon görsel gerekmez."},
    "step3_help": {"EN": "Which keys should the bot press to attack? Comma-separated, in order.",
                    "TR": "Bot saldırmak için hangi tuşlara bassın? Virgülle ayırın, sırasıyla."},
    "add_monster": {"EN": "➕ Add Monster", "TR": "➕ Canavar Ekle"},
    "remove_monster": {"EN": "🗑 Remove", "TR": "🗑 Kaldır"},
    "no_monsters_added": {"EN": "No monsters added yet", "TR": "Henüz canavar eklenmedi"},
    "monsters_added": {"EN": "{n} monster(s) added", "TR": "{n} canavar eklendi"},
    "err_no_monsters": {"EN": "Add at least one monster (or enable Keypress Only mode).",
                         "TR": "En az bir canavar ekleyin (ya da Sadece Tuş Vuruşu modunu açın)."},
    "err_no_keys": {"EN": "Enter at least one attack key.", "TR": "En az bir saldırı tuşu girin."},
    "advanced_settings": {"EN": "⚙ Advanced Settings", "TR": "⚙ Gelişmiş Ayarlar"},
    "summary_window": {"EN": "Window: {v}", "TR": "Pencere: {v}"},
    "summary_monsters": {"EN": "Monsters: {v}", "TR": "Canavarlar: {v}"},
    "summary_keys": {"EN": "Keys: {v}", "TR": "Tuşlar: {v}"},
    "ready_to_start": {"EN": "Ready. Press Start when you are.", "TR": "Hazır. İstediğinizde Başlat'a basın."},
}


def get_language():
    try:
        with open(_LANG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            lang = data.get("language", "").upper()
            if lang in ("TR", "EN"):
                return lang
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        pass
    return None


def save_language(lang):
    lang = lang.upper()
    if lang not in ("TR", "EN"):
        lang = "EN"
    try:
        with open(_LANG_FILE, "w", encoding="utf-8") as f:
            json.dump({"language": lang}, f)
    except OSError:
        pass


class Translator:
    def __init__(self, lang=None):
        self.lang = lang or get_language() or "EN"

    def set_language(self, lang):
        self.lang = lang.upper() if lang.upper() in ("TR", "EN") else "EN"
        save_language(self.lang)

    def __call__(self, key, **kwargs):
        entry = _STRINGS.get(key)
        if entry is None:
            return key
        text = entry.get(self.lang, entry.get("EN", key))
        if kwargs:
            try:
                return text.format(**kwargs)
            except (KeyError, IndexError):
                return text
        return text
