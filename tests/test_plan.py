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
    assert s["marketler"] == ["sok"]                    # tek market ve ucuz olanı
