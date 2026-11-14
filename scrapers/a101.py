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

import base64
import json
import re
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from models import Offer
from scrapers.base import log
from scrapers.campaign import CampaignScraper
from scrapers.discovery import page_links
from scrapers.nextjs import discover_links

CHROME_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
             "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36")
# Ürün listesi getiren API'ler: kampanya sayfaları "search", kategori sayfaları "listCategoryProducts"
SEARCH_API_MARKS = ("/CALL/Store/search/", "/CALL/Store/listCategoryProducts/")
# Kapıda kategori sayfaları: /kapida/meyve-sebze veya /kapida/meyve-sebze/meyve
CATEGORY_RE = re.compile(r"a101\.com\.tr/kapida/[a-z0-9-]+(/[a-z0-9-]+)?/?$")
CATEGORY_EXCLUDE = ["aldin-aldin", "haftanin-yildizlari", "_p-", "brosur", "afis",
                    "sepet", "hesabim", "giris", "uye", "yardim", "siparis"]
# /kapida/ altında kategori olmayan bölümler
NON_CATEGORY = {"markalar", "hakkimizda", "sikca-sorulan-sorular", "sozlesmeler", "kampanyalar", "product"}


def a101_category_urls(htmls: list[str], base: str = "https://www.a101.com.tr") -> list[str]:
    """Kapıda sayfalarındaki linklerden ANA kategorileri çıkarır.
    Alt kategori linki (/kapida/su-icecek/gazli-icecekler) görülürse ana kategorisi alınır;
    ana kategori sayfası alt kategorilerin ürünlerini de içeriyor."""
    out = []
    for html in htmls:   # her sayfa ayrı ayrı (birleştirilmiş HTML doğru ayrıştırılmıyor)
        if not html:
            continue
        for u in page_links(html, base, CATEGORY_RE, CATEGORY_EXCLUDE):
            parts = urlparse(u).path.strip("/").split("/")   # ["kapida", "su-icecek", ...]
            if len(parts) < 2 or parts[1] in NON_CATEGORY:
                continue
            out.append(f"{base}/kapida/{parts[1]}")
    return list(dict.fromkeys(out))
FORBIDDEN_HEADERS = {"host", "content-length", "cookie", "connection", "accept-encoding", "user-agent",
                     "referer", "origin"}


def with_search_window(url: str, start: int, limit: int) -> str:
    """Arama API adresindeki base64 'data' parametresinin from/limit değerlerini değiştirir."""
    parts = urlparse(url)
    q = {k: v[0] for k, v in parse_qs(parts.query).items()}
    data = json.loads(base64.b64decode(q["data"] + "=" * (-len(q["data"]) % 4)).decode())
    data["from"], data["limit"] = start, limit
    q["data"] = base64.b64encode(json.dumps(data, separators=(",", ":")).encode()).decode()
    return urlunparse(parts._replace(query=urlencode(q)))


def iter_a101_products(obj, _depth: int = 0):
    """Yanıtın neresinde olursa olsun A101 ürün kayıtlarını bulur
    (arama API'sinde 'results' altında, kategori API'sinde alt kategorilere bölünmüş olabilir)."""
    if _depth > 30:
        return
    if isinstance(obj, dict):
        attrs, price = obj.get("attributes"), obj.get("price")
        if isinstance(attrs, dict) and attrs.get("name") and isinstance(price, dict):
            yield obj
            return
        for v in obj.values():
            yield from iter_a101_products(v, _depth + 1)
    elif isinstance(obj, list):
        for v in obj:
            yield from iter_a101_products(v, _depth + 1)


