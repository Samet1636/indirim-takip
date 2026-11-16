"""Beslenme planı sunucusunun (api/) testleri. Ağa çıkmaz; gerçek katalog yerine küçük bir dosya kullanır."""
from __future__ import annotations

import json
import time

import pytest
from fastapi.testclient import TestClient

from api import main
from api.isler import IsKuyrugu

KISI = dict(kilo=75, boy=178, yas=23, cinsiyet="erkek", aktivite="orta", hedef="koru")


@pytest.fixture
def istemci(tmp_path, monkeypatch):
    katalog = tmp_path / "katalog.json"
    katalog.write_text(json.dumps([{"market": "sok", "name": "Domates Kg", "price": 30.0}], ensure_ascii=False),
                       encoding="utf-8")
    monkeypatch.setenv("KATALOG_YOLU", str(katalog))
    with TestClient(main.uygulama_olustur()) as c:
        yield c


def bekle(c, is_id, sure=60):
    son = time.time() + sure
    while time.time() < son:
        r = c.get(f"/plan/{is_id}").json()
        if r["durum"] in ("bitti", "hata"):
            return r
        time.sleep(0.05)
    raise AssertionError("iş zamanında bitmedi")


def test_saglik(istemci):
    assert istemci.get("/saglik").json() == {"durum": "ok", "katalog_urun_sayisi": 1}


def test_urun_arama(tmp_path, monkeypatch):
    katalog = tmp_path / "katalog.json"
    katalog.write_text(json.dumps([
        {"market": "sok", "name": "Mis Süt 1 L", "price": 36.0, "discount_pct": None},
        {"market": "migros", "name": "SÜTAŞ Süt 1 L", "price": 40.0, "discount_pct": 10},
        {"market": "migros", "name": "Pınar Ayran", "price": 20.0, "discount_pct": None},
    ], ensure_ascii=False), encoding="utf-8")
    monkeypatch.setenv("KATALOG_YOLU", str(katalog))
    with TestClient(main.uygulama_olustur()) as c:
        r = c.get("/urunler", params={"q": "sut"}).json()                 # ü/Ü farkı önemsiz
        assert r["toplam"] == 2 and [p["price"] for p in r["urunler"]] == [36.0, 40.0]
        assert c.get("/urunler", params={"q": "süt", "market": "migros"}).json()["toplam"] == 1
        assert c.get("/urunler", params={"siralama": "indirim"}).json()["urunler"][0]["discount_pct"] == 10
        r = c.get("/urunler", params={"adet": 2, "sayfa": 2}).json()
        assert r["toplam"] == 3 and len(r["urunler"]) == 1


def test_hedef_ve_guvenlik(istemci):
    r = istemci.post("/hedef", json=KISI)
    assert r.status_code == 200
    assert r.json()["hedef"]["kcal"] == 2716 and "tıbbi tavsiye değildir" in r.json()["not"]
    r = istemci.post("/hedef", json={**KISI, "yas": 16})                  # 18 yaş altı -> Türkçe hata
    assert r.status_code == 422 and "18 yaş" in r.json()["detail"]
    assert istemci.post("/hedef", json={**KISI, "cinsiyet": "x"}).status_code == 422
    assert istemci.post("/hedef", json={**KISI, "kilo": 10}).status_code == 422


def test_plan_isi_akisi(istemci, monkeypatch):
    gelen = {}

    def sahte_coz(katalog, kisi, paket, max_market, sure_siniri, **tercih):
        gelen.update(katalog=katalog, kisi=kisi, paket=paket, max_market=max_market, **tercih)
        return {"durum": "Optimal", "plan": [], "alisveris": [], "toplam_tl": 0}

    monkeypatch.setattr(main.plan, "coz", sahte_coz)
    r = istemci.post("/plan", json={**KISI, "paket": "vejetaryen", "market": 1, "ekipman": ["ocak", "airfryer"],
                                    "alerjen": ["gluten"], "max_sure": 30, "ara_ogun": 1})
    assert r.status_code == 202
    s = bekle(istemci, r.json()["is_id"])
    assert s["durum"] == "bitti" and s["sonuc"]["durum"] == "Optimal"
    assert "tıbbi tavsiye değildir" in s["sonuc"]["not"]
    assert gelen["paket"] == "vejetaryen" and gelen["max_market"] == 1 and gelen["kisi"]["kilo"] == 75
    assert gelen["katalog"][0]["name"] == "Domates Kg"
    assert gelen["ekipman"] == ["ocak", "airfryer"] and gelen["alerjen"] == ["gluten"]
    assert gelen["max_sure"] == 30 and gelen["ara_ogun"] == 1 and gelen["haric_malzeme"] == []
    # tanımsız ekipman reddedilir
    assert istemci.post("/plan", json={**KISI, "ekipman": ["kazan"]}).status_code == 422


