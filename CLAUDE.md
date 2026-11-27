# İndirim Takip + Beslenme Planlayıcı

Türkiye'deki marketlerin (Migros, ŞOK, A101, BİM) ürün ve indirim verilerini her gün otomatik
toplayan, bu fiyatlarla kişiye özel haftalık beslenme planı ve en ucuz alışveriş listesi üreten
bir uygulama. Sahibi: Abdulsamet (GTÜ Endüstri Mühendisliği öğrencisi). Hedef: App Store /
Google Play'de yayınlanacak bir mobil uygulama. İletişim dili Türkçe; kod yorumları ve
kullanıcıya dönük metinler Türkçe.

## Mimari

```
scrapers/            Market scraper'ları (hepsi models.Offer listesi döndürür)
  base.py            Ortak HTTP oturumu, istekler arası gecikme, --dump, parse_tr_price
  migros.py          Migros REST API (rest/search/screens/...), fiyatlar KURUŞ
  bim.py             BİM aktüel sayfası (HTML); --katalog ile tam katalog marketfiyati.py'den eklenir
  marketfiyati.py    marketfiyati.org.tr API (TÜBİTAK BİLGEM): BİM, A101 (a101_mf), CarrefourSA, Hakmar,
                     Tarım Kredi. Market başına tek şube (sabit noktaya yakın 3 şubeden en çok ürünlüsü;
                     Hakmar/Tarım Kredi İstanbul, diğerleri Ankara Kızılay). Market başına ~2-4 dk
  sok.py             ŞOK (Next.js RSC). Ürünler: initialSearchResult.results[].product / .prices
  a101.py            A101 Kapıda — Cloudflare korumalı. Playwright + bilgisayardaki Chrome ile
                     Store/search (kampanya) ve Store/listCategoryProducts (kategori) API'lerini dinler
  campaign.py        ŞOK/A101 için ortak kampanya + kategori gezgini
  discovery.py       Kategori keşfi (önce menü linkleri, sonra sitemap)
  nextjs.py          Next.js gömülü JSON ayrıştırıcı (genel)
models.py            Offer veri sınıfı
db.py                SQLite (data/prices.db). products = ürünün son durumu,
                     price_snapshots = sadece fiyat DEĞİŞİNCE satır (fiyat geçmişi)
run.py               Ana giriş noktası (bkz. Komutlar)
github_upload.py     A101 sonucunu GitHub API ile repoya yükler (GH_TOKEN ortam değişkeni)
a101_gunluk.bat      A101'i yerelde tarayıp yükler (Windows Görev Zamanlayıcı, her sabah)
index.html           GitHub Pages'te yayınlanan web arayüzü (data/discounts_today.json okur)
beslenme/
  malzemeler_kaynak.py -> malzemeler.json   48 malzeme, 100 g besin değerleri (YAKLAŞIK)
  tarifler_kaynak.py   -> tarifler.json     44 tarif, gram cinsinden, 1 porsiyon
  tarif_ozet.py        besin hesabı + otomatik etiketler (vejetaryen, vegan, yuksek_protein, pratik)
  miktar.py            ürün adından paket miktarı ("6x200 ml", "2,5 Kg", "15'li", "Domates Kg")
  eslestirme_kurallari.py  malzeme -> ürün eşleştirme kuralları (ad / haric / migros kategorisi), KILER listesi
  eslestirme.py        malzeme başına en ucuz ürün, TL/kg, tarif porsiyon maliyeti
  hedef.py             Mifflin-St Jeor kalori/makro hedefi (güvenlik alt sınırları)
  plan.py              Haftalık plan MILP modeli (PuLP; HiGHS varsa onu, yoksa CBC)
api/                 Beslenme planı sunucusu (FastAPI). Paketleri api/requirements.txt'te
  main.py            GET /saglik, POST /hedef, POST /plan (iş no döner), GET /plan/{is_id};
                     katalog.json'u dosya değişince yeniden okur; "tıbbi tavsiye değildir" notu ekler
  isler.py           Bellekte iş kuyruğu (tek işçi; çözüm ~70 sn). Supabase aşamasında tabloya taşınacak
tests/               pytest testleri (ağa çıkmaz; tests/fixtures altında gerçek site örnekleri)
.github/workflows/daily.yml   Her gün 04:00 UTC: "tara" işi (Migros/ŞOK/BİM + data/imports içe aktar,
                              commit) ve "yayinla" işi (GitHub Pages)
```

