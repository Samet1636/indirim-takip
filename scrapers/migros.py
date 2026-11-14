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

import re

from models import Offer
from scrapers.base import BaseScraper, log
from scrapers.discovery import page_links, sitemap_urls

API = "https://www.migros.com.tr/rest/search/screens/products?q={q}&sayfa={page}"
# Kategori sayfaları da aynı uç noktanın "screens/<kategori-adresi>" haliyle geliyor
CATEGORY_API = "https://www.migros.com.tr/rest/search/screens/{slug}?sayfa={page}"
CATEGORY_RE = re.compile(r"migros\.com\.tr/[a-z0-9-]+-c-[0-9a-z]+/?$")

# Kategori bulunamazsa yedek: geniş kelime listesiyle arama

# Tüm katalogu gezmek yerine sık alınan ürün gruplarını tarıyoruz.
# Kapsamı genişletmek için buraya kelime ekle.
DEFAULT_QUERIES = [
    "süt", "yoğurt", "peynir", "yumurta", "tereyağı", "zeytin", "ekmek",
    "makarna", "pirinç", "bulgur", "un", "şeker", "çay", "kahve", "ayçiçek yağı",
    "zeytinyağı", "tavuk", "kıyma", "sucuk", "deterjan", "şampuan",
    "tuvalet kağıdı", "bisküvi", "çikolata", "cips", "su", "meyve suyu",
]

CATALOG_QUERIES = DEFAULT_QUERIES + [
    "domates", "salatalık", "biber", "soğan", "sarımsak", "patates", "havuç", "kabak", "ıspanak",
    "patlıcan", "taze fasulye", "marul", "maydanoz", "limon", "muz", "elma", "portakal", "mandalina",
    "kırmızı mercimek", "yeşil mercimek", "nohut", "kuru fasulye", "yulaf", "ekmek", "lavaş",
    "tavuk göğüs", "tavuk but", "kıyma", "dana", "balık", "ton balığı", "hindi", "kaşar", "lor",
    "kefir", "ayran", "krema", "tahin", "pekmez", "bal", "reçel", "fıstık ezmesi", "ceviz", "fındık",
    "badem", "salça", "konserve", "sirke", "baharat", "tuz", "maya", "irmik", "şehriye", "nişasta",
    "dondurulmuş", "pizza", "dondurma", "kek", "gofret", "kraker", "kuruyemiş", "maden suyu",
    "kola", "gazoz", "enerji içeceği", "bebek bezi", "mama", "ıslak mendil", "kağıt havlu",
    "bulaşık", "yumuşatıcı", "çamaşır suyu", "diş macunu", "sabun", "duş jeli", "deodorant",
    "kedi maması", "köpek maması",
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

    def scrape(self, katalog: bool = False, kategori_limit: int | None = None) -> list[Offer]:
        found: dict[str, Offer] = {}
        if katalog:
            found.update(self.scrape_categories(kategori_limit))
            if found:
                return list(found.values())   # kategoriler indirimli ürünleri de kapsıyor
            log.warning("migros: kategori taraması sonuç vermedi, geniş kelime listesine geçiliyor")
            self.queries = CATALOG_QUERIES
            self.max_pages = max(self.max_pages, 30)
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

    def category_urls(self) -> list[str]:
        urls = sitemap_urls(self.get, "https://www.migros.com.tr", CATEGORY_RE)
        if not urls:
            try:
                home = self.get("https://www.migros.com.tr/").text
                self.dump("home.html", home)
                urls = page_links(home, "https://www.migros.com.tr", CATEGORY_RE)
            except Exception as e:
                log.warning("migros: ana sayfa alınamadı: %s", e)
        log.info("migros: %d kategori bulundu", len(urls))
        return urls

    def scrape_categories(self, limit: int | None = None) -> dict[str, Offer]:
        found: dict[str, Offer] = {}
        urls = self.category_urls()[: limit or None]
        for i, url in enumerate(urls):
            slug = url.rstrip("/").split("/")[-1]
            prev_keys = None
            for page in range(1, 300):
                try:
                    payload = self.get(CATEGORY_API.format(slug=slug, page=page)).json()
                except Exception as e:
                    log.warning("migros kategori %s s.%d alınamadı: %s", slug, page, e)
                    break
                if page == 1 and i < 3:
                    self.dump(f"kategori_{slug}.json", json.dumps(payload, ensure_ascii=False, indent=1))
                offers = parse_migros_payload(payload)
                keys = {o.market_product_id for o in offers}
                if not offers or keys == prev_keys:   # boş sayfa ya da son sayfanın tekrarı
                    break
                prev_keys = keys
                for o in offers:
                    found.setdefault(o.market_product_id, o)
            log.info("migros kategori %d/%d %s: toplam %d ürün", i + 1, len(urls), slug, len(found))
        return found
