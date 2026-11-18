"""
Market karşılaştırması:
  - karsilastir("süt")            -> her marketin en uygun ürünü, birim fiyatla (TL/L, TL/kg, TL/adet)
  - liste_hesapla(["2 L süt", ...]) -> her market için sepet tutarı, en ucuz tek market, en iyi iki market

Arama:
  1. Sorgu bilinen bir malzemeyse ("süt", "yumurta", "kıyma"...) beslenme/eslestirme_kurallari.py'deki
     özenli kurallar kullanılır (sütlü çikolata, kakaolu süt vb. elenir).
  2. Değilse sorgudaki kelimelerin hepsini içeren ürünler aranır. Kısa kelimeler (≤3 harf) tam kelime
     olarak, uzunlar kelime başı olarak eşleşir; "-li/-lu/-siz" ekli halleri sayılmaz
     ("süt" -> "Sütlü" eşleşmez).

Fiyat: her market için, istenen miktarı karşılayan en ucuz paket kombinasyonu (aynı üründen gerekirse
birden fazla paket). Tartıyla satılan ("Domates Kg") ürünlerde istenen miktar kadar ödenir.
"""
from __future__ import annotations

import itertools
import json
import math
import re
import statistics
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Tuple

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "beslenme"))
import plan  # noqa: E402
from eslestirme_kurallari import K  # noqa: E402
from miktar import norm, norm_ad, parse_quantity  # noqa: E402

BIRIM_AD = {"g": "kg", "ml": "L", "adet": "adet"}
CARPAN = {"g": 1000.0, "ml": 1000.0, "adet": 1.0}       # birim fiyat: TL/kg, TL/L, TL/adet
IYELIK = re.compile(r"s?[iu]|n?in|n?un|ler|lar|leri|lari")   # deterjanı, kahvesi, ekmekler...
EN_FAZLA_KALEM = 40
TOLERANS = 0.25        # istenen miktarın en az %75'ini karşılayan paket sayısı yeterli

_DIZIN: Optional[Dict[str, str]] = None
_ARAMA_ONBELLEK: Dict[tuple, tuple] = {}     # (katalog kimliği, sorgu) -> (katalog, eşleşen ürünler)


def _malzeme_dizini() -> Dict[str, str]:
    """Normalize edilmiş arama terimi -> malzeme id ('sut' -> 'sut', 'kiyma' -> 'dana_kiyma')."""
    global _DIZIN
    if _DIZIN is None:
        malz = json.loads((KOK / "beslenme" / "malzemeler.json").read_text(encoding="utf-8"))
        _DIZIN = {}
        for m in malz:
            if m["id"] not in K:
                continue
            for terim in [m["ad"], *m.get("arama", [])]:
                _DIZIN.setdefault(norm(re.sub(r"\(.*?\)", "", terim)), m["id"])
    return _DIZIN


def _kelime_var(t: str, kelimeler: List[str]) -> bool:
    """Kelimenin kendisi ya da iyelik/çoğul ekli hali: 'kahve' -> 'kahvesi' evet, 'kahverengi' hayır;
    'sut' -> 'sutlu' hayır; 'deterjan' -> 'deterjani' evet."""
    return any(w == t or (w.startswith(t) and IYELIK.fullmatch(w[len(t):])) for w in kelimeler)


_SAYI_RE = re.compile(r"(\d+)\s*'?\s*(?:li|lu|adet)\b")


def urun_miktari(ad: str) -> Tuple[Optional[float], Optional[str]]:
    """Paket miktarı. 'Yumurta 6'lı 53-62 G' gibi adlarda sondaki küçük gram değeri tek bir parçanın
    ağırlığıdır; o zaman adet (6) kullanılır."""
    q, u = parse_quantity(ad)
    sayi = _SAYI_RE.search(norm(ad))
    if sayi and (u is None or (u in ("g", "ml") and q is not None and q <= 100)):
        return float(sayi.group(1)), "adet"
    return q, u


def _acik_satis(urun: dict, q: float, birim: str) -> bool:
    """Adında rakam olmayan 'Kg' ürünleri tartıyla satılır (istenen miktar kadar alınır)."""
    return birim == "g" and q == 1000 and not re.search(r"\d", norm_ad(urun["name"]))