Mobil uygulama ayrı klasörde (ayrı git deposu, uzak deposu yok): `C:\Users\90534\indirim-app`
(Expo SDK 58 + Expo Router, kod `src/` altında). Sekmeler: İndirimler (GitHub Pages JSON) / Ürünler
(`/urunler`) / Plan (karşılama -> `src/app/sihirbaz.js` 10 adımlı soru sihirbazı -> hesaplama -> sonuç)
/ Liste. `src/app/tarif/[id].js` tarif detayı. Tasarım sistemi `src/lib/tema.js`; yazı tipi Plus Jakarta
Sans, Text/TextInput'u react-native'den değil `src/components/Yazi.js`'den al (fontWeight'i doğru
dosyaya çevirir). Profil + son plan AsyncStorage'da. Sunucu adresi `src/lib/api.js` (geliştirmede
bilgisayarın yerel IP'si:8000; `--tunnel` ile Plan/Ürünler çalışmaz).
Telefonda Expo Go ile açılır: `npx expo start` (aynı Wi-Fi). Web önizleme: `npx expo start --web`.
Paket ekledikten sonra Metro'yu `--clear` ile yeniden başlat (yoksa "Unable to resolve module").

## Veri akışı

1. GitHub Actions (her sabah): `python run.py --skip a101 --katalog --import-dir data/imports`
   -> data/prices.db, data/discounts_today.json, data/katalog.json güncellenir, commit'lenir, Pages'e yayınlanır.
2. A101 artık GitHub'da marketfiyati'den gelir (`a101_mf`, mağaza fiyatları). Yerel bilgisayar
   (Görev Zamanlayıcı, a101_gunluk.bat) A101 Kapıda'yı tarayıp `data/imports/a101.json` yükler; bu dosya
   sadece YEDEK: son 2 günde ≥500 marketfiyati A101 ürünü varsa içe aktarılmaz (run.py A101_YEDEK_ESIGI),
   yoksa aynı ürün iki kez görünürdü. 23-26.11.2026'da bilgisayar açılmadığı için A101 uygulamadan düşmüştü.
3. A101 Kapıda GitHub sunucularından taranamaz (Cloudflare "Bir dakika lütfen..." -> 403). Bunu tekrar deneme.
4. Katalog kapsamı (16.11.2026): Migros ~18.700 (tam), ŞOK ~2.900 (tam; en büyük kategori 28 sayfa),
   A101 ~2.250 (Kapıda tam; 17 kategori, ~2,5 dk), BİM ~2.300 (19.11.2026: ~1.750 katalog + ~570 aktüel).
   - BİM'in fiyatlı tam kataloğu bim.com.tr'de yok; marketfiyati.org.tr'den alınıyor (~80 istek, ~4 dk).
   - marketfiyati.org.tr (TÜBİTAK BİLGEM) kullanım koşulları yazılı izin istiyor. Kullanıcı izin aldığını
     19.11.2026'da bildirdi. Migros ve ŞOK kendi sitelerinden (daha geniş), diğerleri buradan. Uygulamada
     kaynak notu (karsilastir.js KaynakNotu) kalmalı. İstekler arası gecikmeyi kaldırma, şube sayısını artırma.
   - Plan varsayılan olarak ülke genelindeki 5 zincirle kurulur (api/main.py ULKE_GENELI); Hakmar ve
     Tarım Kredi bölgesel, ancak `marketler` ile seçilirse girer. 5+ markette aday ürün sayısı düşürülür
     (her_market=2) ve baskın paketler elenir; yoksa çözücü 60 sn'ye sığmıyor.

## Komutlar

```
pytest -q                                                      # tüm testler — her değişiklikten sonra çalıştır
python run.py --only sok --katalog --kategori-limit 2 --dump   # bir marketi hızlı dene, ham veriyi data/raw'a kaydet
python run.py --only a101 --katalog --dump --goster            # A101'i tarayıcı penceresi görünür dene
python beslenme/tarif_ozet.py                                  # tarif besin tablosu
python beslenme/eslestirme.py data/katalog.json                # fiyat eşleştirme + tarif maliyetleri
python beslenme/plan.py --kilo 75 --boy 178 --yas 23 --cinsiyet erkek --aktivite orta --hedef koru --market 2
sunucu.bat                                                     # sunucu (her klasörden çalışır, port 8000, telefon için 0.0.0.0)
                                                               # uvicorn'u elle çalıştırırken proje klasöründe ol, yoksa "No module named 'api'"
```

## Önemli kurallar ve tuzaklar

- **Python sürümü:** Bilgisayarda Anaconda'nın eski Python'u var (3.9 civarı). Her .py dosyasının
  başında `from __future__ import annotations` olmalı; 3.10+ sözdizimi (match, çalışma zamanında
  `X | Y` tipleri) kullanma.
- **Kodlama:** Windows varsayılanı cp1254. Dosya okurken/yazarken HER ZAMAN `encoding="utf-8"` ver
  (testlerde de). CSV'ler Excel için `utf-8-sig` ve `;` ayraçlı. `.bat` dosyaları CRLF satır sonlu.
