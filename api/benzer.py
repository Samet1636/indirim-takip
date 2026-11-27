"""
Ürün detay sayfası için: bir ürünün birim fiyatı, öteki marketlerdeki karşılığı ve daha ucuz benzerleri.

Benzerlik: ürün adlarındaki kelimelerin ağırlıklı örtüşmesi (nadir kelime = daha ayırt edici, örn.
marka ve çeşit; "süt" gibi çok geçen kelimelerin ağırlığı düşük). Aday ürünler, ürünün türünü
belirten kelimeyi (Türkçe tamlamada sondaki kelime: "Yağlı Süt" -> süt) taşıyanlardır;
"Kahve Beyazlatıcısı" gibi yan ürünler karsilastirma._kelime_eslesir ile elenir.
"""
from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from typing import Dict, List, Optional, Set, Tuple

from .karsilastirma import (  # beslenme/ yolunu da ekler
    _YAN_URUN, BIRIM_AD, CARPAN, _kelime_eslesir, miktar_metni, urun_miktari)
from miktar import norm_ad  # noqa: E402

# Benzerlikte sayılmayan kelimeler: birimler, ambalaj, genel sıfatlar
_GURULTU = {"kg", "gr", "gram", "ml", "lt", "litre", "cl", "adet", "li", "lu", "x", "cesitleri", "cesit",
            "cesitli", "paket", "yeni", "ve", "ile", "the", "pet", "cam", "sise", "kutu", "teneke", "poset",
            "kavanoz", "eko", "ekonomik", "avantaj", "avantajli", "firsat", "boy", "buyuk", "kucuk", "aile"}

FARKLI_MARKA = 0.85      # marka farklıysa benzerlik bununla çarpılır
AYNI_ESIK = 0.8          # aynı marka + bu benzerliğin üstü + paket miktarı yakın: "aynı ürün"
MARKET_ESIK = 0.45       # öteki markette karşılık sayılmak için en az benzerlik
UCUZ_ESIK = 0.4          # "daha ucuz benzerleri" için en az benzerlik
EN_FAZLA_UCUZ = 6


_EKLER = ("leri", "lari", "si", "su", "i", "u")
_SERTLESME = {"g": "k", "b": "p"}         # fıstığı -> fistig -> fistik, kitabı -> kitab -> kitap


def kok(t: str) -> str:
    """Kaba kök: iyelik/çoğul ekini at, yumuşamayı geri al ('fistigi' -> 'fistik', 'kahvesi' -> 'kahve').
    İki tarafta da aynı uygulandığı için ara sıra yanlış kök ('yagli' -> 'yagl') sorun olmaz."""
    for ek in _EKLER:
        if t.endswith(ek) and len(t) - len(ek) >= 4:
            t = t[:-len(ek)]
            if t[-1] in _SERTLESME:
                t = t[:-1] + _SERTLESME[t[-1]]
            break
    return t


def kelimeler(ad: str) -> List[str]:
    """Addaki anlamlı kelimelerin kökleri, sırasıyla (rakamlar ve birimler atılır)."""
    return [kok(t) for t in ham_kelimeler(ad)]


def ayir(sirali: List[str]) -> Tuple[Optional[str], Set[str]]:
    """(marka, gövde): ilk kelime marka sayılır ('Dost Yağlı Süt' -> dost, {yagli, sut}).
    Tek kelimelik adlarda ('Domates Kg') marka yok."""
    if len(sirali) <= 1:
        return None, set(sirali)
    n = 2 if tuple(sirali[:2]) in _IKI_KELIMELI_MARKA and len(sirali) > 2 else 1
    return " ".join(sirali[:n]), set(sirali[n:])


_IKI_KELIMELI_MARKA = {(kok(a), kok(b)) for a, b in
                       [("tarim", "kredi"), ("bili", "bili"), ("dr", "oetker"), ("ana", "gida")]}


