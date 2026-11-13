"""
A101 Kapıda – "Aldın Aldın" ürünleri.

A101'in sitesi Cloudflare bot korumalı: normal HTTP istekleri (requests, curl_cffi) 403 alıyor.
Bu yüzden bilgisayardaki gerçek Chrome'u (Playwright ile) açıp Kapıda'nın Aldın Aldın
sayfasına giriyoruz. Sayfa açılırken tarayıcı ürün listesini A101'in kendi arama
API'sinden çekiyor:

    https://rio.a101.com.tr/.../CALL/Store/search/<mağaza>?...&data=<base64>
    data = {"channel":"SLOT","filters":[{"field":"promotionCode","value":"Z110"}],"from":0,"limit":500}

Biz bu yanıtı yakalayıp okuyoruz. Yanıttaki her ürün:
    {"id", "attributes": {"name", "seoUrl", "brand"}, "images": [{"url"}],
     "price": {"normal": 45900, "discounted": 22900, "discountRate": 50}, "stock": 3}
Fiyatlar KURUŞ cinsinden.

Kurulum:  pip install playwright
(Bilgisayarda Chrome veya Edge varsa ayrıca tarayıcı indirmek gerekmez.)
Tarayıcıyı görerek denemek için:  python run.py --only a101 --dump --goster
"""
from __future__ import annotations

import json

from models import Offer
from scrapers.base import log
from scrapers.campaign import CampaignScraper
from scrapers.nextjs import discover_links

CHROME_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
             "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36")
SEARCH_API_MARK = "/CALL/Store/search/"


def parse_a101_search(data: dict) -> list[Offer]:
    """A101 Store/search API yanıtını Offer listesine çevirir."""
    offers = []
    for r in (data or {}).get("results") or []:
        attrs = r.get("attributes") or {}
        price = r.get("price") or {}
        name = (attrs.get("name") or "").strip()
        normal = price.get("normal")
        current = price.get("discounted") or normal
        if not name or not isinstance(current, (int, float)) or current <= 0:
            continue
        if r.get("isEnabled") is False or (isinstance(r.get("stock"), int) and r["stock"] <= 0):
            continue
        regular = normal / 100 if isinstance(normal, (int, float)) and normal > current else None
        images = r.get("images") or []
        image = images[0].get("url") if images and isinstance(images[0], dict) else None
        cats = r.get("categories") or []
        offers.append(Offer(
            market="a101",
            market_product_id=str(r.get("id") or attrs.get("seoUrl") or name),
            name=name,
            price=round(current / 100, 2),
            regular_price=round(regular, 2) if regular else None,
            url=attrs.get("seoUrl"),
            image_url=image,
            category=cats[-1].get("name") if cats and isinstance(cats[-1], dict) else None,
            is_campaign=True,   # Aldın Aldın ürünü (indirim oranı olmasa da kampanya fiyatı)
        ))
    return offers


class A101Scraper(CampaignScraper):
    market = "a101"
    base = "https://www.a101.com.tr"
    seed_urls = ["https://www.a101.com.tr/kapida/aldin-aldin"]
    # Ana sayfadan sadece Kapıda'daki (ürün listeli) kampanya sayfalarını al; afiş/broşür
    # sayfaları resimden ibaret olduğu için atlanır.
    keywords = ["/kapida/aldin-aldin", "/kapida/haftanin-yildizlari", "/kapida/firsat",
                "/kapida/indirim", "/kapida/kampanya"]
    exclude = ["brosur", "afis", "giris", "uye", "sepet", "hesabim", "yardim"]
    max_collections = 3
    impersonate_browser = False   # HTTP oturumu kullanılmıyor, tarayıcı kullanılıyor
    headful = False               # True: tarayıcı penceresi görünür açılır (deneme için)

    def scrape(self):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            log.warning("a101: playwright kurulu değil. Kurmak için: pip install playwright")
            return []

        found: dict[str, Offer] = {}
        with sync_playwright() as pw:
            # Önce bilgisayarda kurulu Chrome/Edge (bot korumasına karşı daha inandırıcı),
            # yoksa Playwright'ın kendi Chromium'u.
            browser = None
            for channel in ("chrome", "msedge", None):
                try:
                    browser = pw.chromium.launch(channel=channel, headless=not self.headful,
                                                 args=["--disable-blink-features=AutomationControlled"])
                    log.info("a101: tarayıcı: %s", channel or "playwright chromium")
                    break
                except Exception as e:
                    log.debug("a101: %s açılamadı: %s", channel, e)
            if browser is None:
                log.warning("a101: hiçbir tarayıcı açılamadı. Chrome kurulu değilse: "
                            "python -m playwright install chromium")
                return []

            ctx = browser.new_context(locale="tr-TR", user_agent=CHROME_UA,
                                      viewport={"width": 1366, "height": 900},
                                      timezone_id="Europe/Istanbul")
            ctx.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            page = ctx.new_page()
            search_responses = []
            page.on("response", lambda r: search_responses.append(r) if SEARCH_API_MARK in r.url else None)

            def visit(url, label):
                search_responses.clear()
                resp = page.goto(url, wait_until="domcontentloaded", timeout=60_000)
                status = resp.status if resp else "?"
                try:   # çerez penceresi
                    page.get_by_role("button", name="REDDET").click(timeout=3000)
                except Exception:
                    pass
                # Arama API'sinin yanıtını bekle (en fazla ~15 sn)
                for _ in range(30):
                    if search_responses:
                        break
                    page.wait_for_timeout(500)
                page.wait_for_timeout(1500)
                html = page.content()
                self.dump(f"{label}.html", html)
                if self.dump_dir:
                    page.screenshot(path=str(self.dump_dir / f"a101_{label}.png"))
                log.info("a101: %s açıldı (HTTP %s, başlık: %r)", url, status, page.title())
                if status == 403 or "Just a moment" in page.title():
                    log.warning("a101: bot korumasına takıldı. --goster ile pencereyi açıp bak.")
                offers = []
                for k, r in enumerate(list(search_responses), 1):
                    try:
                        data = r.json()
                    except Exception:
                        continue
                    if self.dump_dir:
                        (self.dump_dir / f"a101_{label}_search{k}.json").write_text(
                            json.dumps({"url": r.url, "data": data}, ensure_ascii=False, indent=1),
                            encoding="utf-8")
                    got = parse_a101_search(data)
                    log.info("a101:   arama API'si -> %d ürün", len(got))
                    offers += got
                return html, offers

            try:
                try:   # ana sayfa: hem çerezler alınır hem de yeni kampanya linkleri aranır
                    home, _ = visit(self.base, "home")
                    discovered = discover_links(home, self.base, self.keywords, self.exclude)
                except Exception as e:
                    log.warning("a101: ana sayfa açılamadı: %s", e)
                    discovered = []
                links = list(self.seed_urls) + discovered
                links = list(dict.fromkeys(links))[: len(self.seed_urls) + self.max_collections]
                log.info("a101: taranacak sayfalar: %s", links)
                for i, url in enumerate(links):
                    try:
                        _, offers = visit(url, f"sayfa{i}")
                    except Exception as e:
                        log.warning("a101: %s açılamadı: %s", url, e)
                        continue
                    new = sum(1 for o in offers if o.market_product_id not in found)
                    for o in offers:
                        found.setdefault(o.market_product_id, o)
                    log.info("a101: %s -> %d ürün (%d yeni)", url, len(offers), new)
            finally:
                browser.close()

        if not found:
            log.warning("a101: hiç ürün bulunamadı. 'python run.py --only a101 --dump --goster' ile kontrol et")
        return list(found.values())
