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
import math
import re
import time
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


_ADAY_ONBELLEK: dict = {}


def _adaylar_onbellekli(mid: str, katalog: list) -> list:
    """Malzeme -> ürün eşleştirmesi katalog değişmedikçe aynıdır; her plan isteğinde 25.000 ürünü
    yeniden taramak yerine sonucu sakla (zayıf sunucuda plan süresinin yarısı buraya gidiyordu)."""
    anahtar = (id(katalog), len(katalog), katalog[0].get("name") if katalog else None,
               katalog[-1].get("name") if katalog else None)
    if _ADAY_ONBELLEK.get("_katalog") != anahtar:
        _ADAY_ONBELLEK.clear()
        _ADAY_ONBELLEK["_katalog"] = anahtar
    if mid not in _ADAY_ONBELLEK:
        _ADAY_ONBELLEK[mid] = adaylar(mid, katalog)
    return _ADAY_ONBELLEK[mid]


def onbellek_isit(katalog: list) -> None:
    """Sunucu açılırken tüm malzemelerin eşleştirmesini önceden hesaplar."""
    for mid in K:
        _adaylar_onbellekli(mid, katalog)


def urun_adaylari(katalog: list[dict], malzemeler: set[str], marketler: set[str] | None, her_market: int = 3):
    """Her malzeme için, her marketten kg'ı en ucuz birkaç ürün + en küçük paket + paket fiyatı en
    düşük ürün. Sonuncusu önemli: haftada 30 g kullanılan bal/tahin için 850 g'lık dev kavanoz
    yerine küçük ve ucuz paket seçilebilsin."""
    out = {}
    for mid in malzemeler:
        if mid not in K:
            continue
        c = [p for p in _adaylar_onbellekli(mid, katalog) if not marketler or p["market"] in marketler]
        secilen = []
        for m in {p["market"] for p in c}:
            mc = [p for p in c if p["market"] == m]
            secilen += mc[:her_market]
            for ek in (min(mc, key=lambda p: p["miktar_g"]), min(mc, key=lambda p: p["price"])):
                if ek not in secilen:
                    secilen.append(ek)
        for p in secilen:
            # adı rakam içermeyen "Kg" ürünleri tartıyla satılır -> istenen miktar kadar alınabilir
            p["acik_satis"] = p["miktar_g"] == 1000 and not re.search(r"\d", norm(p["name"]))
        # Aynı markette en az bu kadar büyük ve bundan pahalı olmayan başka paket varsa bu ürüne hiç gerek
        # yok (o paket her durumda en az onun kadar iyi). Modeli küçültür: 5+ markette çözücü süreye sığmıyordu.
        secilen = [p for p in secilen if not any(
            q is not p and q["market"] == p["market"] and q["miktar_g"] >= p["miktar_g"] and q["price"] <= p["price"]
            and (q["miktar_g"], q["price"]) != (p["miktar_g"], p["price"]) and q["acik_satis"] == p["acik_satis"]
            for q in secilen)]
        if secilen:          # hiç ürünü olmayan malzeme listeye girmesin (o malzemeyi kullanan tarifler elenir)
            out[mid] = secilen
    return out


# Tartıyla satılan ürünlerde (sarımsak, domates, soğan...) markette alınabilecek en az miktar (g).
# Plan 50 g sarımsak isterse alışveriş listesine en az bu kadar yazılır; model de bu fazlayı maliyete katar.
ACIK_SATIS_MIN_G = 250
ACIK_SATIS_MIN_OZEL: dict = {}          # malzemeye özel istisna gerekirse: {"zencefil": 100}


def acik_satis_min_kg(mid: str) -> float:
    return ACIK_SATIS_MIN_OZEL.get(mid, ACIK_SATIS_MIN_G) / 1000


# Öğle ve akşam yemeğinde aynı gün tekrarlanmaması gereken "ana" malzemeler
BAZ_MALZEME = ["kirmizi_mercimek", "yesil_mercimek", "nohut", "kuru_fasulye", "barbunya", "tavuk_gogus",
               "tavuk_but", "dana_kiyma", "ton_baligi", "makarna", "kinoa"]

# Haftalık plan için öğün türü başına gereken en az farklı tarif (tarif haftada ≤2 kez)
EN_AZ_TARIF = {"kahvalti": 4, "ana": 7}
TUR_ADI = {"kahvalti": "kahvaltı", "ana": "ana yemek", "ara": "ara öğün", "yan": "yan yemek"}


