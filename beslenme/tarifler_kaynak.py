# Tarif listesi kaynağı -> tarifler.json üretir.
# Gramajlar 1 porsiyon içindir. Besin değeri ve etiketler (vejetaryen, yüksek protein vb.)
# elle yazılmaz; tarif_ozet.py malzemelerden otomatik hesaplar.
# ogunler: kahvalti / ana (öğle veya akşam) / ara / yan (ana yemeğin yanına)
# artan: True ise çok porsiyon pişirilip ertesi güne kalabilir
import json

T = []
def t(id, ad, ogunler, sure, malz, adimlar, artan=False, aralik=(0.75, 1.5)):
    T.append({"id": id, "ad": ad, "ogunler": ogunler, "sure_dk": sure,
              "porsiyon_araligi": list(aralik), "artan": artan,
              "malzemeler": [{"malzeme": k, "gram": v} for k, v in malz.items()],
              "adimlar": adimlar})

# ---------------- KAHVALTI ----------------
t("menemen", "Menemen", ["kahvalti"], 15,
  {"yumurta": 110, "domates": 150, "sivri_biber": 40, "zeytinyagi": 8, "tam_bugday_ekmegi": 50, "tuz_baharat": 1},
  ["Biberleri zeytinyağında birkaç dakika sotele.", "Doğranmış domatesi ekle, suyunu çekene kadar pişir.",
   "Yumurtaları kırıp karıştır, kıvamını bulunca ocaktan al. Ekmekle servis et."])
t("kahvalti_tabagi", "Klasik kahvaltı tabağı", ["kahvalti"], 10,
  {"yumurta": 110, "beyaz_peynir": 40, "zeytin": 25, "domates": 100, "salatalik": 100, "tam_bugday_ekmegi": 60},
  ["Yumurtaları 8-9 dakika haşla.", "Peynir, zeytin, domates ve salatalıkla tabağa diz, ekmekle servis et."])
t("yulaf_lapasi", "Muzlu cevizli yulaf lapası", ["kahvalti"], 10,
  {"yulaf": 50, "sut": 200, "muz": 100, "ceviz": 10},
  ["Yulafı sütle kısık ateşte 5 dakika, koyulaşana kadar pişir.", "Dilimlenmiş muz ve ceviz ekleyerek servis et."])
t("gece_yulafi", "Yoğurtlu gece yulafı", ["kahvalti", "ara"], 5,
  {"yulaf": 45, "yogurt": 150, "sut": 50, "elma": 100, "bal": 8},
  ["Yulaf, yoğurt ve sütü kavanozda karıştır, buzdolabında bir gece beklet.", "Sabah rendelenmiş elma ve bal ekle."])
t("ispanakli_omlet", "Ispanaklı lorlu omlet", ["kahvalti"], 12,
  {"yumurta": 110, "ispanak": 80, "lor": 50, "zeytinyagi": 5, "tam_bugday_ekmegi": 50, "tuz_baharat": 1},
  ["Ispanağı zeytinyağında söndür.", "Lor ile çırpılmış yumurtayı üzerine dök, kısık ateşte pişir. Ekmekle servis et."])
t("peynirli_tost", "Domatesli kaşarlı tost", ["kahvalti"], 8,
  {"tam_bugday_ekmegi": 80, "kasar": 35, "domates": 60, "salatalik": 80},
  ["Ekmeklerin arasına kaşar ve domates dilimleri koy.", "Tost makinesinde veya tavada kızart, salatalıkla servis et."])
t("fistik_ezmeli_ekmek", "Fıstık ezmeli muzlu ekmek", ["kahvalti", "ara"], 3,
  {"tam_bugday_ekmegi": 60, "fistik_ezmesi": 20, "muz": 100},
  ["Ekmeğe fıstık ezmesi sür.", "Üzerine muz dilimleri diz."])
t("sebzeli_omlet", "Sebzeli omlet", ["kahvalti"], 12,
  {"yumurta": 110, "kabak": 60, "sivri_biber": 30, "domates": 60, "kasar": 15, "zeytinyagi": 5, "tam_bugday_ekmegi": 50, "tuz_baharat": 1},
  ["Kabak ve biberi zeytinyağında yumuşat, domatesi ekle.", "Çırpılmış yumurtayı dök, üzerine kaşar serp, kapağı kapalı pişir."])
t("cilbir", "Çılbır", ["kahvalti"], 15,
  {"yumurta": 110, "yogurt": 120, "sarimsak": 3, "tereyagi": 7, "tam_bugday_ekmegi": 50, "tuz_baharat": 1},
  ["Yoğurdu ezilmiş sarımsakla karıştır.", "Yumurtaları sirkeli kaynar suda 3 dakika poşe et, yoğurdun üzerine al.",
   "Tereyağını pul biberle eritip üzerine gezdir."])
t("lorlu_kahvalti", "Ballı cevizli lor tabağı", ["kahvalti"], 5,
  {"lor": 120, "bal": 10, "ceviz": 10, "domates": 100, "salatalik": 100, "tam_bugday_ekmegi": 50},
  ["Lorun üzerine bal ve ceviz ekle.", "Domates, salatalık ve ekmekle servis et."])

# ---------------- ANA YEMEKLER (öğle / akşam) ----------------
t("mercimek_corbasi", "Mercimek çorbası", ["ana"], 35,
  {"kirmizi_mercimek": 60, "sogan": 30, "havuc": 30, "patates": 40, "zeytinyagi": 7, "limon": 10, "tam_bugday_ekmegi": 50, "tuz_baharat": 1},
  ["Soğanı zeytinyağında kavur, doğranmış havuç ve patatesi ekle.", "Yıkanmış mercimeği ve sıcak suyu ekleyip 25 dakika pişir.",
   "Blenderdan geçir, limonla servis et."], artan=True)
t("ezogelin", "Ezogelin çorbası", ["ana"], 35,
  {"kirmizi_mercimek": 50, "bulgur": 20, "pirinc": 10, "sogan": 30, "salca": 10, "tereyagi": 7, "tam_bugday_ekmegi": 50, "tuz_baharat": 1},
  ["Soğanı tereyağında kavur, salçayı ekle.", "Mercimek, bulgur ve pirinci ekleyip suyla 30 dakika pişir.",
   "Nane ve pul biberle tatlandır."], artan=True)
t("yesil_mercimek_yemegi", "Yeşil mercimek yemeği", ["ana"], 40,
  {"yesil_mercimek": 70, "bulgur": 15, "sogan": 40, "salca": 10, "zeytinyagi": 8, "tuz_baharat": 1},
  ["Soğanı zeytinyağında kavur, salçayı ekle.", "Haşlanmış mercimek ve bulguru ekleyip suyla 20 dakika pişir."], artan=True)
t("kuru_fasulye", "Kuru fasulye", ["ana"], 60,
  {"kuru_fasulye": 80, "sogan": 40, "salca": 15, "zeytinyagi": 8, "tuz_baharat": 1},
  ["Fasulyeyi bir gece önceden ıslat, haşla.", "Soğanı kavur, salçayı ekle.", "Fasulye ve suyunu ekleyip 30 dakika pişir."],
  artan=True)
t("nohut_yemegi", "Nohut yemeği", ["ana"], 60,
  {"nohut": 75, "sogan": 40, "salca": 15, "domates": 60, "zeytinyagi": 8, "tuz_baharat": 1},
  ["Nohudu bir gece önceden ıslat, haşla.", "Soğan, salça ve domatesi kavur.", "Nohudu ekleyip 25 dakika pişir."], artan=True)
t("tavuk_sote", "Sebzeli tavuk sote", ["ana"], 25,
  {"tavuk_gogus": 150, "sivri_biber": 50, "domates": 100, "sogan": 40, "zeytinyagi": 8, "tuz_baharat": 1},
  ["Kuşbaşı tavuğu suyunu çekene kadar sotele.", "Soğan ve biberi ekle, ardından domatesi ekleyip 10 dakika pişir."], artan=True)
t("firin_tavuk_patates", "Fırında tavuk but ve patates", ["ana"], 50,
  {"tavuk_but": 180, "patates": 200, "sogan": 30, "zeytinyagi": 10, "salca": 5, "tuz_baharat": 1},
  ["Tavuk ve elma dilim patatesleri salça, zeytinyağı ve baharatla harmanla.", "200 derece fırında 40 dakika pişir."],
  artan=True)
t("tavuklu_bulgur", "Tavuklu bulgur pilavı", ["ana"], 35,
  {"tavuk_gogus": 120, "bulgur": 70, "sogan": 30, "sivri_biber": 30, "salca": 10, "zeytinyagi": 7, "tuz_baharat": 1},
  ["Tavuğu küçük doğrayıp sotele.", "Soğan, biber ve salçayı ekle.", "Bulgur ve iki katı sıcak suyu ekleyip demlenene kadar pişir."],
  artan=True)
t("tavuklu_makarna", "Tavuklu domates soslu makarna", ["ana"], 25,
  {"tavuk_gogus": 120, "makarna": 80, "domates": 100, "sarimsak": 5, "zeytinyagi": 7, "tuz_baharat": 1},
  ["Makarnayı haşla.", "Tavuğu sotele, sarımsak ve rendelenmiş domatesi ekleyip sos yap.", "Makarnayı sosla karıştır."])
t("ton_makarna_salatasi", "Ton balıklı makarna salatası", ["ana"], 20,
  {"makarna": 70, "ton_baligi": 80, "salatalik": 60, "domates": 60, "zeytinyagi": 8, "limon": 15, "maydanoz": 10, "tuz_baharat": 1},
  ["Makarnayı haşlayıp soğut.", "Ton balığı ve doğranmış sebzelerle karıştır, zeytinyağı ve limonla tatlandır."])
t("ton_salata", "Ton balıklı yeşil salata", ["ana"], 10,
  {"ton_baligi": 100, "marul": 100, "domates": 80, "salatalik": 80, "zeytinyagi": 8, "limon": 15, "tam_bugday_ekmegi": 50},
  ["Sebzeleri doğra.", "Ton balığını ekle, zeytinyağı ve limonla karıştır. Ekmekle servis et."])
t("izmir_kofte", "Fırında İzmir köfte", ["ana"], 50,
  {"dana_kiyma": 120, "patates": 150, "domates": 80, "sivri_biber": 30, "sogan": 20, "salca": 10, "tuz_baharat": 1},
  ["Kıymayı rendelenmiş soğan ve baharatla yoğur, köfte şekli ver.", "Patates, biber ve domatesle tepsiye diz.",
   "Salçalı su gezdirip 200 derecede 35 dakika pişir."], artan=True)
t("kiymali_makarna", "Kıymalı makarna", ["ana"], 25,
  {"dana_kiyma": 80, "makarna": 80, "sogan": 30, "salca": 10, "domates": 60, "tuz_baharat": 1},
  ["Makarnayı haşla.", "Kıymayı soğanla kavur, salça ve domatesi ekleyip sos yap.", "Makarnayı sosla karıştır."])
