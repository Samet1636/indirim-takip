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

json.dump(T, open("tarifler.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(T), "tarif")
