"""
Kategori sayfalarını bulmak için ortak araçlar.

Önce sitenin sitemap'ine bakıyoruz (robots.txt -> Sitemap: satırları). Sitemap, sitedeki
tüm kategori adreslerini listelediği için en güvenilir kaynak. Bulunamazsa ana sayfadaki
linklere düşüyoruz.
"""
from __future__ import annotations

import gzip
import re
from typing import Callable, Iterable
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from scrapers.base import log

_LOC = re.compile(r"<loc>\s*([^<\s]+)\s*</loc>", re.I)


def _text(resp) -> str:
    data = resp.content
    if data[:2] == b"\x1f\x8b":           # .xml.gz
        data = gzip.decompress(data)
    return data.decode("utf-8", errors="replace")


def sitemap_urls(get: Callable, base: str, pattern: re.Pattern, max_sitemaps: int = 40) -> list[str]:
    """robots.txt'teki sitemap'lerden pattern'e uyan adresleri toplar (iç içe sitemap destekli)."""
    queue: list[str] = []
    try:
        robots = get(urljoin(base, "/robots.txt")).text
        queue = [l.split(":", 1)[1].strip() for l in robots.splitlines() if l.lower().startswith("sitemap:")]
    except Exception as e:
        log.info("robots.txt okunamadı: %s", e)
    if not queue:
        queue = [urljoin(base, "/sitemap.xml")]
    seen, found = set(), []
    while queue and len(seen) < max_sitemaps:
        sm = queue.pop(0)
        if sm in seen:
            continue
        seen.add(sm)
        try:
            xml = _text(get(sm))
        except Exception as e:
            log.info("sitemap okunamadı %s: %s", sm, e)
            continue
        locs = _LOC.findall(xml)
        if "<sitemapindex" in xml[:2000].lower():
            # Önce adı kategori/category geçen alt sitemap'ler
            locs.sort(key=lambda u: 0 if re.search(r"categ|kategori", u, re.I) else 1)
            queue.extend(locs)
        else:
            found.extend(u for u in locs if pattern.search(u))
    return list(dict.fromkeys(found))


def page_links(html: str, base: str, pattern: re.Pattern, exclude: Iterable[str] = ()) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    host = urlparse(base).netloc
    out = []
    for a in soup.find_all("a", href=True):
        u = urljoin(base, a["href"]).split("#")[0].split("?")[0]
        if urlparse(u).netloc == host and pattern.search(u) and not any(x in u for x in exclude):
            out.append(u)
    return list(dict.fromkeys(out))


def slug_to_category(url: str) -> str:
    """'https://www.sokmarket.com.tr/meyve-ve-sebze-c-20' -> 'Meyve Ve Sebze'"""
    slug = urlparse(url).path.rstrip("/").split("/")[-1]
    slug = re.sub(r"-c-[0-9a-z]+$", "", slug)
    return slug.replace("-", " ").title()
