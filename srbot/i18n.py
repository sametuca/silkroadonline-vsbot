"""Turkish / English texts.

`t("key")` returns the text in the current language; `{name}` placeholders are
filled from keyword arguments. Turkish is the default and the fallback.
"""

LANGUAGES = {"tr": "Türkçe", "en": "English"}
_current = "tr"

# key: (Türkçe, English)
S = {
    # -- language screen / generic ------------------------------------------------
    "lang_title": ("Dil / Language", "Dil / Language"),
    "lang_hint": ("Programı hangi dilde kullanmak istersin?", "Which language do you want to use?"),
    "back": ("Geri", "Back"),
    "next": ("İleri", "Next"),
    "finish": ("Bitir", "Finish"),
    "cancel": ("İptal", "Cancel"),
    "close": ("Kapat", "Close"),
    "retry": ("Tekrar ara", "Search again"),

    # -- wizard ------------------------------------------------------------------
    "wizard_subtitle": ("Birkaç adımda hazırla", "Set up in a few steps"),
    "step_game": ("Oyun", "Game"),
    "step_monster": ("Canavar", "Monster"),
    "step_keys": ("Tuşlar", "Keys"),
    "win_title": ("Oyun penceresini seç", "Pick the game window"),
    "win_hint": ("Oyunu pencere modunda aç. Pencere listede yoksa oyunu açıp ⟳ düğmesine bas.",
                 "Run the game in windowed mode. If it is not in the list, open the game and press ⟳."),
    "mon_title": ("Hangi canavara vuracağız?", "Which monster should we hit?"),
    "mon_hint": ("Oyunda canavarın üstünde yazan adı birebir aynı yaz (büyük/küçük harf fark etmez). "
                 "Birden fazla canavar için virgülle ayır.",
                 "Type the name exactly as shown above the monster in the game (case does not matter). "
                 "Separate several monsters with commas."),
    "mon_placeholder": ("Örn: Mangyang", "E.g. Mangyang"),
    "mon_read_btn": ("🔍  Adı ekrandan oku (isteğe bağlı)", "🔍  Read the name from the screen (optional)"),
    "mon_searching": ("Aranıyor...", "Searching..."),
    "mon_note": ("Normal, şampiyon ve dev canavarlar aynı adı taşır, bu yüzden tek ad hepsini kapsar.",
                 "Normal, champion and giant monsters share the same name, so one name covers all of them."),
    "keys_title": ("Tuşlar ve seçenekler", "Keys and options"),
    "keys_hint": ("Skill çubuğundaki tuşları gir. Birden fazlası sırayla basılır (örn. 1,2,3,4).",
                  "Enter the keys from your skill bar. Several keys are pressed in turn (e.g. 1,2,3,4)."),
    "keys_attack": ("Saldırı tuşları", "Attack keys"),
    "roam_switch": ("Canavar yoksa gezinerek ara", "Search by roaming when no monster is around"),
    "radius_text": ("Kasılma alanı: başladığın yerden en fazla {n} adım uzağa gider (canavarı gördükçe merkez kayar)",
                    "Farming area: goes at most {n} steps from where you started (the centre moves as monsters are seen)"),
    "err_no_window": ("Önce oyun penceresini seç. Oyun açık değilse aç ve ⟳ düğmesine bas.",
                      "Pick the game window first. If the game is not running, start it and press ⟳."),
    "err_no_monster": ("Canavarın adını yaz (oyunda üstünde göründüğü gibi).",
                       "Type the monster's name (as it appears above it in the game)."),
    "language_label": ("Dil", "Language"),

    # -- dashboard ---------------------------------------------------------------
    "settings_title": ("Hazırlanan ayarlar", "Your settings"),
    "change_settings": ("⚙  Ayarları değiştir", "⚙  Change settings"),
    "overlay_switch": ("Canavarları ekranda işaretle", "Mark monsters on screen"),
    "advanced": ("Gelişmiş", "Advanced"),
    "log_title": ("Günlük", "Log"),
    "about_btn": ("Hakkında", "About"),
    "test_scan": ("Test taraması", "Test scan"),
    "start": ("BAŞLAT", "START"),
    "stop": ("DURDUR", "STOP"),
    "sum_game": ("Oyun", "Game"),
    "sum_target": ("Hedef", "Target"),
    "sum_attack": ("Saldırı tuşları", "Attack keys"),
    "sum_roam": ("Gezinme", "Roaming"),
    "sum_roam_on": ("radara göre, {n} adım alan", "by radar, {n}-step area"),
    "off": ("kapalı", "off"),
    "none": ("yok", "none"),
    "ready_log": ("Hazır. BAŞLAT'a basınca bot oyun penceresini öne alıp avlanmaya başlar.",
                  "Ready. Press START and the bot brings the game to the front and starts hunting."),

    # -- advanced ----------------------------------------------------------------
    "detector": ("Tespit:", "Detector:"),
    "mode_auto": ("Otomatik", "Automatic"),
    "mode_ocr": ("Sadece OCR", "OCR only"),
    "mode_model": ("Sadece model", "Model only"),
    "rec_start": ("Eğitim verisi topla", "Collect training data"),
    "rec_stop": ("Veri toplamayı durdur", "Stop collecting"),
    "rec_count": ("Kayıtlı kare: {n}", "Saved frames: {n}"),
    "train": ("Modeli eğit", "Train model"),
    "training": ("Eğitiliyor...", "Training..."),
    "rec_stopped_log": ("Veri toplama durdu. Veri setinde {n} kare var.", "Collecting stopped. The dataset has {n} frames."),
    "rec_need_target": ("Önce hedef canavarı gir; etiketler canavar isminden üretilir.",
                        "Enter the target monster first; labels are made from its name."),
    "rec_while_hunting": ("Bot avlanırken kareler kaydedilecek.", "Frames will be saved while the bot hunts."),
    "train_frozen": ("Eğitim exe içinden yapılamaz: kaynak koddan 'python -m srbot.train' çalıştır.",
                     "Training is not possible from the exe: run 'python -m srbot.train' from source."),
    "train_more_frames": ("Eğitim için daha fazla kare gerek (şu an {n}, öneri 100+).",
                          "More frames are needed to train (now {n}, 100+ recommended)."),
    "train_started": ("Eğitim başladı (CPU'da dakikalar sürebilir). Bu sırada botu başlatma.",
                      "Training started (can take minutes on CPU). Do not start the bot meanwhile."),
    "train_done": ("Eğitim bitti, model kullanıma hazır.", "Training finished, the model is ready."),
    "train_failed": ("Eğitim başarısız (kod {code}). Ayrıntı için terminalde 'python -m srbot.train' çalıştır.",
                     "Training failed (code {code}). Run 'python -m srbot.train' in a terminal for details."),
    "train_error": ("Eğitim başlatılamadı: {err}", "Could not start training: {err}"),

    # -- dialogs -----------------------------------------------------------------
    "found_title": ("Canavarlar bulundu", "Monsters found"),
    "notfound_title": ("Canavar bulunamadı", "No monster found"),
    "notfound_text": ("Ekranda canavar ismi okunamadı.\n\nKarakterini canavarların yakınına götür, oyun "
                      "penceresinin üstünün açık olduğundan emin ol ya da adı elle yaz.",
                      "No monster name could be read on screen.\n\nMove your character near the monsters, make sure "
                      "the game window is uncovered, or type the name by hand."),
    "found_header": ("Ekranda şunları buldum.\nHangisine vuracağız?", "Here is what I found.\nWhich one should we hit?"),
    "found_count": ("{name}  ({n} adet)", "{name}  ({n} on screen)"),
    "found_others": ("Diğerleri başka oyuncu veya NPC olabilir, bu yüzden işaretsiz.",
                     "The others may be players or NPCs, so they are unticked."),
    "use_this": ("Bunu kullan", "Use this"),
    "about_title": ("Hakkında", "About"),
    "about_version": ("Sürüm {v}", "Version {v}"),
    "about_desc": ("Ekrandaki canavarları isim etiketinden tanıyan,\nbellek okumayan açık kaynaklı av botu.",
                   "An open-source hunting bot that recognises monsters from their\nname labels and never reads game memory."),
    "about_dev": ("Geliştirici: {name}", "Developer: {name}"),
    "about_project": ("Proje sayfası", "Project page"),
    "about_license": ("MIT Lisansı", "MIT License"),

    # -- test scan / run control -------------------------------------------------
    "scan_window_missing": ("Oyun penceresi bulunamadı. 'Ayarları değiştir' ile yeniden seç.",
                            "Game window not found. Pick it again with 'Change settings'."),
    "scan_need_target": ("Önce hedef canavarı gir ('Ayarları değiştir').", "Enter the target monster first ('Change settings')."),
    "scan_found": ("Test taraması ({mode}): {n} canavar bulundu ({names}).", "Test scan ({mode}): {n} monsters found ({names})."),
    "scan_none": ("Test taraması ({mode}): hedef canavar görünmüyor. Oyun penceresinin üstü açık mı, ad doğru mu?",
                  "Test scan ({mode}): no target monster visible. Is the game window uncovered and the name correct?"),
    "scan_error": ("Arama hatası: {err}", "Search error: {err}"),
    "no_attack_keys": ("Uyarı: saldırı tuşu girilmedi, bot sadece canavara tıklayacak.",
                       "Warning: no attack key entered, the bot will only click the monster."),
    "hotkey_failed": ("Global kısayol kurulamadı; düğmeyi kullan.", "Could not register the global hotkey; use the button."),

    # -- bot (engine) ------------------------------------------------------------
    "state_idle": ("Beklemede", "Idle"),
    "state_scanning": ("Canavar aranıyor", "Searching for monsters"),
    "state_confirming": ("Hedef doğrulanıyor", "Confirming target"),
    "state_attacking": ("Saldırıyor", "Attacking"),
    "state_roaming": ("Canavar aranıyor (geziyor)", "Searching (roaming)"),
    "admin_hint": ("Oyun yönetici olarak çalışıyor, bu program değil: Windows tuş ve tıklamaları sessizce engelliyor. "
                   "Programı yönetici olarak yeniden başlat.",
                   "The game runs as administrator and this program does not: Windows silently blocks keys and clicks. "
                   "Restart the program as administrator."),
    "bot_key_failed": ("'{key}' tuşu gönderilemedi (desteklenmeyen tuş adı olabilir).",
                       "Could not send key '{key}' (unsupported key name?)."),
    "bot_started": ("Bot başladı.", "Bot started."),
    "bot_stopped": ("Bot durdu.", "Bot stopped."),
    "bot_no_focus": ("Oyun penceresi öne alınamadı; üstü kapalıysa tespit bozulur.",
                     "Could not bring the game to the front; detection suffers if it is covered."),
    "bot_window_closed": ("Oyun penceresi kapandı, bot durdu.", "The game window closed, the bot stopped."),
    "bot_error": ("Hata: {err}", "Error: {err}"),
    "bot_idle": ("Yakında hedef canavar görünmüyor, aranıyor...", "No target monster nearby, searching..."),
    "bot_retry_focus": ("Oyun penceresi öne alınamadı, tekrar deneniyor.", "Could not bring the game to the front, retrying."),
    "bot_target": ("Hedef: {name} {pos}", "Target: {name} {pos}"),
    "bot_click_rejected": ("Tıklama Windows tarafından reddedildi (yönetici yetkisi gerekebilir).",
                           "Windows rejected the click (administrator rights may be needed)."),
    "bot_keys_sent": ("Saldırı tuşları sırayla gönderiliyor: {keys}", "Sending attack keys in turn: {keys}"),
    "bot_killed": ("{name} öldü (toplam {n}, {k} tuşa basıldı).", "{name} died (total {n}, {k} key presses)."),
    "bot_timeout": ("Hedef zaman aşımına uğradı, atlanıyor.", "Target timed out, skipping."),
    "bot_corpse": ("{name} zaten ölüydü, sıradakine geçiliyor.", "{name} was already dead, moving to the next one."),
    "bot_panel_debug": ("Hedef penceresi görünmedi (şerit {dark:.2f}, kontrast {contrast:.0f}, yazı {text}). Kare kaydedildi: {path}",
                        "Target window not seen (strip {dark:.2f}, contrast {contrast:.0f}, text {text}). Frame saved: {path}"),
    "bot_panel_off": ("Hedef penceresi okunamadı, etiket yöntemine dönüldü.",
                      "Could not read the target window, falling back to name labels."),
    "bot_wrong_target": ("Seçilen '{name}' hedef değil, atlanıyor.", "Selected '{name}' is not a target, skipping."),
    "bot_stalled": ("Canavar can kaybetmiyor (ulaşılamıyor olabilir), atlanıyor.",
                    "The monster is not losing health (maybe unreachable), skipping."),
    "roam_radar": ("Radarda {n} canavar noktası var, ona doğru yürünüyor.", "The radar shows {n} monster dots, walking toward one."),
    "roam_home": ("Radar boş, kasılma alanına geri dönülüyor.", "The radar is empty, walking back to the farming area."),
    "roam_wander": ("Radar boş, alanın içinde kısa adımlarla aranıyor.", "The radar is empty, searching in short steps inside the area."),
    "roam_rejected": ("Gezinme tıklaması reddedildi (yönetici yetkisi gerekebilir).",
                      "The roaming click was rejected (administrator rights may be needed)."),

    # -- start-up ----------------------------------------------------------------
    "admin_required_title": ("Yönetici yetkisi gerekli", "Administrator rights required"),
    "admin_required_text": ("Bu program oyuna tuş ve tıklama gönderebilmek için yönetici olarak çalışmak zorundadır.\n"
                            "Açılan Windows onay penceresinde 'Evet' de ve programı tekrar başlat.\n\n"
                            "This program must run as administrator to send keys and clicks to the game.\n"
                            "Choose 'Yes' in the Windows prompt and start the program again.",
                            "Bu program oyuna tuş ve tıklama gönderebilmek için yönetici olarak çalışmak zorundadır.\n"
                            "Açılan Windows onay penceresinde 'Evet' de ve programı tekrar başlat.\n\n"
                            "This program must run as administrator to send keys and clicks to the game.\n"
                            "Choose 'Yes' in the Windows prompt and start the program again."),
}


def set_language(code):
    global _current
    _current = code if code in LANGUAGES else "tr"


def get_language():
    return _current


def t(name, /, **kwargs):
    """Text for `name` in the current language (positional-only so placeholders may be called `key`)."""
    entry = S.get(name)
    if entry is None:
        return name
    text = entry[1] if _current == "en" else entry[0]
    return text.format(**kwargs) if kwargs else text
