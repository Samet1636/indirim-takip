"""SQLite veritabanı. İleride PostgreSQL/Supabase'e geçmek için şema aynı kalabilir."""
from __future__ import annotations
import sqlite3
from datetime import date, timedelta
from pathlib import Path
from models import Offer

SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    market            TEXT NOT NULL,
    market_product_id TEXT NOT NULL,
    name              TEXT NOT NULL,
    url               TEXT,
    image_url         TEXT,
    category          TEXT,
    UNIQUE (market, market_product_id)
);

-- Her gün her ürün için bir fiyat kaydı: fiyat geçmişi buradan çıkar.
CREATE TABLE IF NOT EXISTS price_snapshots (
    product_id    INTEGER NOT NULL REFERENCES products(id),
    scraped_on    TEXT NOT NULL,
    price         REAL NOT NULL,
    regular_price REAL,
    discount_pct  REAL,
    is_campaign   INTEGER NOT NULL DEFAULT 0,
    valid_from    TEXT,
    PRIMARY KEY (product_id, scraped_on)
);

-- Uygulamanın ana ekranı bu view'dan beslenir.
CREATE VIEW IF NOT EXISTS todays_discounts AS
SELECT p.market, p.name, p.url, p.image_url, p.category,
       s.price, s.regular_price, s.discount_pct, s.is_campaign, s.valid_from, s.scraped_on
FROM price_snapshots s
JOIN products p ON p.id = s.product_id
WHERE s.scraped_on = (SELECT MAX(scraped_on) FROM price_snapshots s2
                      JOIN products p2 ON p2.id = s2.product_id
                      WHERE p2.market = p.market)
  AND (s.is_campaign = 1 OR s.discount_pct IS NOT NULL);
"""


def connect(path: str | Path = "data/prices.db") -> sqlite3.Connection:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def save_offers(conn: sqlite3.Connection, offers: list[Offer]) -> int:
    """Ürünleri ekler/günceller ve günün fiyatını yazar. Aynı gün tekrar çalışırsa üzerine yazar."""
    with conn:
        for o in offers:
            conn.execute(
                """INSERT INTO products (market, market_product_id, name, url, image_url, category)
                   VALUES (?, ?, ?, ?, ?, ?)
                   ON CONFLICT (market, market_product_id) DO UPDATE SET
                     name=excluded.name, url=excluded.url,
                     image_url=COALESCE(excluded.image_url, products.image_url),
                     category=COALESCE(excluded.category, products.category)""",
                (o.market, o.market_product_id, o.name, o.url, o.image_url, o.category),
            )
            pid = conn.execute(
                "SELECT id FROM products WHERE market=? AND market_product_id=?",
                (o.market, o.market_product_id),
            ).fetchone()["id"]
            conn.execute(
                """INSERT OR REPLACE INTO price_snapshots
                   (product_id, scraped_on, price, regular_price, discount_pct, is_campaign, valid_from)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (pid, o.scraped_on, o.price, o.regular_price, o.discount_pct,
                 int(o.is_campaign), o.valid_from),
            )
    return len(offers)


def todays_discounts(conn: sqlite3.Connection, today: str | None = None,
                     max_age_days: int = 7) -> list[dict]:
    """Uygulamada gösterilecek indirimler.

    Kampanya ürünlerinde (BİM aktüel gibi) başlangıcı max_age_days günden eski olan
    dönemler listeden çıkarılır; ileri tarihli dönemler 'yakında' olarak işaretlenir.
    Eski kayıtlar veritabanında kalır (fiyat geçmişi için), sadece listede gösterilmez.
    """
    today_d = date.fromisoformat(today) if today else date.today()
    cutoff = (today_d - timedelta(days=max_age_days)).isoformat()
    rows = conn.execute(
        """SELECT *,
                  CASE WHEN valid_from > :today THEN 'yakında' ELSE 'geçerli' END AS durum
           FROM todays_discounts
           WHERE valid_from IS NULL OR valid_from >= :cutoff
           ORDER BY durum, COALESCE(discount_pct, 0) DESC, market, name""",
        {"today": today_d.isoformat(), "cutoff": cutoff},
    ).fetchall()
    return [dict(r) for r in rows]
