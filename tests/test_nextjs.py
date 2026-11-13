"""A101 / ŞOK için Next.js ayrıştırıcı testleri (ağa çıkmadan)."""
import json

from scrapers.campaign import CampaignScraper
from scrapers.nextjs import discover_links, extract_payloads, find_products, looks_like_kurus

NEXT_DATA_HTML = """<html><body><script id="__NEXT_DATA__" type="application/json">%s</script></body></html>""" % json.dumps({
    "props": {"pageProps": {"banner": {"title": "Aldın Aldın"}, "products": [
        {"id": 11, "name": "Robot Süpürge", "url": "/elektronik/robot-supurge_p-11",
         "price": {"normal": 9999.0, "discounted": 7999.0}, "images": [{"url": "https://cdn/x.jpg"}]},
        {"id": 12, "name": "Filtre Kahve Makinesi", "salePrice": "1.299,50", "originalPrice": "1.499,00"},
        {"id": 13, "name": "Çay 1 kg", "price": 199.9},
    ]}}})

rsc_rows = '0:["$","div",null,{}]\n5:{"items":[{"productId":"A1","productName":"Ayçiçek Yağı 5 L","price":34995,"oldPrice":42995},' \
           '{"productId":"A2","productName":"Un 5 kg","price":12950},{"productId":"A3","productName":"Pirinç 1 kg","price":7950},' \
           '{"productId":"A4","productName":"Makarna","price":1450},{"productId":"A5","productName":"Şeker 3 kg","price":11900}]}\n'
RSC_HTML = "<html><script>self.__next_f.push([1,%s])</script></html>" % json.dumps(rsc_rows)


def test_next_data():
    items = [p for pl in extract_payloads(NEXT_DATA_HTML) for p in find_products(pl)]
    by = {p["name"]: p for p in items}
    assert set(by) == {"Robot Süpürge", "Filtre Kahve Makinesi", "Çay 1 kg"}   # banner ürün sayılmaz
    assert by["Robot Süpürge"]["price"] == 7999.0 and by["Robot Süpürge"]["original"] == 9999.0
    assert by["Robot Süpürge"]["image"] == "https://cdn/x.jpg"
    assert by["Filtre Kahve Makinesi"]["price"] == 1299.5 and by["Filtre Kahve Makinesi"]["original"] == 1499.0
    assert by["Çay 1 kg"]["original"] is None


def test_rsc_and_kurus():
    items = [p for pl in extract_payloads(RSC_HTML) for p in find_products(pl)]
    assert len(items) == 5
    assert looks_like_kurus([p["price"] for p in items])
    assert not looks_like_kurus([199.9, 49.5, 1299.0, 89.9, 15.0])


def test_discover_links():
    home = """<a href="/kategori/sut">Süt</a><a href="/aldin-aldin">Aldın Aldın</a>
              <a href="https://baska.com/firsat">dış</a><a href="/kampanyalar/indirim">İndirimler</a>
              <a href="/uye-girisi">Fırsat için giriş</a>"""
    links = discover_links(home, "https://www.a101.com.tr", ["aldin-aldin", "indirim", "fırsat"], ["giris"])
    assert links == ["https://www.a101.com.tr/aldin-aldin", "https://www.a101.com.tr/kampanyalar/indirim"]


class FakeResp:
    def __init__(self, text): self.text = text


def test_campaign_scraper_end_to_end():
    class S(CampaignScraper):
        market, base, keywords = "a101", "https://www.a101.com.tr", ["aldin-aldin"]
        def get(self, url, **kw):
            if url == self.base:
                return FakeResp('<a href="/aldin-aldin">Aldın Aldın</a>')
            if "page=2" in url:
                return FakeResp(RSC_HTML)        # 2. sayfada yeni ürünler
            if "page=3" in url:
                return FakeResp(RSC_HTML)        # tekrar -> durmalı
            return FakeResp(NEXT_DATA_HTML)
    offers = S().scrape()
    names = {o.name: o for o in offers}
    assert len(offers) == 8
    assert names["Robot Süpürge"].url == "https://www.a101.com.tr/elektronik/robot-supurge_p-11"
    assert names["Robot Süpürge"].discount_pct == 20.0 and names["Robot Süpürge"].is_campaign


def test_sok_real_page():
    from pathlib import Path
    from scrapers.sok import parse_sok_html
    html = (Path(__file__).parent / "fixtures" / "sok_sample.html").read_text(encoding="utf-8")
    items = parse_sok_html(html)
    assert len(items) == 20
    omo = next(p for p in items if p["name"].startswith("Omo Express Fresh Beyaz"))
    assert omo["price"] == 249.0 and omo["original"] == 469.0
    assert omo["url"].endswith("-p-282763") and omo["image"].startswith("https://images.ceptesok.com/")


def test_a101_search_api():
    from pathlib import Path
    from scrapers.a101 import parse_a101_search
    data = json.loads((Path(__file__).parent / "fixtures" / "a101_search_sample.json").read_text(encoding="utf-8"))["data"]
    offers = parse_a101_search(data)
    assert len(offers) == 89
    jacobs = next(o for o in offers if o.name.startswith("Jacobs Southeast"))
    assert jacobs.price == 229.0 and jacobs.regular_price == 459.0 and jacobs.discount_pct == 50.1
    assert jacobs.url.endswith("_p-30000967") and jacobs.image_url.startswith("https://cdn2.a101.com.tr/")
    pepsi = next(o for o in offers if o.name.startswith("Pepsi"))
    assert pepsi.price == 79.5 and pepsi.regular_price is None and pepsi.is_campaign
