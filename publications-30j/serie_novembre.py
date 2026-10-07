# -*- coding: utf-8 -*-
"""Quatrième série : 30 publications de la page Hourdis Madagascar, 20/10 → 18/11/2026.

ANGLE — « la série est proportionnée à la mesure, et chaque réponse finit sur une DATE ».

1. Proportionnée. Le relevé du 18/09/2026 sur 948 messages privés et 21 commentaires de la page
   (LISEZ-MOI.md, § série de 14:00) compte 690 occurrences de thèmes :
   disponibilité/commande 186 · prix 110 · adresse 108 · plancher/dalle 79 · quantités 76 ·
   hauteur 12/15/20 64 · livraison 41 · photos réelles 26.
   Les 30 publications sont réparties au prorata (méthode du plus fort reste, refaite par
   verifier.py à partir de MESURE) : 8 · 5 · 5 · 3 · 3 · 3 · 2 · 1. Le mois répond donc à ce
   qu'on nous demande, dans la proportion où on nous le demande — pas à ce qui nous plaît.

2. Une DATE. Le thème n°1 (186 / 948 messages, 20 %) est « est-ce qu'il y en a ? ». Notre
   réponse honnête n'est pas un stock, c'est un délai : ≈ 30 jours de production + 3 à 7 jours
   de livraison (site/data/produits.json). Un délai se subit ; un calendrier se décide. Chaque
   publication du fil « commande » porte donc des dates réelles, calculées depuis sa propre date
   de parution (champ « calendrier », recalculé par verifier.py : commande + 33 à + 37 jours).
   Règle d'Andry du 06/09/2026 : jamais « en stock » ni « disponible » ; ici, pas même le mot.

3. Saison. Le mois couvre l'entrée de la saison des pluies : qui commande en novembre reçoit en
   décembre. C'est le fil rouge des publications A5, A4 et A8.

Sources de faits, et nulle part ailleurs (comme les trois séries précédentes) :
  - site/data/produits.json  (prix à la pièce, pièces par m², 1 500 Ar/km, délais, zones)
  - site/faq.html            (choix 12/15/20 par portée, pose, étais 21–28 j, dalle 4–5 cm,
                              gaines dans les alvéoles, paiement, enlèvement, remise gros volume)
Le deuxième gisement (141 trouvailles « nouvelle » du bot de veille, lues en lecture seule) a servi
d'INSPIRATION pour trois sujets techniques que les trois séries précédentes n'avaient pas traités —
étaiement (51 trouvailles), dalle de compression et treillis, accès du camion. Aucun texte, aucune
image, aucun chiffre de ces trouvailles n'est repris : ce sont des sources françaises, nos chiffres
restent les nôtres.

Heure : 10:00. C'est la seule heure mesurée sur la page (LISEZ-MOI.md : 170 publications,
0,96 réaction en moyenne à 10 h contre 0,81 à 18 h). ⚠ Mesure NON RECALCULÉE ici (la page est
sanctionnée depuis le 06/10/2026, aucun appel Meta n'a été fait) : l'écart est faible et confondu
avec le type de contenu. Une seule ligne à changer ci-dessous si Andry préfère 18:00.
"""
from serie import CIBLES  # noqa: F401  (mêmes ancres du site que les trois autres séries)

HEURE = "10:00"
CAMPAGNE = "serie-novembre"
PREFIXE = "n"
SORTIE_NOM = "sortie-novembre"
AFFECTATION = "affectation-novembre.json"
NOM = "-novembre"
DEBUT = "2026-10-20"

# Le relevé du 18/09/2026 (948 messages privés + 21 commentaires). verifier.py refait la
# répartition au plus fort reste et refuse la série si les thèmes déclarés n'y collent pas.
MESURE = {
    "commande": 186,    # « misy ve ? », disponibilité → notre réponse est un calendrier
    "prix": 110,
    "adresse": 108,
    "pose": 79,         # plancher / dalle
    "quantites": 76,
    "hauteur": 64,      # 12 / 15 / 20
    "livraison": 41,
    "photos": 26,
}

# Contrôles ajoutés POUR CETTE SÉRIE (verifier.py les empile sur les siens, il n'en retire aucun).
# « stock » est interdit en entier, pas seulement « en stock » : la règle d'Andry du 06/09/2026
# porte sur l'idée, et le mot seul suffit à la faire passer.
INTERDITS_EN_PLUS = [r"\bstock\b", r"\bmisy foana\b", r"\bmisy hatrany\b", r"\bgarantie\b"]
PHOTOS_EXIGEANTES = True   # ≥ 1080 px de large et aucun filigrane sur les photos employées

