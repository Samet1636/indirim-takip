"""
Tarım Kredi Koop Market haftalık kampanyaları (tkkoop.com.tr).

Kampanya listesi:  https://www.tkkoop.com.tr/haftalik-kampanyalar
Her kampanyanın sayfası (/haftalik-kampanyalar/<ad>) sunucu tarafında HTML; başlıkta tarih aralığı
var ("24 - 30 Kasım Yıldönümü Kampanyası"). Ürün kartı:
    <div class="product-card campaigna"><a href=".../urun/<slug>" title="TK YAĞLI SADE SÜT"> ...
        <div class="ss_urun52"><div>12,<span>90</span><div>TL</div></div></div>
Sitede eski fiyat yok; BİM aktüel gibi hepsi kampanya ürünü sayılır (is_campaign=True).
Ürün kataloğu (tüm raf) marketfiyati.org.tr'den gelir (scrapers/marketfiyati.py); kampanya ürünleri
katalogda çift görünmesin diye run.py katalogdan çıkarır.
"""
from __future__ import annotations

import re
from datetime import date
from typing import List, Optional, Tuple
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from models import Offer
from scrapers.base import BaseScraper, log, parse_tr_price
from scrapers.bim import TR_MONTHS

BASE = "https://www.tkkoop.com.tr"
LISTE_URL = BASE + "/haftalik-kampanyalar"
MARKET = "tarim_kredi"


def kampanya_linkleri(html: str) -> List[str]:
    """Kampanya listesindeki kampanya sayfaları (tekrarsız, sırayla)."""
    s = BeautifulSoup(html, "lxml")
    linkler = [urljoin(BASE, a["href"]) for a in s.select("a[href*='/haftalik-kampanyalar/']")]
    return list(dict.fromkeys(l.split("?")[0].rstrip("/") for l in linkler))


def baslangic_tarihi(baslik: str, bugun: Optional[date] = None) -> Optional[str]:
    """'24 - 30 Kasım Yıldönümü' -> '2026-11-24'; '28 Kasım - 3 Aralık' -> '2026-11-28'."""
    harf = "A-Za-zÇĞİÖŞÜçğıöşü"
    m = re.search(rf"(\d{{1,2}})\s*([{harf}]+)?\s*-\s*\d{{1,2}}\s+([{harf}]+)", baslik or "")
    if not m:
        return None
    ay = TR_MONTHS.get((m.group(2) or m.group(3)).lower().replace("i̇", "i"))
    if not ay:
        return None
    bugun = bugun or date.today()
    yil = bugun.year + (1 if ay < bugun.month - 6 else 0) - (1 if ay > bugun.month + 6 else 0)
    try:
        return date(yil, ay, int(m.group(1))).isoformat()
    except ValueError:
        return None


def parse_kampanya(html: str, bugun: Optional[date] = None) -> Tuple[List[Offer], Optional[str]]:
    """Kampanya sayfasındaki ürünler ve kampanyanın başlangıç tarihi."""
    s = BeautifulSoup(html, "lxml")
    baslangic = baslangic_tarihi(s.title.get_text(" ", strip=True) if s.title else "", bugun)
    out, gorulen = [], set()
    for kart in s.select("div.product-card"):
        a = kart.select_one("a[href]")
        fiyat_el = kart.select_one(".ss_urun52")
        ad_el = kart.select_one(".product-title")
        ad = (a.get("title") if a else None) or (ad_el.get_text(" ", strip=True) if ad_el else None)
        fiyat = parse_tr_price(fiyat_el.get_text("", strip=True)) if fiyat_el else None
        if not a or not ad or not fiyat:
            continue
        url = urljoin(BASE, a["href"])
        pid = url.rstrip("/").split("/urun/")[-1]
        if pid in gorulen:
            continue
        gorulen.add(pid)
        img = kart.select_one("img")
        out.append(Offer(
            market=MARKET, market_product_id=f"tk-{pid}", name=" ".join(ad.split()), price=fiyat,
            url=url, image_url=urljoin(BASE, img["src"]) if img and img.get("src") else None,
            is_campaign=True, valid_from=baslangic,
        ))
    return out, baslangic


class TarimKrediScraper(BaseScraper):
    market = MARKET

    def scrape(self, katalog: bool = False, kategori_limit=None) -> List[Offer]:
        try:
            out = self._kampanyalar()
        except Exception:
            log.exception("tarim_kredi: kampanya sayfası okunamadı")
            out = []
        if katalog:
            from scrapers.marketfiyati import MarketFiyatiKatalog
            try:
                out += MarketFiyatiKatalog(MARKET, dump_dir=self.dump_dir, delay=self.delay).scrape(kategori_limit)
            except Exception:
                log.exception("tarim_kredi: marketfiyati kataloğu okunamadı")
        return out

    def _kampanyalar(self) -> List[Offer]:
        html = self.get(LISTE_URL).text
        self.dump("kampanyalar.html", html)
        bulunan: dict = {}
        for i, url in enumerate(kampanya_linkleri(html)):
            sayfa = self.get(url).text
            self.dump(f"kampanya_{i}.html", sayfa)
            urunler, baslangic = parse_kampanya(sayfa)
            log.info("tarim_kredi: %s (başlangıç %s): %d ürün", url, baslangic, len(urunler))
            for o in urunler:
                bulunan.setdefault(o.market_product_id, o)
        if not bulunan:
            log.warning("tarim_kredi: hiç kampanya ürünü bulunamadı, --dump ile sayfaya bak")
        return list(bulunan.values())