- **pulp sürümü:** `requirements.txt`'te `pulp==2.9.0`; bilgisayarda 3.3.0 kurulu ve testler onunla geçiyor.
  4.x kullanma (API'si farklı, `LpVariable(cat=...)` çalışmıyor).
- **git:** PATH'te yok; GitHub Desktop'un içindeki git kullanılıyor
  (`%LOCALAPPDATA%\GitHubDesktop\app-*\resources\app\git\cmd\git.exe`).
- **anyio:** Anaconda'daki jupyter-server `anyio<4` istiyor; FastAPI kurulumu bunu yükseltirse 3.7.1'e geri çek.
- **Eşleştirme kuralları:** `haric` listesi normalize edilmiş ad içinde alt-dize olarak aranır. Türkçe ek
  alan kelimelerde kökü yaz ("gevrek" değil "gevre": gevreği'yi de yakalar). Kelime sınırı için konan
  baş/son boşluk korunur ("un " -> "Uno" markasını elemez).
- **data/ klasörü:** prices.db, discounts_today.json, katalog.json bot tarafından her gün güncellenir.
  Yerel denemelerden sonra bu dosyalardaki değişiklikleri commit'leme (`git restore data/`);
  aksi halde binary çakışma çıkar. Değişikliğe başlamadan önce `git pull` yap.
- **Gizli bilgiler:** GH_TOKEN ve EXPO_TOKEN ortam değişkenlerinde. Hiçbir dosyaya yazma, commit'leme, ekrana basma.
- **Siteleri yorma:** scraper'lardaki istekler arası gecikmeyi kaldırma, istekleri paralelleştirme.
- **Yeni site yapısı öğrenirken:** önce `--dump` ile ham veriyi kaydet, gerçek dosyaya bakarak
  ayrıştırıcı yaz, örneği tests/fixtures'a ekleyip test yaz. Tahmine dayalı ayrıştırıcı yazma.
- **Fiyat birimleri:** Migros ve A101 kuruş (100'e böl), ŞOK ve BİM TL.
- **Besin değerleri yaklaşık:** yayından önce TÜRKOMP (turkomp.tarimorman.gov.tr) ile doğrulanacak.
- **Sağlık güvenliği:** hedef.py'deki alt sınırları (bazal metabolizma, kadın 1200 / erkek 1500 kcal,
  18 yaş altına plan yok) gevşetme. Plan çıktılarında "tıbbi tavsiye değildir" notu kalmalı.
- **Hukuk:** Mağazaya çıkmadan önce marketlerin kullanım koşulları, ürün görselleri ve marka
  kullanımı için hukuki görüş alınacak.

## Plan modeli (beslenme/plan.py) özeti

Kararlar: y[gün,öğün,tarif] ikili, p[...] porsiyon (tarifin aralığında), n[ürün] paket, z[market] ikili.
Amaç: alışveriş maliyeti + market başına ceza (25 TL) + eksik protein cezası (15 TL/g).
Kısıtlar: günde 1 kahvaltı/öğle/akşam zorunlu, yan ve 2 ara öğün isteğe bağlı; kalori hedef ±%7;
protein yumuşak alt sınır; yağ üst sınır; tarif haftada ≤2; aynı gün aynı tarif 1 kez; ≤N market.
Taze ürünler tam paket (israf maliyete girer). KILER ürünleri (bakliyat, yağ, salça...) kullanılan
pay kadar maliyete girer + peşin paket tutarının %15'i stok cezası (dev paket seçimini önler).
Çözüm ~60 sn (zaman sınırı), %1 optimallik boşluğu. highspy kuruluysa HiGHS (CBC'den ~%4 daha iyi amaç;
60 sn'de de optimalliği kanıtlayamıyor, PuLP yine "Optimal" der). Tercihler: ekipman (tarif başına
alternatif ekipman setleri, tarifler_kaynak.py EKIPMAN), alerjen (tarif_ozet.ALERJEN, malzemeden otomatik),
haric_malzeme, max_sure, ara_ogun. Kahvaltı <4 veya ana yemek <7 tarif kalırsa çözücü çalışmadan
"Yetersiz tarif" döner. Aday ürünler: market başına kg'ı en ucuz N + en küçük + paket fiyatı en düşük.

## Yol haritası (sıradaki işler)

1. Plan modelini uygulamaya bağlamak: FastAPI sunucusu (api/) YAPILDI, yerelde çalışıyor.
   Sıradaki: Supabase (kullanıcı profili, kayıtlı planlar; ayrıca her gün commit'lenen
   prices.db / katalog.json repoyu şişirdiği için veri Supabase'e taşınacak), sonra sunucuyu
   internete taşımak (Render / Fly.io vb.).
2. Expo uygulamasına sekmeler: İndirimler / Tüm Ürünler / Beslenme Planı / Alışveriş Listesi.
3. Tarif veritabanını büyütmek (özellikle vejetaryen yüksek proteinli tarifler).
4. Besin değerlerini TÜRKOMP ile doğrulamak.
5. Mağaza yayını (EAS Build, Apple Developer / Google Play hesapları).

## Çalışma şekli

- Büyük bir işe başlamadan önce kısa bir plan çıkar ve onay al.
- Her değişiklikten sonra `pytest -q` çalıştır; testleri kırmadan commit'leme.
- Commit mesajları Türkçe ve kısa olsun. `git push` öncesi kullanıcıya sor.