def parse_a101_search(data: dict, campaign: bool | None = True) -> list[Offer]:
    """A101 Store/search API yanıtını Offer listesine çevirir.
    campaign=None: ürünün kampanya rozeti (promotion) varsa kampanya sayılır (kategori sayfaları)."""
    offers = []
    for r in iter_a101_products(data):
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
            # Aldın Aldın sayfası: indirim oranı olmasa da kampanya fiyatı
            is_campaign=bool(r.get("promotion")) if campaign is None else campaign,
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

    def scrape(self, katalog: bool = False, kategori_limit: int | None = None):
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
            all_json = []   # --dump ile teşhis için: sayfanın çektiği tüm JSON yanıtları
            def on_response(r):
                if any(m in r.url for m in SEARCH_API_MARKS):
                    search_responses.append(r)
                elif self.dump_dir and "json" in (r.headers.get("content-type") or ""):
                    all_json.append(r)
            page.on("response", on_response)

            def visit(url, label):
                search_responses.clear()
                all_json.clear()
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
                if self.dump_dir and label.startswith("kategori"):
                    for k, r in enumerate(list(all_json), 1):
                        try:
                            body = r.json()
                        except Exception:
                            continue
                        (self.dump_dir / f"a101_{label}_json{k}.json").write_text(
                            json.dumps({"url": r.url, "data": body}, ensure_ascii=False, indent=1),
                            encoding="utf-8")
                        log.info("a101:   json%d %s", k, r.url[:140])
                self._last_search = list(search_responses)
                for k, r in enumerate(list(search_responses), 1):
                    try:
                        data = r.json()
                    except Exception:
                        continue
                    if self.dump_dir:
                        kind = "kategori_api" if "listCategoryProducts" in r.url else "search"
                        (self.dump_dir / f"a101_{label}_{kind}{k}.json").write_text(
                            json.dumps({"url": r.url, "data": data}, ensure_ascii=False, indent=1),
                            encoding="utf-8")
                    got = parse_a101_search(data, campaign=None if label.startswith("kategori") else True)
                    total = (data.get("total") or 0) if isinstance(data, dict) else 0
                    if total > len(data.get("results") or []):   # sayfa ürünlerin hepsini istememiş
                        got = self._fetch_all(page, r, total, label) or got
                    log.info("a101:   %s -> %d ürün (toplam %s)",
                             "kategori API'si" if "listCategoryProducts" in r.url else "arama API'si",
                             len(got), total or "?")
                    offers += got
                return html, offers

            try:
                try:   # ana sayfa: hem çerezler alınır hem de yeni kampanya linkleri aranır
                    home, _ = visit(self.base, "home")
                    discovered = discover_links(home, self.base, self.keywords, self.exclude)
                except Exception as e:
                    log.warning("a101: ana sayfa açılamadı: %s", e)
                    home, discovered = "", []
                links = list(self.seed_urls) + discovered
                links = list(dict.fromkeys(links))[: len(self.seed_urls) + self.max_collections]
                log.info("a101: taranacak sayfalar: %s", links)
                pages = [(u, f"sayfa{i}") for i, u in enumerate(links)]
                if katalog:
                    try:   # kategori menüsü Kapıda ana sayfasında
                        kapida_home, _ = visit(self.base + "/kapida", "kapida_home")
                    except Exception as e:
                        log.warning("a101: Kapıda ana sayfası açılamadı: %s", e)
                        kapida_home = ""
                    cats = a101_category_urls([kapida_home, home], self.base)
                    cats = [u for u in cats if u.rstrip("/") not in {l.rstrip("/") for l in links}
                            ][: kategori_limit or None]
                    log.info("a101: %d kategori taranacak", len(cats))
                    pages += [(u, f"kategori{i}") for i, u in enumerate(cats)]
                for url, label in pages:
                    try:
                        _, offers = visit(url, label)
                    except Exception as e:
                        log.warning("a101: %s açılamadı: %s", url, e)
                        continue
                    new = sum(1 for o in offers if o.market_product_id not in found)
                    for o in offers:
                        found.setdefault(o.market_product_id, o)   # önce gelen kampanya bilgisi korunur
                    log.info("a101: %s -> %d ürün (%d yeni)", url, len(offers), new)
            finally:
                browser.close()

        if not found:
            log.warning("a101: hiç ürün bulunamadı. 'python run.py --only a101 --dump --goster' ile kontrol et")
        return list(found.values())

    def _fetch_all(self, page, response, total: int, label: str) -> list[Offer]:
        """Sayfanın yaptığı arama isteğini, tarayıcının içinden daha büyük parçalarla tekrarlar."""
        try:
            headers = {k: v for k, v in response.request.all_headers().items()
                       if not k.startswith(":") and not k.startswith("sec-") and k.lower() not in FORBIDDEN_HEADERS}
        except Exception:
            headers = {}
        offers, step = [], 500
        for start in range(0, min(total, 5000), step):
            url = with_search_window(response.url, start, step)
            try:
                data = page.evaluate(
                    "async ([u, h]) => { const r = await fetch(u, {headers: h}); return await r.json(); }",
                    [url, headers])
            except Exception as e:
                log.warning("a101: %s için ek istek başarısız: %s", label, e)
                break
            got = parse_a101_search(data, campaign=None if label.startswith("kategori") else True)
            offers += got
            if len(data.get("results") or []) < step:
                break
        return offers
