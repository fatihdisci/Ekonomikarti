# Ekonomikarti

Ekonomikarti, ekonomi göstergelerini (döviz, altın, petrol, borsa) çekerek Instagram/X için günlük ve haftalık şık gönderi görselleri ve caption metinleri oluşturan otomasyon projesidir.

## Yayın Takvimi

| Zaman | Kart | İçerik |
|---|---|---|
| Sabah (hergün, 08:45 TRT) | **Açılış Kartı** | 5 gösterge × 4 değişim penceresi (Günlük/Aylık/Yıllık/5 Yıl) |
| Öğle (Pzt-Cum, 13:00 TRT) | **Odak Kartı** | Tek gösterge × tarihsel snapshot (1 yıl, 5 yıl önce). Rotasyon: Pzt USD, Sal EUR, Çar Gram Altın, Per Brent, Cum BIST |
| Akşam (Pzt-Cum, 19:00 TRT) | **Kapanış Kartı** | 4 gösterge kapanış snapshot + günün en sert hareketi |
| Cumartesi (11:00 TRT) | **Haftalık Özet** | 5 gösterge × Cuma kapanışı + bu hafta % |
| Pazar (11:00 TRT) | **Yıldız/Kaybeden** | Haftanın en sert yükselen ve düşen göstergesi |

## Kullanım (Usage - TR)

1. **Bağımlılıklar:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Fontları indir** (görseller için gereklidir):
   ```bash
   python scripts/download_fonts.py
   ```

3. **Kartları çalıştır** — her kartın `--dry-run` modu fixture verisiyle çalışır, canlı modda yfinance + OpenRouter kullanır:
   ```bash
   python run_morning.py    [--dry-run]
   python run_noon.py       [--dry-run] [--focus usd_try|eur_try|gram_altin|brent|bist_100]
   python run_evening.py    [--dry-run]
   python run_weekly.py     [--dry-run]
   python run_highlight.py  [--dry-run]
   ```
   Çıktılar: `output/test/<kart>.png` ve `output/test/caption_<kart>.txt` (dry-run) ya da `output/live/...` (canlı).

> **Not:** "Gram Altın" değeri uluslararası ons altın fiyatı ve USD/TRY kuru üzerinden hesaplanmaktadır (yaklaşık değerdir).

## Technical Documentation (EN)

Ekonomikarti is an automated data pipeline that generates daily and weekly economic summary cards for social media (Instagram, X).

### Project Structure
- `src/config.py` — palette, geometry, indicator definitions, rotation maps.
- `src/data/` — data ingestion (`yfinance_api.py`) and payload builders (`calculator.py`).
- `src/render/` — Pillow-based renderers: `morning.py`, `noon.py`, `evening.py`, `weekly.py`, `highlight.py`.
- `src/caption/generator.py` — OpenRouter LLM caption generation (one prompt per card type).
- `src/pipeline.py` — `run_morning`, `run_noon`, `run_evening`, `run_weekly`, `run_highlight` end-to-end pipelines.

### CI/CD
GitHub Actions workflows in `.github/workflows/`:
- `daily-morning.yml` — every day at 05:45 UTC
- `daily-noon.yml` — Mon-Fri at 10:00 UTC
- `daily-evening.yml` — Mon-Fri at 16:00 UTC
- `weekly-saturday.yml` — Saturday at 08:00 UTC
- `weekly-sunday.yml` — Sunday at 08:00 UTC

Each workflow installs deps, downloads fonts, runs the pipeline, and commits the generated PNG + JSON back to the repository. Required secret: `OPENROUTER_API_KEY`.

### Tests
```bash
pytest tests/
```
Coverage: Turkish number/percent formatting, character rendering, dry-run output validation (1080×1350 PNG) for every card type, weekly Friday-resolution logic, biggest-mover and star/loser selection, noon rotation.

## Açık Sorular (Open Questions)

- **Oto-Paylaşım:** Görseller üretildikten sonra Instagram/X hesaplarına API aracılığıyla otomatik gönderim eklenecek mi?
- **Phase 3:** Haftalık karta sparkline (mini grafik), öğle kartına otomatik "önemli hareket" override'ı eklensin mi?
