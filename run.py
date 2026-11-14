"""
Günlük çalıştırılan ana script.

    python run.py                     # tüm marketler
    python run.py --only bim          # tek market
    python run.py --skip a101         # bir marketi atla
    python run.py --dump              # ham yanıtları data/raw/ altına kaydet (debug)
    python run.py --katalog           # indirimlerin yanında TÜM ürünleri de tara
    python run.py --only sok --katalog --kategori-limit 2 --dump   # hızlı deneme

A101 GitHub sunucularından taranamıyor (Cloudflare), bu yüzden:
    Bilgisayarda (a101_gunluk.bat):
        python run.py --only a101 --no-save --export data/imports/a101.json --upload
    GitHub'da:
        python run.py --skip a101 --import-dir data/imports
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import logging
from datetime import date
from pathlib import Path

import db
from models import Offer
from scrapers.a101 import A101Scraper
from scrapers.bim import BimScraper
from scrapers.migros import MigrosScraper
from scrapers.sok import SokScraper

SCRAPERS = {"migros": MigrosScraper, "bim": BimScraper, "a101": A101Scraper, "sok": SokScraper}
OFFER_FIELDS = {f.name for f in dataclasses.fields(Offer)}


def load_offers(path: Path) -> list[Offer]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [Offer(**{k: v for k, v in d.items() if k in OFFER_FIELDS}) for d in data]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=SCRAPERS.keys())
    ap.add_argument("--skip", nargs="*", default=[], choices=SCRAPERS.keys())
    ap.add_argument("--no-scrape", action="store_true", help="hiç tarama yapma (sadece içe aktar)")
    ap.add_argument("--no-save", action="store_true", help="veritabanına ve discounts_today.json'a yazma")
    ap.add_argument("--export", help="taranan ürünleri bu JSON dosyasına yaz")
    ap.add_argument("--upload", action="store_true", help="--export dosyasını GitHub'a yükle")
    ap.add_argument("--import-dir", help="bu klasördeki *.json ürün dosyalarını veritabanına ekle")
    ap.add_argument("--katalog", action="store_true", help="tüm ürünleri (kategorileri) de tara")
    ap.add_argument("--kategori-limit", type=int, help="deneme için en fazla bu kadar kategori tara")
    ap.add_argument("--dump", action="store_true")
    ap.add_argument("--goster", action="store_true", help="A101 için tarayıcı penceresini göster")
    ap.add_argument("--db", default="data/prices.db")
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    conn = None if args.no_save else db.connect(args.db)
    dump_dir = Path("data/raw") if args.dump else None

    failures = 0
    all_offers: list[Offer] = []
    for name, cls in SCRAPERS.items():
        if args.no_scrape or (args.only and name != args.only) or name in args.skip:
            continue
        try:
            scraper = cls(dump_dir=dump_dir)
            if args.goster:
                scraper.headful = True
            offers = scraper.scrape(katalog=args.katalog, kategori_limit=args.kategori_limit)
            all_offers += offers
            changed = db.save_offers(conn, offers) if conn else 0
            disc = sum(o.is_discounted for o in offers)
            logging.info("%s: %d ürün bulundu, %d tanesi indirimde, %d fiyat değişikliği",
                         name, len(offers), disc, changed)
            if not offers:
                failures += 1
        except Exception:
            # Bir market patlarsa diğerleri yine çalışsın
            logging.exception("%s scraper hata verdi", name)
            failures += 1

    if args.export:
        out = Path(args.export)
        out.parent.mkdir(parents=True, exist_ok=True)
        if all_offers:
            payload = json.dumps([dataclasses.asdict(o) for o in all_offers], ensure_ascii=False, indent=1)
            out.write_text(payload, encoding="utf-8")
            logging.info("%s yazıldı (%d ürün)", out, len(all_offers))
            if args.upload:
                from github_upload import upload_file
                try:
                    link = upload_file(out.as_posix(), payload.encode("utf-8"),
                                       f"{out.stem} yerel tarama {date.today().isoformat()}")
                    logging.info("GitHub'a yüklendi: %s", link)
                except Exception:
                    logging.exception("GitHub'a yüklenemedi")
                    failures += 1
        else:
            logging.warning("Ürün bulunamadı, %s yazılmadı/yüklenmedi", out)

    if args.import_dir and conn:
        for f in sorted(Path(args.import_dir).glob("*.json")):
            try:
                offers = load_offers(f)
                db.save_offers(conn, offers)
                when = max((o.scraped_on for o in offers), default="?")
                logging.info("%s içe aktarıldı: %d ürün (tarama tarihi %s)", f, len(offers), when)
            except Exception:
                logging.exception("%s içe aktarılamadı", f)
                failures += 1

    if conn:
        # Uygulamanın okuyacağı güncel indirim listesi
        out = Path("data/discounts_today.json")
        out.write_text(json.dumps(db.todays_discounts(conn), ensure_ascii=False, indent=1), encoding="utf-8")
        logging.info("%s yazıldı", out)
        # Tüm ürünler sekmesi için (boyutu küçük tutmak için girintisiz)
        kat = db.catalog(conn)
        Path("data/katalog.json").write_text(json.dumps(kat, ensure_ascii=False, separators=(",", ":")),
                                             encoding="utf-8")
        logging.info("data/katalog.json yazıldı (%d ürün)", len(kat))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
