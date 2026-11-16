"""
Tarif kitabı: tüm tariflerin özeti (süre, kalori, porsiyon maliyeti) ve tek tarif detayı.

Porsiyon maliyeti: her malzemenin bugünkü en ucuz kilo fiyatıyla (hangi marketteyse) gramı kadar.
Yani "bu tarifin malzemesi şu an en ucuz kaça gelir" tahmini; paket artığı sayılmaz.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List, Optional

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "beslenme"))
import plan  # noqa: E402
import tarif_ozet  # noqa: E402
from eslestirme_kurallari import K  # noqa: E402

_ONBELLEK: Dict[str, object] = {}


def _katalog_anahtari(katalog: List[dict]):
    return (id(katalog), len(katalog), katalog[0].get("name") if katalog else None)


def _en_ucuz(mid: str, katalog: List[dict]) -> Optional[dict]:
    if mid not in K:
        return None
    c = plan._adaylar_onbellekli(mid, katalog)      # kg fiyatına göre sıralı
    return c[0] if c else None


def _ozet(t: dict, malz: dict, katalog: List[dict]) -> dict:
    maliyet, eksik = 0.0, 0
    for x in t["malzemeler"]:
        if malz[x["malzeme"]]["dolapta"]:
            continue
        e = _en_ucuz(x["malzeme"], katalog)
        if e:
            maliyet += e["tl_kg"] / 1000 * x["gram"]
        else:
            eksik += 1
    return {"id": t["id"], "ad": t["ad"], "ogunler": t["ogunler"], "sure_dk": t["sure_dk"],
            "besin": tarif_ozet.besin(t, malz), "etiketler": tarif_ozet.etiketler(t, malz),
            "alerjenler": tarif_ozet.alerjenler(t), "ekipman": t.get("ekipman", [["ocak"]]),
            "porsiyon_tl": round(maliyet, 2), "fiyati_bilinmeyen": eksik,
            "malzeme_sayisi": sum(1 for x in t["malzemeler"] if not malz[x["malzeme"]]["dolapta"])}


def ozetler(katalog: List[dict]) -> List[dict]:
    """Tüm tariflerin özeti. Katalog değişmedikçe sonuç saklanır."""
    anahtar = _katalog_anahtari(katalog)
    if _ONBELLEK.get("anahtar") != anahtar:
        malz, tarifler = tarif_ozet.yukle()
        _ONBELLEK["anahtar"] = anahtar
        _ONBELLEK["ozetler"] = [_ozet(t, malz, katalog) for t in tarifler]
    return _ONBELLEK["ozetler"]  # type: ignore[return-value]


def detay(tarif_id: str, katalog: List[dict]) -> Optional[dict]:
    malz, tarifler = tarif_ozet.yukle()
    t = next((x for x in tarifler if x["id"] == tarif_id), None)
    if t is None:
        return None
    malzemeler = []
    for x in t["malzemeler"]:
        m = malz[x["malzeme"]]
        e = None if m["dolapta"] else _en_ucuz(x["malzeme"], katalog)
        malzemeler.append({
            "id": x["malzeme"], "ad": m["ad"], "gram": x["gram"], "dolapta": m["dolapta"],
            # alışveriş listesine eklerken kullanılacak kelime ve (yumurta gibi) adet gramı
            "liste_terimi": (m.get("arama") or [m["ad"]])[0],
            "adet_g": K.get(x["malzeme"], {}).get("adet_g"),
            "en_ucuz": {"market": e["market"], "ad": e["name"], "fiyat": e["price"], "tl_kg": e["tl_kg"],
                        "url": e.get("url")} if e else None,
            "tutar": round(e["tl_kg"] / 1000 * x["gram"], 2) if e else None,
        })
    return {**_ozet(t, malz, katalog), "adimlar": t["adimlar"], "porsiyon_araligi": t["porsiyon_araligi"],
            "malzemeler": malzemeler}
