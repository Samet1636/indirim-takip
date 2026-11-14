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

-- Fiyat geçmişi: sadece fiyat DEĞİŞTİĞİNDE yeni satır eklenir (tüm katalog her gün
-- tarandığı için her gün her ürüne satır yazmak veritabanını gereksiz büyütürdü).
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
"""

# Ürünün "şu anki" durumu products tablosunda tutulur (en son görüldüğü gün ve fiyatı).
CURRENT_COLUMNS = {
    "last_seen": "TEXT", "price": "REAL", "regular_price": "REAL",
    "discount_pct": "REAL", "is_campaign": "INTEGER DEFAULT 0", "valid_from": "TEXT",
}

VIEW = """
DROP VIEW IF EXISTS todays_discounts;
-- Uygulamanın indirim ekranı: her marketin son taramasında görülen indirimli/kampanyalı ürünler
CREATE VIEW todays_discounts AS
SELECT p.market, p.name, p.url, p.image_url, p.category,
       p.price, p.regular_price, p.discount_pct, p.is_campaign, p.valid_from,
       p.last_seen AS scraped_on
FROM products p
WHERE p.last_seen = (SELECT MAX(last_seen) FROM products p2 WHERE p2.market = p.market)
  AND (p.is_campaign = 1 OR p.discount_pct IS NOT NULL);
"""


def connect(path: str | Path = "data/prices.db") -> sqlite3.Connection:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    _migrate(conn)
    conn.executescript(VIEW)
    return conn


def _migrate(conn: sqlite3.Connection) -> None:
    """Eski veritabanlarına yeni sütunları ekler ve son fiyatı geçmişten doldurur."""
    have = {r["name"] for r in conn.execute("PRAGMA table_info(products)")}
    missing = [c for c in CURRENT_COLUMNS if c not in have]
    if not missing:
        return
    with conn:
        for c in missing:
            conn.execute(f"ALTER TABLE products ADD COLUMN {c} {CURRENT_COLUMNS[c]}")
        conn.execute("""
            UPDATE products SET (last_seen, price, regular_price, discount_pct, is_campaign, valid_from) =
              (SELECT s.scraped_on, s.price, s.regular_price, s.discount_pct, s.is_campaign, s.valid_from
               FROM price_snapshots s WHERE s.product_id = products.id
               ORDER BY s.scraped_on DESC LIMIT 1)
            WHERE last_seen IS NULL""")


def save_offers(conn: sqlite3.Connection, offers: list[Offer]) -> int:
    """Ürünleri ekler/günceller. Fiyat değiştiyse (veya ürün yeniyse) geçmişe satır ekler."""
    changed = 0
    with conn:
        for o in offers:
            row = conn.execute(
                "SELECT id, price, regular_price, is_campaign, last_seen FROM products "
                "WHERE market=? AND market_product_id=?", (o.market, o.market_product_id)).fetchone()
            if row and row["last_seen"] and row["last_seen"] > o.scraped_on:
                continue    # elimizde daha yeni bilgi var (eski bir içe aktarma dosyası)
            conn.execute(
                """INSERT INTO products (market, market_product_id, name, url, image_url, category,
                                         last_seen, price, regular_price, discount_pct, is_campaign, valid_from)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT (market, market_product_id) DO UPDATE SET
                     name=excluded.name, url=COALESCE(excluded.url, products.url),
                     image_url=COALESCE(excluded.image_url, products.image_url),
                     category=COALESCE(excluded.category, products.category),
                     last_seen=excluded.last_seen, price=excluded.price,
                     regular_price=excluded.regular_price, discount_pct=excluded.discount_pct,
                     is_campaign=excluded.is_campaign, valid_from=excluded.valid_from""",
                (o.market, o.market_product_id, o.name, o.url, o.image_url, o.category,
                 o.scraped_on, o.price, o.regular_price, o.discount_pct, int(o.is_campaign), o.valid_from),
            )
            pid = row["id"] if row else conn.execute(
                "SELECT id FROM products WHERE market=? AND market_product_id=?",
                (o.market, o.market_product_id)).fetchone()["id"]
            same = row is not None and row["price"] == o.price and row["regular_price"] == o.regular_price \
                and bool(row["is_campaign"]) == o.is_campaign
            if not same:
                conn.execute(
                    """INSERT OR REPLACE INTO price_snapshots
                       (product_id, scraped_on, price, regular_price, discount_pct, is_campaign, valid_from)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (pid, o.scraped_on, o.price, o.regular_price, o.discount_pct,
                     int(o.is_campaign), o.valid_from),
                )
                changed += 1
    return changed


def catalog(conn: sqlite3.Connection, today: str | None = None, stale_days: int = 3) -> list[dict]:
    """Tüm ürünler sekmesi: son stale_days gün içinde görülmüş bütün ürünler."""
    today_d = date.fromisoformat(today) if today else date.today()
    stale = (today_d - timedelta(days=stale_days)).isoformat()
    rows = conn.execute(
        """SELECT market, name, category, price, regular_price, discount_pct, url, image_url
           FROM products WHERE last_seen >= ? ORDER BY market, category, name""", (stale,)).fetchall()
    return [dict(r) for r in rows]


def todays_discounts(conn: sqlite3.Connection, today: str | None = None,
                     max_age_days: int = 7, stale_days: int = 3) -> list[dict]:
    """Uygulamada gösterilecek indirimler.

    Kampanya ürünlerinde (BİM aktüel gibi) başlangıcı max_age_days günden eski olan
    dönemler listeden çıkarılır; ileri tarihli dönemler 'yakında' olarak işaretlenir.
    Eski kayıtlar veritabanında kalır (fiyat geçmişi için), sadece listede gösterilmez.
    Bir marketin son taraması stale_days günden eskiyse (ör. A101'i tarayan bilgisayar
    birkaç gün açılmadıysa) o marketin bayat verisi de gösterilmez.
    """
    today_d = date.fromisoformat(today) if today else date.today()
    cutoff = (today_d - timedelta(days=max_age_days)).isoformat()
    stale = (today_d - timedelta(days=stale_days)).isoformat()
    rows = conn.execute(
        """SELECT *,
                  CASE WHEN valid_from > :today THEN 'yakında' ELSE 'geçerli' END AS durum
           FROM todays_discounts
           WHERE (valid_from IS NULL OR valid_from >= :cutoff)
             AND scraped_on >= :stale
           ORDER BY durum, COALESCE(discount_pct, 0) DESC, market, name""",
        {"today": today_d.isoformat(), "cutoff": cutoff, "stale": stale},
    ).fetchall()
    return [dict(r) for r in rows]