# Aranan kelimeden hemen sonra gelince ürünün asıl kendisini değiştiren kelimeler:
# "Çikolata Kaplı Gofret", "Peynir Aromalı Cips", "Kahve Dolgulu Çikolata"
_YAN_URUN = {"kapli", "kaplamali", "dolgulu", "aromali", "aroma", "parcali", "parcacikli", "soslu", "kremali",
             "karisimi", "tozu", "cicegi", "fincani", "bardagi", "kasigi", "demlik", "demligi", "kutusu",
             "kabi", "seti", "makinesi", "ezmeli", "fistik", "findik", "badem"}
_CESIT_DISI = {"karsi", "karsiti", "etkili", "icin", "ile", "ve", "the", "and"}   # çeşit adı olamayacak kelimeler


def _yan_urun_mu(t: str, kelimeler: List[str]) -> bool:
    """Aranan kelime ürünün kendisi değil de bir niteliği mi? Türkçe tamlamada asıl ürün sondadır:
    'Kahve Beyazlatıcısı', 'Kahve Dünyası' (marka), 'Çay Kurabiyesi' -> kahve/çay değil.
    Kelimenin YALIN hali iyelik ekli bir kelimeyle (-sı/-su) ya da _YAN_URUN'deki bir kelimeyle
    devam ediyorsa ürün yan üründür. 'Türk Kahvesi' gibi kelimenin kendisi ekliyse sorun yok."""
    for i, w in enumerate(kelimeler[:-1]):
        if w != t:
            continue
        sonraki = kelimeler[i + 1]
        if sonraki in _YAN_URUN or (len(sonraki) > 4 and re.search(r"[aeiou]s[iu]$", sonraki)):
            return True
    return False


# Adında geçince ürünün başka bir türden olduğunu gösteren kelimeler: "Çikolata" aranınca
# "Karmen Çikolata Gofret", "Ülker Kek Muz Çikolata" gelmesin. Sorguda geçiyorsa (gofret aranırsa) sayılmaz.
_BASKA_TUR = ("gofret", "biskuvi", "kek", "kurabiye", "pasta", "dondurma", "puding", "cips", "kraker",
              "gevrek", "gevregi", "draje", "sos", "surup", "likor", "krep", "waffle", "kruvasan", "helva")


def _kelime_eslesir(kelimeler_sorgu: List[str], kelimeler_urun: List[str]) -> bool:
    return (all(_kelime_var(t, kelimeler_urun) for t in kelimeler_sorgu)
            and not _yan_urun_mu(kelimeler_sorgu[-1], kelimeler_urun)
            and not any(_kelime_var(b, kelimeler_urun) for b in _BASKA_TUR
                        if not any(t.startswith(b[:4]) for t in kelimeler_sorgu)))


def cesitler(bulunan: List[Tuple[dict, float, str]], sorgu: str, en_fazla: int = 8) -> List[dict]:
    """Aramayı daraltmak için çeşitler: aranan kelimenin hemen önündeki kelime
    ('Filtre Kahve', 'Türk Kahvesi', 'Poşet Çay', 'Kaşar Peyniri'). İlk kelime marka sayılır, alınmaz."""
    sorgu_k = norm(sorgu).split()
    if not sorgu_k:
        return []
    sayac: Counter = Counter()
    etiket: Dict[str, str] = {}
    for p, _, _ in bulunan:
        asil = p["name"].split()
        w = [re.sub(r"[^a-z0-9]", "", norm(x)) for x in asil]
        for i in range(2, len(w)):                # i-1 >= 1: ilk kelime (marka) çeşit olamaz
            if _kelime_var(sorgu_k[-1], [w[i]]):
                once = w[i - 1]
                if len(once) >= 3 and once.isalpha() and once not in sorgu_k and once not in _CESIT_DISI:
                    sayac[once] += 1
                    etiket.setdefault(once, f"{_temiz(asil[i - 1])} {_temiz(asil[i])}")
                break
    if "arada" in etiket:
        etiket["arada"] = "3'ü 1 Arada"
    return [{"id": c, "ad": etiket[c], "adet": n} for c, n in sayac.most_common(en_fazla) if n >= 3]


def _temiz(s: str) -> str:
    return re.sub(r"^[^\w]+|[^\w]+$", "", s)