t("kiymali_ispanak", "Kıymalı ıspanak", ["ana"], 30,
  {"ispanak": 250, "dana_kiyma": 60, "sogan": 30, "pirinc": 15, "salca": 5, "zeytinyagi": 5, "tuz_baharat": 1},
  ["Kıymayı soğanla kavur, salçayı ekle.", "Doğranmış ıspanak ve pirinci ekleyip 15 dakika pişir."], artan=True)
t("kiymali_patlican", "Kıymalı patlıcan musakka", ["ana"], 50,
  {"patlican": 200, "dana_kiyma": 80, "sogan": 30, "domates": 80, "sivri_biber": 20, "aycicek_yagi": 10, "tuz_baharat": 1},
  ["Patlıcanları dilimleyip fırında az yağla pişir.", "Kıymayı soğan, biber ve domatesle kavur.",
   "Patlıcan ve kıymayı kat kat dizip 20 dakika fırında pişir."], artan=True)
t("zeytinyagli_fasulye", "Zeytinyağlı taze fasulye", ["ana", "yan"], 45,
  {"taze_fasulye": 200, "domates": 80, "sogan": 30, "zeytinyagi": 12, "tuz_baharat": 1},
  ["Soğanı zeytinyağında öldür.", "Fasulye ve rendelenmiş domatesi ekleyip kısık ateşte 35 dakika pişir."], artan=True)
t("mucver", "Kabak mücver", ["ana"], 30,
  {"kabak": 200, "yumurta": 55, "un": 25, "beyaz_peynir": 30, "maydanoz": 10, "zeytinyagi": 10, "tuz_baharat": 1},
  ["Kabağı rendeleyip suyunu sık.", "Yumurta, un, peynir ve maydanozla karıştır.", "Az yağlı tavada iki yüzünü kızart."])
t("mercimek_koftesi", "Mercimek köftesi", ["ana", "ara"], 40,
  {"kirmizi_mercimek": 50, "bulgur": 40, "sogan": 30, "salca": 10, "zeytinyagi": 8, "maydanoz": 10, "marul": 50, "limon": 10, "tuz_baharat": 1},
  ["Mercimeği haşla, sıcakken bulguru ekleyip demlendir.", "Kavrulmuş soğan, salça ve maydanozla yoğur.",
   "Köfte şekli verip marulla servis et."], artan=True)
t("firin_sebze", "Fırında sebze ve nohut", ["ana"], 45,
  {"patates": 120, "kabak": 100, "havuc": 60, "patlican": 80, "nohut": 40, "zeytinyagi": 10, "tuz_baharat": 1},
  ["Nohudu haşla.", "Sebzeleri iri doğrayıp nohut, zeytinyağı ve baharatla harmanla.", "200 derecede 35 dakika pişir."],
  artan=True)
t("yogurtlu_makarna", "Yoğurtlu sarımsaklı makarna", ["ana"], 15,
  {"makarna": 90, "yogurt": 120, "sarimsak": 3, "tereyagi": 7, "tuz_baharat": 1},
  ["Makarnayı haşla.", "Sarımsaklı yoğurdu üzerine dök, pul biberli tereyağı gezdir."])
t("tavuk_corbasi", "Sebzeli tavuk çorbası", ["ana"], 40,
  {"tavuk_gogus": 80, "havuc": 40, "patates": 50, "sogan": 20, "pirinc": 15, "limon": 10, "tam_bugday_ekmegi": 50, "tuz_baharat": 1},
  ["Tavuğu haşla, didikle.", "Suyuna doğranmış sebzeleri ve pirinci ekleyip 20 dakika pişir.",
   "Tavuğu geri ekle, limonla servis et."], artan=True)
t("nohutlu_pilav", "Nohutlu pirinç pilavı", ["ana", "yan"], 30,
  {"pirinc": 75, "nohut": 30, "tereyagi": 8, "tuz_baharat": 1},
  ["Haşlanmış nohut ve pirinci tereyağında kavur.", "Sıcak suyu ekleyip kısık ateşte demlendir."], artan=True)

# ---------------- YANLAR ----------------
t("pirinc_pilavi", "Pirinç pilavı", ["yan"], 25,
  {"pirinc": 60, "tereyagi": 6, "tuz_baharat": 1},
  ["Pirinci tereyağında kavur.", "Sıcak suyu ekleyip kısık ateşte demlendir."], artan=True)
t("bulgur_pilavi", "Domatesli bulgur pilavı", ["yan"], 25,
  {"bulgur": 60, "sogan": 20, "domates": 50, "zeytinyagi": 6, "tuz_baharat": 1},
  ["Soğanı kavur, domatesi ekle.", "Bulgur ve sıcak suyu ekleyip demlendir."], artan=True)
t("coban_salatasi", "Çoban salatası", ["yan"], 10,
  {"domates": 120, "salatalik": 100, "sogan": 20, "sivri_biber": 20, "maydanoz": 10, "zeytinyagi": 6, "limon": 10},
  ["Sebzeleri küçük doğra.", "Zeytinyağı ve limonla karıştır."])
t("cacik", "Cacık", ["yan", "ara"], 5,
  {"yogurt": 150, "salatalik": 100, "sarimsak": 2, "tuz_baharat": 1},
  ["Salatalığı rendele.", "Sarımsaklı yoğurtla karıştır, isteğe göre su ekle."])

# ---------------- ARA ÖĞÜNLER ----------------
t("yogurt_bal_ceviz", "Ballı cevizli yoğurt", ["ara"], 2,
  {"yogurt": 200, "bal": 10, "ceviz": 10}, ["Yoğurdun üzerine bal ve ceviz ekle."], aralik=(0.5, 1.5))
t("elma_findik", "Elma ve fındık", ["ara"], 1,
  {"elma": 150, "findik": 20}, ["Elmayı dilimle, fındıkla birlikte ye."], aralik=(0.5, 1.5))
t("muz_fistik", "Fıstık ezmeli muz", ["ara"], 2,
  {"muz": 120, "fistik_ezmesi": 15}, ["Muzu dilimleyip fıstık ezmesiyle ye."], aralik=(0.5, 1.5))
t("ayran", "Ayran", ["ara", "yan"], 2,
  {"yogurt": 150, "tuz_baharat": 1}, ["Yoğurdu su ve tuzla çırp."], aralik=(1, 2))
t("haslanmis_yumurta", "Haşlanmış yumurta", ["ara"], 10,
  {"yumurta": 110, "salatalik": 80, "tuz_baharat": 1}, ["Yumurtaları 9 dakika haşla, salatalıkla ye."], aralik=(0.5, 1.5))
t("humus_havuc", "Humus ve havuç çubukları", ["ara"], 15,
  {"nohut": 40, "tahin": 15, "limon": 10, "sarimsak": 2, "zeytinyagi": 5, "havuc": 100},
  ["Haşlanmış nohudu tahin, limon, sarımsak ve zeytinyağıyla püre yap.", "Havuç çubuklarıyla servis et."], artan=True)
t("portakal_ceviz", "Portakal ve ceviz", ["ara"], 1,
  {"portakal": 200, "ceviz": 15}, ["Portakalı soy, cevizle birlikte ye."], aralik=(0.5, 1.5))
t("lor_bal", "Ballı lor", ["ara"], 2,
  {"lor": 120, "bal": 10}, ["Lorun üzerine bal gezdir."], aralik=(0.5, 1.5))

# =====================================================================================
# 16.11.2026: ÖZGÜN TARİFLER (bu proje için yazıldı; vejetaryen protein, airfryer/fırın,
# pratik seçenekler ağırlıklı). Gramajlar 1 porsiyon, adımlar evde uygulanabilir ayrıntıda.
# =====================================================================================

# ---------------- KAHVALTI (yeni) ----------------
t("lorlu_yumurta_durum", "Lorlu yumurtalı dürüm", ["kahvalti"], 12,
  {"lavas": 65, "yumurta": 110, "lor": 50, "domates": 60, "maydanoz": 8, "zeytinyagi": 4, "tuz_baharat": 1},
  ["Yumurtaları bir kasede lor, ince kıyılmış maydanoz, tuz ve karabiberle çırp.",
   "Tavayı zeytinyağıyla orta ateşte ısıt, karışımı dök ve sürekli karıştırarak yumuşak bir çırpılmış yumurta pişir (3-4 dk).",
   "Lavaşı kuru bir tavada her yüzünü 20'şer saniye ısıt; yumuşar ve kolay sarılır.",
   "Lavaşın ortasına yumurtayı ve ince dilimlenmiş domatesi yerleştir.",
   "Alt kısmını katlayıp yanlardan sararak dürüm yap; ikiye kesip servis et."])
t("yumurtali_muffin", "Fırında sebzeli yumurta muffin", ["kahvalti", "ara"], 25,
  {"yumurta": 165, "ispanak": 40, "kapya_biber": 40, "beyaz_peynir": 30, "zeytinyagi": 3, "tam_bugday_ekmegi": 40, "tuz_baharat": 1},
  ["Fırını (veya airfryer'ı) 180 dereceye ısıt; muffin kalıbının gözlerini zeytinyağıyla yağla.",
   "Ispanağı ince kıy, kapya biberi küçük küpler halinde doğra, peyniri ufala.",
   "Yumurtaları tuz ve karabiberle çırp, sebzeleri ve peyniri ekleyip karıştır.",
   "Karışımı kalıpların 3/4'ünü dolduracak şekilde paylaştır.",
   "Fırında 18-20 dakika (airfryer'da 12-14 dakika) üzeri kızarıp ortası pişene kadar pişir.",
   "Ilıyınca kalıptan çıkar, ekmekle servis et. Buzdolabında 3 gün saklanır."], artan=True)
t("suzme_meyve_kase", "Süzme yoğurtlu meyve kasesi", ["kahvalti", "ara"], 5,
  {"suzme_yogurt": 200, "muz": 100, "yulaf": 25, "ceviz": 10, "bal": 8},
  ["Süzme yoğurdu bir kaseye al, kaşıkla iyice çırparak pürüzsüzleştir.",
   "Muzu ince halkalar halinde dilimle.",
   "Yoğurdun üzerine yulafı serp, muz dilimlerini diz.",
   "Cevizi elinle kırıp üzerine ekle, en son balı gezdir."], aralik=(0.75, 1.5))
t("kefirli_smoothie", "Kefirli yulaf smoothie", ["kahvalti", "ara"], 5,
  {"kefir": 250, "yulaf": 35, "muz": 100, "fistik_ezmesi": 15},
  ["Yulafı blender haznesine koy ve 10 saniye çekerek una yakın hale getir.",
   "Muzu dilimleyip ekle (dondurulmuş muz kullanırsan smoothie daha kıvamlı olur).",
   "Kefiri ve fıstık ezmesini ilave et.",
   "Pürüzsüz olana kadar 30-40 saniye çek; çok koyuysa biraz su ekle.",
   "Bardağa al ve hemen iç."], aralik=(0.75, 1.5))
