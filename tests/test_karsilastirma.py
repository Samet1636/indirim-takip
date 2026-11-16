"""Market karşılaştırması ve alışveriş listesi testleri (ağa çıkmaz, küçük sahte katalogla)."""
from __future__ import annotations

from api import karsilastirma as k

KATALOG = [
    # süt: bilinen malzeme -> eşleştirme kuralları (Migros'ta kategori şartı var)
    {"market": "sok", "name": "Mis Süt 1 L", "price": 36.0, "category": None},
    {"market": "sok", "name": "Mis Süt 200 ml", "price": 12.0, "category": None},
    {"market": "a101", "name": "Birşah Yarım Yağlı Süt 1 L", "price": 34.0, "category": None},
    {"market": "a101", "name": "Birşah Süt 5 L", "price": 150.0, "category": None},
    {"market": "migros", "name": "Pınar Süt 1 L", "price": 45.0, "category": "Günlük Süt"},
    {"market": "migros", "name": "Ülker Sütlü Çikolata 80 G", "price": 30.0, "category": "Çikolata"},
    {"market": "sok", "name": "Mis Kakaolu Süt 200 ml", "price": 15.0, "category": None},
    # yumurta (adet)
    {"market": "sok", "name": "Yumurta 15'li", "price": 90.0, "category": None},
    {"market": "a101", "name": "Yumurta L Boy 30'lu", "price": 160.0, "category": None},
    # domates: tartıyla satılır
    {"market": "sok", "name": "Domates Kg", "price": 40.0, "category": None},
    {"market": "a101", "name": "Domates Kg", "price": 30.0, "category": None},
    # bilinen malzeme olmayan ürün: kelime araması
    {"market": "sok", "name": "Omo Matik Toz Çamaşır Deterjanı 4 Kg", "price": 300.0, "category": None},
    {"market": "migros", "name": "Ariel Toz Çamaşır Deterjanı 6 Kg", "price": 400.0, "category": "Toz Deterjan"},
    {"market": "migros", "name": "Pril Bulaşık Deterjanı 1,5 L", "price": 90.0, "category": "Bulaşık"},
]


def test_satir_ayir():
    assert k.satir_ayir("2 L süt")[:3] == ("sut", 2000.0, "ml")
    assert k.satir_ayir("Domates 1,5 kg")[:3] == ("domates", 1500.0, "g")
    assert k.satir_ayir("30 yumurta") == ("yumurta", None, None, 30)
    assert k.satir_ayir("süt") == ("sut", None, None, None)


def test_tek_urun_karsilastirma_birim_fiyatla():
    r = k.karsilastir("Süt", KATALOG)
    assert r["birim"] == "L"
    adlar = [u["ad"] for u in r["urunler"]]
    assert "Ülker Sütlü Çikolata 80 G" not in adlar and "Mis Kakaolu Süt 200 ml" not in adlar
    # en ucuz litre fiyatı: 5 L'lik paket (30 TL/L)
    assert r["urunler"][0]["ad"] == "Birşah Süt 5 L" and r["urunler"][0]["birim_fiyat"] == 30.0
    assert [m["market"] for m in r["marketler"]] == ["a101", "sok", "migros"]
    assert r["marketler"][1]["birim_fiyat"] == 36.0                   # ŞOK'ta 1 L, 200 ml'den ucuz


def test_yumurta_adedi_ve_kelime_sinirlari():
    assert k.urun_miktari("Mudurnu Yumurta Omega-3 M Boy 6'lı 53-62 G") == (6.0, "adet")
    assert k.urun_miktari("Yumurta L Boy 30'lu") == (30.0, "adet")
    assert k.urun_miktari("Nimet Lavaş 12'li 840 G") == (840.0, "g")      # 840 g paket, adet değil
    kat = [{"market": "sok", "name": "Kayseri Şeker Kahverengi Küp Şeker 500 G", "price": 80.0},
           {"market": "sok", "name": "Yemeneli Türk Kahvesi 100 g", "price": 70.0},
           {"market": "sok", "name": "Nescafe Gold Kahve 100 g", "price": 150.0}]
    assert {u["ad"] for u in k.karsilastir("kahve", kat)["urunler"]} == {"Yemeneli Türk Kahvesi 100 g",
                                                                         "Nescafe Gold Kahve 100 g"}


def test_kelime_aramasi_ekli_halleri_almaz():
    r = k.karsilastir("çamaşır deterjanı", KATALOG)
    assert {u["ad"] for u in r["urunler"]} == {"Omo Matik Toz Çamaşır Deterjanı 4 Kg", "Ariel Toz Çamaşır Deterjanı 6 Kg"}
    assert k.karsilastir("xyz", KATALOG)["toplam"] == 0


def test_liste_en_ucuz_market_ve_ikili_oneri():
    r = k.liste_hesapla(["1 L süt", "30 yumurta", "domates 2 kg", "çamaşır deterjanı", "uçan halı"], KATALOG)
    kalem = {x["satir"]: x for x in r["kalemler"]}
    assert kalem["uçan halı"]["bulunamadi"]
    # 1 L süt: A101'de 1 L paket (34), 5 L değil
    sut_a101 = next(s for s in kalem["1 L süt"]["secenekler"] if s["market"] == "a101")
    assert sut_a101["ad"] == "Birşah Yarım Yağlı Süt 1 L" and sut_a101["tutar"] == 34.0
    # 30 yumurta: ŞOK'ta 2 x 15'li = 180, A101'de 1 x 30'lu = 160
    yum = {s["market"]: s for s in kalem["30 yumurta"]["secenekler"]}
    assert yum["sok"]["adet"] == 2 and yum["sok"]["tutar"] == 180.0 and yum["a101"]["tutar"] == 160.0
    # domates tartıyla: 2 kg A101'de 60 TL
    assert kalem["domates 2 kg"]["secenekler"][0]["tutar"] == 60.0
    tek = r["oneri"]["tek"]
    assert tek["marketler"] == ["sok"] and tek["eksik"] == []         # tüm ürünler sadece ŞOK'ta var
    iki = r["oneri"]["iki"]
    assert iki is not None and set(iki["marketler"]) == {"a101", "sok"} and iki["tasarruf"] > 0
    assert iki["tutar"] == round(34 + 160 + 60 + 300, 2)


def test_api_uclari(tmp_path, monkeypatch):
    import json
    from fastapi.testclient import TestClient
    from api import main
    yol = tmp_path / "katalog.json"
    yol.write_text(json.dumps(KATALOG, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setenv("KATALOG_YOLU", str(yol))
    with TestClient(main.uygulama_olustur()) as c:
        assert c.get("/karsilastir", params={"q": "süt"}).json()["marketler"][0]["market"] == "a101"
        assert c.get("/karsilastir", params={"q": "s"}).status_code == 422
        r = c.post("/liste", json={"kalemler": ["süt", "yumurta"]})
        assert r.status_code == 200 and r.json()["oneri"]["tek"] is not None
        assert c.post("/liste", json={"kalemler": []}).status_code == 422
