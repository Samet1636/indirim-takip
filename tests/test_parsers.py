"""Ağa çıkmadan, örnek yanıtlarla ayrıştırıcıları test eder:  pytest -q"""
import json
from datetime import date
from pathlib import Path

import db
from scrapers.base import parse_tr_price
from scrapers.bim import find_period_links, parse_bim_html, parse_tr_date
from scrapers.migros import parse_migros_payload

FIX = Path(__file__).parent / "fixtures"


def test_parse_tr_price():
    assert parse_tr_price("1.299,90 ₺") == 1299.9
    assert parse_tr_price("49,50") == 49.5
    assert parse_tr_price("7.999,00 ₺") == 7999.0
    assert parse_tr_price("1.299") == 1299.0
    assert parse_tr_price("abc") is None


def test_migros_parser():
    offers = parse_migros_payload(json.loads((FIX / "migros_sample.json").read_text(encoding="utf-8")))
    assert [o.name for o in offers] == ["Pınar Süt Tam Yağlı 1 L", "Sütaş Süt 1 L"]
    pinar, sutas = offers
    assert pinar.price == 44.95 and pinar.regular_price == 54.95
    assert pinar.discount_pct == 18.2 and pinar.is_discounted
    assert sutas.regular_price is None and not sutas.is_discounted
    assert parse_migros_payload({}) == []


def test_marketfiyati_parser():
    from scrapers.marketfiyati import en_yakin_sube, parse_urunler
    veri = json.loads((FIX / "marketfiyati_sample.json").read_text(encoding="utf-8"))
    assert en_yakin_sube(veri["yakin"], "bim") == "bim-U645"
    assert en_yakin_sube(veri["yakin"], "hakmar") is None
    offers = {o.name: o for o in parse_urunler(veri["arama"], "bim")}
    assert len(offers) == 5 and all(o.market == "bim" and o.market_product_id.startswith("mf-") for o in offers.values())
    becel = offers["Becel Klasik Tereyağı Keyfi Margarin 250 Gr"]
    assert becel.price == 43.0 and becel.regular_price == 86.0 and becel.discount_pct == 50.0
    labne = offers["İçim Labne 400 Gr"]
    assert labne.regular_price is None and not labne.is_discounted and labne.category
    assert parse_urunler(veri["arama"], "a101") == []          # başka marketin fiyatı alınmaz
    assert parse_urunler({}) == []


def test_marketfiyati_sube_secimi():
    from scrapers.marketfiyati import ornek_kategoriler, sube_sec
    # 27.11.2026 Tarım Kredi: en yakın şube hiç ürün göstermiyordu
    adaylar = ["tarim_kredi-5373", "tarim_kredi-5372", "tarim_kredi-5500"]
    assert sube_sec(adaylar, {"tarim_kredi-5373": 0, "tarim_kredi-5372": 569, "tarim_kredi-5500": 487}) == "tarim_kredi-5372"
    assert sube_sec(adaylar, {s: 10 for s in adaylar}) == "tarim_kredi-5373"          # eşitse en yakın
    kat = ["Meyve ve Sebze", "Temel Gıda", "İçecek", "Atıştırmalık ve Tatlı"]
    assert ornek_kategoriler(kat) == ["Temel Gıda", "Atıştırmalık ve Tatlı"]
    assert ornek_kategoriler(["A", "B", "C"]) == ["A", "B"]                            # adlar değişirse


def test_bim_parser():
    html = (FIX / "bim_sample.html").read_text(encoding="utf-8")
    offers = parse_bim_html(html, "2026-10-31")
    assert [(o.name, o.price) for o in offers] == [
        ("Robot Süpürge", 7999.0), ("Filtre Kahve Makinesi", 1299.5)]
    assert all(o.is_campaign and o.valid_from == "2026-10-31" for o in offers)
    assert offers[0].url.endswith("/aktuel-urunler/robot-supurge/aktuel.aspx")
    links = find_period_links(html)
    assert len(links) == 2 and links[0][1] is not None


def test_parse_tr_date():
    assert parse_tr_date("31 Ekim Cuma", date(2026, 10, 28)) == "2026-10-31"
    assert parse_tr_date("2 Ocak", date(2026, 12, 30)) == "2027-01-02"