t("mantarli_omlet", "Mantarlı kaşarlı omlet", ["kahvalti"], 12,
  {"yumurta": 110, "mantar": 80, "kasar": 20, "maydanoz": 5, "zeytinyagi": 5, "tam_bugday_ekmegi": 50, "tuz_baharat": 1},
  ["Mantarları ıslak bir bezle silip ince dilimle.",
   "Tavada zeytinyağını ısıt, mantarları suyunu salıp çekene kadar yüksek ateşte sotele (5 dk).",
   "Yumurtaları tuz ve karabiberle çırp, mantarların üzerine dök.",
   "Altı tutunca rendelenmiş kaşarı serp, kapağı kapatıp kısık ateşte 2 dakika pişir.",
   "Kıyılmış maydanozla süsleyip ekmekle servis et."])
t("yulafli_pankek", "Muzlu yulaf pankek", ["kahvalti"], 15,
  {"yulaf": 45, "yumurta": 55, "muz": 100, "sut": 60, "bal": 8, "aycicek_yagi": 3},
  ["Muzu bir kasede çatalla iyice ez.",
   "Yumurta ve sütü ekleyip çırp, ardından yulafı ilave edip 5 dakika dinlendir.",
   "Yapışmaz tavayı kağıt havluyla çok az yağla ve orta ateşte ısıt.",
   "Her pankek için 2 yemek kaşığı hamur dök; kenarları kabarınca çevir (her yüzü 1,5-2 dk).",
   "Üst üste dizip balla servis et."])
t("ispanakli_lavas_gozleme", "Ispanaklı lorlu lavaş gözleme", ["kahvalti", "ana"], 15,
  {"lavas": 70, "ispanak": 80, "lor": 60, "beyaz_peynir": 20, "sogan": 15, "zeytinyagi": 5, "tuz_baharat": 1},
  ["Ispanağı yıkayıp ince kıy, soğanı küçük doğra.",
   "Soğanı yağda 2 dakika kavur, ıspanağı ekleyip sönene kadar karıştır ve ateşten al.",
   "Ispanağı lor ve ufalanmış beyaz peynirle karıştır, tuz ve pul biberle tatlandır.",
   "Harcı lavaşın yarısına yay, diğer yarısını üzerine kapat.",
   "Kuru tavada veya tost makinesinde her yüzü kızarana kadar (2-3 dk) pişir, dilimleyip servis et."])
t("fistikli_yulaf_lapasi", "Fıstık ezmeli yulaf lapası", ["kahvalti"], 8,
  {"yulaf": 50, "sut": 200, "fistik_ezmesi": 15, "muz": 80},
  ["Yulaf ve sütü küçük bir tencerede karıştır.",
   "Orta-kısık ateşte, ara ara karıştırarak koyulaşana kadar 4-5 dakika pişir (mikrodalgada 2 dk, 30 sn arayla karıştırarak).",
   "Ocaktan alıp fıstık ezmesini ekle ve eriyene kadar karıştır.",
   "Kaseye al, üzerine dilimlenmiş muz koyarak servis et."])
t("kapyali_yumurta", "Kapya biberli yumurta kapama", ["kahvalti"], 18,
  {"yumurta": 110, "kapya_biber": 80, "domates": 120, "sogan": 30, "beyaz_peynir": 25, "zeytinyagi": 6,
   "tam_bugday_ekmegi": 50, "tuz_baharat": 1},
  ["Soğanı ince, kapya biberi şerit doğra; domatesin kabuğunu soyup küp küp kes.",
   "Soğanı zeytinyağında pembeleşene kadar kavur, biberi ekleyip 3 dakika daha pişir.",
   "Domatesi ekle, kimyon ve pul biberle tatlandırıp suyunu biraz çekene kadar 5 dakika pişir.",
   "Kaşıkla iki çukur aç, yumurtaları kır; kapağı kapatıp akı pişene kadar 4-5 dakika beklet.",
   "Üzerine beyaz peynir ufalayıp ekmekle sıcak servis et."])
t("tahinli_suzme_kase", "Tahinli ballı süzme yoğurt", ["kahvalti", "ara"], 3,
  {"suzme_yogurt": 180, "tahin": 12, "bal": 10, "ceviz": 10, "elma": 80},
  ["Süzme yoğurdu kaseye al.",
   "Tahin ve balı küçük bir kapta karıştırıp yoğurdun üzerine gezdir.",
   "Elmayı küçük küpler halinde doğra, kırılmış cevizle birlikte üzerine ekle."], aralik=(0.75, 1.5))
t("kinoa_kahvalti_kasesi", "Kinoalı kahvaltı kasesi", ["kahvalti"], 20,
  {"kinoa": 45, "yumurta": 55, "domates": 80, "salatalik": 80, "beyaz_peynir": 30, "zeytinyagi": 5, "limon": 5, "tuz_baharat": 1},
  ["Kinoayı süzgeçte bol suyla yıka (acılığı gider).",
   "İki katı suyla tencereye al, kaynayınca kısık ateşte 12-15 dakika suyunu çekene kadar pişir.",
   "Bu sırada yumurtayı 8 dakika haşla, soğuk suya alıp soy ve ikiye kes.",
   "Domates ve salatalığı küp doğra.",
   "Kinoayı kaseye al; sebzeleri, peyniri ve yumurtayı yerleştir, zeytinyağı ve limonla tatlandır."])
t("lavas_pizza", "Airfryer'da yumurtalı lavaş pizza", ["kahvalti", "ana"], 12,
  {"lavas": 65, "yumurta": 55, "kasar": 30, "domates": 60, "kapya_biber": 30, "salca": 5, "tuz_baharat": 1},
  ["Salçayı 1 yemek kaşığı su ve kekikle açıp lavaşın üzerine ince bir tabaka halinde sür.",
   "Domates ve kapya biberi ince dilimleyip lavaşa yerleştir, rendelenmiş kaşarın yarısını serp.",
   "Ortada küçük bir çukur bırakıp yumurtayı kır, kalan kaşarı kenarlara serp.",
   "Airfryer'da 180 derecede 7-8 dakika (fırında 200 derecede 10 dk) yumurta akı pişene kadar pişir.",
   "Dilimleyip sıcak servis et."])

# ---------------- ANA YEMEKLER (yeni) ----------------
t("firin_karnabahar_nohut", "Fırında karnabahar ve nohut, yoğurtlu", ["ana"], 45,
  {"karnabahar": 250, "nohut": 50, "zeytinyagi": 12, "yogurt": 100, "sarimsak": 3, "limon": 5, "tuz_baharat": 1},
  ["Nohudu bir gece önceden ıslat, düdüklüde 15 veya tencerede 45 dakika haşla, süzüp kurula.",
   "Karnabaharı küçük çiçeklere ayır; nohutla birlikte zeytinyağı, kimyon, toz kırmızı biber ve tuzla harmanla.",
   "Fırın tepsisine (veya airfryer sepetine) tek kat yay.",
   "200 derecede 25-30 dakika (airfryer'da 190 derecede 18-20 dk), yarısında karıştırarak kenarları kızarana kadar pişir.",
   "Yoğurdu ezilmiş sarımsak, limon ve tuzla karıştır.",
   "Sebzeleri tabağa al, sarımsaklı yoğurtla servis et."], artan=True)
t("barbunya_pilaki", "Zeytinyağlı barbunya pilaki", ["ana"], 75,
  {"barbunya": 70, "havuc": 40, "patates": 60, "sogan": 40, "sarimsak": 4, "zeytinyagi": 12, "salca": 8, "limon": 8,
   "maydanoz": 5, "tuz_baharat": 1},
  ["Barbunyayı bir gece önceden ıslat; ertesi gün suyunu değiştirip 35-40 dakika (düdüklüde 12 dk) diri kalacak şekilde haşla.",
   "Soğanı yarım ay, havucu halka, patatesi küp doğra; sarımsağı ince kıy.",
   "Zeytinyağında soğanı ve sarımsağı 3 dakika kavur, salçayı ekleyip kokusu çıkana kadar karıştır.",
   "Havuç ve patatesi ekle, 2 dakika çevir; barbunyayı ve sebzelerin üzerini geçecek kadar sıcak su ilave et.",
   "Kapağı kapalı, kısık ateşte sebzeler yumuşayana kadar 20 dakika pişir.",
   "Limon suyunu ekle; ılık ya da soğuk, kıyılmış maydanozla servis et."], artan=True)
t("mantarli_tavuk_sote", "Mantarlı tavuk sote", ["ana"], 25,
  {"tavuk_gogus": 140, "mantar": 120, "kapya_biber": 60, "sogan": 30, "zeytinyagi": 8, "tam_bugday_ekmegi": 50, "tuz_baharat": 1},
  ["Tavuğu kuşbaşı, mantarları dilim, biberi ve soğanı şerit doğra.",
   "Geniş tavada zeytinyağını iyice ısıt, tavuğu tek kat yay ve rengi dönene kadar yüksek ateşte 5-6 dakika sotele.",
   "Tavuğu kenara al; aynı tavada soğan ve mantarı mantarlar suyunu çekene kadar pişir.",
   "Biberi ekleyip 2 dakika daha çevir, tavuğu geri al.",
   "Tuz, karabiber ve kekikle tatlandırıp 2 dakika birlikte pişir; ekmekle servis et."], artan=True)
t("airfryer_tavuk_sebze", "Airfryer'da yoğurtlu tavuk ve sebze", ["ana"], 30,
  {"tavuk_gogus": 160, "yogurt": 40, "kabak": 100, "kapya_biber": 60, "patates": 120, "zeytinyagi": 8, "sarimsak": 3,
   "tuz_baharat": 1},
  ["Tavuğu iri küp doğra; yoğurt, ezilmiş sarımsak, yarım tatlı kaşığı yağ, pul biber ve tuzla en az 15 dakika marine et.",
   "Patatesi elma dilim, kabağı ve biberi iri parçalar halinde doğra; kalan yağ ve baharatla harmanla.",
   "Patatesleri airfryer'da 190 derecede 8 dakika ön pişir.",
   "Tavuğu ve diğer sebzeleri ekleyip 190 derecede 12-14 dakika, yarısında sepeti sallayarak pişir (fırında 200 derecede 30 dk).",
   "Tavuğun içi beyazlaşıp sebzeler kızarınca servis et."], artan=True)
t("brokolili_tavuklu_makarna", "Brokolili tavuklu makarna", ["ana"], 25,
  {"makarna": 75, "tavuk_gogus": 110, "brokoli": 120, "sarimsak": 4, "kasar": 15, "zeytinyagi": 7, "tuz_baharat": 1},
  ["Brokoliyi küçük çiçeklere ayır. Makarnayı tuzlu suda haşla; süzmeden 3 dakika önce brokoliyi aynı tencereye ekle.",
   "Bir kepçe makarna suyunu ayırıp makarna ve brokoliyi süz.",
   "Tavada yağı ısıt, küçük doğranmış tavuğu 5-6 dakika sotele, ince kıyılmış sarımsağı ekleyip 30 saniye çevir.",
   "Makarna ve brokoliyi tavaya al, ayırdığın suyu ekleyip 1 dakika karıştır.",
   "Rendelenmiş kaşarı ve karabiberi ekleyip eriyene kadar karıştır, hemen servis et."])
