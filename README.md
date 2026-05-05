# Ekonomikartı (Fiyat Hafızası) 📈

Ekonomikartı, finansal piyasa verilerini (Döviz, Altın, Petrol, Borsa) otomatik olarak çeken, bu verileri tarihsel pencerelerle kıyaslayan ve sosyal medyada paylaşılmaya hazır, modern ve şık bilgi kartları (PNG) üreten bir otomasyon sistemidir.

## 🎨 Yeni Görsel Kimlik & Tasarım

Proje, 2026 Mayıs ayında yapılan büyük bir revizyonla tamamen modern, "premium" bir **Koyu Tema (Dark Mode)** yapısına geçmiştir.

### 🌈 Renk Paleti
- **Arka Plan (Deep Navy):** `#0B132B` - Kartın ana zemini.
- **Yüzey (Surface Blue):** `#1C2A46` - Veri kutucuklarının (widget) rengi.
- **Vurgu (Amber Gold):** `#FBBF24` - Marka ismi ve önemli başlıklar.
- **Pozitif (Emerald):** `#10B981` - Artış gösteren veriler.
- **Negatif (Rose Red):** `#EF4444` - Azalış gösteren veriler.
- **Metin (Slate White):** `#F8FAFC` - Ana içerik yazıları.

### 🔡 Tipografi
- **Inter (Regular, SemiBold, Bold):** Gösterge isimleri, açıklamalar ve marka başlığı için kullanılan ana font.
- **JetBrains Mono (Medium, Bold):** Sayısal veriler, fiyatlar ve yüzdelik değişimler için kullanılan monospaced font.

### 🖼️ Kart Düzeni
- **Kutu (Card) Tasarımı:** Her veri grubu, köşeleri 24px yuvarlatılmış (rounded rectangle) şık kutucuklar içerisinde sunulur.
- **Dinamik Ölçeklendirme:** Ana veriler ve yüzdelik değişimler, okunabilirliği artırmak adına optimize edilmiş font boyutlarıyla çizilir.
- **Yorum Alanı (Footer):** Kartların alt kısmında LLM tarafından üretilen piyasa analizi, büyük puntolarla (24px) yer alır.

---

## 🏗️ Proje Yapısı (Neyin Nerede?)

```text
Ekonomikarti/
├── .github/workflows/    # Günlük (Sabah-Öğle-Akşam) ve Haftalık otomasyon akışları (Actions)
├── assets/fonts/         # Kartlarda kullanılan Inter ve JetBrains Mono font dosyaları
├── data/
│   ├── manual/           # Manuel müdahale gerektiren (akaryakıt vb.) veri girişleri
│   └── output/           # Çekilen ham verilerin (JSON) saklandığı geçici klasör
├── output/
│   ├── live/             # Üretilen son güncel PNG kartlar ve metin (caption) dosyaları
│   └── test/             # Geliştirme sırasında test amaçlı üretilen görseller
├── src/
│   ├── data/             # Veri çekme (TCMB, Yahoo Finance) ve hesaplama motorları
│   ├── render/           # Kart çizim mantığı (Morning, Noon, Evening, Weekly, Highlight)
│   ├── caption/          # LLM tabanlı (Gemini) otomatik caption/yorum üretici
│   ├── pipeline.py       # Veriyi çekip, görseli üretip, caption'ı hazırlayan ana akış
│   └── config.py         # Renkler, fontlar, geometri ve gösterge tanımları (Merkezi Ayarlar)
├── run_morning.py        # Sabah kartını (08:00) üreten tetikleyici script
├── run_noon.py           # Öğle "Odak" kartını üreten tetikleyici script
├── run_evening.py        # Akşam "Kapanış" kartını üreten tetikleyici script
└── run_weekly.py         # Haftalık özet kartlarını üreten tetikleyici script
```

---

## 🚀 Çalıştırma

1. **Bağımlılıkları Kurun:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Fontları İndirin:**
   ```bash
   python scripts/download_fonts.py
   ```

3. **Bir Kart Üretin (Örn: Sabah Kartı):**
   ```bash
   python run_morning.py
   ```

## 🛠️ Teknolojiler
- **Python 3.10+**
- **Pillow (PIL):** Görsel oluşturma ve tipografi işleme.
- **yfinance & TCMB EVDS:** Canlı piyasa verileri.
- **OpenRouter (Gemini):** Akıllı piyasa yorumları.
- **GitHub Actions:** Tam otomatik zamanlanmış (cron) çalışma.
