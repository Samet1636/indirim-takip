"""
Beslenme planı sunucusu (FastAPI). Mobil uygulama bu adreslerle konuşur:

  GET  /saglik            sunucu ve katalog durumu
  GET  /urunler           tüm ürünlerde arama (?q=süt&market=sok&siralama=ucuz&sayfa=1)
  POST /hedef             kalori/makro hedefi (anında)
  POST /plan              haftalık plan işini başlatır -> {"is_id": ...}
  GET  /plan/{is_id}      işin durumu; bittiyse plan + alışveriş listesi

Çalıştırma (proje klasöründe):
  uvicorn api.main:app --reload
  -> http://127.0.0.1:8000/docs  (tarayıcıdan deneme sayfası)
"""
from __future__ import annotations

import json
import os
import sys
import threading
from pathlib import Path
from typing import List, Literal, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "beslenme"))
import plan  # noqa: E402
from hedef import hesapla  # noqa: E402
from miktar import norm  # noqa: E402

from .isler import IsKuyrugu  # noqa: E402

TIBBI_NOT = "Bu plan genel bilgilendirme amaçlıdır, tıbbi tavsiye değildir."
SURE_SINIRI = int(os.environ.get("PLAN_SURE_SINIRI", "60"))


# ---------------------------------------------------------------- katalog
class Katalog:
    """data/katalog.json'u okur; dosya değişince (bot her sabah günceller) yeniden yükler."""

    def __init__(self, yol: Path):
        self.yol = yol
        self._veri: List[dict] = []
        self._mtime: Optional[float] = None
        self._kilit = threading.Lock()

    def getir(self) -> List[dict]:
        with self._kilit:
            mtime = self.yol.stat().st_mtime
            if mtime != self._mtime:
                self._veri = json.loads(self.yol.read_text(encoding="utf-8"))
                self._mtime = mtime
            return self._veri


def katalog_yolu() -> Path:
    return Path(os.environ.get("KATALOG_YOLU", str(KOK / "data" / "katalog.json")))


# ---------------------------------------------------------------- girdiler
class Kisi(BaseModel):
    kilo: float = Field(..., ge=35, le=250, description="kg")
    boy: float = Field(..., ge=130, le=230, description="cm")
    yas: int = Field(..., ge=0, le=100)   # 18 yaş kuralı hedef.py'de (tek yerde kalsın)
    cinsiyet: Literal["erkek", "kadin"]
    aktivite: Literal["hareketsiz", "hafif", "orta", "yuksek", "cok_yuksek"] = "orta"
    hedef: Literal["kilo_ver", "koru", "kilo_al"] = "koru"


class PlanIstegi(Kisi):
    paket: Literal["ekonomik", "vejetaryen", "yuksek_protein", "pratik"] = "ekonomik"
    market: int = Field(2, ge=1, le=4, description="en fazla kaç markete gidilsin")


def kisi_sozlugu(k: Kisi) -> dict:
    return dict(kilo=k.kilo, boy=k.boy, yas=k.yas, cinsiyet=k.cinsiyet, aktivite=k.aktivite, hedef=k.hedef)


# ---------------------------------------------------------------- uygulama
def uygulama_olustur() -> FastAPI:
    app = FastAPI(title="İndirim Takip — Beslenme Planı", version="0.1.0")
    # Expo web önizlemesi için; telefon uygulaması CORS'a takılmaz. Kimlik bilgisi taşınmıyor.
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET", "POST"], allow_headers=["*"])
    app.state.katalog = Katalog(katalog_yolu())
    app.state.kuyruk = IsKuyrugu()

    @app.exception_handler(ValueError)
    async def deger_hatasi(_, e: ValueError):
        # hedef.py'nin güvenlik kontrolleri (18 yaş altı vb.) kullanıcıya Türkçe mesajla döner
        return JSONResponse(status_code=422, content={"detail": str(e)})

    @app.get("/saglik")
    def saglik():
        try:
            n = len(app.state.katalog.getir())
        except FileNotFoundError:
            n = 0
        return {"durum": "ok", "katalog_urun_sayisi": n}

    @app.get("/urunler")
    def urunler(q: str = "", market: Optional[str] = None, siralama: Literal["ucuz", "indirim", "ad"] = "ucuz",
                sayfa: int = Query(1, ge=1), adet: int = Query(40, ge=1, le=100)):
        """Tüm ürünler kataloğunda arama (Türkçe karakter ve büyük/küçük harf duyarsız)."""
        kelimeler = norm(q).split()
        sonuc = [p for p in app.state.katalog.getir()
                 if (not market or p["market"] == market)
                 and all(k in norm(p["name"]) for k in kelimeler)]
        anahtar = {
            "ucuz": lambda p: p["price"],
            "indirim": lambda p: -(p.get("discount_pct") or 0),
            "ad": lambda p: norm(p["name"]),
        }[siralama]
        sonuc.sort(key=anahtar)
        bas = (sayfa - 1) * adet
        return {"toplam": len(sonuc), "sayfa": sayfa, "urunler": sonuc[bas:bas + adet]}

    @app.post("/hedef")
    def hedef(k: Kisi):
        h = hesapla(**kisi_sozlugu(k))
        return {"hedef": h.__dict__, "not": TIBBI_NOT}

    @app.post("/plan", status_code=202)
    def plan_baslat(istek: PlanIstegi):
        kisi = kisi_sozlugu(istek)
        hesapla(**kisi)   # 18 yaş altı vb. geçersiz girdiler iş kuyruğuna girmeden reddedilsin
        katalog = app.state.katalog.getir()

        def is_():
            return plan.coz(katalog, kisi, paket=istek.paket, max_market=istek.market,
                            sure_siniri=SURE_SINIRI)

        is_id = app.state.kuyruk.gonder(is_)
        return {"is_id": is_id, "durum": "bekliyor", "tahmini_sure_sn": SURE_SINIRI + 10}

    @app.get("/plan/{is_id}")
    def plan_durum(is_id: str):
        kayit = app.state.kuyruk.getir(is_id)
        if not kayit:
            raise HTTPException(404, "Bu numarayla bir plan işi bulunamadı (süresi dolmuş olabilir).")
        cevap = {"is_id": is_id, "durum": kayit["durum"]}
        if kayit["durum"] in ("bekliyor", "calisiyor"):
            cevap["onundeki_is"] = app.state.kuyruk.sira(is_id)
        elif kayit["durum"] == "bitti":
            cevap["sonuc"] = {**kayit["sonuc"], "not": TIBBI_NOT}
        else:
            cevap["hata"] = "Plan hesaplanırken bir hata oluştu. Lütfen tekrar deneyin."
        return cevap

    return app


app = uygulama_olustur()