t("ton_durum", "Ton balıklı yoğurtlu dürüm", ["ana"], 10,
  {"lavas": 70, "ton_baligi": 80, "suzme_yogurt": 40, "marul": 40, "domates": 60, "salatalik": 50, "limon": 5, "tuz_baharat": 1},
  ["Ton balığının suyunu iyice süz ve çatalla dağıt.",
   "Süzme yoğurt, limon suyu, karabiber ve az tuzla karıştır.",
   "Marulu ince kıy; domates ve salatalığı ince dilimle.",
   "Lavaşa önce marulu, sonra ton karışımını ve sebzeleri yerleştir.",
   "Sıkıca sarıp ikiye kes; hemen servis et."])
t("tavuk_durum", "Tavuk dürüm", ["ana"], 20,
  {"lavas": 70, "tavuk_gogus": 130, "yogurt": 50, "marul": 40, "domates": 60, "sogan": 20, "zeytinyagi": 6, "tuz_baharat": 1},
  ["Tavuğu ince şeritler halinde doğra, kimyon, pul biber ve tuzla harmanla.",
   "Tavada yağı ısıt, tavuğu yüksek ateşte 6-7 dakika kızarana kadar pişir (airfryer'da 190 derecede 10 dk).",
   "Yoğurda tuz ve isteğe göre ezilmiş sarımsak ekle.",
   "Lavaşı ısıt; yoğurt sür, marul, domates, ince soğan ve tavuğu diz.",
   "Sıkıca sarıp kuru tavada iki yüzünü 30 saniye bastırarak mühürle."])
t("nohutlu_kinoa_salatasi", "Nohutlu kinoa salatası", ["ana"], 25,
  {"kinoa": 60, "nohut": 45, "domates": 80, "salatalik": 80, "maydanoz": 15, "limon": 15, "zeytinyagi": 10, "tuz_baharat": 1},
  ["Nohudu önceden ıslatıp haşla (veya önceki günden haşlanmışı kullan).",
   "Kinoayı yıkayıp iki katı suyla 12-15 dakika suyunu çekene kadar pişir, tepside soğut.",
   "Domates, salatalık ve maydanozu küçük doğra.",
   "Limon suyu, zeytinyağı, tuz ve sumakla sos hazırla.",
   "Tüm malzemeleri sosla karıştır; buzdolabında 10 dakika dinlendirip servis et."], artan=True)
t("sebzeli_mercimek_yahni", "Sebzeli kırmızı mercimek yahnisi", ["ana"], 35,
  {"kirmizi_mercimek": 60, "kabak": 80, "havuc": 50, "sogan": 30, "salca": 10, "zeytinyagi": 8, "tam_bugday_ekmegi": 40,
   "tuz_baharat": 1},
  ["Mercimeği suyu berraklaşana kadar yıka.",
   "Soğanı yemeklik, havucu ve kabağı küp doğra.",
   "Zeytinyağında soğanı kavur, havucu ekleyip 3 dakika çevir, salçayı ekle.",
   "Mercimek ve kabağı ekle, 2 su bardağı sıcak su ilave et.",
   "Kısık ateşte mercimek dağılmadan yumuşayana kadar 20 dakika pişir; kimyon ve pul biberle tatlandır.",
   "Ekmekle servis et."], artan=True)
t("ispanak_kavurma_yumurta", "Yumurtalı ıspanak kavurması", ["ana"], 20,
  {"ispanak": 250, "yumurta": 110, "sogan": 40, "yogurt": 80, "zeytinyagi": 8, "tam_bugday_ekmegi": 50, "tuz_baharat": 1},
  ["Ispanağı bol suda yıkayıp iri kıy, soğanı ince doğra.",
   "Geniş tavada soğanı zeytinyağında pembeleşene kadar kavur.",
   "Ispanağı ekleyip söndür ve suyunu çekene kadar 5-6 dakika pişir; tuz ve pul biber ekle.",
   "Ispanağın içinde iki çukur aç, yumurtaları kır ve kapağı kapalı 4 dakika pişir.",
   "Yanında yoğurt ve ekmekle servis et."])
t("mantarli_bulgur", "Mantarlı bulgur pilavı", ["ana", "yan"], 30,
  {"bulgur": 70, "mantar": 100, "sogan": 30, "kapya_biber": 40, "tereyagi": 6, "zeytinyagi": 4, "tuz_baharat": 1},
  ["Soğanı ve kapya biberi küçük, mantarı dilim doğra.",
   "Tencerede yağları ısıt; soğanı kavur, mantarı ekleyip suyunu çekene kadar pişir.",
   "Biberi ve bulguru ekleyip 2 dakika kavur.",
   "Bulgurun iki katı sıcak su ve tuz ekle; kaynayınca kısık ateşte suyunu çekene kadar 15 dakika pişir.",
   "Ocaktan alıp kapağın altına kağıt havlu koyarak 10 dakika demlendir."], artan=True)
t("firin_kofte_brokoli", "Fırında köfte ve brokoli", ["ana"], 40,
  {"dana_kiyma": 110, "brokoli": 150, "patates": 120, "sogan": 20, "yumurta": 15, "zeytinyagi": 6, "tuz_baharat": 1},
  ["Kıymayı rendelenmiş soğan, az yumurta, kimyon, karabiber ve tuzla 3-4 dakika yoğur; köfte şekli ver.",
   "Patatesi elma dilim doğra, brokoliyi çiçeklere ayır; ikisini zeytinyağı ve tuzla harmanla.",
   "Patatesleri tepsiye yay ve 200 derecede 10 dakika ön pişir.",
   "Köfteleri ve brokoliyi ekleyip 15-18 dakika daha pişir (airfryer'da 190 derecede 12-14 dk, yarısında çevir).",
   "Köftelerin içi pişince sıcak servis et."], artan=True)
t("kiymali_karnabahar", "Kıymalı karnabahar yemeği", ["ana"], 35,
  {"karnabahar": 250, "dana_kiyma": 60, "sogan": 30, "salca": 10, "zeytinyagi": 5, "yogurt": 80, "tuz_baharat": 1},
  ["Karnabaharı küçük çiçeklere ayırıp yıka.",
   "Tencerede kıymayı suyunu çekene kadar kavur, soğanı ekleyip pembeleştir.",
   "Salçayı ekle, kokusu çıkınca karnabaharı ilave edip 2 dakika çevir.",
   "Yarım su bardağı sıcak su ekle; kapağı kapalı, kısık ateşte karnabahar yumuşayana kadar 20 dakika pişir.",
   "Yoğurtla servis et."], artan=True)
t("tavuklu_kinoa_kase", "Tavuklu kinoa kasesi", ["ana"], 30,
  {"kinoa": 55, "tavuk_gogus": 120, "brokoli": 100, "kapya_biber": 50, "suzme_yogurt": 40, "limon": 8, "zeytinyagi": 7,
   "tuz_baharat": 1},
  ["Kinoayı yıkayıp iki katı suyla 12-15 dakika pişir.",
   "Tavuğu baharatlayıp tavada (veya airfryer'da 190 derecede 12 dk) pişir ve dilimle.",
   "Brokoliyi 4 dakika buharda veya kaynar suda haşla; kapya biberi şerit doğra.",
   "Süzme yoğurdu limon suyu, tuz ve karabiberle karıştırıp sos yap.",
   "Kaseye kinoayı al, tavuk ve sebzeleri yerleştir, sosu ve zeytinyağını gezdir."])
t("firin_frittata", "Fırında sebzeli omlet (frittata)", ["ana", "kahvalti"], 30,
  {"yumurta": 165, "kabak": 100, "kapya_biber": 50, "ispanak": 50, "beyaz_peynir": 30, "zeytinyagi": 6, "tuz_baharat": 1},
  ["Fırını 180 dereceye ısıt. Kabağı rendeleyip suyunu sık, biberi küp, ıspanağı ince doğra.",
   "Sebzeleri zeytinyağında 4-5 dakika sotele.",
   "Yumurtaları peynir, tuz ve karabiberle çırp; sebzeleri ekleyip karıştır.",
   "Yağlanmış küçük fırın kabına dök.",
   "18-20 dakika (airfryer'da 170 derecede 14 dk) ortası pişene kadar pişir; dilimleyip servis et."], artan=True)
t("lavas_borek", "Lorlu ıspanaklı lavaş böreği", ["ana"], 35,
  {"lavas": 75, "ispanak": 100, "lor": 70, "yumurta": 55, "yogurt": 40, "zeytinyagi": 6, "tuz_baharat": 1},
  ["Ispanağı ince kıy; lor, tuz ve karabiberle karıştır.",
   "Yumurta, yoğurt ve zeytinyağını çırparak sos hazırla.",
   "Lavaşları ikiye kes; yağlanmış kaba bir kat lavaş koy, sostan sür, ıspanaklı harçtan serp.",
   "Bu şekilde kat kat devam et; en üste lavaş ve kalan sosu sür.",
   "180 derecede 25 dakika (airfryer'da 170 derecede 15 dk) üzeri kızarana kadar pişir.",
   "10 dakika dinlendirip dilimle."], artan=True)
t("nohutlu_ispanak", "Nohutlu ıspanak yemeği", ["ana"], 30,
  {"ispanak": 250, "nohut": 45, "sogan": 30, "salca": 8, "zeytinyagi": 8, "yogurt": 80, "tuz_baharat": 1},
  ["Nohudu önceden ıslatıp haşla.",
   "Soğanı zeytinyağında kavur, salçayı ekleyip 1 dakika çevir.",
   "Kıyılmış ıspanağı ekleyip söndür.",
   "Nohudu ve yarım su bardağı sıcak suyu ilave et; kısık ateşte 15 dakika pişir.",
   "Yoğurtla servis et."], artan=True)
t("mercimekli_kinoa_salatasi", "Yeşil mercimekli kinoa salatası", ["ana"], 35,
  {"yesil_mercimek": 45, "kinoa": 45, "kapya_biber": 60, "salatalik": 80, "maydanoz": 15, "limon": 15, "zeytinyagi": 10,
   "beyaz_peynir": 30, "tuz_baharat": 1},
  ["Yeşil mercimeği dağılmadan, diri kalacak şekilde 20-25 dakika haşla ve süz.",
   "Kinoayı yıkayıp iki katı suyla 12-15 dakika pişir; ikisini de soğumaya bırak.",
   "Kapya biber, salatalık ve maydanozu küçük doğra.",
   "Limon, zeytinyağı, tuz ve nar ekşisi (varsa) ile sos hazırla.",
   "Hepsini karıştır, üzerine beyaz peynir ufala."], artan=True)
t("brokoli_corbasi", "Yoğurtlu brokoli çorbası", ["ana"], 25,
  {"brokoli": 200, "patates": 60, "sogan": 30, "yogurt": 80, "zeytinyagi": 7, "tam_bugday_ekmegi": 50, "tuz_baharat": 1},
  ["Soğanı zeytinyağında yumuşayana kadar kavur.",
   "Brokoliyi ve küp doğranmış patatesi ekle, üzerini 2 parmak geçecek kadar sıcak su ilave et.",
   "Sebzeler yumuşayana kadar 15 dakika pişir.",
   "Blenderdan geçirip pürüzsüz hale getir (blender yoksa patates ezicisiyle ez).",
   "Ocaktan alıp ılımasını bekle, yoğurdu bir kepçe çorbayla ılıtıp ekle; tuz ve karabiberle servis et."], artan=True)
