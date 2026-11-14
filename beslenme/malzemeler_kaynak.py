# Malzeme listesi kaynağı -> malzemeler.json üretir.
# Besin değerleri 100 g için YAKLAŞIK değerlerdir (USDA FoodData Central / genel kaynaklar).
# Yayına çıkmadan önce TÜRKOMP (turkomp.tarimorman.gov.tr) ile doğrulanmalı.
# alanlar: id, ad, kategori, kcal, protein, karb, yag, lif, arama, paket_g, dolapta
import json

M = [
 # id, ad, kategori, kcal, prot, karb, yag, lif, arama terimleri, tipik paket (g, None=açık satış), dolapta
 ("yumurta","Yumurta","hayvansal",143,12.6,0.7,9.5,0,["yumurta"],600,False),
 ("beyaz_peynir","Beyaz peynir","sut_urunu",264,14.2,4.1,21.3,0,["beyaz peynir"],500,False),
 ("lor","Lor peyniri","sut_urunu",98,12.5,3.5,4.0,0,["lor peyniri","lor"],500,False),
 ("kasar","Kaşar peyniri","sut_urunu",360,25,2,28,0,["kaşar"],400,False),
 ("yogurt","Yoğurt","sut_urunu",61,3.5,4.7,3.3,0,["yoğurt"],1000,False),
 ("sut","Süt","sut_urunu",61,3.2,4.8,3.3,0,["süt"],1000,False),
 ("zeytin","Siyah zeytin","bitkisel",160,1.5,5,15,3,["siyah zeytin","zeytin"],400,False),
 ("domates","Domates","sebze",18,0.9,3.9,0.2,1.2,["domates"],None,False),
 ("salatalik","Salatalık","sebze",15,0.7,3.6,0.1,0.5,["salatalık"],None,False),
 ("sivri_biber","Sivri biber","sebze",20,0.9,4.6,0.2,1.7,["sivri biber","biber"],None,False),
 ("sogan","Kuru soğan","sebze",40,1.1,9.3,0.1,1.7,["kuru soğan","soğan"],None,False),
 ("sarimsak","Sarımsak","sebze",149,6.4,33,0.5,2.1,["sarımsak"],None,False),
 ("patates","Patates","sebze",77,2.0,17,0.1,2.2,["patates"],None,False),
 ("havuc","Havuç","sebze",41,0.9,9.6,0.2,2.8,["havuç"],None,False),
 ("kabak","Kabak","sebze",17,1.2,3.1,0.3,1.0,["kabak"],None,False),
 ("ispanak","Ispanak","sebze",23,2.9,3.6,0.4,2.2,["ıspanak"],None,False),
 ("patlican","Patlıcan","sebze",25,1.0,5.9,0.2,3.0,["patlıcan"],None,False),
 ("taze_fasulye","Taze fasulye","sebze",31,1.8,7.0,0.1,3.4,["taze fasulye"],None,False),
 ("marul","Marul","sebze",15,1.4,2.9,0.2,1.3,["marul"],None,False),
 ("maydanoz","Maydanoz","sebze",36,3.0,6.3,0.8,3.3,["maydanoz"],None,False),
 ("limon","Limon","meyve",29,1.1,9.3,0.3,2.8,["limon"],None,False),
 ("muz","Muz","meyve",89,1.1,22.8,0.3,2.6,["muz"],None,False),
 ("elma","Elma","meyve",52,0.3,13.8,0.2,2.4,["elma"],None,False),
 ("portakal","Portakal","meyve",47,0.9,11.8,0.1,2.4,["portakal"],None,False),
 ("kirmizi_mercimek","Kırmızı mercimek (kuru)","bakliyat",350,24,60,1.5,11,["kırmızı mercimek"],1000,False),
 ("yesil_mercimek","Yeşil mercimek (kuru)","bakliyat",352,24.6,63,1.1,10.7,["yeşil mercimek"],1000,False),
 ("nohut","Nohut (kuru)","bakliyat",364,19,61,6,17,["nohut"],1000,False),
 ("kuru_fasulye","Kuru fasulye (kuru)","bakliyat",333,23.6,60,0.8,15,["kuru fasulye"],1000,False),
 ("bulgur","Bulgur","tahil",342,12.3,75.9,1.3,18.3,["bulgur"],1000,False),
 ("pirinc","Pirinç","tahil",365,7.1,80,0.7,1.3,["pirinç"],1000,False),
 ("makarna","Makarna","tahil",371,13,75,1.5,3.2,["makarna"],500,False),
 ("yulaf","Yulaf ezmesi","tahil",389,16.9,66,6.9,10.6,["yulaf"],500,False),
 ("tam_bugday_ekmegi","Tam buğday ekmeği","tahil",247,13,41,3.4,7,["tam buğday ekmeği","tam buğday"],400,False),
 ("un","Buğday unu","tahil",364,10,76,1,2.7,["un"],1000,False),
 ("tavuk_gogus","Tavuk göğüs","et",120,22.5,0,2.6,0,["tavuk göğüs","piliç göğüs"],500,False),
 ("tavuk_but","Tavuk but (derisiz)","et",121,19.7,0,4.1,0,["tavuk but","piliç but","pirzola"],500,False),
 ("dana_kiyma","Dana kıyma","et",254,17.2,0,20,0,["dana kıyma","kıyma"],500,False),
 ("ton_baligi","Ton balığı (suda, süzülmüş)","balik",116,25.5,0,0.8,0,["ton balığı"],160,False),
 ("tahin","Tahin","bitkisel",595,17,21,54,9,["tahin"],300,False),
 ("fistik_ezmesi","Fıstık ezmesi","bitkisel",588,25,20,50,6,["fıstık ezmesi"],340,False),
 ("ceviz","Ceviz içi","kuruyemis",654,15.2,13.7,65.2,6.7,["ceviz"],150,False),
 ("findik","Fındık içi","kuruyemis",628,15,16.7,60.8,9.7,["fındık"],150,False),
 ("bal","Bal","diger",304,0.3,82.4,0,0.2,["bal"],450,False),
 ("salca","Domates salçası","diger",82,4.3,18.9,0.5,4.1,["domates salçası","salça"],700,False),
 ("zeytinyagi","Zeytinyağı","yag",884,0,0,100,0,["zeytinyağı"],1000,False),
 ("aycicek_yagi","Ayçiçek yağı","yag",884,0,0,100,0,["ayçiçek yağı"],1000,False),
 ("tereyagi","Tereyağı","yag",717,0.9,0.1,81,0,["tereyağı"],250,False),
 # dolapta olduğu varsayılanlar: haftalık alışverişe girmez, besin değeri ihmal edilir
 ("tuz_baharat","Tuz ve baharatlar","dolap",0,0,0,0,0,[],None,True),
]
out = [dict(zip(["id","ad","kategori","kcal","protein","karb","yag","lif","arama","paket_g","dolapta"], r)) for r in M]
json.dump(out, open("malzemeler.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(out), "malzeme")
