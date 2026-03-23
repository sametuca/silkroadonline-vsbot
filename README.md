# Silkroad Vision Bot 🎮

**Automatic Hunter Bot for Silkroad Online with Template-Based Monster Detection**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Platform: Windows](https://img.shields.io/badge/platform-Windows-blue)]()

---

## 📖 Language / Dil

**[🇬🇧 English Version](#-english-version) | [🇹🇷 Türkçe Sürüm](#-türkçe-sürüm)**

---

# 🇬🇧 ENGLISH VERSION

## 🎯 Key Features

- **⌨️ Keypress Only Mode** (Optional)
  - Press only specified keys without monster selection
  - Fast, safe, and requires no setup
  
- **📸 Template-Based Monster Detection**
  - Detect monsters using PNG files from the `monsters/` folder
  - Image matching with OpenCV `cv2.matchTemplate`
  - Adjustable confidence threshold
  - Short-term repeat-click prevention for dead targets

- **🖱️ Flexible Input Method Selection**
  - Auto (Automatic - recommended)
  - SendInput (Hardware-level scan codes)
  - PyDirectInput (Alternative input)
  - Keyboard Library (Fallback option)

- **⚙️ Customizable Settings**
  - Skill interval (0.1 - 1.0 seconds)
  - Mob interval (0.1 - 2.0 seconds)
  - Template confidence threshold (0.1 - 0.9)
  - Custom key combinations

- **📊 Live Statistics**
  - Monster kill counter
  - Runtime duration
  - Real-time log output

### 📋 System Requirements

- **Windows 10/11**
- **Python 3.8 or higher**
- **Game running in windowed mode** (not fullscreen)

---

## 🚀 Installation

### 1. Clone the Project
```bash
git clone https://github.com/yourusername/silkroad-vision-bot.git
cd silkroad-vision-bot
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

Or manually:
```bash
pip install pyautogui pydirectinput keyboard pillow opencv-python numpy
```

### 3. Prepare Monster Templates ⭐ IMPORTANT

**For Template-Based Monster Detection:**

1. **Get close to a monster in-game**
2. **Take a screenshot with Windows + Shift + S**
3. **Select the area showing the monster's name or body** (where you can clearly see the name)
4. **Save as PNG format** using Paint or similar
5. **Copy to `monsters/` folder**

**Example: Big White Spider Template**

Your template should look like this:

```
📋 Template Example (Big White Spider):
┌──────────────────────────────┐
│  Big White Spider            │  ← Clearly visible name
│  [Monster body visual]       │  ← Name and body
└──────────────────────────────┘
```

**File Naming Examples:**
```
monsters/
├── bighwhitespider.png
├── earthghostsoldier.png
├── shakram.png
├── edimmu.png
└── (more monster PNGs...)
```

**📌 Important Tips:**

| Tip | Description |
|-----|-------------|
| **CLEAR IMAGE** | Select an area where you can clearly see the monster name or body |
| **GOOD LIGHTING** | Take screenshots in good lighting conditions, not too dark or too bright |
| **ZOOM LOCKED** | If you change the zoom level in-game, capture new templates |
| **PNG FORMAT REQUIRED** | Do not use other formats (.jpg, .bmp), only PNG |
| **TEST AFTER ADDING** | Test after adding templates to verify confidence scores in logs |

---

## 🌐 Language Selection

**On First Launch:**
- A language selection dialog appears when the app opens
- Choose 🇬🇧 **English** or 🇹🇷 **Turkish**
- Your selection is saved in `language.json`
- The app opens in your selected language on subsequent launches

**To Change Language:**
```bash
# Delete language.json file
del language.json

# Restart the program
python bot_gui.py
```

### Start with GUI (Recommended)
```bash
python bot_gui.py
```

Or on Windows:
- Double-click the `run_gui.bat` file
- Or run as Administrator: Right-click `run_gui.bat` → Run as administrator

---

## ⚙️ Settings and Configuration

### 1. **Keypress Only Mode** ✓ Default OFF

```
☑ Keypress Only Mode (Monster detection disabled)
```

- **When enabled:** Bot will only press keys, no monster detection
- **When disabled:** Template-based monster detection is active → Hunt with PNG templates

### 2. **Target Monsters** (Optional)

```
Target Monsters: shakram,edimmu
```

- Specify monster names separated by commas
- If left empty, bot searches for all templates in `monsters/` folder
- Matching is based on file names (without extension)

### 3. **Skill Keys**

```
Skill Keys: 1,2,3,4
```

Specify keys the bot should press, separated by commas:
- Example: `q,w,e,r`
- Example: `1,2,3,4,5`

### 4. **Skill Interval**

```
Skill Interval: 0.15 seconds
```

- Wait time between each key press
- Low value = Fast attack
- High value = Longer delay between keys

### 5. **Mob Interval**

```
Mob Interval: 0.2 seconds
```

- Wait time after killing a monster before proceeding
- Low = Fast hunting, High = More controlled

### 6. **Input Method** (Key Sending)

```
Input Method: Auto (Recommended)
```

**Options:**
- **Auto:** System automatically selects the appropriate method
- **SendInput:** Direct Windows API hardware key press (Most reliable)
- **PyDirectInput:** Alternative library
- **Keyboard:** Fallback option

### 7. **Hunt Region** (Monster Detection Area)

Click the **"🎯 Set Hunt Region"** button

Steps:
1. Click the button
2. When the "OK" dialog appears, the screen will turn gray
3. **Click and drag your mouse** on the game area where monsters appear
4. Release mouse button to confirm selection

### 8. **Template Confidence Threshold**

```
Template Threshold: 0.40
```

- **Low value (0.1):** Very sensitive - detects almost anything
- **High value (0.9):** Very strict - only exact matches
- **Recommended:** 0.35 - 0.50

**Debug Tip:** If you see "Confidence = X.XX" in logs, matching is working. If not, reduce the threshold.

---

## 📸 How Template-Based Monster Detection Works

### Preparation Phase
1. Place monster PNG files in `monsters/` folder
2. Bot loads them automatically on startup → You'll see "Template loaded" in logs

### Working Phase
1. Bot captures a screenshot from Hunt Region
2. Searches for each template on screen (OpenCV `cv2.matchTemplate`)
3. If match confidence exceeds threshold:
   - Click the detected location
   - Press skill keys
   - Search for next monster

### Dead Target Re-click Prevention

- Bot remembers the target name + location for a short time
- If the same name appears at the same location again (e.g., dead monster label lingering), target is skipped
- This prevents your character from repeatedly running toward dead targets outside the farming area

### Debug Techniques
- Log shows "Confidence = 0.XX" → Match successful! ✅
- Excessive triggers in logs → Threshold too low (increase it)
- No matches in logs → Threshold too high (decrease it)

**Example Log Output:**
```
✅ Hunt region set: X=640, Y=200, W=400, H=300
🎯 Template Mode: ON
📸 Template 'bighwhitespider' loaded
Confidence = 0.65 ← Good match!
Confidence = 0.42 ← Acceptable
Confidence = 0.38 ← Only detected if threshold is 0.35
```

---

## ⌨️ Hotkeys

- **Q:** Stop the bot (while in-game)
- **START/STOP buttons:** Control from GUI

---

## 🚨 Troubleshooting

### Bot not clicking on monsters
**Checklist:**
1. Is Keypress Only Mode OFF? (Must be OFF for template detection)
2. Are there PNG files in `monsters/` folder?
3. Is Hunt Region correctly set?
4. Is Template Threshold too high? → Lower it (e.g., 0.40 → 0.30)
5. Does bot log show "NO templates loaded"? If yes, templates not found

### Keys not working in-game
**Try in order:**
1. Run as Administrator: Right-click `run_gui.bat` → Run as administrator
2. Change Input Method: GUI → Select "SendInput"
3. Switch game to windowed mode: Not fullscreen
4. Focus game window: Click on game window before starting bot

### GUI won't open
```bash
python bot_gui.py
```

If you get an error:
```bash
pip install --upgrade tkinter
```

---

## 📁 File Structure

```
silkroad-vision-bot/
│
├── bot_gui.py              # Main GUI application
├── bot.py                  # Command-line version
├── requirements.txt        # Python dependencies
├── run_gui.bat            # Windows GUI launcher
├── README.md              # This file
│
├── monsters/              # Monster templates (PNG files)
│   ├── bighwhitespider.png
│   ├── earthghostsoldier.png
│   └── .gitkeep
│
└── tools/                 # Utility scripts
    └── fetch_tabler_icons.py
```

---

## 💡 Usage Tips

### Quick Start
1. Start with template mode by default:
   - Add 2-3 PNG files to `monsters/` folder
   - Set Hunt Region
   - Optionally specify target monsters
   - Start

2. **To set up monster detection:**
   - Add 2-3 PNG files to `monsters/` folder
   - Keep Keypress Only Mode OFF (default)
   - Set Hunt Region
   - Start bot

### Template Selection
- Select a section where the monster name is clearly visible
- Don't take screenshots in very dark or very bright lighting
- Recapture templates if you change the zoom level in-game

### Performance Optimization
- Adjust template threshold based on log output:
  - Seeing "Confidence = 0.X" → Good, keep current threshold
  - Not seeing matches → Reduce threshold by 0.05 and retry

---

## ⚠️ Disclaimer

This bot is provided for educational purposes. Use at your own risk.

**Warnings:**
- The software author is not responsible for account bans
- Ensure you follow the game's rules
- Extended use may put your account at risk
- Read the game's Terms of Service carefully

---

## 📜 License

Open source under MIT License. See [LICENSE](LICENSE) for details.

---

**Happy hunting! 🎯**

---

---

# 🇹🇷 TÜRKÇE SÜRÜM

## 🎯 Temel Özellikler

- **⌨️ Tuş Vuruşu Modu** (Opsiyonel)
  - Canavar seçimi olmaksızın sadece belirtilen tuşları basma
  - Hızlı, güvenli ve ayarlama gerekmez
  
- **📸 Şablon Tabanlı Canavar Tespiti**
  - `monsters/` klasöründeki PNG dosyalarla canavarlara karşı gözlem yapma
  - OpenCV `cv2.matchTemplate` kullanarak görüntü eşleştirme
  - Ayarlanabilir güven eşiği (Threshold)
  - Aynı canavar etiketi ekranda kalsa bile kısa süreli tekrar tıklama engeli

- **🖱️ Esnek İnput Yöntemi Seçimi**
  - Auto (Otomatik - önerilen)
  - SendInput (Hardware-level tuş kodları)
  - PyDirectInput (Alternatif girdi)
  - Keyboard Library (Fallback seçeneği)

- **⚙️ Kişiselleştirilebilir Ayarlar**
  - Tuş aralığı (0.1 - 1.0 saniye)
  - Canavar arası bekleme (0.1 - 2.0 saniye)
  - Şablon güven eşiği (0.1 - 0.9)
  - Özel tuş kombinasyonları

- **📊 Canlı İstatistikler**
  - Öldürülen canavar sayacı
  - Çalışma süresi
  - Gerçek zamanlı log çıktısı

### 📋 Sistem Gereksinimleri

- **Windows 10/11**
- **Python 3.8 veya daha yüksek**
- **Oyun pencereli modda çalışıyor** (tam ekran değil)

---

## 🚀 Kurulum

### 1. Projeyi İndir
```bash
git clone https://github.com/yourusername/silkroad-vision-bot.git
cd silkroad-vision-bot
```

### 2. Python Bağımlılıklarını Yükle
```bash
pip install -r requirements.txt
```

Veya manuel:
```bash
pip install pyautogui pydirectinput keyboard pillow opencv-python numpy
```

### 3. Canavar Şablonlarını Hazırla ⭐ ÖNEMLİ

**Şablon Tabanlı Canavar Tespiti için:**

1. **Oyunda bir canavara yaklaş**
2. **Windows + Shift + S** ile ekran parçası al
3. **Canavarın adının veya gövdesinin göründüğü kısmı seç** (ismini net görebileceğin kısım)
4. **Paint veya benzeri programda kaydederken PNG format seç**
5. **`monsters/` klasörüne kopyala**

**Örnek: Big White Spider Şablonu**

Şablonunuz şöyle görünmelidir:

```
📋 Şablon Örneği (Big White Spider):
┌──────────────────────────────┐
│  Big White Spider            │  ← Net görünen isim
│  [Canavar gövdesi görseli]   │  ← İsim ve gövde
└──────────────────────────────┘
```

**Dosya Adlandırma Örnekleri:**
```
monsters/
├── bighwhitespider.png
├── earthghostsoldier.png
├── shakram.png
├── edimmu.png
└── (daha fazla canavar PNG'si...)
```

**📌 Önemli İpuçları:**

| İpucu | Açıklama |
|-------|----------|
| **NET RESİM SEÇ** | Canavar ismini veya gövdesini net görebileceğin bölümü seç |
| **İYİ AYDINLATMA** | Çok karanlık veya aşırı parlak yerlerden screenshot alma |
| **ZOOM SEVİYESİ SABİT** | Oyundaki zoom seviyesini değiştirirsen, yeni template al |
| **PNG FORMAT ŞART** | Başka formatlar (.jpg, .bmp) kullanma, sadece PNG |
| **SONRA TEST ET** | Template ekledikten sonra bot başlatıp confidence score'u kontrol et |

---

## 🌐 Dil Seçimi

**İlk Açılışta:**
- Uygulama açıldığında dil seçim penceresi gösterilir
- 🇹🇷 **Türkçe** veya 🇬🇧 **English** seçin
- Seçim `language.json` dosyasında kaydediliyor
- Sonraki açılışlarda otomatik seçilen dilde açılır

**Dili Değiştirmek İçin:**
```bash
# language.json dosyasını sil
del language.json

# Sonra programı yeniden çalıştır
python bot_gui.py
```

### GUI ile Başlat (Önerilen)
```bash
python bot_gui.py
```

Veya Windows'da:
- `run_gui.bat` dosyasına çift tıkla
- Veya Yönetici olarak çalıştır: `run_gui.bat` → Sağ tıkla → Yönetici olarak çalıştır

---

## ⚙️ Ayarlar ve Konfigürasyon

### 1. **Tuş Vuruşu Modu** ✓ Varsayılan KAPALI

```
☑ Sadece Tuş Vuruşu Modu (Canavar seçimi kapalı)
```

- **Etkinleştirildiğinde:** Bot sadece tuşları basacak, canavar araması yapmayacak
- **Devre dışı:** Şablon tabanlı canavar tespiti aktifleşir → PNG şablonlarla avlanır

### 2. **Aranacak Canavarlar** (Opsiyonel)

```
Aranacak Canavarlar: shakram,edimmu
```

- Virgülle birden fazla isim yazabilirsin
- Boş bırakırsan `monsters/` klasöründeki tüm şablonlarda arar
- Eşleşme, `monsters/` klasöründeki dosya adına göre yapılır (uzantısız)

### 3. **Skill Tuşları**

```
Skill Tuşları: 1,2,3,4
```

Botun basacağı tuşları virgülle ayırarak belirt:
- Örnek: `q,w,e,r`
- Örnek: `1,2,3,4,5`

### 4. **Skill Aralığı**

```
Skill Aralığı: 0.15 saniye
```

- Her tuş basışı arasında bekle
- Düşük değer = Hızlı hücum
- Yüksek değer = Tuş arası daha uzun

### 5. **Canavar Arası Bekleme**

```
Canavar Arası Bekleme: 0.2 saniye
```

- Canavar öldürüldükten sonra ilerlemeden önce bekle
- Düşük = Hızlı av, Yüksek = Daha kontrollü

### 6. **Input Yöntemi** (Tuş Gönderme)

```
Input Yöntemi: Auto (Önerilen)
```

**Seçenekler:**
- **Auto:** Sistem otomatik uygun yöntemi seçer
- **SendInput:** Windows API doğrudan hardware tuş basması (En güvenilir)
- **PyDirectInput:** Alternatif kütüphane
- **Keyboard:** Fallback seçeneği

### 7. **Hunt Region** (Canavar Tespiti Alanı)

**"🎯 Hunt Region Seç"** butonuna tıkla

Adımlar:
1. Buton düğmesine tıkla
2. Açılan pencerede "OK"ye basınca ekran gri olur
3. **Farenle** oyun içinde canavarlara baktığın bölgeyi seç (tıklayıp sürükle)
4. Fare düğmesini bırak - bölge kaydedilir

### 8. **Şablon Güven Eşiği**

```
Şablon Eşiği: 0.40
```

- **Düşük değer (0.1):** Çok hassas - hemen hemen her şeyi tespit eder
- **Yüksek değer (0.9):** Çok katı - sadece tam eşleşmeleri tespit eder
- **Önerilen:** 0.35 - 0.50

**Debug İpucu:** Log penceresinde "Confidence = X.XX" görürsen eşleşme başarılı demektir. Görmüyorsan eşiği düşür.

---

## 📸 Şablon Tabanlı Canavar Tespiti Nasıl Çalışır?

### Hazırlık Aşaması
1. `monsters/` klasörüne canavar PNG'lerini koy
2. Bot başlatıldığında otomatik yüklenir → Log'ta "Şablon yüklendi" mesajı görürsün

### Çalışma Aşaması
1. Bot, Hunt Region'dan screenshot alır
2. Her şablonu ekranda arar (OpenCV `cv2.matchTemplate`)
3. Güven eşiğinden yukarı eşleşme bulursa:
   - Bulduğu konuma tıkla
   - Skill tuşlarını bas
   - Sonraki canavar ara

### Ölü Hedefe Tekrar Tıklama Engeli

- Bot, tıkladığı hedefin adını + konumunu kısa süreli hafızada tutar
- Aynı isim aynı noktada tekrar bulunursa (ör. ölen canavarın etiketi birkaç saniye kaldığında) hedef atlanır
- Böylece karakterin sürekli aynı ölü hedefe yürüyüp farm alanından uzaklaşması engellenir

### Debug Teknikleri
- Log penceresinde "Confidence = 0.XX" görüyorsan → Eşleşme başarılı! ✅
- Aşırı sık tetikleme görüyorsan → Eşik çok düşük (artır)
- Hiç eşleşme görmüyorsan → Eşik çok yüksek (azalt)

**Örnek Log Çıktıları:**
```
✅ Hunt region ayarlandı: X=640, Y=200, W=400, H=300
🎯 Şablon Modu: AÇIK
📸 'bighwhitespider' şablonu yüklendi
Confidence = 0.65 ← İyi eşleşme!
Confidence = 0.42 ← Kabul edilebilir
Confidence = 0.38 ← Sadece eşik 0.35 ise algılanır
```

---

## ⌨️ Tuşlar

- **Q:** Botu durdur (oyun penceresinde)
- **BAŞLAT/DUR:** GUI'dan kontrol et

---

## 🚨 Sorun Giderme

### Bot canavarlara tıklamıyor
**Kontrol listesi:**
1. Tuş Vuruşu Modu KAPALI mı? (Kapalı olması gerekir şablon tespiti için)
2. `monsters/` klasöründe PNG dosyaları var mı?
3. Hunt Region doğru mu seçildi?
4. Şablon Eşiği çok yüksek mi? → Düşür (örn: 0.40 → 0.30)
5. Bot log'larında "NO templates loaded" mi yazıyor? Eğer öyle, şablon bulunamıyor demektir

### Tuşlar oyunda çalışmıyor
**Sırasıyla dene:**
1. Yönetici olarak çalıştır: `run_gui.bat` → Sağ tıkla → Yönetici olarak çalıştır
2. Input Yöntemi değiştir: GUI'da "SendInput"ı seç
3. Oyunu pencereli moda al: Tam ekran değil, pencereli
4. Oyun penceresine odaklan: Botu çalıştırmadan önce oyun açık ve seçili olsun

### GUI açılmıyor
```bash
python bot_gui.py
```

Hata alırsan:
```bash
pip install --upgrade tkinter
```

---

## 📁 Dosya Yapısı

```
silkroad-vision-bot/
│
├── bot_gui.py              # Ana GUI uygulaması
├── bot.py                  # Komut satırı versiyonu
├── requirements.txt        # Python bağımlılıkları
├── run_gui.bat            # Windows GUI başlatıcı
├── README.md              # Bu dosya
│
├── monsters/              # Canavar şablonları (PNG dosyaları)
│   ├── bighwhitespider.png
│   ├── earthghostsoldier.png
│   └── .gitkeep
│
└── tools/                 # Yardımcı scriptler
    └── fetch_tabler_icons.py
```

---

## 💡 Kullanım İpuçları

### Hızlı Başlangıç
1. Varsayılan şablon modu ile başla:
   - `monsters/` klasörüne 2-3 PNG ekle
   - Hunt Region'u seç
   - Gerekirse Aranacak Canavarlar alanına isim yaz
   - Başlat

2. **Canavar Tespiti kurmak için:**
   - `monsters/` klasörüne 2-3 PNG ekle
   - Tuş Vuruşu Modu KAPALI kalsın (varsayılan)
   - Hunt Region'u seç
   - Botu başlat

### Şablon Seçimi
- Canavar adını net görebileceğin kısım seç
- Zifiri karanlık veya aşırı aydınlık yerlerde screenshot alma
- Zoom seviyesini değiştirirsen, yeni şablonlar al

### Performans Optimizasyonu
- Şablon eşiğini log'u okuyarak ayarla:
  - "Confidence = 0.X" görüyorsan, iyiydir
  - Görmüyorsan → Eşiği 0.05 düşür ve yeniden dene

---

## ⚠️ Sorumluluk Reddi

Bu bot eğitim amaçlı yazılmıştır. Kullanımın riski size aittir.

**Uyarılar:**
- Hesabın yasaklanmasından yazılım yazarı sorumlu değildir
- Oyun kurallarına uyduğunuzdan emin olun
- Uzun süreli kullanımda hesabınızı riske atabilirsiniz
- Oyunun Hizmet Şartları'nı okuduğunuzdan emin olun

---

## 📜 Lisans

MIT Lisansı altında açık kaynaklı. Detaylar için [LICENSE](LICENSE) dosyasına bakın.

---

**Başarılı avlar! 🎯**
