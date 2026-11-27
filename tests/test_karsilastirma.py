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


KAHVE = [{"market": m, "name": ad, "price": fiyat} for m, ad, fiyat in (
    ("a101", "Cafex Kahve Beyazlatıcısı 200 G", 50.0),            # kahve değil: beyazlatıcı
    ("migros", "Kahve Dünyası Tambol Sütlü Çikolata 77 G", 60.0),  # marka adında "Kahve"
    ("migros", "Galler Yumuşak Kahve Dolgulu Bitter Çikolata 65 G", 70.0),
    ("a101", "Cafex 3'ü 1 Arada Kahve 500 G", 150.0),
    ("a101", "Keyfe Türk Kahvesi 100 G", 70.0),
    ("sok", "Yemeneli Türk Kahvesi 100 g", 70.0),
    ("migros", "Migros Türk Kahvesi 100 G", 72.0),
    ("a101", "Cafex Filtre Kahve 250 G", 235.0),
    ("sok", "Grandeo Filtre Kahve 250 g", 235.0),
    ("migros", "Caffe Milano Filtre Kahve 500 G", 460.0),
    ("sok", "Karmen Çikolata Gofret 38 g", 10.0),                  # çikolata aranınca gofret gelmez
    ("migros", "Ülker Sütlü Çikolata 60 G", 30.0),
    ("a101", "Eti Sütlü Çikolata 60 G", 28.0),
    ("sok", "Torku Sütlü Çikolata 60 G", 29.0),
)]


def test_kahve_aramasi_yan_urunleri_almaz_ve_cesit_sunar():
    r = k.karsilastir("kahve", KAHVE)
    adlar = {u["ad"] for u in r["urunler"]}
    assert not any("Beyazlatıcı" in a or "Çikolata" in a for a in adlar), adlar
    assert r["toplam"] == 7
    cesit = {c["id"]: c for c in r["cesitler"]}
    assert cesit["turk"]["ad"] == "Türk Kahvesi" and cesit["turk"]["adet"] == 3
    assert cesit["filtre"]["ad"] == "Filtre Kahve" and "keyfe" not in cesit   # ilk kelime marka
    f = k.karsilastir("kahve", KAHVE, cesit="filtre")
    assert f["cesit"] == "filtre" and f["toplam"] == 3 and all("Filtre" in u["ad"] for u in f["urunler"])
    assert k.karsilastir("kahve", KAHVE, cesit="olmayan")["cesit"] is None      # bilinmeyen çeşit yok sayılır
    ck = k.karsilastir("çikolata", KAHVE)
    assert "Karmen Çikolata Gofret 38 g" not in {u["ad"] for u in ck["urunler"]} and ck["toplam"] == 5
    assert k.karsilastir("gofret", KAHVE)["toplam"] == 1                      # aranan türse elenmez


EKMEK = [{"market": m, "name": ad, "price": fiyat} for m, ad, fiyat in (
    ("sok", "Uno Anadolu Tost Ekmeği 550 g", 50.0),               # ünsüz yumuşaması: ekmek -> ekmeği
    ("migros", "Uno Büyük Tost Ekmeği 550 G", 55.0),
    ("a101", "Nimet Tost Ekmek 550 G", 40.0),
    ("a101", "Nimet Tam Buğday Ekmeği 350 G", 35.0),
    ("sok", "Uno Anadolu Tam Buğday Ekmeği 350 g", 45.0),
    ("migros", "İhe Tam Buğday Ekmeği 400 G", 60.0),
    ("migros", "İyilik Çavdarlı Ekmek 400 G", 63.0),
    ("migros", "Untad Çavdar Ekmeği 500 G", 120.0),
    ("sok", "Uno Anadolu Çavdarlı Tava Ekmegi 450 g", 82.0),
    ("migros", "Schar Mix B Glutensiz Ekmek Unu 1 Kg", 300.0),     # un, ekmek değil
    ("a101", "Onefis Etli Ekmek Dondurulmuş 440 G", 150.0),        # yemek
    ("sok", "Ülker Sürmix Ekmek Üstü Peynirli Çikolatalı Sürme 180 g", 60.0),
)]


def test_ekmek_cesitleri_ve_ekmek_unu():
    r = k.karsilastir("ekmek", EKMEK)
    adlar = {u["ad"] for u in r["urunler"]}
    assert "Uno Anadolu Tost Ekmeği 550 g" in adlar
    assert not any(x in a for a in adlar for x in ("Unu", "Etli", "Sürme")), adlar
    assert r["toplam"] == 9
    cesit = {c["id"]: c for c in r["cesitler"]}
    assert cesit["tost"]["adet"] == 3
    assert cesit["tam bugday"]["ad"] == "Tam Buğday Ekmeği" and cesit["tam bugday"]["adet"] == 3
    assert cesit["cavdar"]["adet"] == 3                     # Çavdar + Çavdarlı tek çeşit
    assert {u["ad"] for u in k.karsilastir("ekmek", EKMEK, cesit="cavdar")["urunler"]} == {
        "İyilik Çavdarlı Ekmek 400 G", "Untad Çavdar Ekmeği 500 G", "Uno Anadolu Çavdarlı Tava Ekmegi 450 g"}
    assert k.karsilastir("ekmek", EKMEK, cesit="tam bugday")["toplam"] == 3
    assert k._kelime_var("ekmek", ["ekmegi"]) and not k._kelime_var("ekmek", ["ekmegin" + "x"])


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
        assert c.get("/karsilastir", params={"q": "süt", "cesit": "yok"}).json()["cesit"] is None
        r = c.post("/liste", json={"kalemler": ["süt", "yumurta"]})
        assert r.status_code == 200 and r.json()["oneri"]["tek"] is not None
        assert c.post("/liste", json={"kalemler": []}).status_code == 422
        # sadece seçilen marketler: A101 ve ŞOK seçilince Migros hiç önerilmez
        r = c.post("/liste", json={"kalemler": ["süt"], "marketler": ["a101", "sok"]}).json()
        assert {s["market"] for k in r["kalemler"] for s in k["secenekler"]} <= {"a101", "sok"}
        assert c.post("/liste", json={"kalemler": ["süt"], "marketler": ["metro"]}).status_code == 422
