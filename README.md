# Ekonomikarti

Ekonomikarti, her sabah ekonomi verilerini (döviz, altın, petrol, borsa) çekerek şık bir Instagram/X gönderi görseli ve caption metni oluşturan otomasyon projesidir.

## Kullanım (Usage - TR)

Sistemi çalıştırmak için aşağıdaki adımları izleyebilirsiniz:

1. **Gereksinimlerin Yüklenmesi:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Fontların İndirilmesi:**
   Görsellerin düzgün oluşturulabilmesi için öncelikle fontların indirilmesi gerekmektedir.
   ```bash
   python scripts/download_fonts.py
   ```

3. **Çalıştırma:**
   Şu an için sistem test verileriyle (dry-run) çalışmaktadır. Görseli oluşturmak için:
   ```bash
   python run_morning.py --dry-run
   ```
   Bu komut sonucunda `output/test/morning.png` ve `output/test/caption.txt` dosyaları oluşturulacaktır.

> **Not:** "Gram Altın" değeri doğrudan bir API'den gelmek yerine uluslararası ons altın fiyatı ve USD/TRY kuru üzerinden formülize edilerek hesaplanmaktadır. Bu nedenle belirtilen değer **yaklaşık** bir değerdir.

## Technical Documentation (EN)

Ekonomikarti is an automated data pipeline that generates daily economic summary cards for social media (Instagram, X).

### Project Structure
- `src/config.py`: Static configuration, palettes, geometries, and indicator mapping.
- `src/data/`: Data ingestion modules (e.g., TCMB EVDS parser).
- `src/render/`: Pillow-based rendering engine.
- `src/pipeline.py`: The main execution pipeline.

### CI/CD
A GitHub Actions workflow (`.github/workflows/daily-morning.yml`) is configured to run automatically every morning at 05:45 UTC (08:45 TRT). It sets up the environment, fetches the latest data, generates the output assets, and commits them back to the repository.

### Tests
Tests are built with `pytest` and can be run via:
```bash
pytest tests/
```
The test suite ensures robust formatting, correct JSON parsing (TCMB API), Turkish character rendering, and validating the dry-run output constraints (e.g., ensuring a 1080x1350 PNG is correctly generated).

## Açık Sorular (Open Questions)

- **Canlı Veri Geçişi:** Gerçek API entegrasyonları tamamlanıp canlı (live) veri akışına ne zaman geçilecek?
- **Caption Model Güncellemesi:** Caption üretimi için kullanılacak OpenRouter LLM modelinde spesifik bir prompt engineering optimizasyonu yapılacak mı?
- **Akşam/Öğle Modülleri:** `render/evening.py` ve `render/noon.py` için veri kaynakları ve tasarımlar nasıl kurgulanacak?
- **Oto-Paylaşım:** Görsel ve metin üretildikten sonra Instagram/X hesaplarına API aracılığıyla otomatik gönderim (auto-post) özelliği eklenecek mi?