t("mantar_corbasi", "Sütlü mantar çorbası", ["ana"], 25,
  {"mantar": 150, "sut": 150, "un": 12, "tereyagi": 8, "sogan": 20, "tam_bugday_ekmegi": 50, "tuz_baharat": 1},
  ["Mantarları küçük doğra, soğanı ince kıy.",
   "Tereyağında soğanı kavur, mantarları ekleyip suyunu çekene kadar pişir.",
   "Unu ekleyip 1 dakika kavur, ardından 1 su bardağı sıcak suyu topaklanmaması için çırparak ekle.",
   "Sütü ekle ve kısık ateşte karıştırarak 8-10 dakika koyulaşana kadar pişir.",
   "İsteğe göre yarısını blenderdan geçir; tuz ve karabiberle servis et."])
t("firin_tavuk_karnabahar", "Fırında tavuk but ve karnabahar", ["ana"], 45,
  {"tavuk_but": 170, "karnabahar": 200, "sogan": 30, "zeytinyagi": 10, "salca": 5, "yogurt": 60, "tuz_baharat": 1},
  ["Salçayı zeytinyağı, kekik, pul biber ve tuzla karıştırıp sos yap.",
   "Tavuk butları ve karnabahar çiçeklerini sosla iyice harmanla, soğanı iri doğrayıp ekle.",
   "Tepsiye tek kat yay.",
   "200 derecede 35-40 dakika (airfryer'da 190 derecede 22-25 dk) tavuğun içi pişip derisi kızarana kadar pişir.",
   "Yoğurtla servis et."], artan=True)
t("ton_kinoa_salatasi", "Ton balıklı kinoa salatası", ["ana"], 20,
  {"kinoa": 50, "ton_baligi": 80, "domates": 80, "salatalik": 80, "marul": 40, "limon": 10, "zeytinyagi": 8, "tuz_baharat": 1},
  ["Kinoayı yıkayıp iki katı suyla 12-15 dakika pişir ve soğut.",
   "Ton balığını süzüp dağıt.",
   "Domates, salatalık ve marulu doğra.",
   "Tüm malzemeleri limon, zeytinyağı ve tuzla karıştırıp servis et."])
t("tavuk_fajita", "Kapya biberli tavuk fajita", ["ana"], 25,
  {"tavuk_gogus": 140, "kapya_biber": 80, "sogan": 50, "lavas": 65, "yogurt": 40, "zeytinyagi": 8, "tuz_baharat": 1},
  ["Tavuğu, kapya biberi ve soğanı ince şeritler halinde doğra.",
   "Tavuğu kimyon, toz kırmızı biber, sarımsak tozu ve tuzla harmanla.",
   "Çok kızgın tavada tavuğu 5 dakika pişir, biber ve soğanı ekleyip 4 dakika daha yüksek ateşte çevir.",
   "Lavaşları ısıt; yoğurt sürüp tavuklu karışımı paylaştır.",
   "Sarıp hemen servis et."])
t("kiymali_yesil_mercimek", "Kıymalı yeşil mercimek", ["ana"], 45,
  {"yesil_mercimek": 60, "dana_kiyma": 50, "sogan": 30, "salca": 10, "bulgur": 15, "zeytinyagi": 5, "yogurt": 60,
   "tuz_baharat": 1},
  ["Mercimeği yıkayıp 15 dakika ön haşla, suyunu süz.",
   "Kıymayı kavur, soğanı ekleyip pembeleştir, salçayı ilave et.",
   "Mercimek ve bulguru ekleyip 2 su bardağı sıcak su ilave et.",
   "Kısık ateşte mercimekler yumuşayana kadar 20-25 dakika pişir.",
   "Yoğurtla servis et."], artan=True)
t("firin_kiymali_kabak", "Fırında kıymalı kabak", ["ana"], 40,
  {"kabak": 250, "dana_kiyma": 70, "domates": 80, "sogan": 25, "kasar": 15, "zeytinyagi": 5, "tuz_baharat": 1},
  ["Kabakları boyuna ikiye kes, içini kaşıkla oyarak kayık şekli ver; oyduğun kısmı doğra.",
   "Kıymayı soğanla kavur, kabak içi ve rendelenmiş domatesi ekleyip 5 dakika pişir.",
   "Kabak kayıklarını harçla doldur, tepsiye diz.",
   "Üzerine kaşar serp; 190 derecede 25 dakika (airfryer'da 180 derecede 15 dk) pişir."], artan=True)
t("barbunyali_bulgur_salatasi", "Barbunyalı bulgur salatası", ["ana"], 30,
  {"barbunya": 45, "bulgur": 50, "domates": 80, "kapya_biber": 50, "maydanoz": 15, "limon": 15, "zeytinyagi": 10,
   "tuz_baharat": 1},
  ["Barbunyayı önceden ıslatıp diri kalacak şekilde haşla.",
   "Bulguru bir kaba al, üzerini geçecek kadar kaynar su dökerek kapağı kapalı 15 dakika şişir.",
   "Domates, biber ve maydanozu küçük doğra.",
   "Bulgur, barbunya ve sebzeleri limon, zeytinyağı, tuz ve pul biberle karıştır."], artan=True)
t("airfryer_falafel", "Airfryer'da falafel ve yoğurt", ["ana"], 30,
  {"nohut": 70, "sogan": 30, "maydanoz": 20, "sarimsak": 4, "un": 10, "zeytinyagi": 5, "yogurt": 80, "marul": 50,
   "tuz_baharat": 1},
  ["Nohudu bir gece önceden ıslat (haşlama!), süzüp kurula.",
   "Nohut, soğan, maydanoz, sarımsak, kimyon ve tuzu blenderda iri kum kıvamına gelene kadar çek.",
   "Unu ekleyip karıştır; ceviz büyüklüğünde parçalar alıp hafifçe bastırarak köfte yap.",
   "Üzerlerine fırçayla zeytinyağı sür; airfryer'da 190 derecede 12-14 dakika, yarısında çevirerek pişir (fırında 200 derecede 20 dk).",
   "Yoğurt ve marulla servis et."])

# ---------------- SADECE AIRFRYER / FIRIN İLE YAPILAN ANA YEMEKLER ----------------
# Ocak gerektirmez (haşlama/soteleme yok). Mutfağında yalnızca airfryer ya da fırın olanlar için.
t("af_sebzeli_kasarli_durum", "Airfryer'da kaşarlı sebzeli çıtır dürüm", ["ana"], 15,
  {"lavas": 75, "kasar": 45, "kapya_biber": 50, "mantar": 60, "ispanak": 30, "zeytinyagi": 3, "tuz_baharat": 1},
  ["Mantarı ve kapya biberi çok ince dilimle, ıspanağı iri kıy.",
   "Lavaşın yarısına rendelenmiş kaşarın yarısını yay; sebzeleri diz, tuz ve kekik serp, kalan kaşarı ekle.",
   "Lavaşı ikiye katlayıp üzerine fırçayla çok az zeytinyağı sür.",
   "Airfryer'da 180 derecede 6-7 dakika, yarısında çevirerek (fırında 200 derecede 10 dk) kızarana kadar pişir.",
   "Üçgen dilimleyip sıcak servis et."])
t("af_lorlu_rulo_borek", "Airfryer'da lorlu ıspanaklı rulo börek", ["ana"], 20,
  {"lavas": 75, "lor": 90, "ispanak": 80, "yumurta": 30, "yogurt": 80, "zeytinyagi": 5, "tuz_baharat": 1},
  ["Ispanağı ince kıyıp tuzla ovarak suyunu sık; lor, karabiber ve pul biberle karıştır.",
   "Lavaşı ikiye kes, harcı uzun kenar boyunca yayıp sıkıca rulo sar.",
   "Yumurtayı zeytinyağıyla çırpıp ruloların üzerine sür.",
   "Airfryer'da 180 derecede 9-10 dakika (fırında 190 derecede 18 dk) altın rengi olana kadar pişir.",
   "Yoğurtla servis et."], artan=True)
t("af_yumurtali_patates", "Fırında kaşarlı yumurtalı patates", ["ana"], 30,
  {"patates": 250, "yumurta": 110, "kasar": 25, "zeytinyagi": 6, "tuz_baharat": 1},
  ["Patatesi küçük küpler halinde doğra; zeytinyağı, tuz, kekik ve toz biberle harmanla.",
   "Airfryer'a uygun kapta 190 derecede 15 dakika, bir kez karıştırarak pişir (fırında 210 derecede 22 dk).",
   "Patateslerin arasında iki çukur açıp yumurtaları kır, kaşarı serp.",
   "170 derecede 5-6 dakika daha, yumurta akı pişene kadar pişir."])
t("af_mantar_dolmasi", "Kaşarlı lorlu mantar dolması", ["ana"], 20,
  {"mantar": 200, "kasar": 35, "lor": 60, "sarimsak": 3, "tam_bugday_ekmegi": 70, "zeytinyagi": 5, "tuz_baharat": 1},
  ["Mantarların saplarını çıkar; sapları ince kıy.",
   "Kıyılmış sapları lor, ezilmiş sarımsak, tuz ve karabiberle karıştır.",
   "Mantar şapkalarına zeytinyağı sür, harcı doldur ve üzerine kaşar serp.",
   "Airfryer'da 180 derecede 10-12 dakika (fırında 200 derecede 18 dk) pişir.",
   "Ekmeği son 2 dakika yanına koyup kızart, birlikte servis et."])
t("af_peynirli_karnabahar", "Fırında kaşarlı karnabahar", ["ana"], 30,
  {"karnabahar": 300, "yumurta": 55, "kasar": 35, "yogurt": 60, "tam_bugday_ekmegi": 50, "zeytinyagi": 5, "tuz_baharat": 1},
  ["Karnabaharı küçük çiçeklere ayır; zeytinyağı ve tuzla harmanla.",
   "Airfryer'da 180 derecede 12 dakika (fırında 200 derecede 18 dk) yumuşayana kadar ön pişir.",
   "Yumurta, yoğurt, karabiber ve kaşarın yarısını çırp.",
   "Karnabaharı fırın kabına al, sosu gezdir, kalan kaşarı serp.",
   "170 derecede 8-10 dakika üzeri kızarana kadar pişir; ekmekle servis et."], artan=True)
t("af_beyaz_peynirli_sebze", "Fırında beyaz peynirli sebze", ["ana"], 30,
  {"patlican": 150, "kabak": 150, "kapya_biber": 80, "beyaz_peynir": 70, "zeytinyagi": 10, "tam_bugday_ekmegi": 60,
   "tuz_baharat": 1},
  ["Patlıcan, kabak ve kapya biberi iri küp doğra.",
   "Zeytinyağı, kekik, tuz ve pul biberle harmanla.",
   "Airfryer'da 190 derecede 15-17 dakika, iki kez sallayarak (fırında 210 derecede 25 dk) pişir.",
   "Beyaz peyniri iri parçalar halinde üzerine ekle, 3 dakika daha pişir.",
   "Ekmekle servis et."], artan=True)