class _Dizin:
    def __init__(self, katalog: List[dict]):
        self.katalog = katalog
        self.sirali: List[List[str]] = [kelimeler(p["name"]) for p in katalog]
        self.kel: List[Set[str]] = [set(s) for s in self.sirali]
        df = Counter(t for s in self.kel for t in s)
        n = len(katalog)
        self.idf: Dict[str, float] = {t: math.log((n + 1) / (c + 1)) + 0.5 for t, c in df.items()}
        self.ters: Dict[str, List[int]] = defaultdict(list)
        for i, s in enumerate(self.kel):
            for t in s:
                self.ters[t].append(i)
        self.yer: Dict[Tuple[str, str], int] = {(p["market"], p["name"]): i for i, p in enumerate(katalog)}

    def agirlik(self, t: str) -> float:
        return self.idf.get(t, math.log(len(self.katalog) + 1) + 0.5)

    def benzerlik(self, a: List[str], b: List[str]) -> Tuple[float, bool]:
        """(benzerlik 0-1, aynı marka mı). Markalar ayrı tutulur: her marketin kendi markası var,
        'Dost Yağlı Süt' ile 'Pınar Yağlı Süt' benzer sayılmalı. Farklı marka hafifçe düşürülür."""
        ma, ga = ayir(a)
        mb, gb = ayir(b)
        birlesim = sum(self.agirlik(t) for t in ga | gb)
        g = sum(self.agirlik(t) for t in ga & gb) / birlesim if birlesim else 0.0
        ayni_marka = ma is not None and ma == mb
        return (g if ayni_marka else g * FARKLI_MARKA), ayni_marka


_ONBELLEK: Dict[str, object] = {}


def _dizin(katalog: List[dict]) -> _Dizin:
    d = _ONBELLEK.get("dizin")
    if d is None or d.katalog is not katalog:      # katalog yenilenince dizin de yenilenir
        d = _ONBELLEK["dizin"] = _Dizin(katalog)
    return d


def _ozet(p: dict, q: Optional[float], birim: Optional[str], benzerlik: Optional[float] = None) -> dict:
    birim_fiyat = round(p["price"] / q * CARPAN[birim], 2) if q and birim and p.get("price") else None
    d = {"market": p["market"], "ad": p["name"], "fiyat": p["price"], "eski_fiyat": p.get("regular_price"),
         "indirim": p.get("discount_pct"), "kategori": p.get("category"), "url": p.get("url"),
         "gorsel": p.get("image_url"), "paket": miktar_metni(q, birim) if q and birim else None,
         "birim_fiyat": birim_fiyat, "birim": BIRIM_AD[birim] if birim else None}
    if benzerlik is not None:
        d["benzerlik"] = round(benzerlik, 2)
    return d


_SIFAT = re.compile(r".{2,}(l[iu]|s[iu]z)$")      # yağlı, tuzlu, şekersiz: tür olamaz


def ham_kelimeler(ad: str) -> List[str]:
    return [t for t in re.findall(r"[a-z]+", norm_ad(ad)) if len(t) >= 2 and t not in _GURULTU]


def tur_kelimesi(ad: str) -> Optional[str]:
    """Ürünün türü (kök): sondaki sıfat olmayan kelime. 'Dost Yağlı Süt 1 Lt' -> 'sut',
    'Pınar Süt %1 Yağlı 1 L' -> 'sut' (sondaki 'Yağlı' sıfat)."""
    ham = ham_kelimeler(ad)
    for t in reversed(ham):
        if not _SIFAT.fullmatch(t):
            return kok(t)
    return kok(ham[-1]) if ham else None


def _yan_urun(tur: str, ham: List[str]) -> bool:
    """Tür kelimesinden hemen sonra onu niteleyen bir kelime gelirse ürün başka bir şeydir:
    'Yer Fıstığı Ezmesi', 'Kahve Beyazlatıcısı', 'Süt Tozu' (karsilastirma._yan_urun_mu'nun köklü hali)."""
    for i, w in enumerate(ham[:-1]):
        if kok(w) == tur:
            sonraki = ham[i + 1]
            if sonraki in _YAN_URUN or (len(sonraki) > 4 and re.search(r"[aeiou]s[iu]$", sonraki)):
                return True
    return False


def yuzdeler(ad: str) -> Set[float]:
    """Addaki yüzde değerleri: '%0,5 Yağlı' -> {0.5}. Yağ/kakao oranı farklıysa ürün aynı değildir."""
    return {float(x.replace(",", ".")) for x in re.findall(r"%\s*(\d+(?:[.,]\d+)?)", ad)}


