# Silkroad Vision Bot

Ekrandaki canavarları **isim etiketinden** tanıyıp seçen ve tuş vuruşu gönderen, ekran görüntüsü tabanlı av botu (v3, sıfırdan yeniden yazıldı).

Oyun sürecine bağlanmaz, bellek okumaz, ağ trafiğine dokunmaz. Sadece ekrandaki pikselleri okur ve oyuncunun yapabileceği tuş/fare girdisini gönderir.

## Kullanım

1. Oyunu **pencere modunda** aç ve penceresinin üstünün açık olduğundan emin ol.
2. `python main.py` (veya Releases'tan `SilkroadVisionBot.exe`). Oyun penceresi otomatik seçilir.
3. Saldırı tuşunu gir (ör. `1`), istersen loot tuşunu da.
4. **BAŞLAT** (veya **F9**). Hedef daha önce seçilmediyse bot önce ekrana bakar ve
   *"Ekranda Mangyang (5 adet) buldum, bu canavarlara mı vuracağım?"* diye sorar. **Evet** deyince av başlar.

Canavar listesi yazmana gerek yok. Normal, şampiyon ve dev canavarlar aynı adı taşıdığı için tek hedef olarak
yakalanır. Hedef kaydedilir, sonraki seferde doğrudan BAŞLAT yeter. Başka bir canavara geçmek için **Yeniden ara**.
Oyuncunun kendi adı pencere başlığından (`[Murkrow]`) okunup otomatik elenir; ekranda başka isimler de çıkarsa
(başka oyuncular, NPC) varsayılan olarak yalnızca en kalabalık grup işaretli gelir.

**Test taraması** düğmesi, botu çalıştırmadan neyi tanıdığını önizlemede yeşil kutularla gösterir.

### Windows uyarıları

Exe imzasız olduğu için SmartScreen "Bilinmeyen yayıncı" uyarısı verebilir: **Ek bilgi → Yine de çalıştır**.
Tuş gönderen ve ekran okuyan her program gibi, bazı antivirüsler yanlışlıkla işaretleyebilir. Kaynak kodun tamamı
bu depoda açıktır, exe'yi isteyen kendisi `.\build.ps1` ile derleyebilir.

### Yönetici yetkisi (önemli)

Oyun yönetici olarak çalışıyorsa, bu program yönetici değilken Windows (UIPI) gönderdiği tuş ve tıklamaları
**sessizce yutar**: bot canavarı görür ama hiçbir şey olmaz. Program bunu otomatik tespit eder, kenar çubuğunda
uyarı gösterir ve **Yönetici olarak yeniden başlat** düğmesi sunar.

## Eğitim verisi toplama (YOLO için)

Sol paneldeki **Gelişmiş** altında bulunan **Eğitim verisi topla** düğmesi, sen oynarken (ya da bot avlanırken) kareleri kaydeder.
Her karede canavarın adı OCR ile okunur ve sprite kutusu isim etiketinin konumundan otomatik çıkarılır, elle kutu çizmek gerekmez.
Çıktı `dataset/` klasöründe YOLO formatındadır (`images/`, `labels/`, `classes.txt`). Benzer kareler ve 1 sn'den sık kayıtlar atlanır.
Önizlemede turuncu kutular kaydedilecek sprite kutularını gösterir.

## Model eğitimi (YOLO)

1. Veri topla (yukarıda). Canavar başına birkaç yüz kare, farklı açı, mesafe ve ışıkla iyi sonuç verir.
2. Bir kez `pip install -r requirements-train.txt` (yalnızca eğitim için, torch içerir).
3. Arayüzde **Modeli eğit** (ya da `python -m srbot.train`). CPU'da onlarca kare birkaç dakika sürer.
4. Bittiğinde `models/monsters.onnx` oluşur. **Tespit: Otomatik** modu modeli kendiliğinden kullanır, model yoksa OCR'a döner.

Çıkarım yalnızca `onnxruntime` ile çalışır (torch gerekmez, yaklaşık 40 ms/kare), bu yüzden exe küçük kalır.
Model modunda yeni kare kaydedilmez, kayıt OCR etiketlerine dayanır.

## Nasıl çalışır

1. Ekrandaki beyaz, ince, kenarlıklı yazı blokları bulunur (HUD, minimap, sohbet gibi sabit alanlar hariç).
2. Her blok [RapidOCR](https://github.com/RapidAI/RapidOCR) (ONNX, ayrı kurulum gerektirmez) ile okunur.
3. Okunan isim, listendeki isimlerle bulanık eşleştirilir (`Mangyang` ≈ `Mangyan9`).
4. Oyuncuya en yakın eşleşen etiketin biraz altına tıklanır, saldırı tuşlarına basılır.
5. Etiket birkaç taramada kaybolunca canavar ölmüş sayılır, loot tuşuna basılır ve döngü başa döner.

Durumlar: `Canavar aranıyor → Hedef doğrulanıyor → Saldırıyor → Loot toplanıyor`.

## Yol haritası

- [x] **A:** Yeni yapı, OCR ile tespit, CustomTkinter arayüzü
- [x] **B:** Kayıt modu ve OCR ile otomatik etiketleme (YOLO eğitim verisi)
- [x] **C:** YOLO eğitimi ve çıkarımı
- [x] **D:** Paketleme ve CI (exe derleme, otomatik test, sürüm yayını)

## Geliştirme

```bash
pip install -r requirements.txt
python main.py
```

Ayarlar `config.json` dosyasında saklanır (git'e girmez).

```bash
pip install pytest
pytest                                       # birim testleri (OCR tespiti, kayıt, YOLO çözümleme, av döngüsü)
.\build.ps1                                  # dist\SilkroadVisionBot.exe derler ve duman testinden geçirir
SilkroadVisionBot.exe --selftest sonuc.txt   # exe içindeki OCR/onnxruntime'ı doğrular
```

`main` dalına her push'ta GitHub Actions testleri çalıştırır, exe'yi derler, `--selftest` ile doğrular ve
[Releases](../../releases/latest) altındaki "latest" sürümü günceller. Eğitim bağımlılıkları (torch vb.) exe'ye
bilerek dahil edilmez, bu yüzden exe yaklaşık 100 MB'tır.

## Lisans

MIT
