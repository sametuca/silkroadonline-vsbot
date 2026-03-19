# 📸 Örnek Şablonlar (Example Templates)

Bu klasör, bot kullanıcılarına örnek template görselleri sunması için oluşturulmuştur.

## Örnek: Big White Spider

Attachment'taki **Big White Spider** fotoğrafını buraya kaydedilmesi gerekmektedir:

**Dosya Adı:** `bighwhitespider_example.png`

### Kaydedilme Adımları:

1. **Attachment'tan Fotoğrafı Kaydet:**
   - VS Code'daki attachment'taki "Big White Spider" görüntüsü üzerinde sağ tıkla
   - "Farklı kaydet" (Save Image As) seçeneğini tıkla
   - Dosya adını `bighwhitespider_example.png` olarak gir

2. **Klasöre Kopyala:**
   - Kaydedilen dosyayı buraya kopyala: `docs/`
   - Sonuç: `docs/bighwhitespider_example.png`

3. **README.md'de Gösterilecek:**
   - Ana README.md'de bu dosya görselle gösterilecek
   - Kullanıcılar template nasıl görünmesi gerektiğini görebilecek

### Template Neleri İçermeli:

✅ **İyi Template Özellikleri:**
- Canavar adı **net ve okunur** halde
- Oyun ekranında alınan **gerçek screenshot**
- Canavar gövdesinin bir kısmı veya tamamı
- Zoom seviyesi oyundaki ile eşleşen

❌ **Kötü Template Örnekleri:**
- Çok karanlık veya aşırı parlak yerler
- Canavar isminin görülmediği kısımlar
- Zoom level'ı farklı olan screenshots
- JPEG, BMP gibi başka format dosyalar

### Daha Fazla Template Eklemek

Projede başka canavar şablonalarınız varsa, örnek olması için buraya da kopyalayabilirsiniz:

```
docs/
├── bighwhitespider_example.png     # Örnek
├── earthghostsoldier_example.png   # Diğer örnek
└── README.md                        # Bu dosya
```

---

**Not:** Gerçek kullanım için template'leriniz ana `monsters/` klasöründe olmalıdır! 
Bu `docs/` klasörü yalnızca dokumentasyon için örneklerdir.