t("af_ekmek_kayigi", "Yumurtalı kaşarlı ekmek kayığı", ["ana", "kahvalti"], 15,
  {"tam_bugday_ekmegi": 90, "yumurta": 110, "kasar": 25, "domates": 60, "tuz_baharat": 1},
  ["Ekmek dilimlerinin ortasını bastırarak çukurlaştır (ya da küçük bir somunun içini oy).",
   "Çukurlara ince domates dilimi koy, yumurtaları kır.",
   "Tuz, karabiber ve kaşar serp.",
   "Airfryer'da 170 derecede 8-9 dakika (fırında 190 derecede 12 dk) yumurta pişene kadar pişir."])
t("af_brokoli_mucver", "Airfryer'da brokoli mücveri", ["ana"], 25,
  {"brokoli": 200, "yumurta": 55, "un": 25, "beyaz_peynir": 40, "zeytinyagi": 6, "yogurt": 80, "tuz_baharat": 1},
  ["Çiğ brokoliyi rendeyle ya da bıçakla pirinç iriliğinde kıy.",
   "Yumurta, un, ufalanmış peynir, tuz ve karabiberle karıştır.",
   "Pişirme kağıdına kaşıkla yassı köfteler bırak, üzerlerine zeytinyağı sür.",
   "Airfryer'da 190 derecede 12-14 dakika, yarısında çevirerek (fırında 200 derecede 20 dk) pişir.",
   "Yoğurtla servis et."], artan=True)
t("af_lorlu_kabak_sandal", "Lorlu kabak sandal", ["ana"], 30,
  {"kabak": 300, "lor": 100, "yumurta": 30, "kasar": 25, "tam_bugday_ekmegi": 50, "zeytinyagi": 4, "tuz_baharat": 1},
  ["Kabakları boyuna ikiye kes, içini kaşıkla oyup oyduğun kısmı ince kıy.",
   "Kıyılmış kabak içini lor, yumurta, tuz, karabiber ve dereotu (varsa) ile karıştır.",
   "Kabak kayıklarına zeytinyağı sür, harcı doldur, kaşar serp.",
   "Airfryer'da 180 derecede 15-17 dakika (fırında 190 derecede 25 dk) pişir; ekmekle servis et."], artan=True)
t("af_sebzeli_omlet", "Airfryer'da mantarlı sebzeli omlet", ["ana", "kahvalti"], 20,
  {"yumurta": 165, "mantar": 80, "kapya_biber": 50, "ispanak": 40, "kasar": 25, "tam_bugday_ekmegi": 50, "tuz_baharat": 1},
  ["Mantarı ince dilimle, biberi küçük küp doğra, ıspanağı kıy.",
   "Yumurtaları tuz ve karabiberle çırp; sebzeleri ve kaşarı ekle.",
   "Yağlanmış ısıya dayanıklı kaba dök.",
   "Airfryer'da 170 derecede 12-14 dakika (fırında 180 derecede 18 dk) ortası pişene kadar pişir.",
   "Dilimleyip ekmekle servis et."])
t("af_patates_rosti", "Çıtır patates mücveri ve yoğurt", ["ana"], 25,
  {"patates": 250, "yumurta": 55, "un": 15, "zeytinyagi": 6, "yogurt": 120, "tuz_baharat": 1},
  ["Patatesi rendele, temiz bir bezle suyunu iyice sık.",
   "Yumurta, un, tuz ve karabiberle karıştır.",
   "Pişirme kağıdına ince yassı köfteler bırak, zeytinyağı sür.",
   "Airfryer'da 190 derecede 14-16 dakika, yarısında çevirerek (fırında 210 derecede 22 dk) çıtırlaşana kadar pişir.",
   "Sarımsaklı ya da sade yoğurtla servis et."])
t("af_kasarli_tavuk_brokoli", "Airfryer'da kaşarlı tavuk ve brokoli", ["ana"], 25,
  {"tavuk_gogus": 160, "kasar": 25, "brokoli": 150, "patates": 120, "zeytinyagi": 6, "tuz_baharat": 1},
  ["Tavuğu yanından keserek kelebek gibi aç; tuz, toz biber ve kekikle ov.",
   "Patatesi ince elma dilim doğra, yağ ve tuzla harmanlayıp 190 derecede 8 dakika ön pişir.",
   "Tavuğu ve brokoli çiçeklerini ekle, 10 dakika daha pişir (fırında toplam 30 dk, 200 derece).",
   "Tavuğun üzerine kaşarı koyup 2 dakika eriyene kadar beklet."], artan=True)
t("af_kofte_patates", "Airfryer'da köfte ve patates", ["ana"], 30,
  {"dana_kiyma": 120, "sogan": 20, "patates": 200, "zeytinyagi": 4, "yogurt": 60, "tuz_baharat": 1},
  ["Kıymayı rendelenmiş soğan, kimyon, karabiber ve tuzla 3 dakika yoğurup yassı köfteler yap.",
   "Patatesi elma dilim doğra, zeytinyağı ve tuzla harmanla.",
   "Patatesleri airfryer'da 190 derecede 10 dakika pişir.",
   "Köfteleri ekleyip 10-12 dakika daha, yarısında çevirerek pişir (fırında 200 derecede toplam 35 dk).",
   "Yoğurtla servis et."], artan=True)
t("af_ton_kasarli_lavas", "Ton balıklı kaşarlı sıcak lavaş", ["ana"], 12,
  {"lavas": 70, "ton_baligi": 80, "kasar": 30, "domates": 60, "kapya_biber": 30, "tuz_baharat": 1},
  ["Ton balığını süzüp çatalla dağıt; küçük doğranmış kapya biber ve karabiberle karıştır.",
   "Lavaşın yarısına kaşarın yarısını, ton karışımını ve domates dilimlerini diz; kalan kaşarı ekle.",
   "Lavaşı kapatıp airfryer'da 180 derecede 6 dakika, bir kez çevirerek (fırında 200 derecede 9 dk) pişir.",
   "Dilimleyip servis et."])

# ---------------- ARA ÖĞÜNLER (yeni) ----------------
t("kefir_findik", "Kefir ve fındık", ["ara"], 1,
  {"kefir": 250, "findik": 15}, ["Kefiri bardağa al, fındıkla birlikte tüket."], aralik=(0.5, 1.5))
t("suzme_bal_ceviz", "Süzme yoğurt, bal ve ceviz", ["ara"], 2,
  {"suzme_yogurt": 150, "bal": 8, "ceviz": 10},
  ["Süzme yoğurdu kaseye al.", "Üzerine kırılmış ceviz ekleyip balı gezdir."], aralik=(0.5, 1.5))
t("lorlu_salata", "Lorlu domates salatalık", ["ara", "yan"], 5,
  {"lor": 100, "domates": 100, "salatalik": 100, "zeytinyagi": 5, "maydanoz": 5, "tuz_baharat": 1},
  ["Domates ve salatalığı küp doğra.", "Loru ufala, kıyılmış maydanozla birlikte ekle.",
   "Zeytinyağı, tuz ve kekikle karıştır."], aralik=(0.5, 1.5))
t("elma_fistik_ezmesi", "Fıstık ezmeli elma dilimleri", ["ara"], 3,
  {"elma": 150, "fistik_ezmesi": 15},
  ["Elmayı çekirdeklerini çıkararak ince dilimle.", "Her dilimin üzerine biraz fıstık ezmesi sür."], aralik=(0.5, 1.5))
t("nohut_cerezi", "Airfryer'da baharatlı nohut çerezi", ["ara"], 25,
  {"nohut": 40, "zeytinyagi": 4, "tuz_baharat": 1},
  ["Haşlanmış nohudu kağıt havluyla iyice kurula (kurudukça çıtır olur).",
   "Zeytinyağı, kimyon, toz kırmızı biber ve tuzla harmanla.",
   "Airfryer'da 190 derecede 15-18 dakika (fırında 200 derecede 30 dk), birkaç kez sallayarak çıtırlaşana kadar pişir.",
   "Soğuyunca kavanozda 3 gün saklanır."], artan=True, aralik=(0.5, 1.5))
t("kefirli_muz_smoothie", "Kefirli muz smoothie", ["ara"], 4,
  {"kefir": 200, "muz": 100, "yulaf": 15},
  ["Muzu dilimle.", "Kefir ve yulafla blenderda pürüzsüz olana kadar çek.", "Hemen iç."], aralik=(0.5, 1.5))
t("yogurtlu_yulaf", "Süzme yoğurtlu yulaf kasesi", ["ara", "kahvalti"], 3,
  {"suzme_yogurt": 150, "yulaf": 30, "bal": 8, "portakal": 100},
  ["Süzme yoğurt ve yulafı karıştır.", "Portakalı soyup dilimleyerek ekle, balı gezdir."], aralik=(0.5, 1.5))
t("peynir_ceviz", "Beyaz peynir, ceviz ve salatalık", ["ara"], 2,
  {"beyaz_peynir": 40, "ceviz": 15, "salatalik": 120},
  ["Salatalığı çubuk şeklinde doğra.", "Beyaz peynir ve cevizle birlikte tabağa al."], aralik=(0.5, 1.5))
t("tarcinli_elma", "Fırında tarçınlı cevizli elma", ["ara"], 20,
  {"elma": 180, "ceviz": 10, "bal": 6},
  ["Elmayı yıkayıp çekirdek evini oy, ikiye kes.",
   "Oyuk kısımlara kırılmış ceviz koy, tarçın serp ve bal gezdir.",
   "Airfryer'da 180 derecede 12 dakika, fırında 190 derecede 20 dakika ya da mikrodalgada 3-4 dakika yumuşayana kadar pişir."],
  aralik=(0.5, 1.5))
t("tahinli_muz", "Tahinli muz", ["ara"], 2,
  {"muz": 120, "tahin": 10}, ["Muzu dilimle.", "Üzerine tahin gezdir, isteğe göre tarçın serp."], aralik=(0.5, 1.5))

# ---------------- YANLAR (yeni) ----------------
t("brokoli_salatasi", "Limonlu brokoli salatası", ["yan"], 10,
  {"brokoli": 150, "limon": 10, "zeytinyagi": 6, "sarimsak": 2, "tuz_baharat": 1},
  ["Brokoliyi küçük çiçeklere ayır ve kaynar suda 3 dakika haşla.",
   "Hemen buzlu suya alarak rengini koru, süz.",
   "Limon, zeytinyağı, ezilmiş sarımsak ve tuzla karıştır."], artan=True)
t("airfryer_patates", "Airfryer'da baharatlı patates", ["yan"], 25,
  {"patates": 180, "zeytinyagi": 6, "tuz_baharat": 1},
  ["Patatesleri kabuklu ya da soyulmuş, elma dilim kes ve 10 dakika soğuk suda beklet.",
   "Suyunu süzüp kağıt havluyla iyice kurula.",
   "Zeytinyağı, kekik, toz biber ve tuzla harmanla.",
   "Airfryer'da 190 derecede 18-20 dakika (fırında 210 derecede 30 dk), yarısında sallayarak pişir."])
