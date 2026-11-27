"""Malzeme-ürün eşleştirme ve miktar ayıklama testleri."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "beslenme"))
from eslestirme import adaylar, fiyat_tablosu, tarif_maliyetleri  # noqa: E402
from miktar import parse_quantity  # noqa: E402


def test_parse_quantity():
    assert parse_quantity("Pınar Süt 1 L") == (1000.0, "ml")
    assert parse_quantity("Sütaş Süt 6x200 ml") == (1200.0, "ml")
    assert parse_quantity("Mis Uht Süt %3.1 Yağlı 200 ml") == (200.0, "ml")
    assert parse_quantity("Ülker Mercimek 2,5 Kg") == (2500.0, "g")
    assert parse_quantity("Domates Kg") == (1000.0, "g")
    assert parse_quantity("Keskinoğlu Yumurta 15'li") == (15.0, "adet")
    assert parse_quantity("Toy Toy Sürpriz Yumurta 2*20 g") == (40.0, "g")
    assert parse_quantity("Maydanoz Demet") == (None, None)


KATALOG = [
    {"market": "sok", "name": "Kuru Soğan Kg", "price": 24.9, "category": None},
    {"market": "migros", "name": "Soğan Kuru Dökme Kg", "price": 41.95, "category": "Patates, Soğan, Sarımsak"},
    {"market": "migros", "name": "Ülker Çizi Peynir & Soğan 50 G", "price": 25.0, "category": "Kraker"},
    {"market": "sok", "name": "Mis Süt 1 L", "price": 34.95, "category": None},
    {"market": "sok", "name": "Mis Kakaolu Süt 200 ml", "price": 16.5, "category": None},
    {"market": "migros", "name": "Keskinoğlu M 10'lu Yumurta", "price": 109.95, "category": "Yumurta"},
    {"market": "sok", "name": "Kinder Joy Yumurta Çikolata 20 g", "price": 42.75, "category": None},
    {"market": "sok", "name": "Crown Portakal 1,5 L", "price": 29.0, "category": None},
    {"market": "sok", "name": "Portakal Kg", "price": 49.9, "category": None},
]


def test_eslestirme_eler_ve_birim_fiyat():
    sogan = adaylar("sogan", KATALOG)
    assert [p["name"] for p in sogan] == ["Kuru Soğan Kg", "Soğan Kuru Dökme Kg"]   # kraker elendi
    sut = adaylar("sut", KATALOG)
    assert [p["name"] for p in sut] == ["Mis Süt 1 L"]                              # kakaolu elendi
    assert round(sut[0]["tl_kg"], 2) == round(34.95 / 1030 * 1000, 2)              # yoğunluk 1.03
    yum = adaylar("yumurta", KATALOG)
    assert len(yum) == 1 and yum[0]["miktar_g"] == 600                              # 10 x 60 g
    assert [p["name"] for p in adaylar("portakal", KATALOG)] == ["Portakal Kg"]      # meyve suyu elendi


def test_yeni_marketlerdeki_yanlis_eslesmeler():
    # 27.11.2026: CarrefourSA / Hakmar / Tarım Kredi ürün adlarıyla çıkan yanlış eşleşmeler
    yanlis = {
        "tavuk_but": "Yumoş Açık Hava Etkisi Mavi Gelincik 1.44 Lt",          # "gel-incik"
        "bal": "Bal Kabağı Soyulmuş 1 Kg",
        "tereyagi": "Sana Tereyağ Lezzeti 250 Gr",
        "zeytin": "Dalan Granül Matik Zeytin Mucizesi 1 Kg",
        "sivri_biber": "Mutlu Çarliston Makarna 500 Gr",
        "ispanak": "Tatsu Ispanaklı Peynirli Gül Böreği 1 Kg",
        "patates": "SuperFresh Patates Garnitürü 450 Gr",
        "tam_bugday_ekmegi": "Filiz Tam Buğday Kalem 350 Gr",
        "kinoa": "Sek Quark Kayısı-Kinoa 140 Gr",
        "yulaf": "Alpro Yulaf İçeceği 1 Lt",
        "suzme_yogurt": "Elmas Hanım Süzme Yoğurtlu Tarhana 400 Gr",
        "ceviz": "Harmony Ceviz Parçacıklı Tahin Kreması 400 Gr",
    }
    for mid, ad in yanlis.items():
        assert adaylar(mid, [{"market": "carrefour", "name": ad, "price": 50.0, "category": None}]) == [], (mid, ad)
    dogru = {"tavuk_but": "Şenpiliç Lezita Kemiksiz Tavuk But 1 Kg", "bal": "Carrefour Çiçek Balı 460 Gr",
             "tereyagi": "Carrefour Tereyağı 500 Gr", "zeytin": "Nadide Siyah Zeytin 600 Gr"}
    for mid, ad in dogru.items():
        assert len(adaylar(mid, [{"market": "hakmar", "name": ad, "price": 50.0, "category": None}])) == 1, (mid, ad)


def test_gevrek_ekmek_veya_yulaf_sayilmaz():
    # "Gevreği" normalize edilince "gevregi" olur; "gevrek" kuralı bunu yakalamıyordu
    katalog = [
        {"market": "sok", "name": "Kellogg's Special K Klasik Tam Buğday ve Pirinç Gevreği 420 g",
         "price": 195.0, "category": None},
        {"market": "sok", "name": "Uno Tam Buğday Ekmeği 400 g", "price": 30.0, "category": None},
        {"market": "sok", "name": "Söke Tam Buğday Un 1 kg", "price": 40.0, "category": None},
        {"market": "sok", "name": "Nestle Yulaf Gevreği 400 g", "price": 120.0, "category": None},
        {"market": "sok", "name": "Folife Yulaf Ezmesi 500 g", "price": 48.0, "category": None},
    ]
    # gevrek ve un elenir, "Uno" markası ("un " kuralına rağmen) elenmez
    assert [p["name"] for p in adaylar("tam_bugday_ekmegi", katalog)] == ["Uno Tam Buğday Ekmeği 400 g"]
    assert [p["name"] for p in adaylar("yulaf", katalog)] == ["Folife Yulaf Ezmesi 500 g"]


def test_nuhun_makarnasi_un_sayilmaz():
    katalog = [
        {"market": "a101", "name": "Nuh'un Ankara Spagetti Makarnası 500 G", "price": 29.5, "category": None},
        {"market": "a101", "name": "Nuh'un Ankara Buğday Unu 1 Kg", "price": 40.0, "category": None},
        {"market": "sok", "name": "Söke Un 5 Kg", "price": 150.0, "category": None},
    ]
    adlar = [p["name"] for p in adaylar("un", katalog)]
    assert "Nuh'un Ankara Spagetti Makarnası 500 G" not in adlar
    assert set(adlar) == {"Nuh'un Ankara Buğday Unu 1 Kg", "Söke Un 5 Kg"}


def test_a101_hazir_urunler_malzeme_sayilmaz():
    # A101'de kategori süzgeci yok; ad kuralları hazır ürünleri elemeli (gerçek A101 ürün adları)
    yanlislar = {
        "kasar": ["Kaşarlı Poğaça 70 G", "Aktaşlar Pidemiss Kaşarlı Pide Dondurulmuş 400 G"],
        "kabak": ["Atiye Laçin Çıtır Kabak Reçeli 350 G", "Tadım Kabak Çekirdeği 180 G"],
        "patlican": ["Çokça Köz Patlıcan 510 G", "Patlıcanlı Rulo Börek 75 G", "Burcu Sumaklı Kuru Patlıcan Dolmalık 50 G"],
        "maydanoz": ["Onet Maydanozlu Dana Köfte 500 G"],
        "patates": ["Ziyafe Patatesli Hingel Mantı 400 G"],
        "findik": ["Algida Boom Boom Kakao Fındık 80 ml", "Çerezya Tuzlu Fındık Kuruyemiş 150 G"],
        "tavuk_gogus": ["Çokça Hindi Fileto 120 G"],
        "sarimsak": ["Muti Sarımsak Dondurulmuş 225 G"],
        "ton_baligi": ["Dardanel Mısırlı Ton Balığı 160 G"],
    }
    for malzeme, adlar in yanlislar.items():
        katalog = [{"market": "a101", "name": a, "price": 50.0, "category": None} for a in adlar]
        assert adaylar(malzeme, katalog) == [], malzeme


def test_yeni_malzemeler_eslesir():
    # gerçek katalog adları (16.11.2026); her malzeme için doğru ürün alınır, benzer hazır ürünler elenir
    durumlar = {
        "suzme_yogurt": (("Mis Süzme Yoğurt 900 g", "sok", None),
                         ["Migros Süzme Peynir 500 G", "Eker Çilekli Süzme Yoğurt 150 G"]),
        "kefir": (("Birşah Sade Kefir 1 L", "a101", None),
                  ["Altınkılıç Kefirix Orman Meyveli 250 Ml", "Altınkılıç Kefirim Çilekli Kefir 1 L"]),
        "mantar": (("Kültür Mantarı 400 G", "migros", "Egzotik Sebzeler"),
                   ["Samba Trüf Mantarı Patates Cipsi 135 G", "Knorr Kremalı Mantar Çorbası 68 G"]),
        "brokoli": (("Brokoli Kg", "migros", "Mevsim Sebzeleri"),
                    ["Belu Brokoli Çorbası 60 G", "Lods İçilebilir Brokoli Yemeği 500 Ml"]),
        "kinoa": (("Yayla Gurme Beyaz Kinoa 250 G", "a101", None),
                  ["Ülker Altınbaşak Çörekotlu & Kinoalı Bisküvi 5x40 G", "Yayla Gurme Fit Kırmızı Kinoalı Bulgur 360 G"]),
        "lavas": (("Nimet Lavaş 12'li 840 G", "a101", None), []),
        "barbunya": (("Anadolu Mutfağı Barbunya 1 kg", "sok", None),
                     ["Çokça Barbunya Pilaki 400 G", "SuperFresh Barbunya Dondurulmuş 450 G"]),
    }
    for malzeme, ((dogru, market, kategori), yanlislar) in durumlar.items():
        katalog = [{"market": market, "name": dogru, "price": 50.0, "category": kategori}]
        katalog += [{"market": "a101", "name": y, "price": 10.0, "category": None} for y in yanlislar]
        assert [p["name"] for p in adaylar(malzeme, katalog)] == [dogru], malzeme
    lavas = adaylar("lavas", [{"market": "a101", "name": "Nimet Lavaş 12'li 840 G", "price": 79.0, "category": None}])
    assert lavas[0]["miktar_g"] == 840                     # "12'li" adet değil, 840 g paket


def test_tarif_maliyeti_hesaplanir():
    tablo = fiyat_tablosu(KATALOG)
    satirlar = {s["id"]: s for s in tarif_maliyetleri(tablo)}
    assert satirlar["menemen"]["porsiyon_tl"] > 0
    assert "domates" in satirlar["menemen"]["eksik_fiyat"]       # katalogda domates yok -> raporlanır
