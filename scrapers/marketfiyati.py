"""
marketfiyati.org.tr (TÜBİTAK BİLGEM): zincir marketlerin şube bazında tüm ürünleri.

Kullanılan marketler: BİM (sitesinde sadece aktüel var), A101 (Kapıda sitesi Cloudflare'li),
CarrefourSA ve Hakmar (kendi scraper'ımız yok). Migros ve ŞOK kendi sitelerinden daha geniş
geldiği için oradan alınmaz. Kullanım koşulları yazılı izin istiyor; izin 19.11.2026'da alındı
(bkz. CLAUDE.md). Kaynak uygulamada belirtilmeli.

API (sitenin kendi kullandığı, JSON):
    GET  /api/v3/info/categories                  kategori ağacı (ana kategoriler: "Temel Gıda" ...)
    POST /api/v2/nearest   {latitude, longitude, distance}           -> yakındaki şubeler
    POST /api/v3/searchByCategories {pages, size, menu_category, latitude, longitude, distance, depots}
         -> {numberOfFound, content: [{id, title, brand, imageUrl, refinedVolumeOrWeight,
             main_category, productDepotInfoList: [{depotId, price, discountlessPrice, discount ...}]}]}
Sayfa başına en fazla 25 ürün döner. Fiyatlar TL.

Market başına tek bir şube taranır (zincir fiyatları büyük ölçüde aynı): sabit bir noktaya en
yakın şube her çalıştırmada yeniden bulunur, şube kapanırsa diğerine geçilir.
"""
from __future__ import annotations

import json
import random
import time
from typing import List, Optional

from models import Offer
from scrapers.base import BaseScraper, log

API = "https://api.marketfiyati.org.tr/api"
SITE = "https://marketfiyati.org.tr"
ANKARA = {"latitude": 39.9208, "longitude": 32.8541}    # Kızılay (genel bir nokta)
ISTANBUL = {"latitude": 41.0602, "longitude": 28.9877}  # Şişli
KONUMLAR = {"hakmar": ISTANBUL, "tarim_kredi": ISTANBUL}   # Hakmar Ankara'da yok; Tarım Kredi'nin Ankara verisi boş
KONUM = ANKARA
SAYFA = 25                                              # API'nin verdiği en fazla ürün sayısı


def en_yakin_sube(yakinlar: List[dict], market: str) -> Optional[str]:
    """/nearest yanıtından o marketin en yakın şubesinin kimliği ('bim-U645')."""
    adaylar = yakin_subeler(yakinlar, market, 1)
    return adaylar[0] if adaylar else None


def yakin_subeler(yakinlar: List[dict], market: str, n: int = 3) -> List[str]:
    """O marketin en yakın n şubesi, yakından uzağa."""
    adaylar = [d for d in yakinlar if d.get("marketName") == market and d.get("id")]
    return [d["id"] for d in sorted(adaylar, key=lambda d: d.get("distance") or 0)[:n]]


ORNEK_KATEGORILER = ("Temel Gıda", "Atıştırmalık ve Tatlı")


def ornek_kategoriler(kategoriler: List[str]) -> List[str]:
    """Şube karşılaştırması için iki kategori (adları değişirse listenin ilk ikisi)."""
    secili = [k for k in ORNEK_KATEGORILER if k in kategoriler]
    return secili if len(secili) == 2 else kategoriler[:2]


def sube_sec(adaylar: List[str], sayilar: dict) -> str:
    """En çok ürünü olan şube; eşitse en yakın olan (adaylar yakından uzağa sıralı)."""
    return max(adaylar, key=lambda s: (sayilar.get(s, 0), -adaylar.index(s)))


def parse_urunler(veri: dict, market: str = "bim") -> List[Offer]:
    """searchByCategories yanıtını Offer listesine çevirir (sadece o marketin şube fiyatları)."""
    out = []
    for p in veri.get("content") or []:
        fiyatlar = [d for d in p.get("productDepotInfoList") or [] if d.get("marketAdi") == market and d.get("price")]
        if not fiyatlar or not p.get("title"):
            continue
        d = min(fiyatlar, key=lambda x: x["price"])
        eski = d.get("discountlessPrice")
        out.append(Offer(
            market=market,
            market_product_id=f"mf-{p['id']}",
            name=" ".join(p["title"].split()),
            price=float(d["price"]),
            regular_price=float(eski) if d.get("discount") and eski and eski > d["price"] else None,
            url=None,
            image_url=p.get("imageUrl"),
            category=p.get("main_category") or p.get("menu_category"),
        ))
    return out


