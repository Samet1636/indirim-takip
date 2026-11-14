"""
Kampanya sayfalarını gezen ortak scraper (A101 ve ŞOK bunu kullanıyor).

Akış: ana sayfa -> kampanya linklerini bul -> her kampanya sayfasını (sayfa sayfa) gez ->
gömülü JSON'dan ürünleri çıkar.
"""
from __future__ import annotations

import re
from typing import Optional
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse

from models import Offer
from scrapers.base import BaseScraper, log
from scrapers.nextjs import discover_links, extract_payloads, find_products, looks_like_kurus


def _with_page(url: str, param: str, page: int) -> str:
    parts = urlparse(url)
    q = dict(parse_qsl(parts.query))
    q[param] = str(page)
    return urlunparse(parts._replace(query=urlencode(q)))


def _slug(text: str) -> str:
    tr = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
    return re.sub(r"[^a-z0-9]+", "-", text.translate(tr).lower()).strip("-")


class CampaignScraper(BaseScraper):
    market = ""
    base = ""
    seed_urls: list[str] = []       # her zaman denenecek sayfalar
    keywords: list[str] = []        # ana sayfada kampanya linki ararken (önem sırasına göre)
    exclude: list[str] = []         # bu kelimeleri içeren linkleri atla
    max_collections = 4
    max_pages = 5
    page_param = "page"
    first_page_param: Optional[int] = None  # 2. istekte kullanılacak ilk sayfa numarası (None = 2)
    empty_pages_to_stop = 1                 # art arda kaç "yeni ürün yok" sayfasında durulsun
    price_divisor: Optional[float] = None   # None = otomatik (kuruş tespiti)
    impersonate_browser = True              # bu siteler bot korumalı, Chrome gibi görün

    def collect_urls(self) -> list[str]:
        urls = list(self.seed_urls)
        try:
            # Gerçek bir ziyaretçi gibi önce ana sayfa (çerezler de böylece alınır)
            home = self.get(self.base).text
            self.dump("home.html", home)
            found = discover_links(home, self.base, self.keywords, self.exclude)
            log.info("%s: ana sayfada %d kampanya linki bulundu, ilk %d tanesi taranacak: %s",
                     self.market, len(found), self.max_collections, found[: self.max_collections])
            urls += found[: self.max_collections]
        except Exception as e:
            log.warning("%s: ana sayfa alınamadı: %s", self.market, e)
        return list(dict.fromkeys(urls))

    def crawl(self, urls: list[str], max_pages: Optional[int] = None, label: str = "sayfa",
              categories: Optional[dict] = None, stop_mode: str = "yeni_yok",
              start: Optional[int] = None) -> dict[str, dict]:
        """Verilen sayfaları sayfa sayfa gezip ürünleri toplar (anahtar -> ürün).

        stop_mode: "yeni_yok" -> yeni ürün gelmeyen sayfada dur (kampanya sayfaları için)
                   "bos"      -> boş ya da bir öncekinin aynısı olan sayfada dur (kategoriler için;
                                 alt kategoride görülmüş ürünler yüzünden erken durmasın)"""
        raw: dict[str, dict] = {}
        max_pages = max_pages or self.max_pages
        if start is None:
            start = self.first_page_param if self.first_page_param is not None else 2
        for i, url in enumerate(urls):
            empty = 0
            prev_keys = None
            for n in range(max_pages):
                page_url = url if n == 0 else _with_page(url, self.page_param, start + n - 1)
                try:
                    html = self.get(page_url).text
                except Exception as e:
                    log.warning("%s: %s alınamadı: %s", self.market, page_url, e)
                    break
                if n == 0 and i < 5:
                    self.dump(f"{label}{i}.html", html)
                items = self.parse_items(html)
                new = 0
                for p in items:
                    key = p["id"] or p["url"] or p["name"]
                    if key not in raw:
                        if categories and url in categories:
                            p.setdefault("category", categories[url])
                        raw[key] = p
                        new += 1
                log.info("%s: %s -> %d ürün (%d yeni)", self.market, page_url, len(items), new)
                if stop_mode == "bos":
                    keys = {p["id"] or p["url"] or p["name"] for p in items}
                    if not items or keys == prev_keys:
                        break
                    prev_keys = keys
                    continue
                empty = 0 if new else empty + 1
                if empty >= self.empty_pages_to_stop:
                    break
        return raw

    def scrape(self, katalog: bool = False, kategori_limit: Optional[int] = None) -> list[Offer]:
        offers = {o.market_product_id: o for o in self.to_offers(list(self.crawl(self.collect_urls()).values()))}
        if katalog:
            cats = self.category_urls()[: kategori_limit or None]
            log.info("%s: %d kategori taranacak", self.market, len(cats))
            from scrapers.discovery import slug_to_category
            raw = self.crawl(cats, max_pages=self.catalog_max_pages, label="kategori",
                             categories={u: slug_to_category(u) for u in cats}, stop_mode="bos",
                             start=self.catalog_first_page)
            for o in self.to_offers(list(raw.values()), campaign=False):
                offers.setdefault(o.market_product_id, o)   # kampanya bilgisi öncelikli
        return list(offers.values())

    catalog_max_pages = 150
    catalog_first_page: Optional[int] = None   # kategorilerde 2. isteğin sayfa numarası (None = 2)
    category_pattern = None   # alt sınıf: kategori adreslerini tanıyan regex

    def category_urls(self) -> list[str]:
        """Kategori adresleri: önce sitenin menüsündeki linkler (güncel ve sadece ana kategoriler),
        bulunamazsa sitemap (sitemap'te eski/kaldırılmış kategoriler de olabiliyor)."""
        if self.category_pattern is None:
            return []
        from scrapers.discovery import page_links, sitemap_urls
        urls = []
        try:
            urls = page_links(self.get(self.base).text, self.base, self.category_pattern)
        except Exception as e:
            log.warning("%s: ana sayfa alınamadı: %s", self.market, e)
        if urls:
            log.info("%s: menüde %d kategori bulundu", self.market, len(urls))
            return urls
        urls = sitemap_urls(self.get, self.base, self.category_pattern)
        log.info("%s: sitemap'te %d kategori bulundu", self.market, len(urls))
        return urls

    def parse_items(self, html: str) -> list[dict]:
        """Sayfadan ürünleri çıkarır. Siteye özel yapı varsa alt sınıfta değiştirilir."""
        return [p for payload in extract_payloads(html) for p in find_products(payload)]

    def to_offers(self, items: list[dict], campaign: bool = True) -> list[Offer]:
        div = self.price_divisor
        if div is None:
            div = 100.0 if looks_like_kurus([p["price"] for p in items]) else 1.0
            if div != 1.0:
                log.info("%s: fiyatlar kuruş görünüyor, 100'e bölünüyor", self.market)
        offers = []
        for p in items:
            url = urljoin(self.base + "/", p["url"]) if p["url"] else None
            image = urljoin(self.base + "/", p["image"]) if p["image"] else None
            offers.append(Offer(
                market=self.market,
                market_product_id=p["id"] or (urlparse(url).path.strip("/") if url else _slug(p["name"])),
                name=p["name"],
                price=round(p["price"] / div, 2),
                regular_price=round(p["original"] / div, 2) if p["original"] else None,
                url=url,
                image_url=image,
                category=p.get("category"),
                is_campaign=campaign,
            ))
        if not offers and campaign:
            log.warning("%s: hiç ürün bulunamadı. 'python run.py --only %s --dump' ile "
                        "data/raw altındaki dosyaları kontrol et", self.market, self.market)
        return offers
