"""
Migros Sanal Market.

Site bir SPA; ürünler tarayıcıda şu JSON uç noktasından çekiliyor:
    https://www.migros.com.tr/rest/search/screens/products?q=<kelime>&sayfa=<n>
Yanıtta ürünler data.searchInfo.storeProductInfos altında, fiyatlar KURUŞ cinsinden
(6595 = 65,95 TL).

NOT: 'regularPrice' alan adı ve 'sayfa' parametresi doğrulanmalı. İlk çalıştırmada
--dump ile ham yanıtı kaydet, alan adları farklıysa REGULAR_PRICE_KEYS'i güncelle.
"""
from __future__ import annotations
import json
from urllib.parse import quote_plus

from models import Offer
from scrapers.base import BaseScraper, log

API = "https://www.migros.com.tr/rest/search/screens/products?q={q}&sayfa={page}"

# Tüm katalogu gezmek yerine sık alınan ürün gruplarını tarıyoruz.
# Kapsamı genişletmek için buraya kelime ekle.
DEFAULT_QUERIES = [
    "süt", "yoğurt", "peynir", "yumurta", "tereyağı", "zeytin", "ekmek",
    "makarna", "pirinç", "bulgur", "un", "şeker", "çay", "kahve", "ayçiçek yağı",
    "zeytinyağı", "tavuk", "kıyma", "sucuk", "deterjan", "şampuan",
    "tuvalet kağıdı", "bisküvi", "çikolata", "cips", "su", "meyve suyu",
]

PRICE_KEYS = ["shownPrice", "salePrice", "price"]
REGULAR_PRICE_KEYS = ["regularPrice", "listPrice", "originalPrice", "crossedPrice"]


def _first(d: dict, keys: list[str]):
    for k in keys:
        v = d.get(k)
        if isinstance(v, (int, float)) and v > 0:
            return v
    return None


def parse_migros_payload(payload: dict) -> list[Offer]:
    infos = ((payload.get("data") or {}).get("searchInfo") or {}).get("storeProductInfos") or []
    offers = []
    for p in infos:
        if p.get("status") not in (None, "IN_SALE"):
            continue                       # stokta yok / satışta değil
        price = _first(p, PRICE_KEYS)
        if not price or not p.get("name"):
            continue
        regular = _first(p, REGULAR_PRICE_KEYS)
        slug = p.get("prettyName") or str(p.get("id") or p.get("sku"))
        image = None
        imgs = p.get("images") or []
        if imgs and isinstance(imgs[0], dict):
            urls = imgs[0].get("urls") or {}
            image = urls.get("PRODUCT_LIST") or next(iter(urls.values()), None)
        cat = p.get("category")
        offers.append(Offer(
            market="migros",
            market_product_id=slug,
            name=p["name"].strip(),
            price=price / 100,
            regular_price=(regular / 100) if regular and regular > price else None,
            url=f"https://www.migros.com.tr/{slug}",
            image_url=image,
            category=cat.get("name") if isinstance(cat, dict) else None,
        ))
    return offers


class MigrosScraper(BaseScraper):
    market = "migros"

    def __init__(self, queries=None, max_pages: int = 5, **kw):
        super().__init__(**kw)
        self.queries = queries or DEFAULT_QUERIES
        self.max_pages = max_pages
        self.session.headers["Accept"] = "application/json"

    def scrape(self) -> list[Offer]:
        found: dict[str, Offer] = {}
        for q in self.queries:
            for page in range(1, self.max_pages + 1):
                url = API.format(q=quote_plus(q), page=page)
                try:
                    payload = self.get(url).json()
                except Exception as e:
                    log.warning("migros '%s' s.%d alınamadı: %s", q, page, e)
                    break
                if page == 1:
                    self.dump(f"{q}.json", json.dumps(payload, ensure_ascii=False, indent=1))
                offers = parse_migros_payload(payload)
                new = [o for o in offers if o.market_product_id not in found]
                if not new:
                    break                  # sayfa boş ya da tekrar ediyor -> sonraki kelime
                for o in new:
                    found[o.market_product_id] = o
            log.info("migros '%s': toplam %d ürün", q, len(found))
        return list(found.values())
