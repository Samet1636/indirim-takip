"""
BİM'in tam ürün kataloğu: marketfiyati.org.tr (TÜBİTAK BİLGEM).

BİM'in kendi sitesinde sadece aktüel ürünler var. marketfiyati.org.tr şube bazında tüm ürünleri
fiyatıyla yayınlıyor. Kullanım koşulları yazılı izin istiyor; izin 19.11.2026'da alındı
(bkz. CLAUDE.md). Kaynak uygulamada belirtilmeli.

API (sitenin kendi kullandığı, JSON):
    GET  /api/v3/info/categories                  kategori ağacı (ana kategoriler: "Temel Gıda" ...)
    POST /api/v2/nearest   {latitude, longitude, distance}           -> yakındaki şubeler
    POST /api/v3/searchByCategories {pages, size, menu_category, latitude, longitude, distance, depots}
         -> {numberOfFound, content: [{id, title, brand, imageUrl, refinedVolumeOrWeight,
             main_category, productDepotInfoList: [{depotId, price, discountlessPrice, discount ...}]}]}
Sayfa başına en fazla 25 ürün döner. Fiyatlar TL.

Tek bir şube taranır (BİM fiyatları ülke genelinde büyük ölçüde aynı): sabit bir noktaya en
yakın BİM şubesi her çalıştırmada yeniden bulunur, şube kapanırsa diğerine geçilir.
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
KONUM = {"latitude": 39.9208, "longitude": 32.8541}     # Kızılay, Ankara (genel bir nokta)
SAYFA = 25                                              # API'nin verdiği en fazla ürün sayısı


def en_yakin_sube(yakinlar: List[dict], market: str) -> Optional[str]:
    """/nearest yanıtından o marketin en yakın şubesinin kimliği ('bim-U645')."""
    adaylar = [d for d in yakinlar if d.get("marketName") == market and d.get("id")]
    return min(adaylar, key=lambda d: d.get("distance") or 0)["id"] if adaylar else None


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

    def post(self, yol: str, govde: dict) -> dict:
        time.sleep(random.uniform(*self.delay))          # siteyi yormamak için
        r = self.session.post(f"{API}{yol}", json=govde, timeout=30)
        r.raise_for_status()
        return r.json()

    def scrape(self, kategori_limit: Optional[int] = None) -> List[Offer]:
        kategoriler = [c["name"] for c in self.get(f"{API}/v3/info/categories").json().get("content", [])]
        yakin = self.post("/v2/nearest", {**KONUM, "distance": 5})
        self.dump("yakin.json", json.dumps(yakin, ensure_ascii=False))
        sube = en_yakin_sube(yakin, self.market)
        if not sube:
            log.warning("marketfiyati: %s şubesi bulunamadı", self.market)
            return []
        log.info("marketfiyati: %s şubesi %s, %d kategori", self.market, sube, len(kategoriler))
        bulunan: dict = {}
        for kat in kategoriler[:kategori_limit]:
            sayfa, toplam = 0, None
            while toplam is None or sayfa * SAYFA < toplam:
                veri = self.post("/v3/searchByCategories", {"pages": sayfa, "size": SAYFA, "menu_category": [kat],
                                                            **KONUM, "distance": 5, "depots": [sube]})
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