SERIE = [
    # ================================================================= semaine 1 (20 → 26/10)
    {
        "date": "2026-10-20", "slug": "kalandrie-manafatra-anio", "cible": "livraison",
        "theme": "commande",
        "calendrier": {"commande": "2026-10-20", "chantier": ["2026-11-22", "2026-11-26"]},
        "affiche": {"gabarit": "etapes", "badge": "KALANDRIE", "titre": "Manafatra anio ?",
                    "sous_titre": "Ity ny daty marina",
                    "etapes": [("Commande", "talata 20/10"),
                               ("Famokarana", "eo amin'ny 30 andro"),
                               ("Fanaterana", "3 à 7 andro")],
                    "arrivee_libelle": "EO AMIN'NY CHANTIER", "arrivee": "22 – 26/11"},
        "texte": """📅 Manafatra anio, 20/10 : rahoviana no tonga eo amin'ny chantier ?

Amin'ny commande no anaovanay ny hourdis sy ny biriky — ka ny daty no zava-dehibe indrindra, fa tsy ny isa.

1️⃣ Commande anio, 20/10
2️⃣ Famokarana : eo amin'ny 30 andro (famolavolana, fanamainana, fandorana)
3️⃣ Fanaterana : 3 à 7 andro, arakaraka ny halavirana

➡️ Eo amin'ny chantier eo amin'ny 22/11 ka hatramin'ny 26/11.

💡 Izay no antony ilazanay foana : ny daty tianao hanaovana ny dalle no ambarao aminay voalohany. Avy eo vao ny isa.""",
    },
    {
        "date": "2026-10-21", "slug": "tsy-tafiditra-ao-amin-ny-vidiny", "cible": "produits",
        "theme": "prix",
        "affiche": {"gabarit": "question", "badge": "NANONTANY IANAREO",
                    "question": "Io 3 400 Ar io ve dia efa vita ny gorodona ?",
                    "lignes": ["Vidin'ny biriky ihany io", "Tsy tafiditra : poutrelle, treillis, béton",
                               "Tsy tafiditra : mpiasa sy fanaterana"]},
        "texte": """💬 « Io 3 400 Ar io ve dia efa vita ny gorodona ? »

Fanontaniana tsara, ary mendrika valiny mazava : tsia. Ny vidinay dia ny vidin'ny biriky ihany.

Tafiditra ao :
✅ Ny hourdis na ny brique, isaky ny pièce, vita sy voadoro

Tsy tafiditra ao :
❌ Poutrelle, treillis soudé, simenitra sy fasika ho an'ny dalle de compression
❌ Ny mpiasa sy ny fitaovana eny an-toerana
❌ Ny fanaterana : 1 500 Ar isaky ny km manomboka eto Ambohimanga Rova

Milaza izany mialoha izahay mba tsy hisy fahatairana amin'ny farany. Ny devis an-tsoratra no manan-kery.""",
    },
    {
        "date": "2026-10-22", "slug": "aiza-izahay-ambohimanga-rova", "cible": "livraison",
        "theme": "adresse",
        "affiche": {"gabarit": "photo", "badge": "TOERANA", "titre": "Ambohimanga Rova",
                    "sous_titre": "Ny atelier, ny fakana, ny fanaterana"},
        "photo_voulue": "vue d'ensemble du hangar de séchage",
        "texte": """📍 « Aiza no misy anareo ? »

Io no anankiray amin'ny fanontaniana apetrakareo matetika indrindra. Ity ny valiny feno :

🏭 Ambohimanga Rova no misy ny toeram-pamokarana : eo no amolavolana, anamainana ary andorana ny hourdis, ny brique creuse sy ny tuile.
🚚 Avy eo no miainga ny kamiao mankany amin'ny chantier-nao : 1 500 Ar isaky ny km.
🚙 Afaka maka mivantana amin'ny fiaranao ihany koa ianao, ka tsy mandoa saran-dalana.

📞 Antsoy izahay alohan'ny hiaingana : lazainay aminao ny lalana sy ny ora mety, ary omanina ny entana.""",
    },
    {
        "date": "2026-10-23", "slug": "tohana-21-28-andro", "cible": "faq",
        "theme": "pose",
        "affiche": {"gabarit": "carte", "badge": "FAMETRAHANA", "titre": "Ny tohana (étais)",
                    "sous_titre": "21 ka hatramin'ny 28 andro",
                    "lignes": ["1 · Poutrelle apetraka, tohanana", "2 · Hourdis atsofoka an-tanana",
                               "3 · Treillis, dia dalle 4 à 5 cm", "4 · Avelao ny tohana"],
                    "note": "Mandra-pahamafin'ny béton tanteraka"},
        "texte": """🪵 Ny fahadisoana lafo indrindra eny an-chantier : manala ny tohana aloha loatra.

Ahoana no tokony hatao ?

1️⃣ Apetraka eo ambonin'ny rindrina mitondra entana ny poutrelle, dia tohanana tsara.
2️⃣ Atsofoka an-tanana eo anelanelan'ny poutrelle ny hourdis — tsy mila coffrage.
3️⃣ Velarina ny treillis soudé, dia arotsaka ny dalle de compression, 4 à 5 cm.
4️⃣ Avela eo ny tohana mandra-pahamafin'ny béton tanteraka : 21 ka hatramin'ny 28 andro.

⏳ Tsy fe-potoana noforonina ireo andro ireo : izay no ilain'ny béton hahazoany ny tanjany. Manontania ny ingénieur-nao raha misy ahiahy momba ny plan-nao.""",
    },
    {
        "date": "2026-10-24", "slug": "filaharana-sy-lot-malalaka", "cible": "devis",
        "theme": "commande",
        "affiche": {"gabarit": "question", "badge": "NANONTANY IANAREO",
                    "question": "Misy lot efa vita ve, sa manafatra vao misy ?",
                    "lignes": ["Amin'ny commande no anaovanay azy", "Ny lot vita dia efa voatokana",
                               "Raha misy malalaka, antsoinay ianao"]},
        "texte": """💬 « Misy lot efa vita ve, sa manafatra vao misy ? »

Ny valiny marina, tsy misy fanodikodinana :

🧱 Amin'ny commande no anaovanay ny hourdis sy ny biriky. Eo amin'ny 30 andro ny famokarana.
📋 Ny lot efa vita dia voatokana ho an'izay nanao commande talohanao.
📞 Raha misy lot malalaka alohan'ny fotoana, izahay no miantso anao : tsy very ny toeranao.

➡️ Ny fomba tokana hahazoana ny entana amin'ny fotoana ilainao dia ny miditra amin'ny filaharana. Ny devis no milaza ny acompte sy ny ambiny.""",
    },
    {
        "date": "2026-10-25", "slug": "kajy-ao-amin-ny-tranonkala", "cible": "produits",
        "theme": "quantites",
        "affiche": {"gabarit": "capture", "badge": "KAJY", "titre": "Kajy ao anaty finday",
                    "sous_titre": "Surface → pièces → budget", "capture": "calcul"},
        "texte": """📱 Tsy tianao ve ny manisa ? Ny tranonkala no manao azy.

Ao amin'ny hourdis.fonenako.mg, isaky ny vokatra dia misy bokotra « Calculer mes quantités ». Ampidiro ny surface, dia omeny anao avy hatrany :

📐 Ny isan'ny pièce ilaina
💰 Ny budget mifanaraka amin'izany
📝 Ary feno mialoha ny demande de devis

Ohatra hita eo amin'ny sary, hourdis 15 :
40 m² → 360 pièces
360 × 3 000 Ar = 1 080 000 Ar

Tombana izany, tsy tafiditra ny fanaterana sy ny tahiry ho an'ny vaky. Ny devis an-tsoratra no manan-kery.""",
    },
    {
        "date": "2026-10-26", "slug": "tafo-72m2-roa-safidy", "cible": "produits",
        "theme": "prix",
        "affiche": {"gabarit": "carte", "badge": "TAFO", "titre": "Tafo 72 m²",
                    "sous_titre": "Mécanique sa écaille ?",
                    "lignes": ["Mécanique : 2 376 000 Ar", "Écaille : 2 700 000 Ar"],
                    "note": "15 sy 75 isaky ny m² · tsy tafiditra ny fanaterana"},
        "photo_voulue": "tuiles mécaniques rangées sur chant (bande)",
        "texte": """🏠 Tafo 72 m² : tuile mécanique sa tuile écaille ?

Samy tanimanga, samy maharitra. Ny isa no mampitaha azy roa :

🔸 TUILE MÉCANIQUE — 15 isaky ny m²
72 m² → 1 080 tuiles
1 080 × 2 200 Ar = 2 376 000 Ar

🔸 TUILE ÉCAILLE — 75 isaky ny m²
72 m² → 5 400 tuiles
5 400 × 500 Ar = 2 700 000 Ar

Ny mécanique dia haingana kokoa apetraka ary vitsy kokoa ny isany. Ny écaille kosa manome endrika nentim-paharazana, tena tsara amin'ny tafo mideza.

Tsy tafiditra ny fanaterana. Ampio ny tahiry ho an'ny vaky.""",
    },
    # ================================================================= semaine 2 (27/10 → 02/11)
    {
        "date": "2026-10-27", "slug": "faritra-anaterana", "cible": "livraison",
        "theme": "adresse",
        "affiche": {"gabarit": "carte", "badge": "FANATERANA", "titre": "Aiza no anaterana ?",
                    "sous_titre": "Antananarivo sy ny manodidina",
                    "lignes": ["Antananarivo sy ny akaiky", "Ambohimanga · Alasora",
                               "Imerintsiatosika · Andramasina"],
                    "note": "1 500 Ar isaky ny km hatreto Ambohimanga Rova"},
        "photo_voulue": "pile de briques creuses cuites dans la cour (bande)",
        "texte": """🚚 « Manatitra any aminay ve ianareo ? »

Ireto ny faritra anaterana mivantana eny amin'ny chantier :

📍 Antananarivo sy ny manodidina akaiky
📍 Ambohimanga
📍 Alasora
📍 Imerintsiatosika
📍 Andramasina

💰 1 500 Ar isaky ny km, manomboka eto amin'ny toeram-pamokarana Ambohimanga Rova. Voasoratra ao amin'ny devis izany alohan'ny fanekenao.

Lavitra kokoa noho ireo ve ny chantier-nao ? Manontania ihany : dinihinay tsirairay.""",
    },
    {
        "date": "2026-10-28", "slug": "datim-pilana-miverina", "cible": "livraison",
        "theme": "commande",
        "calendrier": {"commande": "2026-11-13", "chantier": ["2026-12-16", "2026-12-20"]},
        "affiche": {"gabarit": "carte", "badge": "KALANDRIE", "titre": "Miverina avy aoriana",
                    "sous_titre": "Daty ilainao → daty commande",
                    "lignes": ["Tianao : 20/12", "− 7 andro : fanaterana",
                               "− 30 andro : famokarana", "= manafatra alohan'ny 13/11"],
                    "note": "Ny daty no tanisao aminay voalohany"},
        "texte": """🔄 Misy fomba tsotra hamantarana hoe rahoviana no tokony hanafatra : miverina avy any aoriana.

Ohatra. Tianao ho vita ny dalle alohan'ny 20/12 :

📅 20/12 — ny daty tianao ho eo amin'ny chantier
➖ 7 andro — ny fanaterana (3 à 7 andro)
➖ 30 andro — ny famokarana
✅ 13/11 — ny daty farany tokony hanaovanao commande

Raha manafatra ny 13/11 ianao, dia eo amin'ny chantier ny entana eo amin'ny 16/12 ka hatramin'ny 20/12.

💡 Soraty ao amin'ny hafatrao ny daty tianao : izahay no manao ny kajy miaraka aminao.""",
    },
    {
        "date": "2026-10-29", "slug": "haavo-araka-ny-portee", "cible": "produits",
        "theme": "hauteur",
        "affiche": {"gabarit": "hauteurs", "badge": "HAAVO", "titre": "12, 15 sa 20 ?",
                    "sous_titre": "Ny portée no mamaritra",
                    "note": "9 isaky ny m² avokoa · ny plan no manapaka"},
        "texte": """📏 Hourdis 12, 15 sa 20 : inona no mamaritra ny safidy ?

Tsy ny vidiny, fa ny PORTÉE — ny elanelana eo amin'ny tohana roa — sy ny entana hozakainy.

🔹 12 cm — 2 800 Ar
Portée kely, hatramin'ny 3 m eo ho eo : gorodona maivana, combles.

🔹 15 cm — 3 000 Ar
Ny mahazatra amin'ny trano fonenana, portée 3 à 4 m.

🔹 20 cm — 3 400 Ar
Portée lava, terrasse azo andehanana, entana mavesatra.

⚠️ Tondro ireo, fa tsy didy : ny ingénieur na ny maçon, miaraka amin'ny plan ny dalle, no mamaritra ny haavo farany.

📐 Mitovy ny isa na inona na inona ny haavo : 9 isaky ny m².""",
    },
    {
        "date": "2026-10-30", "slug": "tahiry-3-5-isan-jato", "cible": "produits",
        "theme": "quantites",
        "affiche": {"gabarit": "carte", "badge": "TAHIRY", "titre": "Ampio 3 à 5 %",
                    "sous_titre": "Ho an'ny vaky sy ny fanapahana",
                    "lignes": ["50 m² → 450 pièces", "+ 5 % = 23 pièces fanampiny",
                               "Dia 473 ny commande"]},
        "photo_voulue": "hourdis crus sur étagères (bande)",
        "texte": """➕ Nahoana no ampiana 3 à 5 % ny commande ?

Satria misy very hatrany, eny an-dalana sy eny an-chantier :
🔸 vaky kely amin'ny fampidinana sy ny fitaterana
🔸 fanapahana eo amin'ny sisiny mba hifanaraka amin'ny refy
🔸 pièce roa na telo tsy mifanaraka amin'ny toerany

Ohatra, gorodona 50 m² :
50 m² → 450 pièces
+ 5 % = 23 pièces fanampiny, dia 473 ny commande.

⏳ Mora lavitra ny mampiditra azy ireo amin'ny commande voalohany, noho ny miandry 30 andro indray ho an'ny pièce roapolo.""",
    },
    {
        "date": "2026-10-31", "slug": "kilaometatra-1500", "cible": "livraison",
        "theme": "livraison",
        "affiche": {"gabarit": "question", "badge": "NANONTANY IANAREO",
                    "question": "Ohatrinona ny fanaterana hatrany amin'ny chantier ?",
                    "lignes": ["1 500 Ar isaky ny km", "12 km : 18 000 Ar", "25 km : 37 500 Ar"]},
        "texte": """💬 « Ohatrinona ny fanaterana hatrany amin'ny chantier ? »

Tsotra ny kajy : 1 500 Ar isaky ny kilaometatra, manomboka eto Ambohimanga Rova.

🚚 Chantier 12 km : 12 × 1 500 Ar = 18 000 Ar
🚚 Chantier 25 km : 25 × 1 500 Ar = 37 500 Ar

Voasoratra mazava ao amin'ny devis ny saran'ny fanaterana, alohan'ny fanekenao. Tsy misy mitsiry any aoriana.

🚙 Manana fiara ve ianao ? Afaka maka mivantana eto Ambohimanga Rova, ka tsy mandoa saran-dalana mihitsy.""",
    },
    {
        "date": "2026-11-01", "slug": "novambra-manafatra", "cible": "livraison",
        "theme": "commande",
        "calendrier": {"commande": "2026-11-01", "chantier": ["2026-12-04", "2026-12-08"]},
        "affiche": {"gabarit": "etapes", "badge": "NOVAMBRA", "titre": "Manafatra ny 01/11 ?",
                    "sous_titre": "Ny kalandrie mitohy",
                    "etapes": [("Commande", "alahady 01/11"),
                               ("Famokarana", "eo amin'ny 30 andro"),
                               ("Fanaterana", "3 à 7 andro")],
                    "arrivee_libelle": "EO AMIN'NY CHANTIER", "arrivee": "04 – 08/12"},
        "texte": """🗓️ Volana novambra. Izay manafatra anio, 01/11, dia mahazo ny entany eo amin'ny 04/12 ka hatramin'ny 08/12.

Io kalandrie io no ampiasain'ny mpanorina zatra :

🧱 Tsy ny gorodona no miandry ny biriky — ny biriky no miandry ny gorodona.
🌧️ Ho avy ny orana be : aleo ny entana efa eo an-toerana sy voasarona, toy izay mbola an-dalana.
📞 Antso iray ihany no ilaina : ny surface, ny haavon'ny hourdis araka ny plan, ary ny toerana.

Hanomboka asa amin'ny Desambra ve ianao ? Amin'ity herinandro ity no fotoana hanafarana.""",
    },
    {
        "date": "2026-11-02", "slug": "rindrina-45m2-biriky-15", "cible": "produits",
        "theme": "prix",
        "affiche": {"gabarit": "carte", "badge": "BUDGET", "titre": "Rindrina 45 m²",
                    "sous_titre": "Brique creuse 15×20×40 cm",
                    "lignes": ["45 m² → 540 briques", "540 × 3 000 Ar = 1 620 000 Ar"],
                    "note": "12 isaky ny m² · tsy tafiditra ny simenitra sy ny fanaterana"},
        "photo_voulue": "briques creuses crues sur étagères (bande)",
        "texte": """🧱 « Rindrina 45 m² : ohatrinona ny biriky ? »

Andao hokajiana miaraka. Brique creuse 15×20×40 cm, izay ampiasaina matetika amin'ny rindrina anatiny :

📐 12 briques isaky ny m² de mur
45 m² → 540 briques
540 × 3 000 Ar = 1 620 000 Ar

Ampio 3 à 5 % ho an'ny vaky : eo amin'ny 567 ny commande.

⚠️ Vidin'ny biriky ihany io. Tsy tafiditra ny simenitra, ny fasika, ny mpiasa ary ny fanaterana. Ny devis an-tsoratra no manan-kery.""",
    },
    # ================================================================= semaine 3 (03 → 09/11)
    {
        "date": "2026-11-03", "slug": "maka-mivantana-fiara", "cible": "livraison",
        "theme": "adresse",
        "affiche": {"gabarit": "question", "badge": "NANONTANY IANAREO",
                    "question": "Afaka maka amin'ny fiarako ve aho ?",
                    "lignes": ["Eny : Ambohimanga Rova", "Antsoy mialoha ny hiaingana",
                               "Omanina ny entana mialoha"]},
        "texte": """💬 « Afaka maka amin'ny fiarako ve aho ? »

Eny tokoa, ary betsaka no manao izany :

🚙 Eto amin'ny toeram-pamokarana Ambohimanga Rova no maka.
📞 Antsoy izahay alohan'ny hiaingana : omenay anao ny lalana sy ny ora mety, ary omanina ny entana mba tsy hiandry ianao.
⚖️ Hamarino ny lanjan'ny entana azon'ny fiaranao zakaina : mavesatra ny tanimanga. Aleo mamerina indroa, toy izay manara-dia fiara feno loatra.
💰 Tsy mandoa saran-dalana ianao raha maka mivantana.

Tsy manana fiara ve ianao ? Izahay no manatitra : 1 500 Ar isaky ny km.""",
    },
    {
        "date": "2026-11-04", "slug": "dalle-de-compression", "cible": "faq",
        "theme": "pose",
        "affiche": {"gabarit": "carte", "badge": "FAMETRAHANA", "titre": "Dalle de compression",
                    "sous_titre": "4 à 5 cm no hateviny",
                    "lignes": ["1 · Treillis soudé velarina", "2 · Béton 4 à 5 cm arotsaka",
                               "3 · Tohana mijanona 21–28 andro"],
                    "note": "Izy no mampiray ny rafitra ho tokana"},
        "texte": """🏗️ Rehefa voapetraka ny hourdis rehetra, mbola tsy vita ny gorodona.

Misy dingana roa farany, ary izy ireo no manome ny tanjaka :

1️⃣ TREILLIS SOUDÉ — velarina manerana ny gorodona manontolo, mifanindry araka ny plan.
2️⃣ DALLE DE COMPRESSION — béton 4 à 5 cm arotsaka eo amboniny.

Izy io no mampiray ny poutrelle, ny hourdis ary ny rindrina ho rafitra tokana. Raha tsy ampy ny hateviny, mihena ny tanjaka.

⚠️ Mijanona eo ny tohana mandra-pahamafiny tanteraka : 21 ka hatramin'ny 28 andro. Ny ingénieur-nao no manome ny refy marina araka ny plan-nao.""",
    },
    {
        "date": "2026-11-05", "slug": "hourdis-15-trano-fonenana", "cible": "produits",
        "theme": "hauteur",
        "affiche": {"gabarit": "carte", "badge": "HOURDIS 15", "titre": "Hourdis 15×33×33 cm",
                    "sous_titre": "Ny mahazatra amin'ny trano", "prix": "3 000 Ar",
                    "lignes": ["Portée 3 à 4 m", "9 isaky ny m²"]},
        "photo_voulue": "hourdis crus sur étagères à montants bleus (bande)",
        "texte": """🧱 Hourdis 15×33×33 cm — 3 000 Ar ny iray

Io no haavo ampiasaina indrindra amin'ny trano fonenana eto Antananarivo, ary misy antony :

📐 Mifanaraka amin'ny portée 3 à 4 m — izay ny refin'ny efitrano matetika
⚖️ Mifandanja : maivana ampy, matanjaka ampy
💰 Antonony eo anelanelan'ny 12 sy ny 20

Ohatra ho an'ny gorodona 36 m² :
36 m² → 324 pièces
324 × 3 000 Ar = 972 000 Ar

Na izany aza, ny plan-nao sy ny ingénieur-nao ihany no manapaka. Rehefa misalasala ianao, alefaso aminay ny refin'ny efitrano : manampy anao izahay.""",
    },
    {
        "date": "2026-11-06", "slug": "orana-sy-ny-entana", "cible": "livraison",
        "theme": "commande",
        "affiche": {"gabarit": "photo", "badge": "FAHAVARATRA", "titre": "Tonga ny orana",
                    "sous_titre": "Ny fotoana sy ny fitehirizana"},
        "photo_voulue": "briques creuses crues dressées sous le hangar (à l'abri)",
        "texte": """🌧️ Niditra ny fahavaratra. Zavatra roa tokony hoeritreretinao.

1️⃣ NY FOTOANA — eo amin'ny 30 andro ny famokarana. Izay manafatra amin'ity volana ity dia mahazo ny entany amin'ny Desambra, fa tsy any anatin'ny orana be.

2️⃣ NY FITEHIRIZANA — rehefa tonga eny an-chantier ny biriky :
🔸 aza apetraka mivantana amin'ny tany mando : asio cale hazo na palette
🔸 saronana bâche, saingy avelao hisy rivotra mandalo
🔸 atao akaiky ny toerana hampiasana azy, mba tsy hamerimberina mitondra

🧱 Ny tanimanga voadoro dia tsy matahotra orana rehefa voapetraka. Ny mando tsy tapaka ambany kosa no manimba ny sisiny.""",
    },
    {
        "date": "2026-11-07", "slug": "sary-tena-izy-atelier", "cible": "production",
        "theme": "photos",
        "affiche": {"gabarit": "collage", "badge": "SARY TENA IZY", "titre": "Ny atelier-nay",
                    "photos": ["p36", "p07", "p34", "p01"]},
        "texte": """📸 Nangataka sary tena izy ianareo. Ireto, tsy nindramina na avy aiza na avy aiza : eto Ambohimanga Rova avokoa.

1️⃣ NY MILINA — mandalo ao ny tanimanga, dia mivoaka miaraka amin'ny lavaka ao anatiny
2️⃣ NY FANAMAINANA — andro maro eo ambonin'ny etalage hazo, tsy azo hafainganina
3️⃣ NY LAFAORO — dorana mandra-pahamafiny ; eo no mivadika mena ny tanimanga
4️⃣ NY VOKATRA — hourdis vita, vonona ho entina eny amin'ny chantier

⏳ Izay no 30 andro resahinay foana. Tsy fiandrasana foana izany : asa.

Inona no tianao hojerena manaraka ? Soraty eo amin'ny commentaire.""",
    },
    {
        "date": "2026-11-08", "slug": "lalana-fidiran-ny-kamiao", "cible": "livraison",
        "theme": "adresse",
        "affiche": {"gabarit": "carte", "badge": "FANATERANA", "titre": "Ny lalana mankeny",
                    "sous_titre": "Efatra jerena mialoha",
                    "lignes": ["1 · Sakan'ny lalana", "2 · Fidirana ao an-tokotany",
                               "3 · Toerana hametrahana", "4 · Olona hampidina"]},
        "texte": """🚚 Alohan'ny handefasanay kamiao, misy zavatra efatra jerenay miaraka aminao :

1️⃣ NY LALANA — saka ampy ve ho an'ny kamiao ? Misy tetezana na fiakarana mideza ve ?
2️⃣ NY FIDIRANA — afaka miditra ao an-tokotany ve ny fiara, sa mijanona eny an-dalana ?
3️⃣ NY TOERANA — aiza no hametrahana ny entana, tsy lavitra ny toerana hampiasana azy ?
4️⃣ NY OLONA — misy mpiasa ve hampidina amin'ny andro hanaterana ?

Fanontaniana tsotra ireo, nefa izy ireo no manavaka ny fanaterana mandeha tsara amin'ny andro very.

📞 Antsoy izahay rehefa misy ahiahy : miresaka mivantana aminao ny mpiandraikitra ny fanaterana.""",
    },
    {
        "date": "2026-11-09", "slug": "vidiny-rehetra-iray-pejy", "cible": "produits",
        "theme": "prix",
        "affiche": {"gabarit": "tarifs", "badge": "VIDINY", "titre": "Ny vidiny rehetra",
                    "sous_titre": "isaky ny pièce · tsy tafiditra ny fanaterana · novambra 2026"},
        "texte": """📋 Ny vidiny rehetra amin'ny pejy iray — novambra 2026

HOURDIS — 9 isaky ny m² de plancher
• 20×33×33 — 3 400 Ar
• 15×33×33 — 3 000 Ar
• 12×33×33 — 2 800 Ar

BRIQUE CREUSE — 12 isaky ny m² de mur
• 20×20×40 — 3 500 Ar
• 15×20×40 — 3 000 Ar
• 10×20×40 — 2 500 Ar

TUILE
• Mécanique — 2 200 Ar (15 isaky ny m²)
• Écaille — 500 Ar (75 isaky ny m²)

HAFA
• Brique repressée — 2 200 Ar · Briquette — 500 Ar
• Plaquette — 500 Ar · Plaquette chinois — 700 Ar
• Tonette — 1 800 Ar

Vidiny isaky ny pièce, tsy tafiditra ny fanaterana. Ho an'ny commande lehibe, miresaha aminay.""",
    },
    # ================================================================= semaine 4 (10 → 18/11)
    {
        "date": "2026-11-10", "slug": "gorodona-tsy-mitovy-endrika", "cible": "produits",
        "theme": "quantites",
        "affiche": {"gabarit": "question", "badge": "NANONTANY IANAREO",
                    "question": "Tsy efa-joro ny gorodonay : ahoana no manisa ?",
                    "lignes": ["Zarao ho efa-joro roa na telo", "Kajio tsirairay, dia ampiana",
                               "Ny totaliny × 9"]},
        "texte": """💬 « Tsy efa-joro ny gorodonay : ahoana no manisa ? »

Tsy sarotra : zarao ho efa-joro kely ny surface, dia ampiana.

Ohatra, gorodona endrika L :
▪️ Faritra voalohany : 6 × 4 = 24 m²
▪️ Faritra faharoa : 3 × 2 = 6 m²
▪️ Totaliny : 24 + 6 = 30 m²

Dia ampiharina ny kajy mahazatra :
30 m² → 270 hourdis, ampio 3 à 5 % ho an'ny vaky.

📐 Raha misy trémie escalier na lavaka ascenseur, esory ny velarany amin'ny totaliny.

Alefaso aminay ao amin'ny hafatra ny refy : izahay no manao ny kajy.""",
    },
    {
        "date": "2026-11-11", "slug": "nahoana-30-andro", "cible": "production",
        "theme": "commande",
        "affiche": {"gabarit": "photo", "badge": "FAMOKARANA", "titre": "Nahoana no 30 andro ?",
                    "sous_titre": "Tsy azo hafainganina ny tanimanga"},
        "photo_voulue": "hourdis secs beige, pas encore cuits",
        "texte": """⏳ « Nahoana no 30 andro ? Tsy azo hafainganina ve ? »

Tsia — ary tsara raha fantatrao ny antony :

1️⃣ FAMOLAVOLANA — mandalo milina ny tanimanga, dia azony ny endriny sy ny lavaka ao anatiny.
2️⃣ FANAMAINANA — andro maro, moramora, amin'ny aloka. Raha hafainganina, mitriatra ny biriky rehefa dorana.
3️⃣ FANDORANA — ao anaty lafaoro. Misy ny fampiakarana sy ny fampidinana ny hafanana : tsy azo atao haingana.
4️⃣ FAMPANGATSIAHANA — alohan'ny hametrahana azy eo amin'ny toeram-pitahirizana.

🧱 Ireo andro ireo no antoka tsy hitriaran'ny tanimanga ao anaty rindrinao mandritra ny taona maro.

Ny sary : hourdis efa maina, mbola tsy voadoro.""",
    },
    {
        "date": "2026-11-12", "slug": "tariby-alohan-ny-coulage", "cible": "faq",
        "theme": "pose",
        "affiche": {"gabarit": "carte", "badge": "FAMETRAHANA", "titre": "Tariby sy fantsona",
                    "sous_titre": "Mandalo ao anaty lavaka",
                    "lignes": ["Tsy mila mandavaka béton", "Soraty amin'ny plan ny lalany",
                               "Alohan'ny dalle de compression"]},
        "photo_voulue": "hourdis crus, alvéoles face à l'objectif (bande)",
        "texte": """⚡ Tsy fantatry ny maro : azon'ny tariby sy ny fantsona aleha ny lavaka ao anatin'ny hourdis.

Izany hoe :
✅ Tsy mila mandavaka ny béton ianao aorian'ny coulage — izay no mandrava ny gorodona vaovao
✅ Milamina ny valindrihana : tsy misy tariby mivoaka
✅ Mora kokoa ny fanamboarana any aoriana : azo tarihina indray ny tariby ao anatiny

⚠️ Fepetra iray : soraty amin'ny plan ny lalan'ny tariby sy ny fantsona ALOHAN'ny handrotsahana ny dalle de compression. Rehefa vita ny béton, lasa sarotra ny manova.

💡 Resaho amin'ny électricien sy ny plombier-nao izany alohan'ny hametrahana ny hourdis.""",
    },
    {
        "date": "2026-11-13", "slug": "fifandraisana-telo", "cible": "devis",
        "theme": "adresse",
        "affiche": {"gabarit": "carte", "badge": "FIFANDRAISANA", "titre": "Telo ny lalana",
                    "sous_titre": "ary maimaim-poana avokoa",
                    "lignes": ["032 47 041 43", "033 71 063 34", "Hafatra eto amin'ny page",
                               "Formulaire ao amin'ny tranonkala"],
                    "note": "Alatsinainy → asabotsy"},
        "texte": """📞 Telo ny fomba hahazoana devis, ary maimaim-poana avokoa :

1️⃣ ANTSO — 032 47 041 43 na 033 71 063 34. Alatsinainy hatramin'ny asabotsy no mamaly izahay.
2️⃣ HAFATRA — eto amin'ity page ity. Soraty ny surface, ny karazana entana ary ny toerana misy ny chantier.
3️⃣ FORMULAIRE — ao amin'ny tranonkala : anarana, laharana finday, toerana. Izahay no miantso anao.

Na iza na iza no safidinao, valianay miaraka amin'ny vidiny, ny saran'ny fanaterana ary ny daty.

💡 Raha ampitainao avy hatrany ny surface sy ny daty tianao, dia azo vita anatin'ny antso iray ny devis.""",
    },
    {
        "date": "2026-11-14", "slug": "devis-an-tsoratra", "cible": "devis",
        "theme": "prix",
        "affiche": {"gabarit": "carte", "badge": "DEVIS", "titre": "An-tsoratra no manan-kery",
                    "sous_titre": "Vidiny · fanaterana · daty",
                    "lignes": ["Vidiny isaky ny pièce sy isa", "Saran'ny fanaterana",
                               "Daty fanaterana nifanarahana", "Fepetra fandoavam-bola"]},
        "texte": """📝 Misy fomba fiasa tsotra miaro anao : ny devis an-tsoratra.

Ny vidiny lazaina an-telefaonina dia tombana. Ny devis kosa milaza :
🔸 ny vidiny isaky ny pièce sy ny isa nangatahinao
🔸 ny saran'ny fanaterana araka ny halavirana
🔸 ny daty fanaterana nifanarahana
🔸 ny fepetra fandoavam-bola

💳 Vola madio na mobile money (Orange Money, MVola, Airtel Money) no raisinay. Ny devis no milaza ny acompte sy ny ambiny.

📂 Tazomy ny devis mandra-pahatongan'ny entana. Raha misy tsy mifanaraka, io no jerenay voalohany.""",
    },
    {
        "date": "2026-11-15", "slug": "hourdis-12-sa-20", "cible": "faq",
        "theme": "hauteur",
        "affiche": {"gabarit": "question", "badge": "NANONTANY IANAREO",
                    "question": "12 sa 20 no tokony halaiko ?",
                    "lignes": ["12 : portée kely, combles", "20 : portée lava, terrasse",
                               "15 : ny trano fonenana mahazatra"]},
        "texte": """💬 « 12 sa 20 no tokony halaiko ? »

Tsy mitovy ny asany, ka tsy ny vidiny no misafidy :

🔹 HOURDIS 12 — 2 800 Ar
Portée kely, hatramin'ny 3 m eo ho eo. Gorodona maivana, combles, rihana tsy hitondra entana mavesatra.

🔹 HOURDIS 20 — 3 400 Ar
Portée lava, terrasse azo andehanana, gorodona hitondra entana mavesatra.

Eo anelanelan'izany ny 15, izay ampiasaina matetika amin'ny trano fonenana.

⚠️ Ny haavon'ny hourdis dia manaraka ny haavon'ny poutrelle. Ny plan ny dalle sy ny ingénieur no mamaritra azy, fa tsy ny budget. Raha tsy misy plan, antsoy aloha ny maçon-nao.""",
    },
    {
        "date": "2026-11-16", "slug": "manafatra-miaraka", "cible": "devis",
        "theme": "commande",
        "affiche": {"gabarit": "question", "badge": "NANONTANY IANAREO",
                    "question": "Kely ny commande-ko : lafo ve ny fanaterana ?",
                    "lignes": ["Manafara miaraka amin'ny mpifanolo", "Iray ny dia, mizara ny sarany",
                               "Devis tokana, daty tokana"]},
        "texte": """💬 « Kely ny commande-ko : lafo ve ny fanaterana ? »

Misy fomba efa nataon'ny mpanjifa maro : manafatra miaraka amin'ny mpifanolo-bodirindrina.

🚚 Ny sarany dia 1 500 Ar isaky ny km : ny lalana no isaina, fa tsy ny isan'ny olona. Raha telo no manafatra miaraka ao an-tanàna iray :
🔸 iray ihany ny dia
🔸 mizara telo ny sarany
🔸 mitovy ny daty fanaterana

📋 Lazao fotsiny anay ny anaran'izay miara-manafatra sy ny toerana : ataonay devis tokana, dia zarainareo.

Manana mpifanolo manorina ihany koa ve ianao ? Zarao aminy ity hafatra ity.""",
    },
    {
        "date": "2026-11-17", "slug": "telo-fito-andro", "cible": "livraison",
        "theme": "livraison",
        "affiche": {"gabarit": "carte", "badge": "FANATERANA", "titre": "3 à 7 andro",
                    "sous_titre": "aorian'ny famokarana",
                    "lignes": ["Halavirana", "Toetry ny lalana", "Ny orana amin'ny fahavaratra"],
                    "note": "Antsoinay ianao alohan'ny hiaingan'ny kamiao"},
        "photo_voulue": "pile de briques cuites dans la cour, four au fond (bande)",
        "texte": """🚚 Rehefa vita ny famokarana, 3 à 7 andro no fanaterana.

Inona no mampiova io elanelana io ?
🔸 ny halavirana manomboka eto Ambohimanga Rova
🔸 ny toetry ny lalana mankeny amin'ny chantier
🔸 ny andro : amin'ny fahavaratra, misy lalana tsy azo aleha rehefa avy ny orana be

Izay no antony ilazanay 3 à 7, fa tsy daty tokana noforonina. Aleonay milaza marina, toy izay mampanantena tsy tanteraka.

📞 Antsoinay ianao alohan'ny hiaingan'ny kamiao, mba hisy olona handray eny an-toerana.""",
    },
    {
        "date": "2026-11-18", "slug": "misaotra-novambra", "cible": "accueil",
        "theme": "commande",
        "calendrier": {"commande": "2026-11-18", "chantier": ["2026-12-21", "2026-12-25"]},
        "affiche": {"gabarit": "photo", "badge": "MISAOTRA", "titre": "Misaotra anareo",
                    "sous_titre": "Vita tanimanga malagasy · Ambohimanga Rova"},
        "photo_voulue": "centaines de briques creuses crues en plein soleil",
        "texte": """🙏 Misaotra anareo nanaraka anay nandritra ity volana ity.

Nanontany ianareo ; niezaka namaly tamin'ny isa sy ny daty izahay : ny vidiny, ny fomba fikajiana, ny haavo, ny fanaterana, ary indrindra ny fotoana.

📅 Mitohy io kalandrie io : izay manafatra anio, 18/11, dia mahazo ny entany eo amin'ny 21/12 ka hatramin'ny 25/12 — alohan'ny Noely.

🧱 Hourdis, brique creuse, tuile : vita tanimanga malagasy, eto Ambohimanga Rova.

Manana tetikasa ho an'ny taona vaovao ve ianao ? Alefaso ny refy sy ny daty tianao, dia omanintsika miaraka ny kalandrie.""",
    },
]