def tarif_sec(tarifler: list, malz: dict, paket: str = "ekonomik", ekipman=None, alerjen=(),
              haric_malzeme=(), max_sure: int | None = None) -> dict:
    """Kullanıcının tercihlerine uyan tarifleri döndürür (id -> tarif + besin)."""
    ayar = PAKETLER[paket]
    sure = min(x for x in (ayar.get("max_sure"), max_sure) if x) if (ayar.get("max_sure") or max_sure) else None
    T = {}
    for t in tarifler:
        if ayar.get("etiket") and ayar["etiket"] not in tarif_ozet.etiketler(t, malz):
            continue
        if sure and t["sure_dk"] > sure:
            continue
        if not tarif_ozet.yapilabilir(t, ekipman):
            continue
        if set(alerjen) & set(tarif_ozet.alerjenler(t)):
            continue
        if set(haric_malzeme) & {x["malzeme"] for x in t["malzemeler"]}:
            continue
        T[t["id"]] = {**t, "besin": tarif_ozet.besin(t, malz)}
    return T


def yetersiz_turler(T: dict) -> list[str]:
    return [tur for tur, n in EN_AZ_TARIF.items() if sum(1 for t in T.values() if tur in t["ogunler"]) < n]


def coz(katalog, kisi: dict, paket: str = "ekonomik", max_market: int = 2, market_ceza: float = 25.0,
        sure_siniri: int = 60, marketler: set[str] | None = None, stok_orani: float = 0.15,
        ekipman=None, alerjen=(), haric_malzeme=(), max_sure: int | None = None, ara_ogun: int = 2) -> dict:
    """stok_orani: kiler ürününde peşin ödenen paket tutarının ne kadarının ayrıca 'ceza' sayılacağı.
    0 olursa model kiler için hep en büyük (kg'ı en ucuz) paketi seçer; bu ilk hafta için çok
    yüksek bir alışveriş tutarı demek. %15, makul boyutlu paketleri tercih ettirir.
    ekipman: kullanıcının mutfağındaki ekipmanlar (None = kısıt yok); alerjen: kaçınılan gruplar
    (tarif_ozet.ALERJEN); haric_malzeme: istenmeyen malzeme id'leri; max_sure: tarif başına en fazla
    dakika; ara_ogun: günde en fazla kaç ara öğün (0-2)."""
    malz, tarifler = tarif_ozet.yukle()
    ayar = PAKETLER[paket]
    h = hesapla(**kisi, yuksek_protein=ayar.get("yuksek_protein", False))
    ogunler = {o: v for o, v in OGUNLER.items()
               if not (o == "ara1" and ara_ogun < 1) and not (o == "ara2" and ara_ogun < 2)}

    T = tarif_sec(tarifler, malz, paket, ekipman, alerjen, haric_malzeme, max_sure)
    if T:
        gerekli = {x["malzeme"] for t in T.values() for x in t["malzemeler"] if not malz[x["malzeme"]]["dolapta"]}
        market_sayisi = len(marketler) if marketler else len({p["market"] for p in katalog})
        U = urun_adaylari(katalog, gerekli, marketler, her_market=3 if market_sayisi <= 4 else 2)
        eksik = [m for m in gerekli if not U.get(m)]
        if eksik:   # fiyatı bulunamayan malzemeyi kullanan tarifleri çıkar
            T = {k: t for k, t in T.items() if not any(x["malzeme"] in eksik for x in t["malzemeler"])}
    yetersiz = yetersiz_turler(T)
    if yetersiz:   # çözücüyü boşuna çalıştırma: haftayı dolduracak kadar tarif yok
        adlar = " ve ".join(TUR_ADI[x] for x in yetersiz)
        return {"durum": "Yetersiz tarif", "hedef": h.__dict__, "yetersiz": yetersiz,
                "mesaj": f"Seçimlerine uyan yeterli {adlar} tarifi yok. Ekipman, süre veya kaçındığın "
                         f"besinlerden birini gevşetmeyi dene; tarif listemiz büyüdükçe bu durum azalacak."}

    def kur_coz(tam_paket: bool, sabit, sure: float):
        """Modeli kurar ve çözer. tam_paket=False: paketler kesirli (hızlı, menüyü seçer).
        sabit: önceki aşamada seçilen menü (y değerleri); verilirse sadece porsiyon ve paketler çözülür."""
        prob = pulp.LpProblem("haftalik_plan", pulp.LpMinimize)
        y, p = {}, {}
        for g in range(7):
            for o, (tur, _) in ogunler.items():
                for tid, t in T.items():
                    if tur in t["ogunler"]:
                        y[g, o, tid] = pulp.LpVariable(f"y_{g}_{o}_{tid}", cat="Binary")
                        p[g, o, tid] = pulp.LpVariable(f"p_{g}_{o}_{tid}", lowBound=0)
                        lo, hi = t["porsiyon_araligi"]
                        prob += p[g, o, tid] >= lo * y[g, o, tid]
                        prob += p[g, o, tid] <= hi * y[g, o, tid]
        if sabit is not None:       # 2. aşama: menü belli, sadece porsiyon ve paketler çözülür
            for k, v in y.items():
                v.bounds(sabit[k], sabit[k])

        # Öğün yapısı
        for g in range(7):
            for o, (tur, zorunlu) in ogunler.items():
                secim = pulp.lpSum(v for (gg, oo, _), v in y.items() if gg == g and oo == o)
                prob += (secim == 1) if zorunlu else (secim <= 1)
            for tid in T:   # aynı gün aynı tarif iki kez olmasın
                ayni = [v for (gg, _, tt), v in y.items() if gg == g and tt == tid]
                if len(ayni) > 1:
                    prob += pulp.lpSum(ayni) <= 1
        for tid in T:       # çeşitlilik: haftada en fazla 2 kez
            prob += pulp.lpSum(v for (_, _, tt), v in y.items() if tt == tid) <= 2
        # Çeşitlilik: aynı gün öğle ve akşamda aynı ana malzeme olmasın (ör. mercimek çorbası + mercimek yahnisi)
        for g in range(7):
            for b in BAZ_MALZEME:
                ayni_baz = [v for (gg, oo, tt), v in y.items() if gg == g and oo in ("ogle", "aksam")
                            and any(x["malzeme"] == b for x in T[tt]["malzemeler"])]
                if len(ayni_baz) > 1:
                    prob += pulp.lpSum(ayni_baz) <= 1

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
            if not us:       # güvenlik: ürünü olmayan malzeme (tarifleri zaten elendi)
                continue
            ihtiyac = pulp.lpSum(v * x["gram"] for (_, _, tt), v in p.items()
                                 for x in T[tt]["malzemeler"] if x["malzeme"] == mid)
            alinan = []
            for i, u in enumerate(us):
                key = f"{mid}_{i}"
                urunler[key] = (mid, u)
                if u["acik_satis"] or not tam_paket:
                    # açık satış: kg cinsinden. 1. aşamada tüm ürünler kesirli (paket yuvarlaması 2. aşamada)
                    n[key] = pulp.LpVariable(f"n_{key}", lowBound=0)
                    if u["acik_satis"] and tam_paket:
                        # markette 50 g sarımsak alınmaz: alınacaksa en az ACIK_SATIS_MIN_G kadar
                        b = pulp.LpVariable(f"b_{key}", cat="Binary")
                        prob += n[key] <= 20 * b
                        prob += n[key] >= acik_satis_min_kg(mid) * b
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
            if not tam_paket and not any(u["acik_satis"] for u in us):
                # 1. aşamada paket israfı tahmini: paketli bir malzeme az da kullanılsa en az bir
                # (en ucuz) paketin parası ödenir. Bunu saymazsak menü çok sayıda malzemeden azar azar
                # kullanır ve 2. aşamada sepet pahalı çıkar.
                w = pulp.LpVariable(f"w_{mid}", cat="Binary")
                prob += ihtiyac <= 50000 * w
                en_ucuz = min(u["price"] for u in us)
                if K[mid].get("kiler"):         # kiler: kullanılan pay + alınan paketin stok cezası
                    maliyet.append(stok_orani * en_ucuz * w)
                else:                           # taze: harcama en az bir paket kadar olur
                    e = pulp.LpVariable(f"e_{mid}", lowBound=0)
                    prob += e >= en_ucuz * w - pulp.lpSum(n[f"{mid}_{i}"] * u["price"] for i, u in enumerate(us))
                    maliyet.append(e)
        prob += pulp.lpSum(z.values()) <= max_market

        prob += (pulp.lpSum(maliyet) + market_ceza * pulp.lpSum(z.values())
                 + PROTEIN_CEZA * pulp.lpSum(eksik_protein.values()))

        if pulp.HiGHS().available():
            solver = pulp.HiGHS(msg=False, timeLimit=sure, gapRel=0.01 if tam_paket else 0.02)
        else:
            solver = pulp.PULP_CBC_CMD(msg=False, timeLimit=sure, gapRel=0.01 if tam_paket else 0.02)
        prob.solve(solver)
        return prob, y, p, n, n_paket, z, urunler, eksik_protein

    # İki aşamalı çözüm: (1) paketleri kesirli sayarak menüyü seç, (2) menüyü sabitleyip paketleri tam
    # sayıyla çöz. Tek seferde çözmeye göre çok daha hızlı uygun plan bulur (zayıf işlemcili sunucu).
    basla = time.time()
    prob, y, p, n, n_paket, z, urunler, eksik_protein = kur_coz(False, None, sure_siniri * 0.75)
    if any((v.value() or 0) > 0.5 for v in y.values()):
        sabit = {k: (1 if (v.value() or 0) > 0.5 else 0) for k, v in y.items()}
        iki = kur_coz(True, sabit, max(5.0, sure_siniri - (time.time() - basla)))
        if pulp.LpStatus[iki[0].status] in ("Optimal", "Not Solved") and any((v.value() or 0) > 0.5 for v in iki[1].values()):
            prob, y, p, n, n_paket, z, urunler, eksik_protein = iki
    durum = pulp.LpStatus[prob.status]
    secilen = sum(1 for v in y.values() if (v.value() or 0) > 0.5)
    if durum not in ("Optimal", "Not Solved") or secilen == 0:
        return {"durum": durum, "hedef": h.__dict__,
                "mesaj": "Bu kısıtlarla uygun plan bulunamadı (market sayısını artır ya da paketi değiştir)."}

    # Sonuç
    plan = []
    for g in range(7):
        secilenler, top = [], {"kcal": 0, "protein": 0, "karb": 0, "yag": 0}
        for o in ogunler:
            for (gg, oo, tt), v in y.items():
                if gg == g and oo == o and v.value() > 0.5:
                    por = p[g, o, tt].value()
                    b = {k: T[tt]["besin"][k] * por for k in top}
                    for k in top:
                        top[k] += b[k]
                    secilenler.append({"ogun": o, "tarif": tt, "ad": T[tt]["ad"], "porsiyon": round(por, 2),
                                       **{k: round(v, 1) for k, v in b.items()}})
        plan.append({"gun": GUNLER[g], "ogunler": secilenler, "toplam": {k: round(v) for k, v in top.items()}})

    # Uygulamadaki tarif detay ekranı için: plandaki tariflerin malzemeleri, adımları, ekipmanı
    kullanilan = {o["tarif"] for d in plan for o in d["ogunler"]}
    tarif_detay = {tid: {"ad": T[tid]["ad"], "sure_dk": T[tid]["sure_dk"], "adimlar": T[tid]["adimlar"],
                         "ekipman": T[tid].get("ekipman", [["ocak"]]), "besin": T[tid]["besin"],
                         "alerjenler": tarif_ozet.alerjenler(T[tid]),
                         "etiketler": tarif_ozet.etiketler(T[tid], malz),
                         "malzemeler": [{"id": x["malzeme"], "ad": malz[x["malzeme"]]["ad"], "gram": x["gram"]}
                                        for x in T[tid]["malzemeler"]]}
                   for tid in kullanilan}

    liste, indirim_kazanci, plan_maliyeti = [], 0.0, 0.0
    # Çözücü süre sınırında durduysa (zayıf işlemcili sunucu) gereğinden fazla paket bırakmış olabilir:
    # her malzemede ihtiyacı aşan fazlayı, kg'ı en pahalı üründen başlayarak kırp.
    deger_of = {key: (var.value() or 0) for key, var in n.items()}
    for mid in U:
        ihtiyac = sum((v.value() or 0) * x["gram"] for (_, _, tt), v in p.items()
                      for x in T[tt]["malzemeler"] if x["malzeme"] == mid)
        anahtarlar = sorted((k for k in deger_of if urunler[k][0] == mid),
                            key=lambda k: -(urunler[k][1]["price"] / urunler[k][1]["miktar_g"]))
        fazla = sum(deger_of[k] * urunler[k][1]["miktar_g"] for k in anahtarlar) - ihtiyac
        for k in anahtarlar:
            if fazla <= 1e-6:
                break
            g = urunler[k][1]["miktar_g"]
            if urunler[k][1]["acik_satis"] or K[mid].get("kiler"):   # kesirli miktar
                azalt = min(deger_of[k], fazla / g)
            else:                                                  # tam paket
                azalt = min(int(deger_of[k] + 1e-6), int(fazla // g))
            deger_of[k] -= azalt
            fazla -= azalt * g

    for key in n:
        deger = deger_of[key]
        if deger < 1e-3:
            continue
        mid, u = urunler[key]
        kiler = bool(K[mid].get("kiler")) and not u["acik_satis"]
        if u["acik_satis"]:
            # en az ACIK_SATIS_MIN_G, 50 g'lık adımlarla yukarı yuvarlanmış (tartıda böyle alınır);
            # fazlası da bu haftanın harcamasıdır
            deger = adet = max(acik_satis_min_kg(mid), math.ceil(deger * 20 - 1e-6) / 20)
        plan_maliyeti += deger * u["price"]                 # bu haftanın planına düşen pay
        if not u["acik_satis"]:
            adet = max(1, math.ceil(deger - 1e-6))      # ihtiyacı karşılayan en az tam paket
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
            "uyarilar": uyarilar, "tarifler": tarif_detay,
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
