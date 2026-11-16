"""Tarif kitabı (api/tarifler.py) testleri: ağa çıkmaz, küçük sahte katalogla."""
from __future__ import annotations

import json

from fastapi.testclient import TestClient

from api import main, tarifler

KATALOG = [
    {"market": "sok", "name": "Domates Kg", "price": 40.0, "category": None},
    {"market": "a101", "name": "Domates Kg", "price": 30.0, "category": None},
    {"market": "sok", "name": "Yumurta 15'li", "price": 90.0, "category": None},
    {"market": "sok", "name": "Sivri Biber Kg", "price": 60.0, "category": None},
]


def test_ozetler_ve_maliyet():
    oz = {t["id"]: t for t in tarifler.ozetler(KATALOG)}
    assert len(oz) >= 100 and "menemen" in oz
    m = oz["menemen"]
    assert m["sure_dk"] == 15 and m["besin"]["kcal"] > 0 and "vejetaryen" in m["etiketler"]
    # domates 150 g (en ucuz A101 30 TL/kg = 4,5 TL) + yumurta 110 g (90 TL / 900 g -> 11 TL) + biber 40 g (2,4 TL)
    assert abs(m["porsiyon_tl"] - (4.5 + 11.0 + 2.4)) < 0.05
    assert m["fiyati_bilinmeyen"] >= 1                       # zeytinyağı ve ekmek sahte katalogda yok


def test_detay_liste_terimleri():
    d = tarifler.detay("menemen", KATALOG)
    assert d["adimlar"] and len(d["adimlar"]) >= 4
    malz = {x["id"]: x for x in d["malzemeler"]}
    assert malz["domates"]["en_ucuz"]["market"] == "a101" and malz["domates"]["tutar"] == 4.5
    assert malz["yumurta"]["adet_g"] == 60 and malz["yumurta"]["liste_terimi"] == "yumurta"
    assert malz["tuz_baharat"]["dolapta"] and malz["tuz_baharat"]["en_ucuz"] is None
    assert malz["zeytinyagi"]["en_ucuz"] is None and malz["zeytinyagi"]["tutar"] is None
    assert tarifler.detay("olmayan_tarif", KATALOG) is None


def test_api(tmp_path, monkeypatch):
    yol = tmp_path / "katalog.json"
    yol.write_text(json.dumps(KATALOG, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setenv("KATALOG_YOLU", str(yol))
    with TestClient(main.uygulama_olustur()) as c:
        liste = c.get("/tarifler").json()["tarifler"]
        assert any(t["id"] == "menemen" for t in liste)
        assert c.get("/tarifler/menemen").json()["ad"] == "Menemen"
        assert c.get("/tarifler/yok").status_code == 404
