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
    "hunt_region": {"EN": "Hunt Region", "TR": "Av Bölgesi"},
    "set_hunt_region": {"EN": "🎯 Set Hunt Region", "TR": "🎯 Av Bölgesi Seç"},
    "region_not_set": {"EN": "Region not set", "TR": "Bölge ayarlanmadı"},
    "region_set": {"EN": "Region: {w}x{h} @ ({x},{y})", "TR": "Bölge: {w}x{h} @ ({x},{y})"},
    "monster_templates": {"EN": "Monster Templates", "TR": "Canavar Şablonları"},
    "add_template": {"EN": "➕ Add Template", "TR": "➕ Şablon Ekle"},
    "templates_loaded": {"EN": "{n} template(s) loaded", "TR": "{n} şablon yüklendi"},
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
    "err_no_region": {"EN": "Set the hunt region first.", "TR": "Önce av bölgesini ayarlayın."},
    "err_no_templates": {"EN": "No templates loaded and Keypress Only Mode is off.", "TR": "Şablon yüklenmedi ve Sadece Tuş Vuruşu Modu kapalı."},
    "hotkey_hint": {"EN": "Hotkeys (work anywhere, even while the game is focused): Ctrl+B start, Ctrl+D or Q stop.",
                    "TR": "Kısayollar (oyun penceresindeyken de çalışır): Ctrl+B başlat, Ctrl+D veya Q durdur."},
    "drag_to_select": {"EN": "Click and drag to select the hunt region, then release. Esc to cancel.",
                        "TR": "Av bölgesini seçmek için tıklayıp sürükleyin, sonra bırakın. İptal için Esc."},
    "template_wizard_hint": {"EN": "Click and drag over the monster's name/body, then release.",
                              "TR": "Canavarın adı/gövdesi üzerinde tıklayıp sürükleyin, sonra bırakın."},
    "template_name_prompt": {"EN": "Template name (used as filename):", "TR": "Şablon adı (dosya adı olarak kullanılır):"},

    "detection_mode": {"EN": "Detection Mode", "TR": "Tespit Modu"},
    "mode_hybrid": {"EN": "Hybrid (color + shape, recommended)", "TR": "Hibrit (renk + şekil, önerilen)"},
    "mode_color": {"EN": "Color only (no templates needed)", "TR": "Sadece renk (şablon gerekmez)"},
    "mode_template": {"EN": "Template only (full-frame)", "TR": "Sadece şablon (tüm ekran)"},
    "mode_ocr": {"EN": "OCR (reads the name, needs easyocr)", "TR": "OCR (ismi okur, easyocr gerekir)"},
    "ocr_unavailable": {"EN": "easyocr not installed - OCR mode disabled", "TR": "easyocr kurulu değil - OCR modu kapalı"},
    "calibrate_color": {"EN": "🎨 Calibrate Nameplate Color", "TR": "🎨 İsim Etiketi Rengini Kalibre Et"},
    "calibrate_hint": {"EN": "Click once directly on a monster's name text.", "TR": "Bir canavarın isim yazısının tam üzerine bir kez tıklayın."},
    "color_calibrated": {"EN": "Nameplate color calibrated", "TR": "İsim etiketi rengi kalibre edildi"},
    "hp_bar": {"EN": "HP Bar (optional, for reliable death detection)", "TR": "HP Bar (opsiyonel, güvenilir ölüm tespiti için)"},
    "set_hp_bar": {"EN": "❤ Set HP Bar Region", "TR": "❤ HP Bar Bölgesi Seç"},
    "hp_bar_hint": {"EN": "Drag a thin box over just the target's HP bar (top-left corner to bottom-right).",
                     "TR": "Hedefin HP barının tam üzerinde ince bir kutu seçin (sol üstten sağ alta)."},
    "hp_bar_not_set": {"EN": "Not set (using timer fallback)", "TR": "Ayarlanmadı (zamanlayıcıya düşülüyor)"},
    "hp_bar_set": {"EN": "HP bar region set", "TR": "HP bar bölgesi ayarlandı"},
    "clear": {"EN": "Clear", "TR": "Temizle"},
    "loot_key": {"EN": "Loot Key (optional)", "TR": "Loot Tuşu (opsiyonel)"},
    "profiles": {"EN": "Profile", "TR": "Profil"},
    "save_profile": {"EN": "💾 Save", "TR": "💾 Kaydet"},
    "load_profile": {"EN": "📂 Load", "TR": "📂 Yükle"},
    "delete_profile": {"EN": "🗑 Delete", "TR": "🗑 Sil"},
    "profile_name_prompt": {"EN": "Profile name:", "TR": "Profil adı:"},
    "profile_saved": {"EN": "Profile '{name}' saved", "TR": "'{name}' profili kaydedildi"},
    "profile_loaded": {"EN": "Profile '{name}' loaded", "TR": "'{name}' profili yüklendi"},
    "profile_deleted": {"EN": "Profile '{name}' deleted", "TR": "'{name}' profili silindi"},
    "no_profile_selected": {"EN": "Select a profile first", "TR": "Önce bir profil seçin"},
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
