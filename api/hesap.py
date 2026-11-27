"""
Kullanıcı hesabı ve haftalık ücretsiz plan hakkı (Supabase).

Uygulama e-posta + şifre ile Supabase'e giriş yapar ve her plan isteğinde oturum anahtarını
(Authorization: Bearer ...) gönderir. Sunucu:
  1. anahtarı Supabase'e sorarak kullanıcıyı doğrular (GET /auth/v1/user),
  2. son 7 günde kaç plan oluşturduğunu plan_kullanim tablosundan okur,
  3. plan başarıyla bitince tabloya bir satır ekler.

Sunucuda GİZLİ anahtar yok: istekler kullanıcının kendi anahtarıyla yapılır; tablodaki satır
düzeyi güvenlik (RLS) her kullanıcının sadece kendi satırlarını görmesini ve eklemesini sağlar,
silme izni yoktur (hak sıfırlanamaz). Tablo kurulumu: supabase_kurulum.sql.

Ortam değişkenleri: SUPABASE_URL, SUPABASE_ANON_KEY (herkese açık anahtar, uygulamada da var).
Tanımlı değilse hesap zorunlu değildir (yerel geliştirme ve testler).
"""
from __future__ import annotations

import os
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

import requests

AYLAR = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim",
         "Kasım", "Aralık"]
TURKIYE = timezone(timedelta(hours=3))


def tarih_metni(t: datetime) -> str:
    """'4 Aralık 21:30' (Türkiye saati)."""
    t = t.astimezone(TURKIYE)
    return f"{t.day} {AYLAR[t.month - 1]} {t:%H:%M}"


class HesapHatasi(Exception):
    """Supabase'e ulaşılamadı vb. (kullanıcının hatası değil)."""


class SupabaseHesap:
    def __init__(self, url: str, anahtar: str, oturum=None):
        self.url = url.rstrip("/")
        self.anahtar = anahtar
        self.http = oturum or requests.Session()
        self._onbellek: Dict[str, Tuple[float, dict]] = {}     # anahtar -> (zaman, kullanıcı)
        self._kilit = threading.Lock()

    def _basliklar(self, token: str) -> dict:
        return {"apikey": self.anahtar, "Authorization": f"Bearer {token}"}

    def kullanici(self, token: str) -> Optional[dict]:
        """Geçerli oturumsa {'id', 'email'}, değilse None. Sonuç 5 dakika saklanır."""
        simdi = time.time()
        with self._kilit:
            k = self._onbellek.get(token)
            if k and simdi - k[0] < 300:
                return k[1]
        try:
            r = self.http.get(f"{self.url}/auth/v1/user", headers=self._basliklar(token), timeout=15)
        except requests.RequestException as e:
            raise HesapHatasi(str(e)) from e
        if r.status_code in (401, 403):
            return None
        if r.status_code != 200:
            raise HesapHatasi(f"auth {r.status_code}")
        j = r.json()
        kullanici = {"id": j["id"], "email": j.get("email")}
        with self._kilit:
            if len(self._onbellek) > 5000:
                self._onbellek.clear()
            self._onbellek[token] = (simdi, kullanici)
        return kullanici

    def kullanimlar(self, token: str, gun: int = 7) -> List[datetime]:
        """Kullanıcının son `gun` gündeki plan zamanları (eskiden yeniye)."""
        bas = (datetime.now(timezone.utc) - timedelta(days=gun)).isoformat()
        try:
            r = self.http.get(f"{self.url}/rest/v1/plan_kullanim", headers=self._basliklar(token), timeout=15,
                              params={"select": "olusturma", "olusturma": f"gte.{bas}", "order": "olusturma.asc"})
        except requests.RequestException as e:
            raise HesapHatasi(str(e)) from e
        if r.status_code != 200:
            raise HesapHatasi(f"rest {r.status_code}")
        return [datetime.fromisoformat(x["olusturma"].replace("Z", "+00:00")) for x in r.json()]

    def kullanim_ekle(self, token: str) -> None:
        try:
            r = self.http.post(f"{self.url}/rest/v1/plan_kullanim", json={}, timeout=15,
                               headers={**self._basliklar(token), "Prefer": "return=minimal"})
        except requests.RequestException as e:
            raise HesapHatasi(str(e)) from e
        if r.status_code not in (200, 201, 204):
            raise HesapHatasi(f"insert {r.status_code}")


def hak_durumu(zamanlar: List[datetime], haftalik: int, gun: int = 7) -> dict:
    """Son 7 gündeki planlara göre kalan hak ve bir sonraki hakkın açılacağı zaman."""
    kalan = max(0, haftalik - len(zamanlar))
    yenilenme = None
    if kalan == 0 and zamanlar:
        # en eski planın üzerinden 7 gün geçince bir hak açılır
        yenilenme = sorted(zamanlar)[len(zamanlar) - haftalik] + timedelta(days=gun)
    return {"haftalik": haftalik, "kalan": kalan,
            "yenilenme": yenilenme.isoformat() if yenilenme else None,
            "yenilenme_metni": tarih_metni(yenilenme) if yenilenme else None}


def ortamdan() -> Optional[SupabaseHesap]:
    url, anahtar = os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_ANON_KEY")
    return SupabaseHesap(url, anahtar) if url and anahtar else None