t("yogurtlu_karnabahar", "Yoğurtlu karnabahar salatası", ["yan"], 15,
  {"karnabahar": 150, "yogurt": 100, "sarimsak": 2, "zeytinyagi": 4, "tuz_baharat": 1},
  ["Karnabaharı küçük çiçeklere ayırıp tuzlu suda 6-7 dakika haşla, süzüp soğut.",
   "Yoğurdu ezilmiş sarımsak ve tuzla karıştır.",
   "Karnabaharı yoğurtla harmanla, üzerine pul biberli zeytinyağı gezdir."])
t("kinoa_pilavi", "Sebzeli kinoa pilavı", ["yan"], 20,
  {"kinoa": 50, "havuc": 30, "sogan": 20, "zeytinyagi": 5, "tuz_baharat": 1},
  ["Kinoayı bol suyla yıka.",
   "Soğan ve havucu küçük doğrayıp zeytinyağında 3 dakika kavur.",
   "Kinoayı ekleyip 1 dakika çevir, iki katı sıcak su ve tuz ekle.",
   "Kısık ateşte suyunu çekene kadar 12-15 dakika pişir, 5 dakika demlendir."], artan=True)
t("mantar_sote", "Mantar sote", ["yan"], 12,
  {"mantar": 150, "sogan": 20, "tereyagi": 5, "maydanoz": 5, "tuz_baharat": 1},
  ["Mantarları dilimle, soğanı ince doğra.",
   "Tavayı iyice ısıt, tereyağında soğanı 1 dakika çevir.",
   "Mantarları ekle, karıştırmadan 2 dakika bekle sonra suyunu çekene kadar sotele.",
   "Tuz, karabiber ve maydanozla servis et."])
t("kisir", "Kısır", ["yan", "ara"], 20,
  {"bulgur": 50, "domates": 60, "kapya_biber": 30, "maydanoz": 15, "salca": 8, "limon": 10, "zeytinyagi": 8,
   "marul": 30, "tuz_baharat": 1},
  ["İnce bulguru kaba al, üzerini geçecek kadar kaynar su dök ve kapağı kapalı 15 dakika şişir.",
   "Salçayı ve zeytinyağını ekleyip bulgurla iyice yoğur.",
   "Domates, kapya biber ve maydanozu çok küçük doğrayıp ekle.",
   "Limon suyu, nar ekşisi (varsa), tuz ve pul biberle tatlandır; marul yapraklarıyla servis et."], artan=True)
t("mevsim_salatasi", "Mevsim salatası", ["yan"], 8,
  {"marul": 80, "domates": 80, "salatalik": 80, "havuc": 30, "limon": 10, "zeytinyagi": 6, "tuz_baharat": 1},
  ["Marulu ince kıy, domates ve salatalığı doğra, havucu rendele.",
   "Limon, zeytinyağı ve tuzla sos hazırla, servis etmeden hemen önce karıştır."])

# ---------------- MEVCUT TARİFLERİN AYRINTILI ADIMLARI ----------------
# İlk 44 tarifin 2-3 satırlık kısa notları, uygulanabilir tarif adımlarıyla değiştirildi.
AYRINTILI = {
    "menemen": ["Biberleri ince halka, domatesleri küçük küp doğra (kabuğunu soyarsan daha yumuşak olur).",
                "Tavada zeytinyağını ısıt, biberleri 2-3 dakika yumuşayana kadar sotele.",
                "Domatesleri ekle, tuzla tatlandırıp suyunu biraz çekene kadar 5 dakika pişir.",
                "Yumurtaları doğrudan tavaya kır, hafifçe karıştırarak kıvamı yumuşakken ocaktan al.",
                "Pul biber serpip ekmekle sıcak servis et."],
    "kahvalti_tabagi": ["Yumurtaları kaynar suya dikkatle bırak ve 8-9 dakika haşla.",
                        "Soğuk suya alıp kabuklarını soy, ikiye kes.",
                        "Domates ve salatalığı dilimle.",
                        "Yumurta, peynir, zeytin ve sebzeleri tabağa diz; ekmekle servis et."],
    "yulaf_lapasi": ["Yulaf ve sütü küçük bir tencereye al.",
                     "Orta-kısık ateşte, ara ara karıştırarak 4-5 dakika koyulaşana kadar pişir (mikrodalgada 2 dk).",
                     "Muzu dilimle, cevizi kır.",
                     "Lapayı kaseye alıp muz ve cevizle süsle; isteğe göre tarçın serp."],
    "gece_yulafi": ["Kavanoz ya da kapaklı bir kaba yulaf, yoğurt ve sütü koyup iyice karıştır.",
                    "Kapağını kapatıp buzdolabında en az 6 saat (bir gece) beklet.",
                    "Sabah elmayı rendele ya da küp doğra.",
                    "Yulafın üzerine elmayı ekle, balı gezdirip soğuk servis et."],
    "ispanakli_omlet": ["Ispanağı yıkayıp ince kıy.",
                        "Tavada zeytinyağını ısıt, ıspanağı ekleyip 1-2 dakika söndür.",
                        "Yumurtaları lor, tuz ve karabiberle çırp, ıspanağın üzerine dök.",
                        "Kısık ateşte, kapağı kapalı 4-5 dakika pişir; ekmekle servis et."],
    "peynirli_tost": ["Ekmek dilimlerinin arasına kaşar ve ince domates dilimleri koy.",
                      "Tost makinesini ısıt (veya tavayı orta ateşe al).",
                      "Tostu makinede 3-4 dakika, tavada her yüzünü 2 dakika bastırarak kızart.",
                      "Salatalık dilimleriyle servis et."],
    "fistik_ezmeli_ekmek": ["Ekmeği isteğe göre kızart.", "Fıstık ezmesini ince bir tabaka halinde sür.",
                            "Muzu halka dilimleyip üzerine diz, tarçın serp."],
    "sebzeli_omlet": ["Kabağı ince yarım ay, biberi halka, domatesi küp doğra.",
                      "Zeytinyağında kabak ve biberi 4 dakika yumuşat, domatesi ekleyip 2 dakika pişir.",
                      "Çırpılmış yumurtayı sebzelerin üzerine dök.",
                      "Kaşarı serp, kapağı kapalı kısık ateşte 3-4 dakika pişir; ekmekle servis et."],
    "cilbir": ["Yoğurdu ezilmiş sarımsak ve tuzla karıştırıp oda sıcaklığına gelmesi için beklet.",
               "Geniş bir tencerede suyu kaynat, 1 yemek kaşığı sirke ekleyip ısıyı kıs.",
               "Yumurtayı bir kaseye kırıp suyu kaşıkla çevirerek oluşan girdabın ortasına bırak; 3 dakika poşe et.",
               "Delikli kepçeyle alıp yoğurdun üzerine yerleştir.",
               "Tereyağını eritip pul biber ekle, köpürünce yumurtaların üzerine gezdir; ekmekle servis et."],
    "lorlu_kahvalti": ["Loru tabağa al, üzerine balı gezdir.", "Cevizi kırıp serp.",
                       "Domates ve salatalığı dilimleyip ekmekle birlikte servis et."],
    "mercimek_corbasi": ["Mercimeği suyu berraklaşana kadar yıka.",
                         "Soğanı yemeklik doğrayıp zeytinyağında kavur; küp havuç ve patatesi ekleyip 3 dakika çevir.",
                         "Mercimeği ve 3 su bardağı sıcak suyu ekle, kısık ateşte 25 dakika pişir.",
                         "Blenderdan geçir (yoksa iyice karıştırarak ez); kıvamı koyuysa su ekle.",
                         "Tuz, kimyon ve pul biberle tatlandır, limonla servis et."],
    "ezogelin": ["Mercimek, bulgur ve pirinci birlikte yıka.",
                 "Tereyağında ince doğranmış soğanı kavur, salçayı ekleyip kokusu çıkana kadar çevir.",
                 "Bakliyatı ve 3 su bardağı sıcak suyu ekle, kısık ateşte 30 dakika pişir.",
                 "Kuru nane ve pul biberi ekleyip 2 dakika daha kaynat; ekmekle servis et."],
    "yesil_mercimek_yemegi": ["Mercimeği yıkayıp 15 dakika ön haşla ve süz.",
                              "Soğanı zeytinyağında kavur, salçayı ekle.",
                              "Mercimek ve bulguru ekleyip 2 su bardağı sıcak su ilave et.",
                              "Kısık ateşte mercimekler yumuşayana kadar 20 dakika pişir; tuz ve pul biberle tatlandır."],
    "kuru_fasulye": ["Fasulyeyi bir gece önceden bol suda ıslat.",
                     "Suyunu değiştirip fasulyeyi 30 dakika (düdüklüde 10 dk) ön haşla, süz.",
                     "Soğanı zeytinyağında kavur, salçayı ekleyip 1 dakika çevir.",
                     "Fasulyeyi ve üzerini 2 parmak geçecek sıcak suyu ekle.",
                     "Kısık ateşte fasulyeler yumuşayana kadar 30-40 dakika pişir; pilavla servis et."],
    "nohut_yemegi": ["Nohudu bir gece önceden ıslat, ertesi gün 45 dakika (düdüklüde 15 dk) haşla.",
                     "Soğanı zeytinyağında kavur, salçayı ve rendelenmiş domatesi ekle.",
                     "Nohudu ve haşlama suyundan 1 su bardağı ekle.",
                     "Kısık ateşte 25 dakika pişir; tuz ve karabiberle tatlandır."],
    "tavuk_sote": ["Tavuğu kuşbaşı, biber ve soğanı şerit, domatesi küp doğra.",
                   "Kızgın tavada tavuğu suyunu salıp çekene kadar 6 dakika sotele.",
                   "Soğan ve biberi ekleyip 3 dakika çevir.",
                   "Domatesi ekle, kekik ve tuzla tatlandırıp 10 dakika pişir."],
    "firin_tavuk_patates": ["Fırını 200 dereceye ısıt.",
                            "Salça, zeytinyağı, kekik, pul biber ve tuzu karıştırıp sos yap.",
                            "Tavuk butları, elma dilim patates ve iri doğranmış soğanı sosla harmanla.",
                            "Tepsiye tek kat yay; 40 dakika (airfryer'da 190 derecede 25 dk) pişir."],
    "tavuklu_bulgur": ["Tavuğu küçük doğrayıp tencerede sotele.",
                       "Soğan ve biberi ekleyip kavur, salçayı ilave et.",
                       "Bulguru ekleyip 2 dakika çevir, iki katı sıcak su ve tuz ekle.",
                       "Kısık ateşte suyunu çekene kadar 15 dakika pişir, 10 dakika demlendir."],
    "tavuklu_makarna": ["Makarnayı tuzlu suda paket süresine göre haşla.",
                        "Tavuğu küçük doğrayıp tavada sotele.",
                        "Sarımsağı ve rendelenmiş domatesi ekleyip 8 dakika sos kıvamına gelene kadar pişir.",
                        "Makarnayı sosa ekleyip karıştır; fesleğen ya da kekikle servis et."],
    "ton_makarna_salatasi": ["Makarnayı haşlayıp soğuk sudan geçir.",
                             "Ton balığını süz, domates, salatalık ve maydanozu doğra.",
                             "Zeytinyağı, limon ve tuzla sos hazırla.",
                             "Tüm malzemeleri karıştırıp buzdolabında 10 dakika dinlendir."],
    "ton_salata": ["Marulu yıkayıp kurula ve doğra.", "Domates ve salatalığı doğra.",
                   "Ton balığını süzüp ekle.", "Zeytinyağı ve limonla karıştırıp ekmekle servis et."],
    "izmir_kofte": ["Kıymayı rendelenmiş soğan, kimyon, karabiber ve tuzla yoğurup köfte şekli ver.",
                    "Patatesleri elma dilim doğrayıp az yağda kızart ya da fırında 10 dakika ön pişir.",
                    "Köfte, patates, biber ve domates dilimlerini tepsiye sırayla diz.",
                    "Salçayı 1 su bardağı sıcak suyla açıp üzerine gezdir.",
                    "200 derecede 35 dakika (airfryer'da 190 derecede 20 dk) pişir."],
    "kiymali_makarna": ["Makarnayı tuzlu suda haşla.",
                        "Kıymayı suyunu çekene kadar kavur, soğanı ekleyip pembeleştir.",
                        "Salça ve rendelenmiş domatesi ekleyip 8 dakika pişir.",
                        "Makarnayı sosla karıştırıp servis et."],
    "kiymali_ispanak": ["Ispanağı yıkayıp iri kıy.",
                        "Kıymayı soğanla kavur, salçayı ekle.",
                        "Ispanak ve yıkanmış pirinci ekle, yarım su bardağı sıcak su ilave et.",
                        "Kısık ateşte 15 dakika pişir; yoğurtla servis et."],
    "kiymali_patlican": ["Patlıcanları alacalı soyup halka dilimle, tuzlu suda 15 dakika beklet ve kurula.",
                         "Az yağla fırında (veya airfryer'da) 15 dakika yumuşayana kadar pişir.",
                         "Kıymayı soğan, biber ve domatesle kavurup harç yap.",
                         "Fırın kabına patlıcan ve kıymayı kat kat diz.",
                         "200 derecede 20 dakika pişir."],
    "zeytinyagli_fasulye": ["Fasulyelerin uçlarını kesip ikiye böl.",
                            "Soğanı zeytinyağında yumuşayana kadar öldür.",
                            "Fasulye ve rendelenmiş domatesi ekle, tuz ve bir tutam şeker serp.",
                            "Yarım su bardağı sıcak su ekleyip kısık ateşte 35 dakika pişir; soğuk servis et."],
    "mucver": ["Kabağı rendeleyip tuzlayarak 10 dakika beklet, suyunu iyice sık.",
               "Yumurta, un, ufalanmış peynir, maydanoz ve dereotuyla karıştır.",
               "Az yağlı tavada kaşıkla bırakıp iki yüzünü 3'er dakika kızart (airfryer'da 190 derecede 12 dk, fırında 200 derecede 20 dk)."],
    "mercimek_koftesi": ["Mercimeği 2 su bardağı suyla dağılana kadar haşla.",
                         "Ocaktan alıp bulguru ekle, kapağı kapalı 20 dakika şişir.",
                         "Soğanı zeytinyağında kavurup salçayı ekle, karışıma ilave et.",
                         "Kıyılmış maydanoz, kimyon ve pul biberle yoğur.",
                         "Köfte şekli verip marul yapraklarıyla, limonla servis et."],
    "firin_sebze": ["Nohudu önceden haşla.",
                    "Patates, kabak, havuç ve patlıcanı iri küp doğra.",
                    "Sebzeleri nohut, zeytinyağı, kekik ve tuzla harmanla.",
                    "200 derecede 35 dakika (airfryer'da 190 derecede 20 dk) karıştırarak pişir."],
    "yogurtlu_makarna": ["Makarnayı tuzlu suda haşla.", "Yoğurdu ezilmiş sarımsakla karıştır.",
                         "Makarnayı tabağa alıp yoğurdu döktür.",
                         "Tereyağını pul biberle eritip üzerine gezdir."],
    "tavuk_corbasi": ["Tavuğu 25 dakika haşla, suyunu ayır ve didikle.",
                      "Tavuk suyuna küp doğranmış havuç, patates, soğan ve yıkanmış pirinci ekle.",
                      "Kısık ateşte 20 dakika pişir.",
                      "Tavuğu geri ekleyip 2 dakika kaynat; limonla servis et."],
    "nohutlu_pilav": ["Pirinci ılık tuzlu suda 15 dakika beklet, süz.",
                      "Tereyağında pirinci 2 dakika kavur, haşlanmış nohudu ekle.",
                      "Pirincin 1,5 katı sıcak su ve tuz ekle.",
                      "Kısık ateşte suyunu çekene kadar pişir, 10 dakika demlendir."],
    "pirinc_pilavi": ["Pirinci ılık tuzlu suda 15 dakika beklet ve süz.",
                      "Tereyağında pirinci taneleri şeffaflaşana kadar kavur.",
                      "1,5 katı sıcak su ve tuzu ekle, kısık ateşte suyunu çekene kadar pişir.",
                      "Kapağın altına kağıt havlu koyup 10 dakika demlendir."],
    "bulgur_pilavi": ["Soğanı zeytinyağında kavur, rendelenmiş domatesi ekleyip 3 dakika pişir.",
                      "Bulguru ekleyip 1 dakika çevir.",
                      "İki katı sıcak su ve tuz ekle, kısık ateşte 15 dakika pişir.",
                      "10 dakika demlendirip servis et."],
    "coban_salatasi": ["Domates, salatalık, soğan ve biberi küçük küp doğra.",
                       "Maydanozu ince kıy.", "Zeytinyağı, limon ve tuzla karıştırıp hemen servis et."],
    "cacik": ["Salatalığı rendele ya da küçük doğra.", "Yoğurdu ezilmiş sarımsak ve tuzla çırp.",
              "Salatalığı ekleyip isteğe göre su ile inceltir, kuru nane serpip servis et."],
    "humus_havuc": ["Haşlanmış nohudu kabuklarını ayıklayarak blender haznesine al.",
                    "Tahin, limon suyu, sarımsak, zeytinyağı ve 2-3 yemek kaşığı haşlama suyunu ekle.",
                    "Pürüzsüz olana kadar 1-2 dakika çek.",
                    "Havuçları çubuk şeklinde doğrayıp humusla servis et."],
}
for _t in T:
    if _t["id"] in AYRINTILI:
        _t["adimlar"] = AYRINTILI[_t["id"]]

