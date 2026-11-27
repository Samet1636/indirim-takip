"""Beslenme planı sunucusunun (api/) testleri. Ağa çıkmaz; gerçek katalog yerine küçük bir dosya kullanır."""
from __future__ import annotations

import json
import time

import pytest
from fastapi.testclient import TestClient

from api import main
from api.isler import IsKuyrugu

KISI = dict(kilo=75, boy=178, yas=23, cinsiyet="erkek", aktivite="orta", hedef="koru")


@pytest.fixture(autouse=True)
def hesapsiz(monkeypatch):
    # Bilgisayarda Supabase ayarları tanımlı olsa bile testler ağa çıkmasın, hesapsız başlasın
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_ANON_KEY", raising=False)


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
    # varsayılan: ülke genelindeki zincirler; bölgesel Hakmar / Tarım Kredi ancak seçilirse
    assert gelen["marketler"] == {"migros", "sok", "a101", "bim", "carrefour"}
    r = istemci.post("/plan", json={**KISI, "marketler": ["hakmar", "migros"]})
    assert bekle(istemci, r.json()["is_id"]) and gelen["marketler"] == {"hakmar", "migros"}
    # tanımsız ekipman / market reddedilir
    assert istemci.post("/plan", json={**KISI, "ekipman": ["kazan"]}).status_code == 422
    assert istemci.post("/plan", json={**KISI, "marketler": ["metro"]}).status_code == 422


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


def test_kisi_basi_plan_siniri(istemci, monkeypatch):
    import threading
    kapi = threading.Event()

    def yavas_coz(*a, **k):
        kapi.wait(5)
        return {"durum": "Optimal", "plan": [], "alisveris": [], "toplam_tl": 0}
    monkeypatch.setattr(main.plan, "coz", yavas_coz)
    monkeypatch.setattr(main, "IP_SAATLIK_PLAN", 2)
    ip_a = {"X-Forwarded-For": "1.1.1.1"}
    ilk = istemci.post("/plan", json=KISI, headers=ip_a)
    assert ilk.status_code == 202
    # aynı kişi, ilki bitmeden ikinci plan isteyemez
    r = istemci.post("/plan", json=KISI, headers=ip_a)
    assert r.status_code == 429 and "Zaten" in r.json()["detail"]
    # başka biri isteyebilir
    assert istemci.post("/plan", json=KISI, headers={"X-Forwarded-For": "2.2.2.2"}).status_code == 202
    kapi.set()
    bekle(istemci, ilk.json()["is_id"])
    ikinci = istemci.post("/plan", json=KISI, headers=ip_a)                   # 2. plan (saatlik sınır 2)
    assert ikinci.status_code == 202
    bekle(istemci, ikinci.json()["is_id"])
    r = istemci.post("/plan", json=KISI, headers=ip_a)                        # 3. plan: saatlik sınır
    assert r.status_code == 429 and "Bir saatte en fazla 2 plan" in r.json()["detail"], r.json()


class SahteHesap:
    """Supabase yerine: 'iyi' ve 'diger' geçerli oturumlar, plan zamanları bellekte."""
    def __init__(self):
        self.kayit = {"iyi": [], "diger": []}

    def kullanici(self, token):
        return {"id": f"u-{token}", "email": f"{token}@ornek.com"} if token in self.kayit else None

    def kullanimlar(self, token, gun=7):
        from datetime import datetime, timedelta, timezone
        sinir = datetime.now(timezone.utc) - timedelta(days=gun)
        return [t for t in self.kayit[token] if t >= sinir]

    def kullanim_ekle(self, token):
        from datetime import datetime, timezone
        self.kayit[token].append(datetime.now(timezone.utc))


