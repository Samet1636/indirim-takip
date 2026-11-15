"""
Malzemeleri market ürünleriyle eşleştirir, birim fiyat (TL/kg) ve tarif maliyetlerini hesaplar.

    python beslenme/eslestirme.py data/katalog.json
        -> beslenme/fiyatlar.json      (malzeme başına market market en ucuz ürün)
        -> beslenme/tarif_maliyet.csv  (tarif başına porsiyon maliyeti)
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from eslestirme_kurallari import K, ORTAK_HARIC  # noqa: E402
from miktar import norm, parse_quantity  # noqa: E402
import tarif_ozet  # noqa: E402

KLASOR = Path(__file__).parent


def adaylar(malzeme_id: str, katalog: list[dict]) -> list[dict]:
    """Bir malzemeye uyan ürünleri, gram başına fiyatlarıyla döndürür."""
    k = K[malzeme_id]
    ad_re = [re.compile(p) for p in k["ad"]]
    # norm() baştaki/sondaki boşluğu siler; "un " gibi kelime sınırı için konmuş boşluklar korunmalı
    # (yoksa "un" -> "Uno Tam Buğday Ekmeği" de elenir)
    haric = [(" " if h.startswith(" ") else "") + norm(h) + (" " if h.endswith(" ") else "")
             for h in k.get("haric", [])] + ORTAK_HARIC
    migros_kat = {norm(c) for c in k.get("migros", [])}
    out = []
    for p in katalog:
        n = norm(p["name"]) + " "
        if not any(r.search(n) for r in ad_re) or any(h in n for h in haric):
            continue
        if p["market"] == "migros" and migros_kat and norm(p.get("category") or "") not in migros_kat:
            continue
        q, birim = parse_quantity(p["name"])
        if k.get("kati") and birim == "ml":
            continue                      # sebze/meyve: litreyle satılan şey meyve suyudur
        if birim == "ml":
            q = q * k.get("yogunluk", 1.0)
        elif birim == "adet":
            if not k.get("adet_g"):
                continue
            q = q * k["adet_g"]
        elif q is None:
            if not k.get("tek_g"):
                continue
            q = k["tek_g"]
        if not q or q <= 0 or not p.get("price"):
            continue
        out.append({**p, "miktar_g": round(q, 1), "tl_kg": round(p["price"] / q * 1000, 2)})
    return sorted(out, key=lambda x: x["tl_kg"])


def fiyat_tablosu(katalog: list[dict]) -> dict:
    tablo = {}
    for mid in K:
        c = adaylar(mid, katalog)
        marketler = {}
        for p in c:
            marketler.setdefault(p["market"], p)       # her marketin en ucuzu
        tablo[mid] = {
            "aday_sayisi": len(c),
            "en_ucuz": c[0] if c else None,
            "marketler": marketler,
            "ilk5": [{k: p[k] for k in ("market", "name", "price", "miktar_g", "tl_kg")} for p in c[:5]],
        }
    return tablo


def tarif_maliyetleri(tablo: dict) -> list[dict]:
    malz, tarifler = tarif_ozet.yukle()
    satirlar = []
    for t in tarifler:
        toplam, eksik = 0.0, []
        for x in t["malzemeler"]:
            if malz[x["malzeme"]]["dolapta"]:
                continue
            e = tablo.get(x["malzeme"], {}).get("en_ucuz")
            if not e:
                eksik.append(x["malzeme"])
                continue
            toplam += e["tl_kg"] / 1000 * x["gram"]
        b = tarif_ozet.besin(t, malz)
        satirlar.append({"id": t["id"], "ad": t["ad"], "ogunler": "/".join(t["ogunler"]),
                         "porsiyon_tl": round(toplam, 2), "kcal": b["kcal"], "protein": b["protein"],
                         "tl_100kcal": round(toplam / b["kcal"] * 100, 2) if b["kcal"] else None,
                         "eksik_fiyat": ", ".join(eksik)})
    return satirlar


def main(katalog_yolu: str):
    katalog = json.loads(Path(katalog_yolu).read_text(encoding="utf-8"))
    tablo = fiyat_tablosu(katalog)
    (KLASOR / "fiyatlar.json").write_text(json.dumps(tablo, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{'MALZEME':18} {'ADAY':>5}  {'TL/kg':>8}  EN UCUZ ÜRÜN")
    for mid, v in tablo.items():
        e = v["en_ucuz"]
        print(f"{mid:18} {v['aday_sayisi']:5d}  {e['tl_kg'] if e else '-':>8}  "
              f"{(e['market'] + ' | ' + e['name'])[:60] if e else 'BULUNAMADI'}")
    satirlar = tarif_maliyetleri(tablo)
    with open(KLASOR / "tarif_maliyet.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(satirlar[0]), delimiter=";")
        w.writeheader()
        w.writerows(satirlar)
    print("\nPORSİYON MALİYETLERİ")
    for s in sorted(satirlar, key=lambda s: s["porsiyon_tl"]):
        print(f"  {s['ad'][:34]:34} {s['porsiyon_tl']:7.2f} TL  {s['kcal']:5.0f} kcal  "
              f"{s['tl_100kcal']} TL/100kcal  {s['eksik_fiyat']}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "data/katalog.json")
