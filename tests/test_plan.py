"""Kalori hedefi ve haftalık plan modelinin testleri (sahte fiyatlarla, hızlı)."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "beslenme"))
import plan  # noqa: E402
from hedef import hesapla  # noqa: E402


def test_hedef_hesabi_ve_guvenlik():
    h = hesapla(kilo=75, boy=178, yas=23, cinsiyet="erkek", aktivite="orta", hedef="koru")
    assert h.bazal == 1752 and h.kcal == 2716
    kadin = hesapla(kilo=50, boy=155, yas=40, cinsiyet="kadin", aktivite="hareketsiz", hedef="kilo_ver")
    assert kadin.kcal >= 1200 and kadin.kcal >= kadin.bazal       # alt sınırların altına inmez
    with pytest.raises(ValueError):
        hesapla(kilo=50, boy=160, yas=16, cinsiyet="kadin")


def test_plan_kisitlari(monkeypatch):
    def sahte_adaylar(katalog, malzemeler, marketler, her_market=3):
        out = {}
        for mid in malzemeler:
            out[mid] = [{"market": m, "name": f"{mid} Kg", "price": fiyat, "miktar_g": 1000.0,
                         "tl_kg": fiyat, "acik_satis": True, "regular_price": None}
                        for m, fiyat in (("sok", 100.0), ("migros", 120.0))]
        return out
    monkeypatch.setattr(plan, "urun_adaylari", sahte_adaylar)
    kisi = dict(kilo=75, boy=178, yas=23, cinsiyet="erkek", aktivite="orta", hedef="koru")
    s = plan.coz([], kisi, max_market=1, sure_siniri=30)
    assert s["durum"] in ("Optimal", "Not Solved") and len(s["plan"]) == 7
    h = s["hedef"]
    sayac = {}
    for gun in s["plan"]:
        assert h["kcal"] * 0.93 - 1 <= gun["toplam"]["kcal"] <= h["kcal"] * 1.07 + 1
        assert gun["toplam"]["protein"] >= h["protein_min"] - 1
        turler = [o["ogun"] for o in gun["ogunler"]]
        assert {"kahvalti", "ogle", "aksam"} <= set(turler)
        for o in gun["ogunler"]:
            sayac[o["tarif"]] = sayac.get(o["tarif"], 0) + 1
    assert max(sayac.values()) <= 2                     # çeşitlilik
    tarif = {t["id"]: t for t in plan.tarif_ozet.yukle()[1]}
    for gun in s["plan"]:                               # öğle + akşamda aynı ana malzeme yok
        ana = [o["tarif"] for o in gun["ogunler"] if o["ogun"] in ("ogle", "aksam")]
        for b in plan.BAZ_MALZEME:
            assert sum(any(x["malzeme"] == b for x in tarif[t]["malzemeler"]) for t in ana) <= 1, (gun["gun"], b)
    assert s["marketler"] == ["sok"]                    # tek market ve ucuz olanı
    # tartıyla satılanlar: en az 250 g, 50 g'lık adımlarla (markette 50 g sarımsak alınmaz)
    for x in s["alisveris"]:
        assert x["birim"] == "kg" and x["adet"] >= 0.25 - 1e-9, x
        assert abs(x["adet"] * 20 - round(x["adet"] * 20)) < 1e-6, x
    # tarif detayları uygulama için döner
    for tid in sayac:
        d = s["tarifler"][tid]
        assert d["adimlar"] and d["malzemeler"] and d["ekipman"]


def test_tarif_tercih_suzgeci():
    malz, tarifler = plan.tarif_ozet.yukle()
    hepsi = plan.tarif_sec(tarifler, malz)
    # sadece mikrodalga: ocak isteyen tarifler elenir, pişirmesizler kalır
    mikro = plan.tarif_sec(tarifler, malz, ekipman=["mikrodalga"])
    assert "menemen" not in mikro and "gece_yulafi" in mikro and "yulaf_lapasi" in mikro
    # airfryer, fırın alternatifi olan tarifi açar
    assert "izmir_kofte" in plan.tarif_sec(tarifler, malz, ekipman=["ocak", "airfryer"])
    assert "izmir_kofte" not in plan.tarif_sec(tarifler, malz, ekipman=["ocak"])
    # alerjen ve istenmeyen malzeme
    assert all("yumurta" not in plan.tarif_ozet.alerjenler(t) for t in
               plan.tarif_sec(tarifler, malz, alerjen=["yumurta"]).values())
    assert "kuru_fasulye" not in plan.tarif_sec(tarifler, malz, haric_malzeme=["kuru_fasulye"])
    assert all(t["sure_dk"] <= 15 for t in plan.tarif_sec(tarifler, malz, max_sure=15).values())
    assert len(hepsi) == len(tarifler)


def test_adaylarda_ucuz_kucuk_paket_var():
    katalog = [{"market": "migros", "name": f"Bal {g} G", "price": fiyat, "category": "Çiçek Balı"}
               for g, fiyat in ((850, 360.0), (1000, 400.0), (2000, 780.0), (460, 230.0), (225, 150.0), (300, 140.0))]
    adlar = {p["name"] for p in plan.urun_adaylari(katalog, {"bal"}, None, her_market=2)["bal"]}
    assert "Bal 300 G" in adlar          # paket fiyatı en düşük
    assert "Bal 225 G" not in adlar      # 300 g daha büyük ve daha ucuz: 225 g'a hiç gerek yok
    katalog[4]["price"] = 120.0          # 225 g artık en ucuz paket -> kalır
    plan._ADAY_ONBELLEK.clear()
    adlar = {p["name"] for p in plan.urun_adaylari(katalog, {"bal"}, None, her_market=2)["bal"]}
    assert "Bal 225 G" in adlar and "Bal 300 G" not in adlar


def test_sure_dolsa_da_sepet_sisirilmez(monkeypatch):
    # Çözücü 2 saniyede kesilse bile (zayıf sunucu) alışveriş listesi ihtiyacı aşan paket içermemeli
    def sahte_adaylar(katalog, malzemeler, marketler, her_market=3):
        return {mid: [{"market": "sok", "name": f"{mid} 500 g", "price": 50.0, "miktar_g": 500.0, "tl_kg": 100.0,
                       "acik_satis": False, "regular_price": None}] for mid in malzemeler}
    monkeypatch.setattr(plan, "urun_adaylari", sahte_adaylar)
    kisi = dict(kilo=75, boy=178, yas=23, cinsiyet="erkek", aktivite="orta", hedef="koru")
    s = plan.coz([], kisi, max_market=1, sure_siniri=2)
    if "plan" not in s:
        return                                           # 2 sn'de çözüm bulunamadıysa sınanacak sepet yok
    malz, tarifler = plan.tarif_ozet.yukle()
    tarif = {t["id"]: t for t in tarifler}
    ihtiyac = {}
    for gun in s["plan"]:
        for o in gun["ogunler"]:
            for x in tarif[o["tarif"]]["malzemeler"]:
                ihtiyac[malz[x["malzeme"]]["ad"]] = ihtiyac.get(malz[x["malzeme"]]["ad"], 0) + x["gram"] * o["porsiyon"]
    for x in s["alisveris"]:
        assert x["adet"] * 500 < ihtiyac[x["malzeme"]] + 500 + 25, x     # en fazla 1 paket yuvarlama payı


def test_urunu_olmayan_malzeme_plani_bozmaz(monkeypatch):
    # 18.11.2026 bulut hatası: bir malzemenin katalogda hiç ürünü yoksa min() boş listede çöküyordu
    def eksikli_adaylar(katalog, malzemeler, marketler, her_market=3):
        return {mid: [{"market": "sok", "name": f"{mid} Kg", "price": 100.0, "miktar_g": 1000.0, "tl_kg": 100.0,
                       "acik_satis": True, "regular_price": None}]
                for mid in malzemeler if mid not in ("eriste", "kinoa", "lavas")}
    monkeypatch.setattr(plan, "urun_adaylari", eksikli_adaylar)
    kisi = dict(kilo=75, boy=178, yas=23, cinsiyet="erkek", aktivite="orta", hedef="koru")
    s = plan.coz([], kisi, max_market=1, sure_siniri=20)
    assert "plan" in s, s
    malz, tarifler = plan.tarif_ozet.yukle()
    tarif = {t["id"]: t for t in tarifler}
    for gun in s["plan"]:                                # fiyatı olmayan malzemeli tarif plana girmez
        for o in gun["ogunler"]:
            assert not {"eriste", "kinoa", "lavas"} & {x["malzeme"] for x in tarif[o["tarif"]]["malzemeler"]}


def test_urun_adaylari_bos_malzemeyi_atlar():
    sonuc = plan.urun_adaylari([{"market": "sok", "name": "Domates Kg", "price": 30.0, "category": None}],
                               {"domates", "eriste"}, None)
    assert "domates" in sonuc and "eriste" not in sonuc


def test_tek_ekipmanla_plan_cikabilir():
    # Sadece airfryer ya da sadece fırın (vejetaryen + 30 dk dahil) haftayı dolduracak kadar tarif bırakmalı
    malz, tarifler = plan.tarif_ozet.yukle()
    for ekipman in (["airfryer"], ["firin"]):
        for paket in ("ekonomik", "vejetaryen"):
            T = plan.tarif_sec(tarifler, malz, paket=paket, ekipman=ekipman, max_sure=30)
            assert plan.yetersiz_turler(T) == [], (ekipman, paket)
            assert sum("ana" in t["ogunler"] for t in T.values()) >= 10, (ekipman, paket)


def test_yetersiz_tarif_hemen_doner():
    kisi = dict(kilo=75, boy=178, yas=23, cinsiyet="erkek", aktivite="orta", hedef="koru")
    s = plan.coz([], kisi, ekipman=["mikrodalga"])           # ana yemek yapılamaz
    assert s["durum"] == "Yetersiz tarif" and "ana" in s["yetersiz"] and "plan" not in s