# ---------------- PİŞİRME EKİPMANI ----------------
# Her tarif için ALTERNATİF ekipman setleri: kullanıcının elinde setlerden biri tam olarak varsa
# tarif yapılabilir. [] = pişirme gerekmez. Listede olmayan tarif varsayılan olarak ocak ister.
# Ekipmanlar: ocak, firin, airfryer, mikrodalga, blender, tost_makinesi
OCAK = [["ocak"]]
PISIRMESIZ = [[]]
EKIPMAN = {
    "kahvalti_tabagi": OCAK, "yulaf_lapasi": [["ocak"], ["mikrodalga"]], "gece_yulafi": PISIRMESIZ,
    "peynirli_tost": [["tost_makinesi"], ["ocak"], ["airfryer"]], "fistik_ezmeli_ekmek": PISIRMESIZ,
    "lorlu_kahvalti": PISIRMESIZ,
    "firin_tavuk_patates": [["firin"], ["airfryer"]], "izmir_kofte": [["firin"], ["airfryer"]],
    "kiymali_patlican": [["ocak", "firin"], ["ocak", "airfryer"]],
    "mucver": [["ocak"], ["airfryer"], ["firin"]], "firin_sebze": [["ocak", "firin"], ["ocak", "airfryer"]],
    "ton_salata": PISIRMESIZ, "coban_salatasi": PISIRMESIZ, "cacik": PISIRMESIZ,
    "yogurt_bal_ceviz": PISIRMESIZ, "elma_findik": PISIRMESIZ, "muz_fistik": PISIRMESIZ, "ayran": PISIRMESIZ,
    "humus_havuc": [["ocak", "blender"]], "portakal_ceviz": PISIRMESIZ, "lor_bal": PISIRMESIZ,
    # yeni tarifler
    "lorlu_yumurta_durum": OCAK, "yumurtali_muffin": [["firin"], ["airfryer"]], "suzme_meyve_kase": PISIRMESIZ,
    "kefirli_smoothie": [["blender"]], "fistikli_yulaf_lapasi": [["ocak"], ["mikrodalga"]],
    "ispanakli_lavas_gozleme": [["ocak"], ["ocak", "tost_makinesi"]], "tahinli_suzme_kase": PISIRMESIZ,
    "lavas_pizza": [["airfryer"], ["firin"]],
    "firin_karnabahar_nohut": [["ocak", "firin"], ["ocak", "airfryer"]],
    "airfryer_tavuk_sebze": [["airfryer"], ["firin"]], "ton_durum": PISIRMESIZ, "tavuk_durum": [["ocak"], ["airfryer"]],
    "firin_kofte_brokoli": [["firin"], ["airfryer"]], "tavuklu_kinoa_kase": OCAK,
    "firin_frittata": [["ocak", "firin"], ["ocak", "airfryer"]], "lavas_borek": [["ocak", "firin"], ["ocak", "airfryer"]],
    "brokoli_corbasi": [["ocak", "blender"], ["ocak"]], "firin_tavuk_karnabahar": [["firin"], ["airfryer"]],
    "firin_kiymali_kabak": [["ocak", "firin"], ["ocak", "airfryer"]],
    "airfryer_falafel": [["blender", "airfryer"], ["blender", "firin"]],
    "kefir_findik": PISIRMESIZ, "suzme_bal_ceviz": PISIRMESIZ, "lorlu_salata": PISIRMESIZ,
    "elma_fistik_ezmesi": PISIRMESIZ, "nohut_cerezi": [["ocak", "airfryer"], ["ocak", "firin"]],
    "kefirli_muz_smoothie": [["blender"]], "yogurtlu_yulaf": PISIRMESIZ, "peynir_ceviz": PISIRMESIZ,
    "tarcinli_elma": [["airfryer"], ["firin"], ["mikrodalga"]], "tahinli_muz": PISIRMESIZ,
    "airfryer_patates": [["airfryer"], ["firin"]], "mevsim_salatasi": PISIRMESIZ,
}
for _t in T:
    # "af_" ile başlayanlar: ocak gerektirmeyen airfryer / fırın tarifleri
    varsayilan = [["airfryer"], ["firin"]] if _t["id"].startswith("af_") else OCAK
    _t["ekipman"] = EKIPMAN.get(_t["id"], varsayilan)

json.dump(T, open("tarifler.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(T), "tarif")
