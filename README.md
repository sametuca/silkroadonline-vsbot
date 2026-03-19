# Silkroad Vision Bot 🎮

**Silkroad Online için Şablon Tabanlı (Template Matching) Canavar Tespit Sistemi ile Yazılmış Otomatik Bot**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Platform: Windows](https://img.shields.io/badge/platform-Windows-blue)]()

---

## 🎯 Temel Özellikler

- **⌨️ Tuş Vuruşu Modu** (Varsayılan)
  - Canavar seçimi olmaksızın sadece belirtilen tuşları basma
  - Hızlı, güvenli ve ayarlama gerekmez
  
- **📸 Şablon Tabanlı Canavar Tespiti**
  - `monsters/` klasöründeki PNG dosyalarla canavarlara karşı gözlem yapma
  - OpenCV `cv2.matchTemplate` kullanarak görüntü eşleştirme
  - Ayarlanabilir hassasiyet (Threshold) seçeneği
  - **Tesseract OCR gerekmez!**

- **🖱️ Esnek İnput Yöntemi Seçimi**
  - Auto (Otomatik - önerilen)
  - SendInput (Hardware-level scan codes)
  - PyDirectInput (Alternatif girdi)
  - Keyboard Library (Fallback seçeneği)

- **⚙️ Kişiselleştirilebilir Ayarlar**
  - Tuş aralığı (0.1 - 1.0 saniye)
  - Canavar arası bekleme (0.1 - 2.0 saniye)
  - Şablon hassasiyet eşiği (0.1 - 0.9)
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

### 3. Monster Şablonlarını Hazırla ⭐ ÖNEMLİ

**Şablon Tabanlı Canavar Tespiti için:**

1. **Oyunda bir canavara yaklaş**
2. **Windows + Shift + S** ile ekran parçası al
3. **Canavarın adının veya gövdesinin göründüğü kısmı** seç
4. **Paint veya benzeri programda** PNG olarak kaydet
5. **`monsters/` klasörüne** kopyala

**Dosya adlandırma örnekleri:**
```
monsters/
├── bighwhitespider.png
├── earthghostsoldier.png
├── shakram.png
└── edimmu.png
```

**İpucu:** Canavar ismini net görünen ekran parçasını seç. Çok parlak veya çok koyu yerlerden screenshot alma.

---

## 🎮 Kullanım

### GUI ile Başlat (Önerilen)
```bash
python bot_gui.py
```

Veya Windows'da:
- `run_gui.bat` dosyasına çift tıkla
- Veya Yönetici olarak çalıştır: `run_gui.bat` → Sağ tıkla → Yönetici olarak çalıştır

---

## ⚙️ Ayarlar ve Konfigürasyon

### 1. **Tuş Vuruşu Modu** ✓ Varsayılan AÇIK

```
☑ Sadece Tuş Vuruşu Modu (Canavar seçimi kapalı)
```

- **Etkinleştirildiğinde:** Bot sadece tuşları basacak, canavar araması yapmayacak
- **Devre dışı:** Şablon tabanlı canavar tespiti aktifleşir → PNG template'lerle avlanır

### 2. **Tuş Kombinasyonları**

```
Skill Keys: 1,2,3,4
```

Botun basacağı tuşları virgülü kullanarak belirt:
- Örnek: `q,w,e,r`
- Örnek: `1,2,3,4,5`

### 3. **Tuş Aralığı**

```
Skill Interval: 0.15 saniye
```

- Her tuş basışı arasında bekle
- Düşük değer = Hızlı hücum
- Yüksek değer = Tuş arası daha uzun

### 4. **Canavar Arası Bekleme**

```
Mob Interval: 0.2 saniye
```

- Canavar öldürüldükten sonra ilerlemeden önce bekle
- Düşük = Hızlı av, Yüksek = Daha kontrollü

### 5. **Input Yöntemi** (Tuş Gönderme)

```
Input Method: Auto (Recommended)
```

**Seçenekler:**
- **Auto:** Sistem otomatik uygun yöntemi seçer
- **SendInput:** Windows API doğrudan hardware tuş basması (En güvenilir)
- **PyDirectInput:** Alternatif kütüphane
- **Keyboard:** Fallback seçeneği

### 6. **Hunt Region** (Canavar Tespiti Alanı)

```
"📍 Set Hunt Region (Template Detection)" butonuna tıkla
```

Adımlar:
1. Buton düğmesine tıkla
2. Açılan pencerede "OK"ye basınca ekran gri olur
3. **Farenle** oyun içinde canavarlara baktığın bölgeyi seç (tıklayıp sürükle)
4. Fare düğmesini bırak - bölge kaydedilir

### 7. **Şablon Hassasiyet Eşiği** (Template Threshold)

```
Template Threshold: 0.40
```

- **Düşük değer (0.1):** Çok hassas - her benzer şeyi tespit eder
- **Yüksek değer (0.9):** Çok katı - sadece tam eşleşmeleri tespit eder
- **Önerilen:** 0.35 - 0.50

**Debug İpucu:** Log penceresinde "Confidence = X.XX" görürsen match başarılı demektir. Görmüyorsan threshold'u düşür.

---

## 📸 Şablon Tabanlı Canavar Tespiti Nasıl Çalışır?

### Hazırlık Aşaması
1. `monsters/` klasörüne canavar PNG'lerini koy
2. Bot başlatıldığında otomatik yüklenir → Log'ta "Template yüklendi" mesajı görürsün

### Çalışma Aşaması
1. Bot, Hunt Region'dan screenshot alır
2. Her template'i ekranda arar (OpenCV `cv2.matchTemplate`)
3. Hassasiyet eşiğinden yukarı match bulursa:
   - Bulduğu konuma tıkla
   - Skill tuşlarını bas
   - Sonraki canavar ara

### Debug Tekniği
- Log penceresinde titreşim görüyorsan → Threshold çok düşük
- Hiç log görmüyorsan → Threshold çok yüksek
- Ore "Confidence = 0.45" → İyi işaret!

---

## ⌨️ Tuşlar

- **Q:** Botu durdur (oyun penceresinde)
- **START/STOP:** GUI'dan kontrol et

---

## 🚨 Sorun Giderme

### Bot canavarlara tıklamıyor
**Kontrol listesi:**
1. Tuş Vuruşu Modu kapalı mı? (Kapalı olması gerekir template tespiti için)
2. `monsters/` klasöründe PNG dosyaları var mı?
3. Hunt Region doğru mu seçildi?
4. Template Threshold çok yüksek mi? → Düşür (örn: 0.40 → 0.30)
5. Bot log'larında "NE template loaded" mi yazıyor? Eğer öyle, template bulunamıyor demektir

### Tuşlar oyunda gitmeyip
**Deneme sırası:**
1. Yönetici olarak çalıştır: `run_gui.bat` → Sağ tıkla → Yönetici olarak çalıştır
2. Input Yöntemi değiştir: GUI'da "SendInput"ı seç (Tuş Vuruşu Modu aktifse)
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
├── bot_gui.py              # Ana GUI programı
├── bot.py                  # Komut satırı versiyonu
├── requirements.txt        # Python bağımlılıkları
├── run_gui.bat            # Windows GUI başlatıcı
├── README.md              # Bu dosya
│
├── monsters/              # Canavar template'leri (PNG dosyaları)
│   ├── bighwhitespider.png
│   ├── earthghostsoldier.png
│   └── .gitkeep
│
└── power_bar/             # (Eski sürümlerde kullanılıyordu)
```

---

## 💡 Kullanım İpuçları

### Hızlı Başlangıç
1. **Tuş Vuruşu Modu**'nde başla (varsayılan):
   - Python'u çalıştır, ayar yapma gerek yok
   - Oyunda manuel tıkla, bot tuşları basacak

2. **Canavar Tespiti kurmak için:**
   - `monsters/` klasörüne 2-3 PNG at
   - Tuş Vuruşu Modu'nu KAP (unchecked)
   - Hunt Region'u seç
   - Başlat

### Template Seçimi
- Canavar adını net görebileceğin kısım seç
- Zifiri karanlık veya aşırı aydınlık yerlerde screenshot alma
- Zoom seviyesini değiştirirsen, yeni template'ler al

### Performans Optimizasyonu
- Template threshold'unu log'u okuyarak ayarla:
  - "Confidence = 0.X" görüyorsan, iyiydir
  - Görmüyorsan → Threshold'u 0.05 düşür ve yeniden dene

---

## ⚠️ Sorumluluk Reddi

Bu bot eğitim amaçlı yazılmıştır. Kullanımın riski size aittir.

**Uyarılar:**
- Bot hesabının yasaklanmasından yazılım yazarı sorumlu değildir
- Oyun kurallarına uyduğunuzdan emin olun
- Uzun süreli kullanımda hesabınızı riske atabilirsiniz
- Oyunun Terms of Service'ini okuduğunuzdan emin olun

---

## 📜 Lisans

MIT Lisansı altında açık kaynaklı. Detaylar için [LICENSE](LICENSE) dosyasına bakın.

---

**Başarılı avlar! 🎯**
