"""Tarif veritabanının tutarlılık testleri."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "beslenme"))
import tarif_ozet  # noqa: E402


def test_tarifler_tutarli():
    malz, tarifler = tarif_ozet.yukle()
    assert tarif_ozet.kontrol(malz, tarifler) == []
    for ogun in ("kahvalti", "ana", "yan", "ara"):
        assert any(ogun in t["ogunler"] for t in tarifler)


def test_besin_hesabi_ve_etiketler():
    malz, tarifler = tarif_ozet.yukle()
    t = {x["id"]: x for x in tarifler}
    menemen = tarif_ozet.besin(t["menemen"], malz)
    assert 300 < menemen["kcal"] < 450
    assert tarif_ozet.besin(t["menemen"], malz, 1.5)["kcal"] == round(menemen["kcal"] * 1.5, 1)
    assert "vegan" in tarif_ozet.etiketler(t["mercimek_corbasi"], malz)
    assert "vejetaryen" not in tarif_ozet.etiketler(t["tavuk_sote"], malz)
    assert "yuksek_protein" in tarif_ozet.etiketler(t["tavuk_sote"], malz)
