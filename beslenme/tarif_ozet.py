"""
Tarifleri kontrol eder ve her tarifin 1 porsiyonluk besin değerini malzemelerden hesaplar.
Etiketler (vejetaryen, vegan, yüksek protein, pratik) de buradan otomatik çıkar.

    python beslenme/tarif_ozet.py        -> tabloyu yazdırır, beslenme/tarifler_ozet.csv üretir
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

KLASOR = Path(__file__).parent
ET_BALIK = {"et", "balik"}
HAYVANSAL = {"et", "balik", "hayvansal", "sut_urunu"}
HAYVANSAL_EK = {"tereyagi", "bal"}


def yukle():
    malz = {m["id"]: m for m in json.loads((KLASOR / "malzemeler.json").read_text(encoding="utf-8"))}
    tarifler = json.loads((KLASOR / "tarifler.json").read_text(encoding="utf-8"))
    return malz, tarifler


def besin(tarif: dict, malz: dict, porsiyon: float = 1.0) -> dict:
    top = {"kcal": 0.0, "protein": 0.0, "karb": 0.0, "yag": 0.0, "lif": 0.0}
    for x in tarif["malzemeler"]:
        m = malz[x["malzeme"]]
        for k in top:
            top[k] += m[k] * x["gram"] / 100 * porsiyon
    return {k: round(v, 1) for k, v in top.items()}


def etiketler(tarif: dict, malz: dict) -> list[str]:
    kategoriler = {malz[x["malzeme"]]["kategori"] for x in tarif["malzemeler"]}
    idler = {x["malzeme"] for x in tarif["malzemeler"]}
    b = besin(tarif, malz)
    e = []
    if not kategoriler & ET_BALIK:
        e.append("vejetaryen")
        if not kategoriler & HAYVANSAL and not idler & HAYVANSAL_EK:
            e.append("vegan")
    if b["kcal"] and b["protein"] * 4 / b["kcal"] >= 0.25:
        e.append("yuksek_protein")
    if tarif["sure_dk"] <= 20:
        e.append("pratik")
    return e


def kontrol(malz: dict, tarifler: list) -> list[str]:
    hatalar, idler = [], set()
    for t in tarifler:
        if t["id"] in idler:
            hatalar.append(f"tekrar eden tarif id: {t['id']}")
        idler.add(t["id"])
        for x in t["malzemeler"]:
            if x["malzeme"] not in malz:
                hatalar.append(f"{t['id']}: bilinmeyen malzeme {x['malzeme']}")
            if x["gram"] <= 0:
                hatalar.append(f"{t['id']}: {x['malzeme']} gramı pozitif olmalı")
        if not set(t["ogunler"]) <= {"kahvalti", "ana", "ara", "yan"}:
            hatalar.append(f"{t['id']}: geçersiz öğün {t['ogunler']}")
    return hatalar


def main():
    malz, tarifler = yukle()
    hatalar = kontrol(malz, tarifler)
    if hatalar:
        raise SystemExit("\n".join(hatalar))
    satirlar = []
    for t in tarifler:
        b = besin(t, malz)
        satirlar.append({"id": t["id"], "ad": t["ad"], "ogunler": "/".join(t["ogunler"]),
                         "sure_dk": t["sure_dk"], **b, "etiketler": ", ".join(etiketler(t, malz))})
    with open(KLASOR / "tarifler_ozet.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(satirlar[0]), delimiter=";")
        w.writeheader()
        w.writerows(satirlar)
    for ogun in ("kahvalti", "ana", "yan", "ara"):
        print(f"\n== {ogun.upper()} ==")
        for s in satirlar:
            if s["ogunler"].split("/")[0] == ogun:
                print(f"  {s['ad'][:32]:32} {s['kcal']:6.0f} kcal  P{s['protein']:5.1f}  K{s['karb']:5.1f}  "
                      f"Y{s['yag']:5.1f}  {s['sure_dk']:3d} dk  {s['etiketler']}")
    print(f"\n{len(tarifler)} tarif, {len(malz)} malzeme. Özet: beslenme/tarifler_ozet.csv")


if __name__ == "__main__":
    main()