def liste_satiri(ad: str) -> str:
    """Alışveriş listesine eklenecek satır: markasız ad ('Dost Yağlı Süt 1 Lt' -> 'Yağlı Süt 1 Lt').
    Liste her markette en ucuz karşılığını arasın diye marka atılır."""
    sirali = kelimeler(ad)
    marka, _ = ayir(sirali)
    if not marka:
        return ad.strip()
    parcalar = ad.split()
    atilacak = len(marka.split())
    # markanın kelimelerini baştan at (ad 'Dr. Oetker ...' gibi noktalı olabilir)
    while parcalar and atilacak and re.findall(r"[a-z]+", norm_ad(parcalar[0])):
        parcalar.pop(0)
        atilacak -= 1
    return " ".join(parcalar) or ad.strip()


def benzerleri(market: str, ad: str, katalog: List[dict], fiyat: Optional[float] = None) -> Optional[dict]:
    """Ürün katalogda yoksa ve fiyat da verilmediyse None."""
    dz = _dizin(katalog)
    i = dz.yer.get((market, ad))
    if i is not None:
        urun = katalog[i]
    elif fiyat:
        urun = {"market": market, "name": ad, "price": float(fiyat)}
    else:
        return None
    q, birim = urun_miktari(urun["name"])
    sirali = kelimeler(urun["name"])
    tur = tur_kelimesi(urun["name"])
    sonuc = {"urun": _ozet(urun, q, birim), "tur": tur, "liste_satiri": liste_satiri(urun["name"]),
             "diger_marketler": [], "daha_ucuz": []}
    if not tur or not urun.get("price"):
        return sonuc

    adaylar = []        # (benzerlik, ürün, miktar, birim)
    for j in dz.ters.get(tur, []):
        if j == i:
            continue
        p = katalog[j]
        if not p.get("price") or (p["market"] == market and p["name"] == urun["name"]):
            continue
        if not _kelime_eslesir([tur], norm_ad(p["name"]).split()) or _yan_urun(tur, ham_kelimeler(p["name"])):
            continue
        b, ayni_marka = dz.benzerlik(sirali, dz.sirali[j])
        if b < min(UCUZ_ESIK, MARKET_ESIK):
            continue
        pq, pb = urun_miktari(p["name"])
        adaylar.append((b, p, pq, pb, ayni_marka))

    def birim_fiyati(p, pq, pb):
        return p["price"] / pq * CARPAN[pb] if pq and pb else None

    # Öteki marketlerdeki karşılık: her marketin en benzer ürünü (eşitse birim fiyatı ucuz olan)
    en_iyi: Dict[str, tuple] = {}
    for b, p, pq, pb, ayni_marka in adaylar:
        if p["market"] == market or b < MARKET_ESIK or (birim and pb != birim):
            continue
        bf = birim_fiyati(p, pq, pb) or p["price"]
        # öncelik: yeterince benzer olanlar içinde benzer boyutta paket (1 L'ye 200 ml değil),
        # sonra benzerlik, sonra birim fiyat
        yakin = bool(q and pq and 0.5 <= pq / q <= 2)
        anahtar = (b >= 0.8, yakin, round(b, 2), -bf)
        onceki = en_iyi.get(p["market"])
        if onceki is None or anahtar > onceki[0]:
            en_iyi[p["market"]] = (anahtar, b, p, pq, pb, ayni_marka)
    for _, b, p, pq, pb, ayni_marka in en_iyi.values():
        o = _ozet(p, pq, pb, b)
        o["ayni"] = bool(ayni_marka and b >= AYNI_ESIK and (not q or (pq and abs(pq - q) <= 0.1 * q))
                         and yuzdeler(p["name"]) == yuzdeler(urun["name"]))
        sonuc["diger_marketler"].append(o)
    sonuc["diger_marketler"].sort(key=lambda o: (o["birim_fiyat"] or o["fiyat"]))

    # Daha ucuz benzerleri: birim fiyatı bu üründen en az %3 düşük olanlar (birim fiyat gerekir)
    kendi = birim_fiyati(urun, q, birim)
    if kendi:
        ucuz = [(birim_fiyati(p, pq, pb), b, p, pq, pb) for b, p, pq, pb, _ in adaylar
                if pb == birim and b >= UCUZ_ESIK]
        ucuz = sorted((x for x in ucuz if x[0] and x[0] < kendi * 0.97), key=lambda x: x[0])
        sonuc["daha_ucuz"] = [_ozet(p, pq, pb, b) for _, b, p, pq, pb in ucuz[:EN_FAZLA_UCUZ]]
    return sonuc
