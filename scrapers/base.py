"""Ortak HTTP ayarları ve yardımcılar."""
from __future__ import annotations
import logging
import random
import re
import time
from pathlib import Path
from typing import Optional

import requests

log = logging.getLogger("scraper")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/129.0 Safari/537.36"
    ),
    "Accept-Language": "tr-TR,tr;q=0.9",
}


BROWSER_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
}


def _browser_session():
    """Gerçek Chrome gibi görünen oturum (bot korumalı siteler için).
    curl_cffi kurulu değilse None döner."""
    try:
        from curl_cffi import requests as creq
    except ImportError:
        return None
    s = creq.Session(impersonate="chrome")
    s.headers.update(BROWSER_HEADERS)
    return s


class BaseScraper:
    market: str = ""
    impersonate_browser: bool = False   # True: bot korumasına takılan siteler için Chrome taklidi

    def __init__(self, dump_dir: Optional[Path] = None, delay: tuple[float, float] = (1.0, 2.5)):
        self.session = _browser_session() if self.impersonate_browser else None
        if self.session is None:
            if self.impersonate_browser:
                log.warning("%s: curl_cffi kurulu değil, normal istekle deneniyor "
                            "(pip install curl_cffi)", self.market)
            self.session = requests.Session()
            self.session.headers.update(HEADERS)
        self.dump_dir = dump_dir   # verilirse ham yanıtlar buraya kaydedilir (debug için)
        self.delay = delay

    def get(self, url: str, **kw) -> requests.Response:
        # Siteleri yormamak için her istekten önce kısa, rastgele bekleme
        time.sleep(random.uniform(*self.delay))
        resp = self.session.get(url, timeout=25, **kw)
        resp.raise_for_status()
        return resp

    def dump(self, name: str, content: str) -> None:
        if self.dump_dir:
            self.dump_dir.mkdir(parents=True, exist_ok=True)
            (self.dump_dir / f"{self.market}_{name}").write_text(content, encoding="utf-8")

    def scrape(self):
        raise NotImplementedError


def parse_tr_price(text: str) -> Optional[float]:
    """'1.299,90 ₺' -> 1299.9 , '49,50' -> 49.5 , '199,' -> 199.0"""
    if not text:
        return None
    t = re.sub(r"[^\d,.]", "", text)
    if not t:
        return None
    if "," in t:
        t = t.replace(".", "").replace(",", ".")
    elif t.count(".") == 1 and len(t.split(".")[1]) == 3:
        t = t.replace(".", "")   # "1.299" binlik ayraç
    t = t.rstrip(".")
    try:
        return float(t)
    except ValueError:
        return None
