# İndirim Takip – Adım 1: Veri toplama

Migros ve BİM'deki indirimli ürünleri her gün otomatik toplayıp SQLite veritabanına yazar.

## Kurulum
```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pytest -q                          # ağ olmadan ayrıştırıcıları test eder
```

## İlk canlı çalıştırma (önemli)
```bash
python run.py --dump
```
`--dump` ham yanıtları `data/raw/` altına kaydeder. Şunları kontrol et:
- **Migros**: `data/raw/migros_süt.json` dosyasında indirim öncesi fiyatın alan adı
  `regularPrice` mı? Değilse `scrapers/migros.py` içindeki `REGULAR_PRICE_KEYS` listesine ekle.
- **BİM**: Hiç ürün gelmediyse `data/raw/bim_aktuel.html` dosyasını aç, ürün kutusunun,
  başlığın ve fiyatın class adlarına bak, `scrapers/bim.py` içindeki seçici listelerini güncelle.

## Çıktılar
- `data/prices.db` → `products` (ürünler) + `price_snapshots` (her gün fiyat, fiyat geçmişi)
- `data/discounts_today.json` → uygulamanın göstereceği günün indirim listesi

## Otomatik günlük çalıştırma
Repoyu GitHub'a yükle; `.github/workflows/daily.yml` her gün 07:00'de (TR) çalışır,
sonuçları repoya commit eder. Actions sekmesinden "Run workflow" ile elle de tetiklenebilir.

GitHub sunucuları yurt dışında. Bir market yurt dışı IP'leri engellerse,
scripti kendi bilgisayarında ya da Türkiye'deki bir VPS'te cron ile çalıştır:
```
0 7 * * * cd /yol/indirim-takip && .venv/bin/python run.py
```

## Yeni market eklemek
`scrapers/` altına `BaseScraper`'dan türeyen bir sınıf yaz, `scrape()` bir `Offer` listesi
döndürsün, sonra `run.py` içindeki `SCRAPERS` sözlüğüne ekle.
