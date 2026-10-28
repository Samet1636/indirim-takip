"""
BİM Aktüel Ürünler.

Aktüel sayfası sunucu tarafında HTML olarak geliyor:
    https://www.bim.com.tr/Categories/100/aktuel-urunler.aspx
Sayfada birden fazla kampanya dönemi (sekme) olabilir; her dönemin anahtarı
'Bim_AktuelTarihKey' parametresiyle açılıyor.

BİM aktüel ürünlerinde "eski fiyat" yok, hepsi kampanya ürünü sayılıyor
(is_campaign=True).

NOT: CSS seçicileri sitenin güncel yapısına göre doğrulanmalı. Seçiciler tutmazsa
--dump ile kaydedilen HTML'e bakıp PRODUCT_SELECTORS vb. listeleri güncelle.
"""
from __future__ import annotations
import re
from datetime import date
from typing import Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from models import Offer
from scrapers.base import BaseScraper, log, parse_tr_price

BASE = "https://www.bim.com.tr"
AKTUEL_URL = BASE + "/Categories/100/aktuel-urunler.aspx"

PRODUCT_SELECTORS = ["div.product", ".productArea .product", "div.inner .product"]
TITLE_SELECTORS = ["h2.title", ".title", "h2", "h3"]
PRICE_SELECTORS = [".priceArea", ".price", ".quantify"]

TR_MONTHS = {"ocak": 1, "şubat": 2, "mart": 3, "nisan": 4, "mayıs": 5, "haziran": 6,
             "temmuz": 7, "ağustos": 8, "eylül": 9, "ekim": 10, "kasım": 11, "aralık": 12}


def _select_text(node, selectors) -> Optional[str]:
    for s in selectors:
        el = node.select_one(s)
        if el and el.get_text(strip=True):
            return el.get_text(" ", strip=True)
    return None


def _slug(text: str) -> str:
    tr = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
    return re.sub(r"[^a-z0-9]+", "-", text.translate(tr).lower()).strip("-")


def parse_tr_date(text: str, today: Optional[date] = None) -> Optional[str]:
    """'31 Ekim Cuma' -> '2026-10-31'"""
    m = re.search(r"(\d{1,2})\s+([A-Za-zÇĞİÖŞÜçğıöşü]+)", text or "")
    if not m:
        return None
    month = TR_MONTHS.get(m.group(2).lower().replace("i̇", "i"))
    if not month:
        return None
    today = today or date.today()
    year = today.year + (1 if month < today.month - 6 else 0)   # yıl dönümü durumu
    try:
        return date(year, month, int(m.group(1))).isoformat()
    except ValueError:
        return None


def parse_bim_html(html: str, valid_from: Optional[str] = None) -> list[Offer]:
    soup = BeautifulSoup(html, "lxml")
    nodes = []
    for s in PRODUCT_SELECTORS:
        nodes = soup.select(s)
        if nodes:
            break
    offers, seen = [], set()
    for n in nodes:
        name = _select_text(n, TITLE_SELECTORS)
        price_text = _select_text(n, PRICE_SELECTORS)
        price = parse_tr_price(price_text or "")
        if not name or not price:
            continue
        link = n.select_one("a[href]")
        url = urljoin(BASE, link["href"]) if link else None
        img = n.select_one("img")
        img_url = None
        if img:
            img_url = urljoin(BASE, img.get("src") or img.get("data-src") or "") or None
        pid = _slug(url.split("/aktuel-urunler/")[-1]) if url and "/aktuel-urunler/" in url else _slug(name)
        if pid in seen:
            continue
        seen.add(pid)
        offers.append(Offer(
            market="bim", market_product_id=pid, name=name, price=price,
            url=url, image_url=img_url, is_campaign=True, valid_from=valid_from,
        ))
    return offers


def find_period_links(html: str) -> list[tuple[str, Optional[str]]]:
    """Sayfadaki kampanya dönemi sekmelerini bulur: [(url, 'YYYY-MM-DD'), ...]"""
    soup = BeautifulSoup(html, "lxml")
    out = []
    for a in soup.select("a[href*='Bim_AktuelTarihKey']"):
        out.append((urljoin(BASE, a["href"]), parse_tr_date(a.get_text(" ", strip=True))))
    return list(dict.fromkeys(out))


class BimScraper(BaseScraper):
    market = "bim"

    def scrape(self) -> list[Offer]:
        html = self.get(AKTUEL_URL).text
        self.dump("aktuel.html", html)
        pages = find_period_links(html) or [(AKTUEL_URL, None)]
        found: dict[str, Offer] = {}
        for i, (url, vfrom) in enumerate(pages):
            page_html = html if url == AKTUEL_URL else self.get(url).text
            if i > 0:
                self.dump(f"aktuel_{i}.html", page_html)
            for o in parse_bim_html(page_html, vfrom):
                found.setdefault(o.market_product_id, o)
        if not found:
            log.warning("bim: hiç ürün bulunamadı, seçicileri kontrol et (--dump)")
        log.info("bim: %d aktüel ürün", len(found))
        return list(found.values())
