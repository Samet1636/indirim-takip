"""Tüm marketlerin scraper'larının ürettiği ortak veri yapısı."""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from datetime import date
from typing import Optional


@dataclass
class Offer:
    market: str                      # "migros", "bim" ...
    market_product_id: str           # marketin kendi ürün kimliği / slug'ı
    name: str                        # "Pınar Süt Tam Yağlı 1 L"
    price: float                     # şu anki (indirimli) fiyat, TL
    regular_price: Optional[float] = None   # indirim öncesi fiyat (biliniyorsa)
    url: Optional[str] = None
    image_url: Optional[str] = None
    category: Optional[str] = None
    is_campaign: bool = False        # aktüel / kampanya ürünü mü
    valid_from: Optional[str] = None # kampanya başlangıcı (YYYY-MM-DD)
    scraped_on: str = field(default_factory=lambda: date.today().isoformat())

    @property
    def discount_pct(self) -> Optional[float]:
        if self.regular_price and self.regular_price > self.price:
            return round(100 * (1 - self.price / self.regular_price), 1)
        return None

    @property
    def is_discounted(self) -> bool:
        return self.is_campaign or self.discount_pct is not None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["discount_pct"] = self.discount_pct
        return d