def test_a101_bilgisayar_yedegi_cift_kayit_olusturmaz(tmp_path, monkeypatch):
    import run
    from models import Offer
    bugun = date.today().isoformat()
    imp = tmp_path / "imports"
    imp.mkdir()
    kapida = [Offer("a101", "kapida-1", "Süt 1 L", 30.0, scraped_on=bugun).__dict__]
    (imp / "a101.json").write_text(json.dumps(kapida, ensure_ascii=False), encoding="utf-8")
    yol = tmp_path / "t.db"
    conn = db.connect(yol)
    db.save_offers(conn, [Offer("a101", f"mf-{i}", f"Ürün {i}", 10.0, scraped_on=bugun) for i in range(3)])
    assert db.fresh_count(conn, "a101", "mf-") == 3
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data").mkdir()                               # run.py çıktıları buraya yazar
    monkeypatch.setattr(run, "A101_YEDEK_ESIGI", 3)          # marketfiyati verisi güncel -> dosya atlanır
    monkeypatch.setattr("sys.argv", ["run.py", "--no-scrape", "--import-dir", str(imp), "--db", str(yol)])
    run.main()
    assert db.connect(yol).execute("SELECT COUNT(*) FROM products WHERE market_product_id='kapida-1'").fetchone()[0] == 0
    monkeypatch.setattr(run, "A101_YEDEK_ESIGI", 500)        # marketfiyati çalışmadıysa yedek alınır
    run.main()
    assert db.connect(yol).execute("SELECT COUNT(*) FROM products WHERE market_product_id='kapida-1'").fetchone()[0] == 1
    katalog = lambda: [p["name"] for p in json.loads((tmp_path / "data" / "katalog.json").read_text(encoding="utf-8"))]  # noqa: E731
    assert "Süt 1 L" in katalog()                            # yedek alındıysa katalogda da görünür
    # Daha önce alınmış Kapıda ürünleri, marketfiyati A101'i gelince katalogda çift görünmez
    monkeypatch.setattr(run, "A101_YEDEK_ESIGI", 3)
    run.main()
    assert "Süt 1 L" not in katalog() and len(katalog()) == 3


def test_db_roundtrip(tmp_path):
    conn = db.connect(tmp_path / "t.db")
    offers = parse_migros_payload(json.loads((FIX / "migros_sample.json").read_text(encoding="utf-8")))
    offers += parse_bim_html((FIX / "bim_sample.html").read_text(encoding="utf-8"))
    db.save_offers(conn, offers)
    db.save_offers(conn, offers)          # aynı gün ikinci çalıştırma tekrar kayıt üretmemeli
    rows = db.todays_discounts(conn)
    names = {r["name"] for r in rows}
    assert names == {"Pınar Süt Tam Yağlı 1 L", "Robot Süpürge", "Filtre Kahve Makinesi"}
    assert conn.execute("SELECT COUNT(*) FROM price_snapshots").fetchone()[0] == 4


def test_old_campaigns_hidden_and_upcoming_marked(tmp_path):
    from models import Offer
    conn = db.connect(tmp_path / "t.db")
    mk = lambda pid, vf: Offer(market="bim", market_product_id=pid, name=pid, price=10,
                               is_campaign=True, valid_from=vf, scraped_on="2026-10-28")
    db.save_offers(conn, [mk("eski", "2026-10-13"), mk("guncel", "2026-10-27"),
                          mk("gelecek", "2026-11-03")])
    rows = {r["name"]: r["durum"] for r in db.todays_discounts(conn, today="2026-10-28")}
    assert rows == {"guncel": "geçerli", "gelecek": "yakında"}


def test_export_import_roundtrip_and_stale(tmp_path):
    import dataclasses
    from models import Offer
    from run import load_offers
    offers = [Offer(market="a101", market_product_id="1", name="Kahve", price=229.0,
                    regular_price=459.0, is_campaign=True, scraped_on="2026-11-13")]
    f = tmp_path / "a101.json"
    f.write_text(json.dumps([dataclasses.asdict(offers[0]) | {"discount_pct": 50.1}], ensure_ascii=False),
                 encoding="utf-8")
    back = load_offers(f)
    assert back == offers
    conn = db.connect(tmp_path / "t.db")
    db.save_offers(conn, back)
    assert len(db.todays_discounts(conn, today="2026-11-14")) == 1      # 1 günlük: gösterilir
    assert db.todays_discounts(conn, today="2026-11-20") == []          # bayat: gizlenir
