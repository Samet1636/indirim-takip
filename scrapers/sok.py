"""
ŞOK Market – indirimli ürünler ve kampanya koleksiyonları.

Site Next.js (app router). Ürünler sayfanın içine gömülü JSON'da şu yapıda geliyor:
    initialSearchResult.results[] = {
        "product": {"id", "name", "path", "images": [{"host", "path"}]},
        "prices":  {"discounted": {"value": 249}, "original": {"value": 469}},
        "hasStock": true, ...
    }
Koleksiyon adresleri her hafta değişebildiği için ana sayfadan da link topluyoruz.
"""
from __future__ import annotations

import re

from scrapers.campaign import CampaignScraper
from scrapers.nextjs import extract_payloads, find_products


def _value(d):
    if isinstance(d, dict):
        v = d.get("value")
        return float(v) if isinstance(v, (int, float)) and v > 0 else None
    return None


def iter_sok_results(obj, _depth=0):
    """JSON içindeki ŞOK ürün kayıtlarını (product + prices) bulur."""
    if _depth > 60:
        return
    if isinstance(obj, dict):
        if isinstance(obj.get("product"), dict) and isinstance(obj.get("prices"), dict):
            yield obj
            return
        for v in obj.values():
            yield from iter_sok_results(v, _depth + 1)
    elif isinstance(obj, list):
        for v in obj:
            yield from iter_sok_results(v, _depth + 1)


def parse_sok_html(html: str) -> list[dict]:
    payloads = extract_payloads(html)
    items = []
    for pl in payloads:
        for r in iter_sok_results(pl):
            prod, prices = r["product"], r["prices"]
            name = prod.get("name")
            original = _value(prices.get("original"))
            current = _value(prices.get("discounted")) or original
            if not name or not current:
                continue
            if r.get("hasStock") is False:
                continue
            if original and original <= current:
                original = None
            img = None
            imgs = prod.get("images") or []
            if imgs and isinstance(imgs[0], dict) and imgs[0].get("path"):
                img = f'{imgs[0].get("host", "https://images.ceptesok.com").rstrip("/")}/{imgs[0]["path"]}'
            items.append({
                "name": name.strip(),
                "price": current,
                "original": original,
                "id": str(prod.get("id") or r.get("id")),
                "url": "/" + prod["path"] if prod.get("path") else None,
                "image": img,
            })
    if not items:   # yapı değişirse genel ayrıştırıcıya düş
        items = [p for pl in payloads for p in find_products(pl)]
    return items


class SokScraper(CampaignScraper):
    market = "sok"
    base = "https://www.sokmarket.com.tr"
    seed_urls = ["https://www.sokmarket.com.tr/indirimli-urunler-cms-pl1"]
    keywords = ["indirimli-urunler", "haftanin-firsat", "haftanın fırsat", "bu-hafta", "bu hafta",
                "firsat", "fırsat", "indirim", "aktuel", "aktüel"]
    exclude = ["giris", "uye", "sepet", "hesabim", "yardim", "magaza", "kariyer", "iletisim",
               "/kampanyalar"]
    max_collections = 4
    max_pages = 20               # indirimli ürünler ~300 ürün, sayfa başı 20
    first_page_param = 1         # sayfa numarası 0'dan mı 1'den mi başlıyor bilinmiyor:
    empty_pages_to_stop = 2      # ?page=1 ilk sayfanın tekrarı olsa bile bir sonrakini dene
    price_divisor = 1.0          # fiyatlar TL cinsinden geliyor
    # Tüm ürünler: kategori adresleri "...-c-20" ile bitiyor
    category_pattern = re.compile(r"sokmarket\.com\.tr/[a-z0-9-]+-c-\d+/?$")
    catalog_max_pages = 150
    catalog_first_page = 2       # ?page=1 ilk sayfanın tekrarı olduğu loglardan biliniyor

    def parse_items(self, html: str) -> list[dict]:
        return parse_sok_html(html)
