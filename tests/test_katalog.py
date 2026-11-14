"""Tüm ürünler (katalog) özelliğinin testleri — ağa çıkmadan."""
import json
import re
import sqlite3
from pathlib import Path

import db
from models import Offer
from scrapers.discovery import sitemap_urls, slug_to_category
from scrapers.sok import SokScraper

FIX = Path(__file__).parent / "fixtures"


class R:
    def __init__(self, text):
        self.text = text
        self.content = text.encode()


def test_sitemap_index():
    pages = {
        "https://x.com/robots.txt": "User-agent: *\nSitemap: https://x.com/sm.xml\n",
        "https://x.com/sm.xml": "<sitemapindex><sitemap><loc>https://x.com/sm-urun.xml</loc></sitemap>"
                                "<sitemap><loc>https://x.com/sm-kategori.xml</loc></sitemap></sitemapindex>",
        "https://x.com/sm-kategori.xml": "<urlset><url><loc>https://x.com/meyve-c-1</loc></url>"
                                         "<url><loc>https://x.com/sut-c-2</loc></url></urlset>",
        "https://x.com/sm-urun.xml": "<urlset><url><loc>https://x.com/elma-p-9</loc></url></urlset>",
    }
    urls = sitemap_urls(lambda u: R(pages[u]), "https://x.com", re.compile(r"-c-\d+$"))
    assert urls == ["https://x.com/meyve-c-1", "https://x.com/sut-c-2"]
    assert slug_to_category("https://www.sokmarket.com.tr/meyve-ve-sebze-c-20") == "Meyve Ve Sebze"


def test_sok_catalog_crawl():
    sample = (FIX / "sok_sample.html").read_text(encoding="utf-8")
    calls = []

    class S(SokScraper):
        seed_urls = []
        def get(self, url, **kw):
            calls.append(url)
            if url.endswith("robots.txt"):
                return R("Sitemap: https://www.sokmarket.com.tr/sm.xml")
            if url.endswith("sm.xml"):
                return R("<urlset><url><loc>https://www.sokmarket.com.tr/deterjan-c-5</loc></url></urlset>")
            if url == "https://www.sokmarket.com.tr/deterjan-c-5":
                return R(sample)
            return R("<html></html>")     # ana sayfa ve 2. sayfa boş

    offers = S().scrape(katalog=True)
    assert len(offers) == 20
    assert all(not o.is_campaign and o.category == "Deterjan" for o in offers)
    assert "https://www.sokmarket.com.tr/deterjan-c-5?page=2" in calls   # ?page=1 atlanıyor


def test_change_only_history_and_migration(tmp_path):
    conn = db.connect(tmp_path / "t.db")
    o = lambda price, day: Offer(market="sok", market_product_id="1", name="Süt", price=price, scraped_on=day)
    db.save_offers(conn, [o(40, "2026-11-10")])
    db.save_offers(conn, [o(40, "2026-11-11")])          # aynı fiyat: geçmişe satır eklenmez
    db.save_offers(conn, [o(35, "2026-11-12")])          # fiyat değişti
    db.save_offers(conn, [o(99, "2026-11-01")])          # eski veri: yok sayılır
    hist = conn.execute("SELECT scraped_on, price FROM price_snapshots ORDER BY scraped_on").fetchall()
    assert [tuple(r) for r in hist] == [("2026-11-10", 40), ("2026-11-12", 35)]
    assert dict(conn.execute("SELECT last_seen, price FROM products").fetchone()) == \
        {"last_seen": "2026-11-12", "price": 35}
    assert len(db.catalog(conn, today="2026-11-13")) == 1

    # Eski şemalı veritabanı yeni sütunlarla güncellenmeli
    old = tmp_path / "old.db"
    c = sqlite3.connect(old)
    c.executescript("""CREATE TABLE products (id INTEGER PRIMARY KEY AUTOINCREMENT, market TEXT NOT NULL,
        market_product_id TEXT NOT NULL, name TEXT NOT NULL, url TEXT, image_url TEXT, category TEXT,
        UNIQUE (market, market_product_id));
        CREATE TABLE price_snapshots (product_id INTEGER NOT NULL, scraped_on TEXT NOT NULL, price REAL NOT NULL,
        regular_price REAL, discount_pct REAL, is_campaign INTEGER NOT NULL DEFAULT 0, valid_from TEXT,
        PRIMARY KEY (product_id, scraped_on));
        INSERT INTO products (market, market_product_id, name) VALUES ('bim', 'x', 'Robot');
        INSERT INTO price_snapshots VALUES (1, '2026-11-12', 7999, NULL, NULL, 1, NULL);""")
    c.commit(); c.close()
    conn2 = db.connect(old)
    rows = db.todays_discounts(conn2, today="2026-11-13")
    assert [r["name"] for r in rows] == ["Robot"]


def test_a101_category_campaign_flag():
    from scrapers.a101 import parse_a101_search
    data = json.loads((FIX / "a101_search_sample.json").read_text(encoding="utf-8"))["data"]
    data["results"][1]["promotion"] = None
    offers = parse_a101_search(data, campaign=None)
    assert offers[0].is_campaign and not offers[1].is_campaign


def test_sok_menu_categories_preferred():
    sample = (FIX / "sok_sample.html").read_text(encoding="utf-8")

    class S(SokScraper):
        def get(self, url, **kw):
            return R(sample)
    urls = S().category_urls()
    assert len(urls) == 19 and "https://www.sokmarket.com.tr/meyve-ve-sebze-c-20" in urls


def test_a101_category_urls_from_real_page():
    from scrapers.a101 import a101_category_urls
    html = (FIX / "a101_kapida_links.html").read_text(encoding="utf-8")
    cats = a101_category_urls([html, "<html></html>"])
    names = [c.rsplit("/", 1)[-1] for c in cats]
    assert "meyve-sebze" in names and "temel-gida" in names and "su-icecek" in names
    assert not any(n in ("markalar", "sozlesmeler", "aldin-aldin", "kampanyalar") for n in names)
    assert all(c.count("/") == 4 for c in cats)          # sadece ana kategoriler


def test_a101_nested_category_response():
    from scrapers.a101 import parse_a101_search
    d = json.loads((FIX / "a101_search_sample.json").read_text(encoding="utf-8"))["data"]
    nested = {"children": [{"name": "Süt", "products": d["results"][:10]},
                           {"name": "Yumurta", "items": {"list": d["results"][10:25]}}]}
    assert len(parse_a101_search(nested, campaign=None)) == 25


def test_a101_real_category_response():
    from scrapers.a101 import parse_a101_search
    data = json.loads((FIX / "a101_kategori_sample.json").read_text(encoding="utf-8"))["data"]
    offers = parse_a101_search(data, campaign=None)
    assert len(offers) == sum(len(c["products"]) for c in data["children"])   # tüm alt kategoriler
    assert len(offers) > 200
