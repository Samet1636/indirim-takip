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
import time
from pathlib import Path
from typing import List, Literal, Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "beslenme"))
import plan  # noqa: E402
import tarif_ozet  # noqa: E402
from hedef import hesapla  # noqa: E402
from miktar import norm, norm_ad  # noqa: E402

from . import karsilastirma  # noqa: E402
from .isler import IsKuyrugu  # noqa: E402

TIBBI_NOT = "Bu plan genel bilgilendirme amaçlıdır, tıbbi tavsiye değildir."
SURE_SINIRI = int(os.environ.get("PLAN_SURE_SINIRI", "60"))
EN_FAZLA_BEKLEYEN = int(os.environ.get("EN_FAZLA_BEKLEYEN", "8"))   # sırada + çalışan plan işi
IP_SAATLIK_PLAN = int(os.environ.get("IP_SAATLIK_PLAN", "6"))       # kişi (IP) başına saatlik plan


def istemci_ip(request) -> str:
    """İsteği yapanın IP adresi. Render gibi bir vekil sunucunun arkasında gerçek adres
    X-Forwarded-For başlığında gelir. Not: bu başlık sahte gönderilebilir; kişi başı sınır kötü
    niyetli birini tamamen durdurmaz, asıl koruma EN_FAZLA_BEKLEYEN genel sınırıdır."""
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "bilinmiyor"


# ---------------------------------------------------------------- katalog
class Katalog:
    """Ürün kataloğu.
    - Yerelde: data/katalog.json'u okur; dosya değişince (bot her sabah günceller) yeniden yükler.
    - Bulutta: KATALOG_URL tanımlıysa kataloğu oradan (GitHub Pages) indirir ve birkaç saatte bir
      yeniler. Böylece sunucuyu her gün yeniden kurmaya gerek kalmaz. İndirme başarısız olursa
      eldeki son katalogla (o da yoksa yerel dosyayla) devam eder."""

    def __init__(self, yol: Path, url: Optional[str] = None, yenile_sn: int = 6 * 3600):
        self.yol = yol
        self.url = url
        self.yenile_sn = yenile_sn
        self._veri: List[dict] = []
        self._mtime: Optional[float] = None
        self._uzak: Optional[List[dict]] = None
        self._sonraki_deneme = 0.0
        self._kilit = threading.Lock()

    def _indir(self) -> List[dict]:
        import requests
        r = requests.get(self.url, timeout=60)
        r.raise_for_status()
        veri = r.json()
        if not isinstance(veri, list) or len(veri) < 1000:   # yarım/bozuk dosyaya karşı
            raise ValueError("katalog beklenenden küçük")
        return veri

    def getir(self) -> List[dict]:
        with self._kilit:
            if self.url:
                if time.time() >= self._sonraki_deneme:
                    try:
                        self._uzak = self._indir()
                        self._sonraki_deneme = time.time() + self.yenile_sn
                    except Exception as e:   # noqa: BLE001
                        print(f"katalog indirilemedi: {type(e).__name__}: {e}", file=sys.stderr)
                        self._sonraki_deneme = time.time() + 600   # 10 dk sonra tekrar dene
                if self._uzak is not None:
                    return self._uzak
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


Ekipman = Literal["ocak", "firin", "airfryer", "mikrodalga", "blender", "tost_makinesi"]
Alerjen = Literal["sut", "yumurta", "gluten", "kuruyemis", "balik", "susam"]

EKIPMAN_ADI = {"ocak": "Ocak", "firin": "Fırın", "airfryer": "Airfryer", "mikrodalga": "Mikrodalga",
               "blender": "Blender", "tost_makinesi": "Tost makinesi"}
ALERJEN_ADI = {"sut": "Süt ürünleri", "yumurta": "Yumurta", "gluten": "Gluten", "kuruyemis": "Kuruyemiş",
               "balik": "Balık", "susam": "Susam / tahin"}


class PlanIstegi(Kisi):
    paket: Literal["ekonomik", "vejetaryen", "yuksek_protein", "pratik"] = "ekonomik"
    market: int = Field(2, ge=1, le=4, description="en fazla kaç markete gidilsin")
    ekipman: Optional[List[Ekipman]] = Field(None, description="mutfaktaki ekipmanlar; boş bırakılırsa kısıt yok")
    alerjen: List[Alerjen] = Field(default_factory=list, description="kaçınılan besin grupları")
    haric_malzeme: List[str] = Field(default_factory=list, description="istenmeyen malzeme id'leri")
    max_sure: Optional[int] = Field(None, ge=5, le=240, description="tarif başına en fazla dakika")
    ara_ogun: int = Field(2, ge=0, le=2, description="günde en fazla kaç ara öğün")


class ListeIstegi(BaseModel):
    kalemler: List[str] = Field(..., min_length=1, max_length=40, description="her satır bir ürün: '2 L süt'")


def kisi_sozlugu(k: Kisi) -> dict:
    return dict(kilo=k.kilo, boy=k.boy, yas=k.yas, cinsiyet=k.cinsiyet, aktivite=k.aktivite, hedef=k.hedef)


