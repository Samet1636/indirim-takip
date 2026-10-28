"""
Günlük çalıştırılan ana script.

    python run.py                 # tüm marketler
    python run.py --only bim      # tek market
    python run.py --dump          # ham yanıtları data/raw/ altına kaydet (debug)
"""
from __future__ import annotations
import argparse
import json
import logging
from pathlib import Path

import db
from scrapers.bim import BimScraper
from scrapers.migros import MigrosScraper

SCRAPERS = {"migros": MigrosScraper, "bim": BimScraper}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=SCRAPERS.keys())
    ap.add_argument("--dump", action="store_true")
    ap.add_argument("--db", default="data/prices.db")
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    conn = db.connect(args.db)
    dump_dir = Path("data/raw") if args.dump else None

    failures = 0
    for name, cls in SCRAPERS.items():
        if args.only and name != args.only:
            continue
        try:
            offers = cls(dump_dir=dump_dir).scrape()
            n = db.save_offers(conn, offers)
            disc = sum(o.is_discounted for o in offers)
            logging.info("%s: %d ürün kaydedildi, %d tanesi indirimde", name, n, disc)
            if n == 0:
                failures += 1
        except Exception:
            # Bir market patlarsa diğerleri yine çalışsın
            logging.exception("%s scraper hata verdi", name)
            failures += 1

    # Uygulamanın okuyacağı güncel indirim listesi
    out = Path("data/discounts_today.json")
    out.write_text(json.dumps(db.todays_discounts(conn), ensure_ascii=False, indent=1), encoding="utf-8")
    logging.info("%s yazıldı", out)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
