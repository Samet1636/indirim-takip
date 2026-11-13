"""
A101 – haftalık "Aldın Aldın" ve diğer kampanya sayfaları.
Site Next.js; ürünler sayfanın içine gömülü JSON'da geliyor.
Kampanya sayfalarının adresi ana sayfadaki linklerden otomatik bulunuyor.
"""
from __future__ import annotations

from scrapers.campaign import CampaignScraper


class A101Scraper(CampaignScraper):
    market = "a101"
    base = "https://www.a101.com.tr"
    seed_urls = []   # ilk denemeden sonra doğru kampanya adresi buraya sabitlenebilir
    keywords = ["aldin-aldin", "aldın aldın", "haftanin-yildizlari", "haftanın yıldızları",
                "firsat", "fırsat", "indirim", "kampanya", "aktuel", "aktüel"]
    exclude = ["giris", "uye", "sepet", "hesabim", "yardim", "magazalar", "kariyer", "iletisim"]
    max_collections = 4