class MarketFiyatiKatalog(BaseScraper):
    """marketfiyati.org.tr'den bir marketin bir şubesindeki tüm ürünler."""

    def __init__(self, market: str = "bim", **kw):
        super().__init__(**kw)
        self.market = market
        self.session.headers.update({"Accept": "application/json", "Origin": SITE, "Referer": SITE + "/"})

    def post(self, yol: str, govde: dict, deneme: int = 3) -> dict:
        for i in range(deneme):
            time.sleep(random.uniform(*self.delay) * (1 + 4 * i))   # siteyi yormamak için; hatada daha uzun bekle
            try:
                r = self.session.post(f"{API}{yol}", json=govde, timeout=30)
                r.raise_for_status()
                return r.json()
            except Exception as e:                                  # bağlantı koptu / geçici sunucu hatası
                if i == deneme - 1:
                    raise
                log.warning("marketfiyati: %s isteği başarısız (%s), tekrar deneniyor", yol, e)
        raise RuntimeError("ulaşılamaz")

    def scrape(self, kategori_limit: Optional[int] = None) -> List[Offer]:
        konum = KONUMLAR.get(self.market, ANKARA)
        kategoriler = [c["name"] for c in self.get(f"{API}/v3/info/categories").json().get("content", [])]
        yakin = self.post("/v2/nearest", {**konum, "distance": 5})
        self.dump("yakin.json", json.dumps(yakin, ensure_ascii=False))
        adaylar = yakin_subeler(yakin, self.market, 3)
        if not adaylar or not kategoriler:
            log.warning("marketfiyati: %s şubesi bulunamadı", self.market)
            return []
        # Şubelerin listesi günden güne değişiyor; en yakın şube bazen hiç ürün göstermiyor (Tarım Kredi
        # 27.11.2026: en yakın şube 0, diğerleri 200-360). En yakın 3 şubeden en çok ürünü olanı seç;
        # tek kategori yanıltıcı olabildiği için iki kategorinin toplamına bak.
        ornekler = ornek_kategoriler(kategoriler)
        sayilar = {}
        for s in adaylar:
            sayilar[s] = sum(self.post("/v3/searchByCategories", {"pages": 0, "size": 1, "menu_category": [k],
                                                                  **konum, "distance": 5, "depots": [s]}
                                       ).get("numberOfFound") or 0 for k in ornekler)
        sube = sube_sec(adaylar, sayilar)
        log.info("marketfiyati: %s şubesi %s (%s örnek ürün sayıları: %s), %d kategori", self.market, sube,
                 "+".join(ornekler), sayilar, len(kategoriler))
        bulunan: dict = {}
        for kat in kategoriler[:kategori_limit]:
            sayfa, toplam = 0, None
            while toplam is None or sayfa * SAYFA < toplam:
                veri = self.post("/v3/searchByCategories", {"pages": sayfa, "size": SAYFA, "menu_category": [kat],
                                                            **konum, "distance": 5, "depots": [sube]})
                if sayfa == 0:
                    self.dump(f"{kat}.json", json.dumps(veri, ensure_ascii=False))
                toplam = veri.get("numberOfFound") or 0
                urunler = parse_urunler(veri, self.market)
                if not veri.get("content"):
                    break
                for o in urunler:
                    bulunan.setdefault(o.market_product_id, o)
                sayfa += 1
                if sayfa > 200:                               # güvenlik sınırı
                    break
            log.info("marketfiyati: %s / %s: %d ürün", self.market, kat, toplam)
        log.info("marketfiyati: %s toplam %d ürün", self.market, len(bulunan))
        return list(bulunan.values())


def _market_scraper(market_adi: str):
    """run.py için market sınıfı: tamamı marketfiyati.org.tr'den gelen marketler (Carrefour, Hakmar...).
    --katalog yoksa sadece indirimdekiler döner (indirimleri bulmak için yine tüm raf taranır)."""
    class _Scraper(MarketFiyatiKatalog):
        market = market_adi

        def __init__(self, **kw):
            super().__init__(market_adi, **kw)

        def scrape(self, katalog: bool = False, kategori_limit: Optional[int] = None) -> List[Offer]:
            urunler = super().scrape(kategori_limit)
            return urunler if katalog else [o for o in urunler if o.is_discounted]

    _Scraper.__name__ = f"MarketFiyati_{market_adi}"
    return _Scraper


CarrefourScraper = _market_scraper("carrefour")
HakmarScraper = _market_scraper("hakmar")
A101MarketFiyatiScraper = _market_scraper("a101")
# Tarım Kredi: scrapers/tarimkredi.py (kendi sitesindeki kampanyalar + buradan katalog)