def test_secenekler(istemci):
    r = istemci.get("/secenekler").json()
    assert {"ocak", "airfryer"} <= {e["id"] for e in r["ekipman"]}
    assert {"sut", "gluten"} <= {a["id"] for a in r["alerjen"]}
    assert any(m["id"] == "tavuk_gogus" for m in r["malzemeler"]) and r["tarif_sayisi"] >= 40


def test_plan_hatalari(istemci, monkeypatch):
    assert istemci.post("/plan", json={**KISI, "yas": 15}).status_code == 422    # kuyruğa hiç girmez
    assert istemci.post("/plan", json={**KISI, "market": 9}).status_code == 422
    assert istemci.get("/plan/yok").status_code == 404

    def patlayan(*a, **k):
        raise RuntimeError("çözücü bulunamadı")
    monkeypatch.setattr(main.plan, "coz", patlayan)
    s = bekle(istemci, istemci.post("/plan", json=KISI).json()["is_id"])
    assert s["durum"] == "hata" and "çözücü" not in s["hata"]                  # iç hata kullanıcıya sızmaz


def test_gercek_model_api_uzerinden(istemci, monkeypatch):
    """Gerçek MILP modeli (sahte fiyatlarla) API'den geçer ve sonuç JSON'a dönüşür."""
    def sahte_adaylar(katalog, malzemeler, marketler, her_market=3):
        return {mid: [{"market": "sok", "name": f"{mid} Kg", "price": 100.0, "miktar_g": 1000.0,
                       "tl_kg": 100.0, "acik_satis": True, "regular_price": None}] for mid in malzemeler}
    monkeypatch.setattr(main.plan, "urun_adaylari", sahte_adaylar)
    monkeypatch.setattr(main, "SURE_SINIRI", 30)
    s = bekle(istemci, istemci.post("/plan", json={**KISI, "market": 1}).json()["is_id"], sure=120)
    assert s["durum"] == "bitti", s
    assert len(s["sonuc"]["plan"]) == 7 and s["sonuc"]["marketler"] == ["sok"]


def test_katalog_urlden_gelir_ve_hata_toleransi(tmp_path):
    yerel = tmp_path / "katalog.json"
    yerel.write_text(json.dumps([{"market": "sok", "name": "Yerel", "price": 1.0}]), encoding="utf-8")
    k = main.Katalog(yerel, url="https://ornek.test/katalog.json", yenile_sn=3600)
    sayac = {"n": 0}

    def patlar():
        sayac["n"] += 1
        raise OSError("ağ yok")
    k._indir = patlar
    assert k.getir()[0]["name"] == "Yerel"            # indirilemezse yerel dosya
    assert k.getir()[0]["name"] == "Yerel" and sayac["n"] == 1   # hemen tekrar denemez (10 dk bekler)
    k._sonraki_deneme = 0                              # süre doldu say
    k._indir = lambda: [{"market": "a101", "name": "Uzak", "price": 2.0}]
    assert k.getir()[0]["name"] == "Uzak"
    k._indir = patlar                                  # sonraki yenileme başarısız -> eldeki uzak veri kalır
    k._sonraki_deneme = 0
    assert k.getir()[0]["name"] == "Uzak"


def test_kuyruk_doluysa_429(istemci, monkeypatch):
    monkeypatch.setattr(main, "EN_FAZLA_BEKLEYEN", 0)
    r = istemci.post("/plan", json=KISI)
    assert r.status_code == 429 and "tekrar dene" in r.json()["detail"]


def test_kuyruk_sira_ve_temizlik():
    k = IsKuyrugu()
    import threading
    kapi = threading.Event()
    ilk = k.gonder(lambda: kapi.wait(5) and {})
    ikinci = k.gonder(lambda: {})
    assert k.sira(ikinci) == 1
    kapi.set()
    for _ in range(100):
        if (k.getir(ikinci) or {}).get("durum") == "bitti":
            break
        time.sleep(0.02)
    assert k.getir(ilk)["durum"] == "bitti" and k.sira(ikinci) == 0
    k.kapat()
