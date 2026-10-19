<div align="center">

# Silkroad Vision Bot

### [🇬🇧 English](README.md) &nbsp;|&nbsp; [🇹🇷 Türkçe](README.tr.md)

Silkroad tarzı MMO'lar için ekran görüntüsü tabanlı otomatik av botu. Canavarları **isim etiketinden** tanır,
hedef seçer, saldırır, loot toplar ve yenisini bulmak için gezinir.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![Platform: Windows](https://img.shields.io/badge/platform-Windows-blue)]()

</div>

Bellek okumaz, paket enjekte etmez, DLL enjekte etmez. Yalnızca ekranda zaten görünen pikselleri okur ve
bir oyuncunun gönderebileceği klavye ve fare girdisini gönderir.

## Hızlı başlangıç

1. [**Releases**](../../releases/latest) sayfasından `SilkroadVisionBot.exe` dosyasını indirip çift tıkla (Python gerekmez).
   Ya da kaynaktan: `pip install -r requirements.txt`, ardından `python main.py`.
2. Oyunu **pencere modunda** aç ve penceresinin üstünü açık tut. Oyun penceresi otomatik seçilir.
3. Saldırı tuşunu gir (ör. `1`), istersen loot tuşunu da.
4. **BAŞLAT**'a bas (veya **F9**).

İlk seferde bot ekrana bakıp sorar:
*"Ekranda Mangyang (5 adet) buldum, bu canavarlara mı vuracağım?"* **Evet** deyince av başlar.

Canavar listesi yazmana gerek yok. Normal, şampiyon ve dev canavarlar aynı adı taşıdığı için tek hedef hepsini kapsar.
Hedef kaydedilir, sonraki seferde doğrudan BAŞLAT yeter. Başka canavara geçmek için **Yeniden ara**'ya bas.
Kendi karakter adın pencere başlığından (`[Adın] ...`) okunup otomatik elenir. Ekranda başka isimler de çıkarsa
(oyuncu, NPC) varsayılan olarak yalnızca en kalabalık grup işaretli gelir.

**Test taraması**, hiçbir şeye saldırmadan botun neyi tanıdığını yeşil kutularla gösterir.

### Gezinme

Ekranda birkaç saniye hedef canavar olmazsa karakter **yakındaki bir zemin noktasına yürür** ve tekrar bakar.
Her birkaç adımda yönünü değiştirir. **"Canavar yoksa gezinerek ara"** anahtarıyla kapatabilirsin.

> Gezinmenin henüz harita sınırı yok. Uzun sürede başladığın bölgeden uzaklaşabilir.

### Yönetici yetkisi (önemli)

Oyun **yönetici olarak** çalışıyorsa ve bu program çalışmıyorsa, Windows (UIPI) botun gönderdiği tüm tuş ve tıklamaları
**sessizce yutar**: bot canavarı görür ama hiçbir şey olmaz. Program bunu otomatik tespit eder, kenar çubuğunda uyarı
gösterir ve **Yönetici olarak yeniden başlat** düğmesi sunar.

### Windows uyarıları

Exe imzasız olduğu için SmartScreen "Bilinmeyen yayıncı" uyarısı verebilir: **Ek bilgi → Yine de çalıştır**.
Tuş gönderen ve ekran okuyan her program gibi, bazı antivirüsler yanlışlıkla işaretleyebilir. Kaynak kodun tamamı bu
depoda açıktır; exe'yi isteyen kendisi `.\build.ps1` ile derleyebilir.

## Nasıl çalışır

1. Ekrandaki beyaz, ince, kenarlıklı yazı blokları bulunur (HUD, minimap, sohbet gibi sabit arayüz hariç).
2. Her blok [RapidOCR](https://github.com/RapidAI/RapidOCR) ile okunur (ONNX, ayrı kurulum gerekmez).
3. Okunan metin hedefle bulanık eşleştirilir (`Mangyang` ≈ `Mangyan9`).
4. En yakın eşleşmenin etiketinin biraz altına tıklanır ve saldırı tuşlarına basılır.
5. Etiket birkaç taramada kaybolunca canavar ölmüş sayılır, loot tuşuna basılır ve döngü başa döner.

Durumlar: `Aranıyor → Doğrulanıyor → Saldırıyor → Loot`, ekranda hiçbir şey yoksa ayrıca `Gezinme`.

## İsteğe bağlı: YOLO modeli eğitmek

OCR kutudan çıktığı gibi çalışır. Eğitilmiş bir dedektör sprite'ın kendisini görebilir, bu da etiketler gizlendiğinde
işe yarar. Gerçek veri gerektirdiği için isteğe bağlı bir yükseltmedir.

1. **Gelişmiş** altında **Eğitim verisi topla**'ya bas ve her zamanki gibi oyna ya da avlan. Kutular isim
   etiketlerinden otomatik etiketlenir, elle çizmen gerekmez. Çıktı `dataset/` klasörüne YOLO formatında yazılır.
2. Canavar başına birkaç yüz kare topla; farklı açı, mesafe ve ışık olsun.
3. Bir kez: `pip install -r requirements-train.txt` (yalnızca eğitim için, torch içerir).
4. **Modeli eğit**'e bas (ya da `python -m srbot.train`). CPU'da dakikalar sürer.
5. `models/monsters.onnx` oluşur ve **Tespit: Otomatik** onu kullanır, model yoksa OCR'a döner.
   Çıkarım yalnızca `onnxruntime` ister (kare başına yaklaşık 40 ms), bu yüzden exe küçük kalır.

Kayıt OCR etiketlerine dayanır, bu yüzden veriyi tespit **OCR** modundayken topla (yalnızca-model modunda değil).

## Geliştirme

```bash
pip install -r requirements.txt pytest
pytest                                       # birim testleri (OCR tespiti, kayıt, YOLO çözümleme, av döngüsü, gezinme)
.\build.ps1                                  # dist\SilkroadVisionBot.exe derler ve duman testinden geçirir
SilkroadVisionBot.exe --selftest sonuc.txt   # derlenmiş exe içindeki OCR/onnxruntime'ı doğrular
```

Ayarlar `config.json` içinde saklanır (git'e girmez). `main` dalına her push'ta GitHub Actions testleri çalıştırır,
exe'yi derler, `--selftest` ile doğrular ve "latest" [sürümünü](../../releases/latest) günceller.
Eğitim bağımlılıkları exe'ye bilerek dahil edilmez, bu yüzden exe yaklaşık 100 MB'tır.

## Hakkında

**Silkroad Vision Bot** v3, **Samet Uca** tarafından geliştirilmektedir.

- GitHub: [github.com/sametuca](https://github.com/sametuca)
- E-posta: [sametuca@hotmail.com](mailto:sametuca@hotmail.com)
- Proje: [github.com/sametuca/silkroadonline-vsbot](https://github.com/sametuca/silkroadonline-vsbot)

Hata bildirimi ve fikirler için [Issues](../../issues) sayfasını kullanabilirsin.

Bot kullanımı bir oyun sunucusunun kurallarına aykırı olabilir. Bu yazılımı nasıl kullandığından sen sorumlusun.

## Lisans

[MIT](LICENSE)
