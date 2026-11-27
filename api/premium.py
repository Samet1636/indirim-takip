"""
Premium abonelik kontrolü (RevenueCat).

Satın alma telefonda Apple / Google'ın kendi ödeme sistemiyle yapılır; RevenueCat aboneliği
kullanıcının Supabase kimliğiyle (app_user_id) eşleştirir. Sunucu, plan isteğinde uygulamaya
güvenmeden RevenueCat'e sorar: bu kullanıcının "premium" hakkı (entitlement) şu an aktif mi?

Ortam değişkeni: REVENUECAT_SECRET_KEY (RevenueCat > Project settings > API keys > Secret key).
GİZLİDİR: sadece Render'ın ayarlarına girilir, hiçbir dosyaya yazılmaz. Tanımlı değilse kimse
premium sayılmaz (yerel geliştirme ve testler).
"""
from __future__ import annotations

import os
import threading
import time
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple
from urllib.parse import quote

import requests

API = "https://api.revenuecat.com/v1"
HAK_ADI = os.environ.get("REVENUECAT_HAK", "premium")      # RevenueCat'teki entitlement kimliği
ONBELLEK_SN = 300


class PremiumHatasi(Exception):
    """RevenueCat'e ulaşılamadı (kullanıcının hatası değil)."""


def _tarih(s: Optional[str]) -> Optional[datetime]:
    return datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None


def aktif_hak(cevap: dict, hak_adi: str = HAK_ADI, simdi: Optional[datetime] = None) -> Tuple[bool, Optional[datetime]]:
    """RevenueCat /subscribers cevabından (aktif mi, bitiş). Bitiş yoksa ömür boyu demektir."""
    simdi = simdi or datetime.now(timezone.utc)
    h = ((cevap.get("subscriber") or {}).get("entitlements") or {}).get(hak_adi)
    if not h:
        return False, None
    bitis = _tarih(h.get("expires_date"))
    # ödeme sorunu yaşayan abonelere mağazanın tanıdığı ek süre
    ek = _tarih(h.get("grace_period_expires_date"))
    son = max([t for t in (bitis, ek) if t], default=None)
    return (son is None or son > simdi), son


class RevenueCat:
    def __init__(self, gizli_anahtar: str, oturum=None):
        self.anahtar = gizli_anahtar
        self.http = oturum or requests.Session()
        self._onbellek: Dict[str, Tuple[float, Tuple[bool, Optional[datetime]]]] = {}
        self._kilit = threading.Lock()

    def durum(self, kullanici_id: str, taze: bool = False) -> Tuple[bool, Optional[datetime]]:
        """(premium mu, abonelik bitişi). Sonuç 5 dakika saklanır; taze=True (satın almadan hemen
        sonra) önbelleği atlar, ama aynı kişi için en fazla 10 sn'de bir."""
        simdi = time.time()
        with self._kilit:
            k = self._onbellek.get(kullanici_id)
            if k and simdi - k[0] < (10 if taze else ONBELLEK_SN):
                return k[1]
        try:
            r = self.http.get(f"{API}/subscribers/{quote(kullanici_id, safe='')}", timeout=15,
                              headers={"Authorization": f"Bearer {self.anahtar}"})
        except requests.RequestException as e:
            raise PremiumHatasi(str(e)) from e
        if r.status_code != 200:
            raise PremiumHatasi(f"revenuecat {r.status_code}")
        sonuc = aktif_hak(r.json())
        with self._kilit:
            if len(self._onbellek) > 5000:
                self._onbellek.clear()
            self._onbellek[kullanici_id] = (simdi, sonuc)
        return sonuc


def ortamdan() -> Optional[RevenueCat]:
    anahtar = os.environ.get("REVENUECAT_SECRET_KEY")
    return RevenueCat(anahtar) if anahtar else None
