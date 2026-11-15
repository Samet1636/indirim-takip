"""Ürün adından paket miktarını çıkarır: 'Sütaş Süt 6x200 ml' -> (1200, 'ml')."""
from __future__ import annotations

import re
from typing import Optional

_TR = str.maketrans("çğıöşüâîû", "cgiosuaiu")


def norm(s: str) -> str:
    """Karşılaştırma için: küçük harf, Türkçe karakterler sadeleşmiş, tek boşluk."""
    s = (s or "").replace("İ", "i").replace("I", "ı").lower().translate(_TR)
    return re.sub(r"\s+", " ", s).strip()


_UNIT = {"kg": ("g", 1000), "kilo": ("g", 1000), "gr": ("g", 1), "g": ("g", 1), "gram": ("g", 1),
         "lt": ("ml", 1000), "l": ("ml", 1000), "litre": ("ml", 1000), "ml": ("ml", 1), "cl": ("ml", 10)}
_U = r"(kg|kilo|gram|gr|g|litre|lt|l|ml|cl)"
_NUM = r"(\d+(?:[.,]\d+)?)"
_MULTI = re.compile(rf"(\d+)\s*(?:x|\*|×)\s*{_NUM}\s*{_U}\b")
_MULTI2 = re.compile(rf"{_NUM}\s*{_U}\s*(?:x|\*|×)\s*(\d+)\b")
_SINGLE = re.compile(rf"(?<![%\d.,]){_NUM}\s*{_U}\b")
_COUNT = re.compile(r"(\d+)\s*(?:'\s*)?(?:li|lu|lı|lü|adet)\b")
_PER_KG = re.compile(r"(?:^|\s)(kg|kilo)(?:\s|$)")


def _f(x: str) -> float:
    return float(x.replace(",", "."))


def parse_quantity(name: str) -> tuple[Optional[float], Optional[str]]:
    """(miktar, birim) döndürür; birim 'g', 'ml' veya 'adet'. Bulunamazsa (None, None)."""
    n = norm(name)
    m = _MULTI.search(n)
    if m:
        unit, k = _UNIT[m.group(3)]
        return int(m.group(1)) * _f(m.group(2)) * k, unit
    m = _MULTI2.search(n)
    if m:
        unit, k = _UNIT[m.group(2)]
        return int(m.group(3)) * _f(m.group(1)) * k, unit
    found = _SINGLE.findall(n)
    if found:
        q, u = found[-1]            # sondaki miktar genelde paket miktarıdır
        unit, k = _UNIT[u]
        return _f(q) * k, unit
    if _PER_KG.search(n):           # "Domates Kg" -> kilogram fiyatı
        return 1000.0, "g"
    m = _COUNT.search(n)
    if m:
        return float(m.group(1)), "adet"
    return None, None
