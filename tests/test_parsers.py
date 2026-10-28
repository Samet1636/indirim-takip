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
    offers = parse_migros_payload(json.loads((FIX / "migros_sample.json").read_text()))
    assert [o.name for o in offers] == ["Pınar Süt Tam Yağlı 1 L", "Sütaş Süt 1 L"]
    pinar, sutas = offers
    assert pinar.price == 44.95 and pinar.regular_price == 54.95
    assert pinar.discount_pct == 18.2 and pinar.is_discounted
    assert sutas.regular_price is None and not sutas.is_discounted
    assert parse_migros_payload({}) == []


def test_bim_parser():
    html = (FIX / "bim_sample.html").read_text()
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


def test_db_roundtrip(tmp_path):
    conn = db.connect(tmp_path / "t.db")
    offers = parse_migros_payload(json.loads((FIX / "migros_sample.json").read_text()))
    offers += parse_bim_html((FIX / "bim_sample.html").read_text())
    db.save_offers(conn, offers)
    db.save_offers(conn, offers)          # aynı gün ikinci çalıştırma tekrar kayıt üretmemeli
    rows = db.todays_discounts(conn)
    names = {r["name"] for r in rows}
    assert names == {"Pınar Süt Tam Yağlı 1 L", "Robot Süpürge", "Filtre Kahve Makinesi"}
    assert conn.execute("SELECT COUNT(*) FROM price_snapshots").fetchone()[0] == 4
