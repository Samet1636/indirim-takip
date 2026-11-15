"""
Haftalık beslenme planı + en ucuz alışveriş listesi (karma tamsayılı doğrusal programlama).

Karar değişkenleri
  y[g,ö,t] ∈ {0,1}  : g. gün, ö. öğünde t tarifi var mı
  p[g,ö,t] ≥ 0      : kaç porsiyon (tarifin porsiyon aralığında)
  n[u]              : üründen kaç paket alınacak (açık satış/kg ürünlerde sürekli)
  z[m] ∈ {0,1}      : m marketine gidilecek mi
Amaç: alışveriş tutarı + gidilen market başına küçük bir ceza  ->  en küçük
Kısıtlar
  - her gün 1 kahvaltı, 1 öğle, 1 akşam ana yemeği; isteğe bağlı yan yemek ve en fazla 2 ara öğün
  - günlük kalori hedefin ±%7'si içinde, protein en az hedef, yağ en fazla hedef
  - bir tarif haftada en fazla 2 kez (çeşitlilik)
  - alınan paketler, haftalık malzeme ihtiyacını karşılamalı. Taze ürünlerde paket tam sayıdır
    (artan kısım israf olarak maliyete girer); kiler ürünlerinde (bakliyat, yağ, salça...) sadece
    kullanılan kısım maliyete girer, çünkü artanı sonraki haftalarda kullanılır
  - en fazla N market

Kullanım:
  python beslenme/plan.py --kilo 75 --boy 178 --yas 23 --cinsiyet erkek --aktivite orta --hedef koru
                          [--paket vejetaryen|yuksek_protein|pratik] [--market 2] [--katalog data/katalog.json]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import pulp

sys.path.insert(0, str(Path(__file__).parent))
import tarif_ozet  # noqa: E402
from eslestirme import adaylar  # noqa: E402
from eslestirme_kurallari import K  # noqa: E402
from hedef import hesapla  # noqa: E402
from miktar import norm  # noqa: E402

GUNLER = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
OGUNLER = {  # öğün yeri -> (uygun tarif türü, zorunlu mu)
    "kahvalti": ("kahvalti", True),
    "ogle": ("ana", True),
    "ogle_yan": ("yan", False),
    "aksam": ("ana", True),
    "aksam_yan": ("yan", False),
    "ara1": ("ara", False),
    "ara2": ("ara", False),
}
PAKETLER = {
    "ekonomik": dict(),
    "vejetaryen": dict(etiket="vejetaryen"),
    "yuksek_protein": dict(yuksek_protein=True),
    "pratik": dict(max_sure=25),
}


def urun_adaylari(katalog: list[dict], malzemeler: set[str], marketler: set[str] | None, her_market: int = 3):
    """Her malzeme için, her marketten en ucuz birkaç ürün (+ en küçük paket)."""
    out = {}
    for mid in malzemeler:
        if mid not in K:
            continue
        c = [p for p in adaylar(mid, katalog) if not marketler or p["market"] in marketler]
        secilen = []
        for m in {p["market"] for p in c}:
            mc = [p for p in c if p["market"] == m]
            secilen += mc[:her_market]
            kucuk = min(mc, key=lambda p: p["miktar_g"])
            if kucuk not in secilen:
                secilen.append(kucuk)
        for p in secilen:
            # adı rakam içermeyen "Kg" ürünleri tartıyla satılır -> istenen miktar kadar alınabilir
            p["acik_satis"] = p["miktar_g"] == 1000 and not re.search(r"\d", norm(p["name"]))
        out[mid] = secilen
    return out


def coz(katalog, kisi: dict, paket: str = "ekonomik", max_market: int = 2, market_ceza: float = 25.0,
        sure_siniri: int = 60, marketler: set[str] | None = None, stok_orani: float = 0.15) -> dict:
    """stok_orani: kiler ürününde peşin ödenen paket tutarının ne kadarının ayrıca 'ceza' sayılacağı.
    0 olursa model kiler için hep en büyük (kg'ı en ucuz) paketi seçer; bu ilk hafta için çok
    yüksek bir alışveriş tutarı demek. %15, makul boyutlu paketleri tercih ettirir."""
    malz, tarifler = tarif_ozet.yukle()
    ayar = PAKETLER[paket]
    h = hesapla(**kisi, yuksek_protein=ayar.get("yuksek_protein", False))

    # Uygun tarifler
    T = {}
    for t in tarifler:
        et = tarif_ozet.etiketler(t, malz)
        if ayar.get("etiket") and ayar["etiket"] not in et:
            continue
        if ayar.get("max_sure") and t["sure_dk"] > ayar["max_sure"]:
            continue
        T[t["id"]] = {**t, "besin": tarif_ozet.besin(t, malz)}

    gerekli = {x["malzeme"] for t in T.values() for x in t["malzemeler"] if not malz[x["malzeme"]]["dolapta"]}
    U = urun_adaylari(katalog, gerekli, marketler)
    eksik = [m for m in gerekli if not U.get(m)]
    if eksik:   # fiyatı bulunamayan malzemeyi kullanan tarifleri çıkar
        T = {k: t for k, t in T.items() if not any(x["malzeme"] in eksik for x in t["malzemeler"])}

    prob = pulp.LpProblem("haftalik_plan", pulp.LpMinimize)
    y, p = {}, {}
    for g in range(7):
        for o, (tur, _) in OGUNLER.items():
            for tid, t in T.items():
                if tur in t["ogunler"]:
                    y[g, o, tid] = pulp.LpVariable(f"y_{g}_{o}_{tid}", cat="Binary")
                    p[g, o, tid] = pulp.LpVariable(f"p_{g}_{o}_{tid}", lowBound=0)
                    lo, hi = t["porsiyon_araligi"]
                    prob += p[g, o, tid] >= lo * y[g, o, tid]
                    prob += p[g, o, tid] <= hi * y[g, o, tid]

    # Öğün yapısı
    for g in range(7):
        for o, (tur, zorunlu) in OGUNLER.items():
            secim = pulp.lpSum(v for (gg, oo, _), v in y.items() if gg == g and oo == o)
            prob += (secim == 1) if zorunlu else (secim <= 1)
        for tid in T:   # aynı gün aynı tarif iki kez olmasın
            ayni = [v for (gg, _, tt), v in y.items() if gg == g and tt == tid]
            if len(ayni) > 1:
                prob += pulp.lpSum(ayni) <= 1
    for tid in T:       # çeşitlilik: haftada en fazla 2 kez
        prob += pulp.lpSum(v for (_, _, tt), v in y.items() if tt == tid) <= 2

    # Günlük besin hedefleri. Protein "yumuşak" kısıt: tutturulamazsa (ör. vejetaryen + düşük kalori)
    # plan yine üretilir, eksik gram başına ceza ödenir ve kullanıcıya bildirilir.
    PROTEIN_CEZA = 15.0   # TL / eksik gram
    eksik_protein = {g: pulp.LpVariable(f"eksik_protein_{g}", lowBound=0) for g in range(7)}
    for g in range(7):
        def gun(alan):
            return pulp.lpSum(v * T[tt]["besin"][alan] for (gg, _, tt), v in p.items() if gg == g)
        prob += gun("kcal") >= h.kcal * 0.93
        prob += gun("kcal") <= h.kcal * 1.07
        prob += gun("protein") + eksik_protein[g] >= h.protein_min
        prob += gun("yag") <= h.yag_max

    # Alışveriş: paketler haftalık ihtiyacı karşılamalı
    n, n_paket, z, maliyet, urunler = {}, {}, {}, [], {}
    for m in {u["market"] for us in U.values() for u in us}:
        z[m] = pulp.LpVariable(f"z_{m}", cat="Binary")
    for mid, us in U.items():
        ihtiyac = pulp.lpSum(v * x["gram"] for (_, _, tt), v in p.items()
                             for x in T[tt]["malzemeler"] if x["malzeme"] == mid)
        alinan = []
        for i, u in enumerate(us):
            key = f"{mid}_{i}"
            urunler[key] = (mid, u)
            if u["acik_satis"]:
                n[key] = pulp.LpVariable(f"n_{key}", lowBound=0)              # kg cinsinden
            elif K[mid].get("kiler"):
                n[key] = pulp.LpVariable(f"n_{key}", lowBound=0)              # kullanılan pay (kesirli)
                n_paket[key] = pulp.LpVariable(f"np_{key}", lowBound=0, upBound=20, cat="Integer")
                prob += n_paket[key] >= n[key]                                 # alınan tam paket
                maliyet.append(stok_orani * u["price"] * n_paket[key])
            else:
                n[key] = pulp.LpVariable(f"n_{key}", lowBound=0, upBound=20, cat="Integer")
            prob += n[key] <= 20 * z[u["market"]]
            alinan.append(n[key] * u["miktar_g"])
            maliyet.append(n[key] * u["price"])
        prob += pulp.lpSum(alinan) >= ihtiyac
    prob += pulp.lpSum(z.values()) <= max_market

    prob += (pulp.lpSum(maliyet) + market_ceza * pulp.lpSum(z.values())
             + PROTEIN_CEZA * pulp.lpSum(eksik_protein.values()))

    if pulp.HiGHS().available():
        solver = pulp.HiGHS(msg=False, timeLimit=sure_siniri, gapRel=0.01)
    else:
        solver = pulp.PULP_CBC_CMD(msg=False, timeLimit=sure_siniri, gapRel=0.01)
    prob.solve(solver)
    durum = pulp.LpStatus[prob.status]
    secilen = sum(1 for v in y.values() if (v.value() or 0) > 0.5)
    if durum not in ("Optimal", "Not Solved") or secilen == 0:
        return {"durum": durum, "hedef": h.__dict__,
                "mesaj": "Bu kısıtlarla uygun plan bulunamadı (market sayısını artır ya da paketi değiştir)."}

    # Sonuç
    plan = []
    for g in range(7):
        ogunler, top = [], {"kcal": 0, "protein": 0, "karb": 0, "yag": 0}
        for o in OGUNLER:
            for (gg, oo, tt), v in y.items():
                if gg == g and oo == o and v.value() > 0.5:
                    por = p[g, o, tt].value()
                    b = {k: T[tt]["besin"][k] * por for k in top}
                    for k in top:
                        top[k] += b[k]
                    ogunler.append({"ogun": o, "tarif": tt, "ad": T[tt]["ad"], "porsiyon": round(por, 2),
                                    **{k: round(v, 1) for k, v in b.items()}})
        plan.append({"gun": GUNLER[g], "ogunler": ogunler, "toplam": {k: round(v) for k, v in top.items()}})

    liste, indirim_kazanci, plan_maliyeti = [], 0.0, 0.0
    for key, var in n.items():
        deger = var.value() or 0
        if deger < 1e-3:
            continue
        mid, u = urunler[key]
        kiler = bool(K[mid].get("kiler")) and not u["acik_satis"]
        plan_maliyeti += deger * u["price"]                 # bu haftanın planına düşen pay
        if u["acik_satis"]:
            adet = round(deger, 2)
        elif key in n_paket:
            adet = max(1, int(round(n_paket[key].value())))
        else:
            adet = int(round(deger))
        tutar = round(adet * u["price"], 2)
        if u.get("regular_price"):
            indirim_kazanci += adet * (u["regular_price"] - u["price"])
        liste.append({"market": u["market"], "malzeme": malz[mid]["ad"], "urun": u["name"],
                      "adet": adet, "birim": "kg" if u["acik_satis"] else "paket",
                      "birim_fiyat": u["price"], "tutar": tutar, "indirimli": bool(u.get("regular_price")),
                      "kiler": kiler, "kullanilan_pay": round(deger, 2) if kiler else None,
                      "url": u.get("url")})
    liste.sort(key=lambda x: (x["market"], x["malzeme"]))
    toplam = round(sum(x["tutar"] for x in liste), 2)
    uyarilar = []
    eksik_gunler = [GUNLER[g] for g in range(7) if (eksik_protein[g].value() or 0) > 1]
    if eksik_gunler:
        ort = sum(eksik_protein[g].value() or 0 for g in range(7)) / 7
        uyarilar.append(f"Protein hedefi bu paketteki tariflerle tutturulamadı ({', '.join(eksik_gunler)}; "
                        f"günde ortalama {ort:.0f} g eksik). Yüksek proteinli tarif eklemek gerekebilir.")
    return {"durum": durum, "hedef": h.__dict__, "paket": paket, "plan": plan, "alisveris": liste,
            "uyarilar": uyarilar,
            "toplam_tl": toplam, "plan_maliyeti_tl": round(plan_maliyeti, 2),
            "gunluk_tl": round(plan_maliyeti / 7, 2),
            "indirim_kazanci_tl": round(indirim_kazanci, 2),
            "marketler": sorted({x["market"] for x in liste})}


def yazdir(s: dict) -> None:
    h = s["hedef"]
    print(f"Hedef: {h['kcal']} kcal/gün, en az {h['protein_min']} g protein, en fazla {h['yag_max']} g yağ "
          f"(bazal {h['bazal']}, harcama {h['harcama']})")
    if "plan" not in s:
        print(s["durum"], s.get("mesaj"))
        return
    for d in s["plan"]:
        t = d["toplam"]
        print(f"\n{d['gun']}: {t['kcal']} kcal, P {t['protein']} g, K {t['karb']} g, Y {t['yag']} g")
        for o in d["ogunler"]:
            print(f"  {o['ogun']:10} {o['ad']:34} x{o['porsiyon']}")
    print("\nALIŞVERİŞ LİSTESİ")
    for m in s["marketler"]:
        print(f"  [{m.upper()}]")
        for x in s["alisveris"]:
            if x["market"] == m:
                ind = " (indirimli)" if x["indirimli"] else ""
                if x["kiler"]:
                    ind += f" [kiler: bu hafta {x['kullanilan_pay']} paketi kullanılıyor]"
                print(f"    {x['adet']} {x['birim']:5} {x['urun'][:50]:50} {x['tutar']:8.2f} TL{ind}")
    print(f"\nAlışveriş tutarı: {s['toplam_tl']} TL (kiler ürünlerinin tamamı dahil)")
    print(f"Planın gerçek haftalık maliyeti: {s['plan_maliyeti_tl']} TL (günlük {s['gunluk_tl']} TL)")
    print(f"İndirim kazancı: {s['indirim_kazanci_tl']} TL")
    for u in s.get("uyarilar", []):
        print("UYARI:", u)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kilo", type=float, required=True)
    ap.add_argument("--boy", type=float, required=True)
    ap.add_argument("--yas", type=int, required=True)
    ap.add_argument("--cinsiyet", choices=["erkek", "kadin"], required=True)
    ap.add_argument("--aktivite", default="orta", choices=["hareketsiz", "hafif", "orta", "yuksek", "cok_yuksek"])
    ap.add_argument("--hedef", default="koru", choices=["kilo_ver", "koru", "kilo_al"])
    ap.add_argument("--paket", default="ekonomik", choices=list(PAKETLER))
    ap.add_argument("--market", type=int, default=2, help="en fazla kaç markete gidilsin")
    ap.add_argument("--katalog", default="data/katalog.json")
    ap.add_argument("--cikti", default="beslenme/son_plan.json")
    a = ap.parse_args()
    katalog = json.loads(Path(a.katalog).read_text(encoding="utf-8"))
    kisi = dict(kilo=a.kilo, boy=a.boy, yas=a.yas, cinsiyet=a.cinsiyet, aktivite=a.aktivite, hedef=a.hedef)
    s = coz(katalog, kisi, paket=a.paket, max_market=a.market)
    Path(a.cikti).write_text(json.dumps(s, ensure_ascii=False, indent=1), encoding="utf-8")
    yazdir(s)
    print("\nNot: Bu plan genel bilgilendirme amaçlıdır, tıbbi tavsiye değildir.")


if __name__ == "__main__":
    main()