# ---------------------------------------------------------------- uygulama
def uygulama_olustur() -> FastAPI:
    app = FastAPI(title="İndirim Takip — Beslenme Planı", version="0.1.0")
    # Expo web önizlemesi için; telefon uygulaması CORS'a takılmaz. Kimlik bilgisi taşınmıyor.
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET", "POST"], allow_headers=["*"])
    app.state.katalog = Katalog(katalog_yolu(), url=os.environ.get("KATALOG_URL") or None)
    app.state.kuyruk = IsKuyrugu()
    app.state.ip_gecmis = {}      # ip -> son bir saatteki plan isteklerinin zamanları
    app.state.ip_son_is = {}      # ip -> son plan işinin numarası
    app.state.ip_kilit = threading.Lock()

    def isit():   # ürün eşleştirmesini ilk plan isteğini bekletmeden, arka planda hazırla
        try:
            plan.onbellek_isit(app.state.katalog.getir())
        except Exception as e:   # noqa: BLE001
            print(f"önbellek ısıtılamadı: {type(e).__name__}: {e}", file=sys.stderr)
    if os.environ.get("KATALOG_URL"):
        threading.Thread(target=isit, daemon=True).start()

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
                 and all(k in norm_ad(p["name"]) for k in kelimeler)]
        anahtar = {
            "ucuz": lambda p: p["price"],
            "indirim": lambda p: -(p.get("discount_pct") or 0),
            "ad": lambda p: norm_ad(p["name"]),
        }[siralama]
        sonuc.sort(key=anahtar)
        bas = (sayfa - 1) * adet
        return {"toplam": len(sonuc), "sayfa": sayfa, "urunler": sonuc[bas:bas + adet]}

    @app.get("/secenekler")
    def secenekler():
        """Soru sihirbazının seçenekleri (uygulama listeleri buradan alır, tek kaynak burası)."""
        malz, tarifler = tarif_ozet.yukle()
        kullanilan = {x["malzeme"] for t in tarifler for x in t["malzemeler"]}
        return {
            "ekipman": [{"id": k, "ad": v} for k, v in EKIPMAN_ADI.items()],
            "alerjen": [{"id": k, "ad": v} for k, v in ALERJEN_ADI.items()],
            "malzemeler": sorted(({"id": m["id"], "ad": m["ad"], "kategori": m["kategori"]}
                                  for m in malz.values() if m["id"] in kullanilan and not m["dolapta"]),
                                 key=lambda m: m["ad"]),
            "tarif_sayisi": len(tarifler),
        }

    @app.get("/karsilastir")
    def karsilastir(q: str = Query(..., min_length=2, max_length=60)):
        """Bir ürünün marketlerdeki fiyatları, birim fiyata (TL/L, TL/kg) göre."""
        return karsilastirma.karsilastir(q, app.state.katalog.getir())

    @app.post("/liste")
    def liste(istek: ListeIstegi):
        """Alışveriş listesi: her marketteki tutar, en ucuz tek market ve en iyi iki market."""
        return karsilastirma.liste_hesapla(istek.kalemler, app.state.katalog.getir())

    @app.post("/hedef")
    def hedef(k: Kisi):
        h = hesapla(**kisi_sozlugu(k))
        return {"hedef": h.__dict__, "not": TIBBI_NOT}

    @app.post("/plan", status_code=202)
    def plan_baslat(istek: PlanIstegi, request: Request):
        kisi = kisi_sozlugu(istek)
        hesapla(**kisi)   # 18 yaş altı vb. geçersiz girdiler iş kuyruğuna girmeden reddedilsin
        if app.state.kuyruk.bekleyen() >= EN_FAZLA_BEKLEYEN:   # herkese açık sunucuda yığılmayı önle
            raise HTTPException(429, "Şu an çok fazla plan hesaplanıyor. Lütfen birkaç dakika sonra tekrar dene.")

        # Kişi başı sınır (IP adresine göre): aynı anda tek plan, saatte en fazla IP_SAATLIK_PLAN plan.
        # Biri sürekli plan isteyerek sunucuyu meşgul edip diğer kullanıcıları bekletemesin.
        ip = istemci_ip(request)
        simdi = time.time()
        with app.state.ip_kilit:
            onceki = app.state.ip_son_is.get(ip)
            if onceki and (app.state.kuyruk.getir(onceki) or {}).get("durum") in ("bekliyor", "calisiyor"):
                raise HTTPException(429, "Zaten hesaplanan bir planın var. O bitince yenisini isteyebilirsin.")
            gecmis = [t for t in app.state.ip_gecmis.get(ip, []) if simdi - t < 3600]
            if len(gecmis) >= IP_SAATLIK_PLAN:
                kalan = int((3600 - (simdi - gecmis[0])) // 60) + 1
                raise HTTPException(429, f"Bir saatte en fazla {IP_SAATLIK_PLAN} plan oluşturabilirsin. "
                                         f"Yaklaşık {kalan} dakika sonra tekrar dene.")
            gecmis.append(simdi)
            app.state.ip_gecmis[ip] = gecmis
            if len(app.state.ip_gecmis) > 10_000:   # bellek şişmesin: bir saati geçen kayıtları at
                app.state.ip_gecmis = {k: v for k, v in app.state.ip_gecmis.items() if simdi - v[-1] < 3600}
        katalog = app.state.katalog.getir()

        def is_():
            return plan.coz(katalog, kisi, paket=istek.paket, max_market=istek.market,
                            sure_siniri=SURE_SINIRI, ekipman=istek.ekipman, alerjen=istek.alerjen,
                            haric_malzeme=istek.haric_malzeme, max_sure=istek.max_sure, ara_ogun=istek.ara_ogun)

        is_id = app.state.kuyruk.gonder(is_)
        with app.state.ip_kilit:
            app.state.ip_son_is[ip] = is_id
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
