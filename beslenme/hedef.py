"""
Kişinin günlük kalori ve makro hedefi.

Bazal metabolizma: Mifflin-St Jeor denklemi. Günlük harcama = bazal x aktivite katsayısı.
Güvenlik: kalori hiçbir zaman bazal metabolizmanın ve sabit bir alt sınırın altına inmez,
18 yaş altı için plan üretilmez. Bu hesap tıbbi tavsiye değildir.
"""
from __future__ import annotations

from dataclasses import dataclass

AKTIVITE = {"hareketsiz": 1.2, "hafif": 1.375, "orta": 1.55, "yuksek": 1.725, "cok_yuksek": 1.9}
HEDEF_CARPAN = {"kilo_ver": 0.85, "koru": 1.0, "kilo_al": 1.10}
PROTEIN_G_KG = {"kilo_ver": 1.6, "koru": 1.2, "kilo_al": 1.6}
ALT_SINIR = {"erkek": 1500, "kadin": 1200}


@dataclass
class Hedef:
    kcal: float
    protein_min: float     # g/gün
    yag_max: float         # g/gün (kalorinin %35'i)
    bazal: float
    harcama: float


def hesapla(kilo: float, boy: float, yas: int, cinsiyet: str, aktivite: str = "orta",
            hedef: str = "koru", yuksek_protein: bool = False) -> Hedef:
    if yas < 18:
        raise ValueError("Bu hesaplama 18 yaş altı için uygun değil; bir uzmana danışılmalı.")
    if cinsiyet not in ALT_SINIR:
        raise ValueError("cinsiyet 'erkek' veya 'kadin' olmalı")
    bazal = 10 * kilo + 6.25 * boy - 5 * yas + (5 if cinsiyet == "erkek" else -161)
    harcama = bazal * AKTIVITE[aktivite]
    kcal = max(harcama * HEDEF_CARPAN[hedef], bazal, ALT_SINIR[cinsiyet])
    protein = kilo * (2.0 if yuksek_protein else PROTEIN_G_KG[hedef])
    protein = min(protein, kcal * 0.35 / 4)     # proteinden gelen kalori %35'i aşmasın
    return Hedef(kcal=round(kcal), protein_min=round(protein), yag_max=round(kcal * 0.35 / 9),
                 bazal=round(bazal), harcama=round(harcama))