def test_hesap_ve_haftalik_hak(istemci, monkeypatch):
    sahte = SahteHesap()
    istemci.app.state.hesap = sahte
    sonuclar = iter([{"durum": "Yetersiz tarif", "yetersiz": ["ana"]},             # plan çıkmadı: hak düşmez
                     {"durum": "Optimal", "plan": [{"gun": "Pzt"}], "alisveris": []},
                     {"durum": "Optimal", "plan": [{"gun": "Pzt"}], "alisveris": []}])
    monkeypatch.setattr(main.plan, "coz", lambda *a, **k: next(sonuclar))
    iyi = {"Authorization": "Bearer iyi"}
    assert istemci.post("/plan", json=KISI).status_code == 401                       # giriş yok
    r = istemci.post("/plan", json=KISI, headers={"Authorization": "Bearer sahte"})
    assert r.status_code == 401 and "tekrar giriş" in r.json()["detail"]
    assert istemci.get("/hak", headers=iyi).json() == {"hesap_gerekli": True, "haftalik": 1, "kalan": 1,
                                                       "yenilenme": None, "yenilenme_metni": None}
    bekle(istemci, istemci.post("/plan", json=KISI, headers=iyi).json()["is_id"])
    assert sahte.kayit["iyi"] == []                                                   # yetersiz tarif: hak duruyor
    s = bekle(istemci, istemci.post("/plan", json=KISI, headers=iyi).json()["is_id"])
    assert s["durum"] == "bitti" and len(sahte.kayit["iyi"]) == 1
    r = istemci.post("/plan", json=KISI, headers=iyi)                                # bu hafta ikinci plan yok
    assert r.status_code == 403 and "Bu haftaki ücretsiz planını kullandın" in r.json()["detail"]
    h = istemci.get("/hak", headers=iyi).json()
    assert h["kalan"] == 0 and h["yenilenme"] and h["yenilenme_metni"]
    # başka bir kullanıcının hakkı etkilenmez
    assert istemci.post("/plan", json=KISI, headers={"Authorization": "Bearer diger"}).status_code == 202


def test_hak_durumu_ve_supabase_istekleri():
    from datetime import datetime, timedelta, timezone
    from api import hesap
    t = datetime(2026, 11, 27, 9, 0, tzinfo=timezone.utc)
    d = hesap.hak_durumu([t], 1)
    assert d["kalan"] == 0 and d["yenilenme"].startswith("2026-12-04") and d["yenilenme_metni"] == "4 Aralık 12:00"
    assert hesap.hak_durumu([], 1)["kalan"] == 1 and hesap.hak_durumu([t], 2)["kalan"] == 1

    class Cevap:
        def __init__(self, kod, govde=None):
            self.status_code, self._g = kod, govde

        def json(self):
            return self._g

    class SahteHttp:
        def __init__(self):
            self.istekler = []

        def get(self, url, headers, timeout, params=None):
            self.istekler.append(("GET", url, headers, params))
            if url.endswith("/auth/v1/user"):
                return Cevap(200, {"id": "abc", "email": "a@b.c"}) if headers["Authorization"] == "Bearer iyi" else Cevap(401)
            return Cevap(200, [{"olusturma": "2026-11-27T09:00:00+00:00"}])

        def post(self, url, json, timeout, headers):
            self.istekler.append(("POST", url, headers, json))
            return Cevap(201)

    http = SahteHttp()
    h = hesap.SupabaseHesap("https://proje.supabase.co/", "acik-anahtar", oturum=http)
    assert h.kullanici("iyi") == {"id": "abc", "email": "a@b.c"} and h.kullanici("kotu") is None
    h.kullanici("iyi")
    assert sum(1 for i in http.istekler if i[1].endswith("/user")) == 2               # 'iyi' önbellekten
    assert h.kullanimlar("iyi") == [t]
    h.kullanim_ekle("iyi")
    yontem, url, basliklar, _ = http.istekler[-1]
    assert yontem == "POST" and url == "https://proje.supabase.co/rest/v1/plan_kullanim"
    assert basliklar["apikey"] == "acik-anahtar" and basliklar["Authorization"] == "Bearer iyi"


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
