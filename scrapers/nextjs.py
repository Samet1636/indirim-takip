"""
Next.js ile yapılmış market sitelerinden (A101, ŞOK) ürün çıkarmak için ortak araçlar.

Bu siteler ürün verisini HTML'in içine JSON olarak gömüyor. İki biçim var:
  1) <script id="__NEXT_DATA__">{...}</script>          (eski "pages" yapısı)
  2) self.__next_f.push([1,"..."]) parçaları             (yeni "app router" yapısı)

Sitenin JSON şemasını önceden bilmediğimiz için, bütün JSON'u dolaşıp
"ürüne benzeyen" nesneleri (adı ve fiyatı olan) topluyoruz. Alan adları
sitede farklıysa aşağıdaki anahtar listelerine eklemek yeterli.
"""
from __future__ import annotations

import json
import re
from statistics import median
from typing import Iterator, Optional
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from scrapers.base import parse_tr_price

NAME_KEYS = ["name", "title", "productName", "displayName", "shortName"]
CURRENT_PRICE_KEYS = ["discountedPrice", "salePrice", "currentPrice", "sellingPrice", "finalPrice",
                      "campaignPrice", "promotionPrice", "specialPrice", "price"]
ORIGINAL_PRICE_KEYS = ["originalPrice", "oldPrice", "listPrice", "regularPrice", "strikeThroughPrice",
                       "strikethroughPrice", "crossedPrice", "normalPrice", "marketPrice", "previousPrice"]
ID_KEYS = ["id", "productId", "sku", "code", "barcode", "productCode"]
URL_KEYS = ["url", "slug", "seoUrl", "link", "href", "path"]
IMAGE_KEYS = ["image", "imageUrl", "images", "thumbnail", "img", "picture", "media"]
VALUE_KEYS = ["value", "amount", "discounted", "current", "normal", "price"]

_RSC_PUSH = re.compile(r'self\.__next_f\.push\(\[1,\s*("(?:[^"\\]|\\.)*")\]\)', re.S)
_RSC_ROW = re.compile(r"^[0-9a-zA-Z]+:(.*)$")


def extract_payloads(html: str) -> list:
    """HTML'deki tüm gömülü JSON'ları döndürür."""
    out = []
    soup = BeautifulSoup(html, "lxml")
    tag = soup.find("script", id="__NEXT_DATA__")
    if tag and tag.string:
        try:
            out.append(json.loads(tag.string))
        except ValueError:
            pass
    # App router: string parçalarını birleştir, satır satır JSON dene
    chunks = []
    for m in _RSC_PUSH.finditer(html):
        try:
            chunks.append(json.loads(m.group(1)))
        except ValueError:
            continue
    for line in "".join(chunks).split("\n"):
        m = _RSC_ROW.match(line)
        if not m:
            continue
        body = m.group(1)
        if not body or body[0] not in "[{":
            continue
        try:
            out.append(json.loads(body))
        except ValueError:
            continue
    # application/ld+json içinde de ürün listesi olabilir
    for t in soup.find_all("script", type="application/ld+json"):
        try:
            out.append(json.loads(t.string or ""))
        except ValueError:
            pass
    return out


def _num(v) -> Optional[float]:
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v) if v > 0 else None
    if isinstance(v, str):
        return parse_tr_price(v)
    if isinstance(v, dict):
        for k in VALUE_KEYS:
            if k in v:
                n = _num(v[k])
                if n:
                    return n
    return None


def _first_num(d: dict, keys: list[str]) -> Optional[float]:
    for k in keys:
        if k in d:
            n = _num(d[k])
            if n:
                return n
    return None


def _prices(d: dict) -> tuple[Optional[float], Optional[float]]:
    current = _first_num(d, CURRENT_PRICE_KEYS)
    original = _first_num(d, ORIGINAL_PRICE_KEYS)
    # "price": {"normal": 50, "discounted": 40} gibi iç içe yapılar
    for k in ("price", "prices", "priceInfo", "pricing", "offers"):
        sub = d.get(k)
        if isinstance(sub, list) and sub and isinstance(sub[0], dict):
            sub = sub[0]
        if isinstance(sub, dict):
            c2 = _first_num(sub, ["discounted", "discountedPrice", "sale", "salePrice", "current", "price", "value"])
            o2 = _first_num(sub, ["normal", "original", "originalPrice", "list", "listPrice", "old", "oldPrice", "regular"])
            if c2:
                current = c2 if not current or (o2 and current >= o2) else min(current, c2)
            if o2 and not original:
                original = o2
    if original and current and original <= current:
        original = None
    return current, original


def _first_str(d: dict, keys: list[str]) -> Optional[str]:
    for k in keys:
        v = d.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return None


def _image(d: dict) -> Optional[str]:
    for k in IMAGE_KEYS:
        v = d.get(k)
        if isinstance(v, list) and v:
            v = v[0]
        if isinstance(v, dict):
            v = _first_str(v, ["url", "src", "imageUrl", "large", "medium", "small"])
        if isinstance(v, str) and (v.startswith("http") or v.startswith("/")):
            return v
    return None


def find_products(obj, _depth: int = 0) -> Iterator[dict]:
    """JSON ağacını dolaşıp ürüne benzeyen nesneleri sadeleştirilmiş halde döndürür."""
    if _depth > 40:
        return
    if isinstance(obj, dict):
        name = _first_str(obj, NAME_KEYS)
        current, original = _prices(obj)
        if name and current and len(name) >= 3 and current < 5_000_000:
            ident = next((obj[k] for k in ID_KEYS if obj.get(k) not in (None, "")), None)
            yield {
                "name": name,
                "price": current,
                "original": original,
                "id": str(ident) if ident is not None else None,
                "url": _first_str(obj, URL_KEYS),
                "image": _image(obj),
            }
            return  # ürünün içindeki alt nesneleri (varyant vb.) ayrıca saymayalım
        for v in obj.values():
            yield from find_products(v, _depth + 1)
    elif isinstance(obj, list):
        for v in obj:
            yield from find_products(v, _depth + 1)


def looks_like_kurus(prices: list[float]) -> bool:
    """Fiyatlar kuruş cinsinden mi? (Hepsi tam sayı ve medyan çok yüksekse)"""
    if len(prices) < 5:
        return False
    return all(float(p).is_integer() for p in prices) and median(prices) >= 5000


def discover_links(html: str, base: str, keywords: list[str], exclude=()) -> list[str]:
    """Ana sayfadaki kampanya/indirim sayfası linklerini, anahtar kelime eşleşmesine göre sıralar."""
    soup = BeautifulSoup(html, "lxml")
    host = urlparse(base).netloc
    scored: dict[str, int] = {}
    for a in soup.find_all("a", href=True):
        href = urljoin(base, a["href"]).split("#")[0]
        if urlparse(href).netloc != host or href.rstrip("/") == base.rstrip("/"):
            continue
        hay = (href + " " + a.get_text(" ", strip=True)).lower()
        if any(x in hay for x in exclude):
            continue
        score = sum(len(keywords) - i for i, kw in enumerate(keywords) if kw in hay)
        if score:
            scored[href] = max(scored.get(href, 0), score)
    return [u for u, _ in sorted(scored.items(), key=lambda kv: -kv[1])]