def adaylar(sorgu: str, katalog: List[dict], cesit: Optional[str] = None
            ) -> Tuple[List[Tuple[dict, float, str]], Optional[str]]:
    """Sorguya uyan ürünler: [(ürün, paket miktarı, birim)], baskın birim.
    cesit verilirse ('filtre') adında o kelime de geçen ürünlerle sınırlanır."""
    nq = norm(sorgu)
    mid = _malzeme_dizini().get(nq)
    if mid:
        bulunan = plan._adaylar_onbellekli(mid, katalog)
    else:
        kelimeler = [t for t in re.findall(r"[a-z0-9]+", nq) if len(t) >= 2]
        if not kelimeler:
            return [], None
        anahtar = (id(katalog), " ".join(kelimeler))
        kayit = _ARAMA_ONBELLEK.get(anahtar)
        if kayit is not None and kayit[0] is katalog:
            bulunan = kayit[1]
        else:                          # çeşit değiştirince tüm katalog yeniden taranmasın
            bulunan = [p for p in katalog if _kelime_eslesir(kelimeler, norm_ad(p["name"]).split())]
            if len(_ARAMA_ONBELLEK) >= 200:
                _ARAMA_ONBELLEK.clear()
            _ARAMA_ONBELLEK[anahtar] = (katalog, bulunan)   # katalog referansı: id yeniden kullanılamaz
    if cesit:
        c = norm(cesit)
        bulunan = [p for p in bulunan if c in norm_ad(p["name"]).split()]
    out = []
    for p in bulunan:
        q, u = urun_miktari(p["name"])
        if q and q > 0 and p.get("price"):
            out.append((p, float(q), u))
    if not out:
        return [], None
    birim = Counter(u for _, _, u in out).most_common(1)[0][0]
    return [x for x in out if x[2] == birim], birim


def _birim_fiyat(p: dict, q: float, birim: str) -> float:
    return p["price"] / q * CARPAN[birim]


def _urun_ozeti(p: dict, q: float, birim: str) -> dict:
    return {"market": p["market"], "ad": p["name"], "fiyat": p["price"], "eski_fiyat": p.get("regular_price"),
            "indirim": p.get("discount_pct"), "birim_fiyat": round(_birim_fiyat(p, q, birim), 2),
            "paket": miktar_metni(q, birim), "url": p.get("url"), "gorsel": p.get("image_url")}


def miktar_metni(q: float, birim: str) -> str:
    if birim == "adet":
        return f"{int(round(q))} adet"
    if q >= 1000:
        s = f"{q / 1000:.2f}".rstrip("0").rstrip(".").replace(".", ",")
        return f"{s} {'kg' if birim == 'g' else 'L'}"
    return f"{int(round(q))} {'g' if birim == 'g' else 'ml'}"


def karsilastir(sorgu: str, katalog: List[dict], adet: int = 30, cesit: Optional[str] = None) -> dict:
    """Tek ürün karşılaştırması: birim fiyata göre sıralı ürünler ve her marketin en iyisi.
    'cesitler' aramayı daraltma seçenekleridir (kahve -> Filtre / Türk Kahvesi / Çekirdek...)."""
    hepsi, _ = adaylar(sorgu, katalog)
    secenek = cesitler(hepsi, sorgu)
    if cesit and not any(c["id"] == cesit for c in secenek):
        cesit = None
    bulunan, birim = adaylar(sorgu, katalog, cesit) if cesit else (hepsi, _)
    if not bulunan:
        return {"sorgu": sorgu, "toplam": 0, "marketler": [], "urunler": [], "cesitler": [], "cesit": None}
    sirali = sorted(bulunan, key=lambda x: _birim_fiyat(*x))
    en_iyi: Dict[str, dict] = {}
    for p, q, u in sirali:
        en_iyi.setdefault(p["market"], _urun_ozeti(p, q, u))
    marketler = sorted(en_iyi.values(), key=lambda x: x["birim_fiyat"])
    return {"sorgu": sorgu, "birim": BIRIM_AD[birim], "toplam": len(sirali), "marketler": marketler,
            "urunler": [_urun_ozeti(p, q, u) for p, q, u in sirali[:adet]],
            "cesitler": secenek, "cesit": cesit}


# ----------------------------------------------------------------------------- alışveriş listesi
_MIKTAR_RE = re.compile(r"\d+(?:[.,]\d+)?\s*(?:x\s*\d+(?:[.,]\d+)?\s*)?"
                        r"(?:kg|kilo|gram|gr|g|litre|lt|l|ml|cl|adet|tane|'?\s*(?:li|lu|li|lu))\b")


