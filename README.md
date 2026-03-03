# Silkroad Vision Bot 🎮

**Advanced Python bot for Silkroad Online with computer vision detection, power bar automation, modern GUI, and anti-ban features.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Platform: Windows](https://img.shields.io/badge/platform-Windows-blue)]()

[English](#english) | [Türkçe](#turkish)

---

## <a name="english"></a>🇬🇧 English

### ✨ Features

- 🔍 **Two Hunt Modes**:
  - **Image Detection**: Traditional monster image recognition (requires screenshots)
  - **Region Mode**: Define a hunt area and specify monster names - bot searches for those monsters within the region only
- ⚡ **Power Bar Automation**: Detects when your power bar is full and automatically presses TAB
- 🖥️ **Modern GUI**: User-friendly interface with real-time statistics and logs
- ⚙️ **Highly Customizable**: 
  - Detection confidence slider
  - Skill interval adjustment
  - Mob interval adjustment
  - Custom skill key mapping
- 🎯 **Smart Targeting**: Attacks closest monsters first to minimize movement
- ⛔ **Static Mode**: Option to disable mouse movement (only attack with skills)
- 📊 **Live Statistics**: Track kills, power usage, and running time
- 🚀 **Maximum Speed**: Optimized for fast farming
- 🛡️ **Anti-Ban Features**: Randomized timings and human-like behavior

### 📋 Requirements

- Windows 10/11
- Python 3.8 or higher
- Game running in windowed mode (recommended)

### 🚀 Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/silkroad-vision-bot.git
cd silkroad-vision-bot
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Prepare monster images**
   - Take screenshots of monster names or bodies
   - Save them as PNG files in the `monsters/` folder
   - Examples: `shakram.png`, `edimmu.png`

4. **(Optional) Prepare power bar image**
   - Take a screenshot of your **FULL** power bar
   - Save it as `bar_full.png` in the `power_bar/` folder

### 🎮 Usage

#### Using GUI (Recommended)
```bash
# Run normally
python bot_gui.py

# Or double-click
run_gui.bat

# Run as Administrator (for better compatibility)
Right-click run_gui.bat → Run as Administrator
```

#### Using Command-Line
```bash
python bot.py
```

### 📐 Configuration

**In the GUI, you can adjust:**

1. **Detection Confidence** (0.5 - 0.95)
   - Lower = Faster but less accurate
   - Higher = More precise but may miss targets
   - Recommended: 0.75 - 0.80

2. **Hunt Mode**
   - **📸 Image Detection**: Uses monster screenshots (requires images in monsters/ folder)
   - **🎯 Region Mode**: Define a hunt area and specify monster names, bot searches for those monsters only within that region
     - Click "Set Hunt Region" button
     - Click OK on the dialog
     - **Draw a rectangle with your mouse** on your game screen (click and drag)
     - Release mouse button to confirm
     - **Enter monster names** in the "Monster Names" field (comma separated, e.g., "shakram, edimmu, giant")
     - The bot uses **smart matching** - spaces, hyphens, and underscores are ignored
     - Examples: "strong earth ghost" matches "strongearthghost.png" or "strong_earth_ghost.png"
     - Bot will search for those specific monsters only within the selected region
     - More accurate than grid clicking - only attacks real monsters!

3. **Skill Interval** (0.1 - 1.0 seconds)
   - Time between skill presses
   - Lower = Faster combat
   - Adjust based on skill cooldowns

4. **Mob Interval** (0.1 - 2.0 seconds)
   - Wait time after killing a mob
   - Lower = Faster farming

5. **Skill Keys**
   - Default: 1,2,3,4
   - Can be changed to any keys (e.g., q,w,e,r)

6. **Static Mode**
   - When enabled, bot won't move mouse
   - Only attacks with skills

7. **Power Bar Detection**
   - Automatically presses TAB when power bar is full
   - Check interval: 5-30 seconds (default: 17)
   - **Two modes available:**
     - **Filtered mode**: Use power bar only for specific mobs (e.g., "giant", "champion")
     - **Always mode**: Use power bar for all mobs whenever it's full

### 🖼️ Screenshot Guide

**For Image Detection Mode:**
1. Stand near a monster
2. Press `Windows + Shift + S`
3. Select only the **monster's name** or its body
4. Paste in Paint and save to `monsters/` folder

**For Power Bar:**
1. Wait for power bar to be **completely full**
2. Press `Windows + Shift + S`
3. Select only the **full bar** (small area)
4. Save as `power_bar/bar_full.png`

### ⌨️ Hotkeys

- **Q**: Stop the bot
- **Start/Stop buttons**: Control bot from GUI

### 🛠️ Troubleshooting

**Bot doesn't find monsters:**
- Lower the detection confidence
- Make sure screenshots are clear and in PNG format
- Check that game zoom level matches screenshot zoom

**Skills not working:**
- Run as Administrator
- Make sure game is in windowed mode
- Check that skill keys match your game settings

**Mouse not moving:**
- Make sure Static Mode is disabled
- Run as Administrator

### 📝 File Structure

```
silkroad-vision-bot/
│
├── bot_gui.py          # GUI version (recommended)
├── bot.py              # Command-line version
├── requirements.txt    # Python dependencies
├── run_gui.bat        # Windows launcher for GUI
├── install.bat        # Dependency installer
│
├── monsters/          # Monster screenshots folder
│   ├── shakram.png
│   └── edimmu.png
│
└── power_bar/         # Power bar screenshots folder
    └── bar_full.png
```

### ⚠️ Disclaimer

This bot is for **educational purposes only**. Use at your own risk. The author is not responsible for any bans or consequences resulting from using this software. Always check your game's Terms of Service before using automation tools.

### 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## <a name="turkish"></a>🇹🇷 Türkçe

### ✨ Özellikler

- 🔍 **İki Avlanma Modu**:
  - **Görüntü Tespiti**: Geleneksel mob resim tanıma (ekran görüntüsü gerektirir)
  - **Bölge Modu**: Bir avlanma alanı belirle ve canavar isimlerini yaz - bot sadece o canavarları o bölgede arar
- ⚡ **Güç Barı Otomasyonu**: Bar dolduğunda otomatik TAB tuşuna basma
- 🖥️ **Modern Arayüz**: Kullanıcı dostu arayüz, canlı istatistikler ve loglar
- ⚙️ **Tamamen Özelleştirilebilir**: 
  - Tespit hassasiyeti ayarı
  - Skill aralığı ayarı
  - Mob aralığı ayarı
  - Özel skill tuş ataması
- 🎯 **Akıllı Hedefleme**: En yakın moblara saldırarak hareketi minimize eder
- ⛔ **Sabit Mod**: Fare hareketini kapatma seçeneği (sadece skill ile saldırı)
- 📊 **Canlı İstatistikler**: Öldürülen mob, güç kullanımı ve çalışma süresi takibi
- 🚀 **Maksimum Hız**: Hızlı farm için optimize edildi
- 🛡️ **Anti-Ban Özellikleri**: Rastgele zamanlamalar ve insansı davranış

### 📋 Gereksinimler

- Windows 10/11
- Python 3.8 veya üzeri
- Oyunun pencere modunda çalışması (önerilen)

### 🚀 Kurulum

1. **Projeyi indirin**
```bash
git clone https://github.com/yourusername/silkroad-vision-bot.git
cd silkroad-vision-bot
```

2. **Bağımlılıkları yükleyin**
```bash
pip install -r requirements.txt
```

3. **Mob resimlerini hazırlayın**
   - Mob isimlerinin veya gövdelerinin ekran görüntüsünü alın
   - `monsters/` klasörüne PNG olarak kaydedin
   - Örnek: `shakram.png`, `edimmu.png`

4. **(Opsiyonel) Güç barı resmini hazırlayın**
   - **DOLU** güç barının ekran görüntüsünü alın
   - `power_bar/` klasörüne `bar_full.png` olarak kaydedin

### 🎮 Kullanım

#### Arayüz ile (Önerilen)
```bash
# Normal çalıştırma
python bot_gui.py

# Veya çift tıklayın
run_gui.bat

# Yönetici olarak çalıştırma (daha iyi uyumluluk için)
run_gui.bat → Sağ tık → Yönetici olarak çalıştır
```

#### Komut Satırı ile
```bash
python bot.py
```

### 📐 Yapılandırma

**Arayüzde ayarlayabilirsiniz:**

1. **Tespit Hassasiyeti** (0.5 - 0.95)
   - Düşük = Hızlı ama daha az doğru
   - Yüksek = Daha kesin ama hedefi kaçırabilir
   - Önerilen: 0.75 - 0.80

2. **Avlanma Modu**
   - **📸 Görüntü Tespiti**: Mob ekran görüntüleri kullanır (monsters/ klasöründe resim gerekir)
   - **🎯 Bölge Modu**: Bir avlanma alanı belirle ve canavar isimlerini yaz, bot sadece o canavarları o bölgede arar
     - "Set Hunt Region" butonuna tıkla
     - Açılan pencerede OK'e bas
     - **Oyun ekranında fareyle dikdörtgen çiz** (tıklayıp sürükle)
     - Fare butonunu bırakarak onayla
     - **Canavar isimlerini gir** "Monster Names" alanına (virgülle ayrılmış, örn: "shakram, edimmu, giant")
     - Bot sadece seçilen bölgede bu canavarları arayacak
     - Izgara tıklamasından daha doğru - sadece gerçek canavarları hedef alır!

3. **Skill Aralığı** (0.1 - 1.0 saniye)
   - Skill basışları arası süre
   - Düşük = Daha hızlı dövüş
   - Skill cooldown'larınıza göre ayarlayın

4. **Mob Aralığı** (0.1 - 2.0 saniye)
   - Mob öldürme sonrası bekleme
   - Düşük = Daha hızlı farm

5. **Skill Tuşları**
   - Varsayılan: 1,2,3,4
   - İstediğiniz tuşlara değiştirilebilir (örn: q,w,e,r)

6. **Sabit Mod**
   - Aktif olduğunda fare hareket etmez
   - Sadece skill ile saldırır

7. **Güç Barı Tespiti**
   - Bar dolduğunda otomatik TAB basar
   - Kontrol aralığı: 5-30 saniye (varsayılan: 17)
   - **İki mod mevcut:**
     - **Filtreli mod**: Güç barını sadece belirli moblar için kullan (örn: "giant", "champion")
     - **Her zaman modu**: Güç barını tüm moblar için dolu olduğunda kullan

### 🖼️ Ekran Görüntüsü Rehberi

**Mob Tespiti için:**
1. Bir mobun yanına gidin
2. `Windows + Shift + S` tuşlarına basın
3. Sadece **mob ismini** veya gövdesini seçin
4. Paint'e yapıştırıp `monsters/` klasörüne kaydedin

**Güç Barı için:**
1. Güç barının **tamamen dolmasını** bekleyin
2. `Windows + Shift + S` tuşlarına basın
3. Sadece **dolu barı** seçin (küçük alan)
4. `power_bar/bar_full.png` olarak kaydedin

### ⌨️ Kısayol Tuşları

- **Q**: Botu durdur
- **Başlat/Durdur butonları**: Arayüzden bot kontrolü

### 🛠️ Sorun Giderme

**Bot mob bulamiyor:**
- Tespit hassasiyetini düşürün
- Ekran görüntülerinin net ve PNG formatında olduğundan emin olun
- Oyun zoom seviyesinin ekran görüntüsüyle aynı olduğunu kontrol edin

**Skiller çalışmıyor:**
- Yönetici olarak çalıştırın
- Oyunun pencere modunda olduğundan emin olun
- Skill tuşlarının oyun ayarlarınızla eşleştiğini kontrol edin

**Fare hareket etmiyor:**
- Sabit Mod'un kapalı olduğundan emin olun
- Yönetici olarak çalıştırın

### ⚠️ Uyarı

Bu bot **sadece eğitim amaçlıdır**. Kullanım riski size aittir. Yazılımı kullanmanın sonucunda oluşan banlar veya sonuçlardan yazar sorumlu değildir. Otomasyon araçlarını kullanmadan önce her zaman oyununuzun Hizmet Koşullarını kontrol edin.

### 📜 Lisans

Bu proje MIT Lisansı altında lisanslanmıştır - detaylar için [LICENSE](LICENSE) dosyasına bakın.

### 🤝 Katkıda Bulunma

Katkılar memnuniyetle karşılanır! Lütfen Pull Request göndermekten çekinmeyin.

---

### 💖 Support

If you find this project useful, please give it a ⭐️!

For issues or questions, please open an issue on GitHub.
