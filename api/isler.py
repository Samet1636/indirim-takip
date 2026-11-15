"""
Arka plan iş kuyruğu: plan çözümü ~1 dakika sürdüğü için istek hemen bir iş numarası döner,
telefon sonucu birkaç saniyede bir sorar.

Şimdilik işler bellekte tutulur (sunucu yeniden başlarsa kaybolur). Supabase aşamasında
sonuçlar `planlar` tablosuna yazılacak.
"""
from __future__ import annotations

import itertools
import threading
import time
import traceback
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Dict, Optional

SAKLAMA_SN = 60 * 60     # biten işler 1 saat saklanır
EN_FAZLA_IS = 200        # bellekte tutulacak en fazla iş


class IsKuyrugu:
    def __init__(self, isci_sayisi: int = 1):
        # Çözücü işlemciyi tam kullanır; aynı anda tek iş çözmek hem daha hızlı hem daha güvenli
        self._havuz = ThreadPoolExecutor(max_workers=isci_sayisi, thread_name_prefix="plan")
        self._isler: Dict[str, Dict[str, Any]] = {}
        self._kilit = threading.Lock()
        # Sıra için zaman damgası yetmez: Windows'ta time.time() ~15 ms çözünürlüklü, art arda
        # gelen iki iş aynı zamanı alabilir. Artan sayaç sırayı kesin belirler.
        self._sayac = itertools.count()

    def gonder(self, fonk: Callable[[], dict]) -> str:
        self._temizle()
        is_id = uuid.uuid4().hex
        with self._kilit:
            self._isler[is_id] = {"durum": "bekliyor", "sira_no": next(self._sayac), "bitis": None,
                                  "sonuc": None, "hata": None}
        self._havuz.submit(self._calistir, is_id, fonk)
        return is_id

    def _calistir(self, is_id: str, fonk: Callable[[], dict]) -> None:
        self._guncelle(is_id, durum="calisiyor")
        try:
            sonuc = fonk()
            self._guncelle(is_id, durum="bitti", sonuc=sonuc, bitis=time.time())
        except Exception as e:   # noqa: BLE001 — hata kullanıcıya iş durumu olarak döner
            traceback.print_exc()
            self._guncelle(is_id, durum="hata", hata=f"{type(e).__name__}: {e}", bitis=time.time())

    def _guncelle(self, is_id: str, **alanlar) -> None:
        with self._kilit:
            if is_id in self._isler:
                self._isler[is_id].update(alanlar)

    def getir(self, is_id: str) -> Optional[Dict[str, Any]]:
        with self._kilit:
            kayit = self._isler.get(is_id)
            return dict(kayit) if kayit else None

    def sira(self, is_id: str) -> int:
        """Bu işten önce bekleyen/çalışan iş sayısı (kullanıcıya 'sırada 2 kişi var' demek için)."""
        with self._kilit:
            kayit = self._isler.get(is_id)
            if not kayit or kayit["durum"] not in ("bekliyor", "calisiyor"):
                return 0
            return sum(1 for k in self._isler.values()
                       if k["durum"] in ("bekliyor", "calisiyor") and k["sira_no"] < kayit["sira_no"])

    def _temizle(self) -> None:
        simdi = time.time()
        with self._kilit:
            eski = [k for k, v in self._isler.items() if v["bitis"] and simdi - v["bitis"] > SAKLAMA_SN]
            for k in eski:
                del self._isler[k]
            biten = sorted((v["bitis"], k) for k, v in self._isler.items() if v["bitis"])
            while len(self._isler) >= EN_FAZLA_IS and biten:
                del self._isler[biten.pop(0)[1]]

    def kapat(self) -> None:
        self._havuz.shutdown(wait=False)