def satir_ayir(satir: str) -> Tuple[str, Optional[float], Optional[str], Optional[int]]:
    """'2 L süt' -> ('süt', 2000, 'ml', None);  '3 domates' -> ('domates', None, None, 3)."""
    n = norm(satir)
    q, u = parse_quantity(satir)
    sorgu = _MIKTAR_RE.sub(" ", n)
    carpan = None
    m = re.match(r"^\s*(\d+)\s+", sorgu) or re.search(r"\s(\d+)\s*$", sorgu)
    if m and not q:
        carpan = int(m.group(1))
        sorgu = sorgu.replace(m.group(0), " ")
    sorgu = re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", sorgu)).strip()
    return sorgu, (float(q) if q else None), u, carpan


def _en_ucuz_secim(urunler: List[Tuple[dict, float, str]], miktar: float) -> dict:
    """Bir marketteki ürünlerden istenen miktarı en ucuza karşılayan seçim."""
    en_iyi = None
    for p, q, u in urunler:
        if _acik_satis(p, q, u):
            paket, tutar = round(miktar / q, 3), p["price"] * miktar / q
        else:
            # %25 tolerans: 5 kg istenince 4 kg'lık tek paket yeter (2 paket alıp 8 kg taşımak yerine)
            paket = max(1, math.ceil(miktar / q - TOLERANS))
            tutar = paket * p["price"]
        if en_iyi is None or tutar < en_iyi["tutar"] - 1e-9:
            en_iyi = {**_urun_ozeti(p, q, u), "adet": paket, "tutar": round(tutar, 2), "acik_satis": _acik_satis(p, q, u)}
    return en_iyi


def liste_hesapla(satirlar: List[str], katalog: List[dict]) -> dict:
    kalemler = []
    for satir in [s.strip() for s in satirlar if s and s.strip()][:EN_FAZLA_KALEM]:
        sorgu, q, u, carpan = satir_ayir(satir)
        bulunan, birim = adaylar(sorgu, katalog) if sorgu else ([], None)
        if not bulunan:
            kalemler.append({"satir": satir, "sorgu": sorgu, "bulunamadi": True, "secenekler": []})
            continue
        if q and (u == birim or {u, birim} == {"g", "ml"}):     # g ile ml'yi yaklaşık eşit say
            miktar = q
        elif birim == "adet" and carpan:
            miktar = float(carpan)
        else:   # miktar yazılmamış: tipik paket (ortanca), "3 süt" gibi yazıldıysa o kadar paket
            miktar = statistics.median(x[1] for x in bulunan) * (carpan or 1)
        pazar: Dict[str, List] = {}
        for x in bulunan:
            pazar.setdefault(x[0]["market"], []).append(x)
        secenekler = sorted((_en_ucuz_secim(us, miktar) for us in pazar.values()), key=lambda s: s["tutar"])
        kalemler.append({"satir": satir, "sorgu": sorgu, "miktar": miktar_metni(miktar, birim),
                         "bulunamadi": False, "secenekler": secenekler})

    bulunan_kalemler = [k for k in kalemler if not k["bulunamadi"]]
    marketler = sorted({s["market"] for k in bulunan_kalemler for s in k["secenekler"]})

    def sepet(secili: Tuple[str, ...]) -> dict:
        tutar, eksik, dagilim = 0.0, [], []
        for k in bulunan_kalemler:
            uygun = [s for s in k["secenekler"] if s["market"] in secili]
            if uygun:
                s = min(uygun, key=lambda s: s["tutar"])
                tutar += s["tutar"]
                dagilim.append({"satir": k["satir"], "market": s["market"], "tutar": s["tutar"]})
            else:
                eksik.append(k["satir"])
        return {"marketler": list(secili), "tutar": round(tutar, 2), "eksik": eksik, "dagilim": dagilim}

    tek = sorted((sepet((m,)) for m in marketler), key=lambda s: (len(s["eksik"]), s["tutar"]))
    iki = sorted((sepet(c) for c in itertools.combinations(marketler, 2)), key=lambda s: (len(s["eksik"]), s["tutar"]))
    hepsi = sepet(tuple(marketler)) if marketler else None
    oneri = {"tek": tek[0] if tek else None, "iki": None, "hepsi": hepsi}
    if iki and tek:
        a, b = tek[0], iki[0]
        # ikinci markete gitmek ancak eksik ürünü tamamlıyorsa ya da kayda değer tasarruf varsa önerilir
        if len(b["eksik"]) < len(a["eksik"]) or a["tutar"] - b["tutar"] >= max(15.0, a["tutar"] * 0.05):
            oneri["iki"] = {**b, "tasarruf": round(a["tutar"] - b["tutar"], 2)}
    return {"kalemler": kalemler, "marketler": tek, "oneri": oneri}
