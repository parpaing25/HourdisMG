# -*- coding: utf-8 -*-
"""Deuxième série : 30 publications photo à 14:00 (19/09 → 18/10/2026), en plus des reels de 18:00.

Demande d'Andry (18/09/2026) : « fais des publications encore pour 30 jours, à chaque 14 h,
regarde les publications nécessaires et attirantes ».

« Nécessaires » : bâties sur ce que les clients demandent VRAIMENT. Relevé du 18/09 sur 948
messages privés et 21 commentaires de la page (thèmes comptés par script, aucun nom retenu) :
disponible/stock 186 · prix 110 · adresse 108 · plancher/dalle 79 · quantités 76 · hauteur
12/15/20 64 · livraison 41 · photos réelles 26 · pose (« atoroy fametrahana hourdis »).
Les questions sont REFORMULÉES, jamais citées avec un nom.
« Attirantes » : budgets chiffrés sur des cas réels (10 m × 8 m, mur de 40 m × 2,5 m), vraies
photos de l'atelier, pose pas à pas, quiz, vocabulaire du chantier.

Mêmes sources que la série de 18:00 : site/data/produits.json et site/faq.html, rien d'autre.
Aucun sujet ne double le reel de 18:00 du même jour.
"""
from serie import CIBLES  # noqa: F401  (mêmes cibles sur le site)

HEURE = "14:00"
CAMPAGNE = "serie14h"
PREFIXE = "k"
SORTIE_NOM = "sortie-14h"
AFFECTATION = "affectation14.json"
NOM = "-14h"
DEBUT = "2026-09-19"

SERIE = [
    {
        "date": "2026-09-19", "slug": "misy-foana-ve", "cible": "devis",
        "affiche": {"gabarit": "question", "badge": "NANONTANY IANAREO",
                    "question": "Misy foana ve ny hourdis, sa manao commande vao misy ?",
                    "lignes": ["Amin'ny commande no anaovanay azy", "Famokarana : ≈ 30 andro",
                               "Lot malalaka ? Antsoinay ianao"]},
        "texte": """❓ « Misy foana ve ny hourdis, sa manao commande vao misy ? »

Io no fanontaniana apetrakareo matetika indrindra amin'ny hafatra. Ny valiny marina :

✅ Amin'ny commande no anaovanay ny hourdis sy ny brique : eo amin'ny 30 andro eo ho eo ny famokarana.
✅ Ny lot vita dia efa voatokana matetika ho an'izay nanao commande talohanao.
✅ Raha misy lot malalaka alohan'ny fotoana, antsoinay avy hatrany ianao.

💡 Noho izany, manaova commande araka izay azo atao aloha, mba ho tafiditra amin'ny filaharana ianao.""",
    },
    {
        "date": "2026-09-20", "slug": "budget-plancher-10x8", "cible": "produits",
        "affiche": {"gabarit": "carte", "badge": "BUDGET", "titre": "Plancher 10 m × 8 m",
                    "sous_titre": "80 m² → 720 hourdis",
                    "lignes": ["Hourdis 12 : 2 016 000 Ar", "Hourdis 15 : 2 160 000 Ar", "Hourdis 20 : 2 448 000 Ar"],
                    "note": "+ 3 à 5 % ho an'ny vaky · tsy tafiditra ny fanaterana"},
        "texte": """💰 « Plancher 10 m × 8 m : ohatrinona ny hourdis ? »

Fanontaniana nalefanareo tato ho ato. Andao hokajiana :

📐 Surface : 10 m × 8 m = 80 m²
🧱 Isan'ny hourdis : 80 m² × 9 = 720 pièces

Arakaraka ny hourdis nosafidian'ny ingénieur na ny chef de chantier :
• Hourdis 12 : 720 × 2 800 Ar = 2 016 000 Ar
• Hourdis 15 : 720 × 3 000 Ar = 2 160 000 Ar
• Hourdis 20 : 720 × 3 400 Ar = 2 448 000 Ar

➕ Ampio 3 à 5 % ho an'ny vaky sy ny fanapahana.
🚚 Tsy tafiditra ao ny fanaterana (1 500 Ar isaky ny km).
Ny devis an-tsoratra no manan-kery.""",
    },
    {
        "date": "2026-09-21", "slug": "valiny-haingana", "cible": "devis",
        "affiche": {"gabarit": "carte", "badge": "TORO-HEVITRA", "titre": "Valiny haingana ?",
                    "sous_titre": "Ireto no alefaso aminay",
                    "lignes": ["1 · Hourdis 12, 15 sa 20 ?", "2 · Surface na isany", "3 · Toerana hanaterana",
                               "4 · Daty ilanao azy"]},
        "texte": """📩 Te hahazo vidiny sy délai haingana ve ianao ?

Rehefa mandefa hafatra aminay ianao, ampidiro avy hatrany ireto :
1️⃣ Ny vokatra : hourdis 12, 15 sa 20 · brique creuse 10, 15 sa 20 · tuile
2️⃣ Ny surface (m²) na ny isany ilainao
3️⃣ Ny toerana hanaterana (tanàna, fokontany)
4️⃣ Ny daty ilanao azy

Amin'izay dia afaka manome anao vidiny, saran'ny fanaterana ary délai marina izahay, tsy mila mifampiresaka imbetsaka. Azonao atao koa ny mameno ny formulaire devis ao amin'ny site.""",
    },
    {
        "date": "2026-09-22", "slug": "sary-tena-izy-hourdis", "cible": "production",
        "affiche": {"gabarit": "collage", "badge": "SARY TENA IZY", "titre": "Ny hourdis-nay",
                    "photos": ["p01", "p10", "p37", "p02"]},
        "texte": """📸 « Misy sary tena izy ve ? »

Eny ! Ireto sary ireto dia nalaina teto amin'ny toeram-pamokaranay eto Ambohimanga Rova, tsy sary avy amin'ny internet :

1️⃣ Hourdis vita fandorana
2️⃣ Hourdis maina, andrasana ho dorana
3️⃣ Ny toerana fanamainana
4️⃣ Hourdis vao voaforona, eo ambonin'ny talantalana

Mila sary fanampiny amin'ny vokatra iray ve ianao ? Andefaso hafatra izahay : alefanay aminao amin'ny Messenger.""",
    },
    {
        "date": "2026-09-23", "slug": "fametrahana-1-poutrelle", "cible": "faq",
        "affiche": {"gabarit": "carte", "badge": "FAMETRAHANA 1/3", "titre": "Ny poutrelle",
                    "sous_titre": "Dingana voalohany",
                    "lignes": ["Eo ambonin'ny rindrina mitondra entana", "Elanelana : 33 cm eo ho eo",
                               "Étais tsara alohan'ny zavatra hafa"]},
        "texte": """🏗️ Fametrahana plancher hourdis — dingana 1/3 : ny poutrelle

Fanontaniana matetika : « Mba atoroy ny fametrahana hourdis. » Andao atomboka :

1️⃣ Apetraka eo ambonin'ny rindrina mitondra entana ny poutrelle.
2️⃣ Ny elanelana (entraxe) eo amin'ny poutrelle roa : 33 cm eo ho eo amin'ny hourdis-nay — araho foana ny plan.
3️⃣ Asiana étais (tohana) tsara ny poutrelle alohan'ny hametrahana na inona na inona.

⚠️ Ny ingénieur na ny chef de chantier no mamaritra ny poutrelle sy ny isan'ny étais.
Dingana 2 : amin'ny 28 septambra.""",
    },
    {
        "date": "2026-09-24", "slug": "afaka-maka-mivantana", "cible": "livraison",
        "affiche": {"gabarit": "question", "badge": "NANONTANY IANAREO",
                    "question": "Afaka tonga maka mivantana eny aminareo ve ?",
                    "lignes": ["Eny, amin'ny camion-nareo", "Ambohimanga Rova", "Miantsoa aloha foana"]},
        "texte": """❓ « Afaka tonga maka mivantana eny amin'ny toerana misy anareo ve ? »

✅ Eny. Afaka tonga maka amin'ny camion-nareo ianareo, eto Ambohimanga Rova (lalana mandalo an'i Sabotsy Namehana).
📞 Miantsoa aloha foana : hamarinina raha efa vonona ny commande-nareo, ary hisy olona handray anareo.
🚚 Raha tsy manana fiara ianao, manatitra izahay any Antananarivo sy ny manodidina (1 500 Ar isaky ny km).""",
    },
    {
        "date": "2026-09-25", "slug": "budget-rindrina-40m", "cible": "produits",
        "affiche": {"gabarit": "carte", "badge": "BUDGET", "titre": "Rindrina 40 m × 2,5 m",
                    "sous_titre": "100 m² → 1 200 briques",
                    "lignes": ["Brique creuse 20 : 4 200 000 Ar", "Brique creuse 15 : 3 600 000 Ar"],
                    "note": "+ 3 à 5 % ho an'ny vaky · tsy tafiditra ny fanaterana"},
        "texte": """💰 « Rindrina 2,5 m ny haavony, 40 m ny halavany : firy ny brique ilaina ? »

📐 Surface : 40 m × 2,5 m = 100 m²
🧱 Brique creuse : 100 m² × 12 = 1 200 pièces

• Brique creuse 20×20×40 : 1 200 × 3 500 Ar = 4 200 000 Ar
• Brique creuse 15×20×40 : 1 200 × 3 000 Ar = 3 600 000 Ar

➖ Raha misy varavarana na varavarankely, esory ny surface-ny.
➕ Ampio 3 à 5 % ho an'ny vaky.
🚚 Tsy tafiditra ao ny fanaterana. Ny devis an-tsoratra no manan-kery.""",
    },
    {
        "date": "2026-09-26", "slug": "voambolana-1", "cible": "faq",
        "affiche": {"gabarit": "carte", "badge": "VOAMBOLANA", "titre": "Plancher hourdis",
                    "sous_titre": "Teny 4 tokony ho fantatra",
                    "lignes": ["Poutrelle", "Hourdis (entrevous)", "Treillis soudé", "Dalle de compression"]},
        "texte": """📖 VOAMBOLANA — teny 4 henonao eo amin'ny chantier

🔩 POUTRELLE : andry lava apetraka eo ambonin'ny rindrina mitondra entana ; izy sy ny dalle no mitondra ny lanjan'ny plancher.
🧱 HOURDIS (entrevous) : apetraka eo anelanelan'ny poutrelle roa, manolo ny coffrage ary manamaivana ny plancher.
🕸️ TREILLIS SOUDÉ : harato vy apetraka eo ambonin'ny hourdis alohan'ny handatsahana béton.
🏗️ DALLE DE COMPRESSION : béton 4 à 5 cm arotsaka eo ambony, mampitambatra ny zava-drehetra.

Fantatrao izao ny tenin'ny maçon-nao 😉""",
    },
    {
        "date": "2026-09-27", "slug": "brique-10-15-20", "cible": "produits",
        "affiche": {"gabarit": "carte", "badge": "BRIQUE CREUSE", "titre": "10, 15 sa 20 ?",
                    "sous_titre": "Iza no ho an'ny rindrina inona ?",
                    "lignes": ["10 cm · cloison · 2 500 Ar", "15 cm · façade · 3 000 Ar",
                               "20 cm · mitondra entana · 3 500 Ar"]},
        "texte": """🧱 Brique creuse 10, 15 sa 20 : iza no ho an'ny rindrina inona ?

12 pièces isaky ny m² daholo, 20 × 40 cm ny tavany. Ny hateviny no tsy mitovy :
• 10 cm — 2 500 Ar : rindrina fisarahana (cloison) ao anatin'ny trano
• 15 cm — 3 000 Ar : rindrina ivelany sy façade
• 20 cm — 3 500 Ar : rindrina mitondra entana, miaraka amin'ny chaînage

Ny ingénieur na ny chef de chantier no mamaritra araka ny plan-nao.""",
    },
    {
        "date": "2026-09-28", "slug": "fametrahana-2-hourdis", "cible": "faq",
        "affiche": {"gabarit": "carte", "badge": "FAMETRAHANA 2/3", "titre": "Ny hourdis",
                    "sous_titre": "Dingana faharoa",
                    "lignes": ["Apetraho amin'ny tanana", "Tsy mila coffrage", "Mandehana amin'ny hazo fisaka"]},
        "texte": """🏗️ Fametrahana plancher hourdis — dingana 2/3 : ny hourdis

1️⃣ Rehefa voapetraka sy voatohana ny poutrelle, ampidirina amin'ny tanana eo anelanelan'ny poutrelle roa ny hourdis.
2️⃣ Tsy mila coffrage hazo : ny hourdis mihitsy no manolo azy.
3️⃣ Aza mandeha mivantana eo ambonin'ny hourdis : mandehana amin'ny hazo fisaka apetraka eo ambonin'ny poutrelle.
4️⃣ Tsarovy : mandalo ao anaty lavaky ny hourdis ny gaine électrique sy ny tuyau — ataovy alohan'ny coulage ny lalana handehanany.

Dingana 3 : amin'ny 3 oktobra.""",
    },
    {
        "date": "2026-09-29", "slug": "vidiny-hourdis-ankehitriny", "cible": "produits",
        "affiche": {"gabarit": "question", "badge": "NANONTANY IANAREO",
                    "question": "Fa tsy 2 800 Ar ve ny hourdis 15 ?",
                    "lignes": ["Hourdis 12 · 2 800 Ar", "Hourdis 15 · 3 000 Ar", "Hourdis 20 · 3 400 Ar"]},
        "texte": """❓ « Fa tsy 2 800 Ar ve ny hourdis 15×33×33 ? »

Nisy vidiny taloha nivezivezy, ka andao hazavaina. Ireto ny vidiny ankehitriny, isaky ny pièce :

🧱 Hourdis 12×33×33 — 2 800 Ar
🧱 Hourdis 15×33×33 — 3 000 Ar
🧱 Hourdis 20×33×33 — 3 400 Ar

Ny vidiny rehetra dia hita ao amin'ny site, ary ny devis an-tsoratra no manan-kery. Ho an'ny commande lehibe, miresaha aminay.""",
    },
    {
        "date": "2026-09-30", "slug": "hourdis-12-15-20-haavony", "cible": "produits",
        "affiche": {"gabarit": "hauteurs", "badge": "HOURDIS", "titre": "12, 15 sa 20 ?",
                    "sous_titre": "Ny haavony ihany no tsy mitovy",
                    "note": "33 × 33 cm daholo · 9 isaky ny m²"},
        "texte": """📏 Inona no dikan'ny « 12×33×33 », « 15×33×33 », « 20×33×33 » ?

Mitovy daholo ny halavany sy ny sakany : 33 × 33 cm. Ny isa voalohany no ny HAAVONY :
• Hourdis 12 : 12 cm ny haavony — portée kely (hatramin'ny 3 m eo ho eo), plancher maivana
• Hourdis 15 : 15 cm — ny mahazatra amin'ny trano fonenana, portée 3 à 4 m
• Hourdis 20 : 20 cm — portée lava, terrasse, entana mavesatra

Ireo dia ordres de grandeur : ny ingénieur na ny chef de chantier no mamaritra araka ny plan-nao.
Na inona na inona haavony : 9 pièces isaky ny m².""",
    },
    {
        "date": "2026-10-01", "slug": "budget-tafo-100m2", "cible": "produits",
        "affiche": {"gabarit": "carte", "badge": "BUDGET", "titre": "Tafo 100 m²",
                    "sous_titre": "Tuile mécanique sa écaille ?",
                    "lignes": ["Mécanique : 3 300 000 Ar", "Écaille : 3 750 000 Ar"],
                    "note": "Refeso ny tafo mihitsy (pente, débord) · + 3 à 5 %"},
        "texte": """💰 Tafo 100 m² : ohatrinona ny tuile ?

🏠 Tuile mécanique (15 isaky ny m²) : 100 × 15 = 1 500 pièces
→ 1 500 × 2 200 Ar = 3 300 000 Ar

🔶 Tuile écaille (75 isaky ny m²) : 100 × 75 = 7 500 pièces
→ 7 500 × 500 Ar = 3 750 000 Ar

⚠️ Ny surface-n'ny tafo dia lehibe kokoa noho ny surface-n'ny trano : ampio ny pente sy ny débord. Refeso eo amin'ny tafo mihitsy, na anontanio ny chef de chantier.
➕ Ampio 3 à 5 % ho an'ny vaky.""",
    },
    {
        "date": "2026-10-02", "slug": "sary-tena-izy-brique-tuile", "cible": "produits",
        "affiche": {"gabarit": "collage", "badge": "SARY TENA IZY", "titre": "Brique sy tuile",
                    "photos": ["p15", "p20", "p23", "p29"]},
        "texte": """📸 Sary tena izy — brique sy tuile

Nalaina teto amin'ny toeram-pamokaranay eto Ambohimanga Rova :
1️⃣ Brique creuse vao voaforona, andrasana ho maina
2️⃣ Brique creuse vita fandorana
3️⃣ Tuile mécanique voalahatra
4️⃣ Tuile sy plaquette décorative

Te hahita akaiky kokoa ve ianao ? Tongava — fa miantsoa aloha — na andefaso hafatra izahay.""",
    },
    {
        "date": "2026-10-03", "slug": "fametrahana-3-dalle", "cible": "faq",
        "affiche": {"gabarit": "carte", "badge": "FAMETRAHANA 3/3", "titre": "Treillis sy dalle",
                    "sous_titre": "Dingana fahatelo",
                    "lignes": ["Treillis soudé eo ambony", "Béton 4 à 5 cm", "Étais : 21 à 28 andro"]},
        "texte": """🏗️ Fametrahana plancher hourdis — dingana 3/3 : ny dalle

1️⃣ Apetraho eo ambonin'ny hourdis sy ny poutrelle ny treillis soudé.
2️⃣ Arotsaho ny dalle de compression : béton 4 à 5 cm, mampitambatra ny zava-drehetra.
3️⃣ Avelao eo ny étais mandra-pahamafin'ny béton : matetika 21 à 28 andro.

✅ Vita ny plancher-nao : maivana kokoa, béton vitsy kokoa, tsy nisy coffrage hazo manontolo.
Mila hourdis ho an'ny plancher-nao ve ianao ? Kajio ny isany ao amin'ny site.""",
    },
    {
        "date": "2026-10-04", "slug": "plaquette-decorative", "cible": "devis",
        "affiche": {"gabarit": "photo", "badge": "PLAQUETTE", "titre": "Plaquette sy briquette",
                    "sous_titre": "Manomboka amin'ny 500 Ar ny iray"},
        "texte": """✨ Plaquette sy briquette : ho an'ny rindrina tsy mila enduit

Te hanana rindrina na façade miavaka ve ianao ? Manao plaquette sy briquette terre cuite koa izahay :
• Plaquette — 500 Ar (72 isaky ny m²)
• Plaquette chinois — 700 Ar (50 isaky ny m²)
• Briquette — 500 Ar (82 isaky ny m²)

Misy modely maromaro : andefaso hafatra izahay, alefanay aminao ny sarin'ireo modely.""",
    },
    {
        "date": "2026-10-05", "slug": "firy-andro-vao-vita", "cible": "livraison",
        "affiche": {"gabarit": "question", "badge": "NANONTANY IANAREO",
                    "question": "Firy andro vao vita ny entana commandina ?",
                    "lignes": ["Famokarana : ≈ 30 andro", "Fanaterana : 3 à 7 andro", "Manafara 5 herinandro mialoha"]},
        "texte": """❓ « Firy andro vao vita ny entana commandina ? »

⏱️ Famokarana : eo amin'ny 30 andro eo ho eo, satria anaovanay vaovao ho anao ny hourdis sy ny brique (fanamainana, fandorana).
🚚 Fanaterana : 3 à 7 andro aorian'ny fanamafisana, arakaraka ny halavirana sy ny toetry ny lalana.
📞 Raha misy lot malalaka alohan'izay, antsoinay ianao.

💡 Manafara 5 herinandro eo ho eo mialoha ny andro hilanao azy.""",
    },
    {
        "date": "2026-10-06", "slug": "budget-cloison-20m2", "cible": "produits",
        "affiche": {"gabarit": "carte", "badge": "BUDGET", "titre": "Cloison 20 m²",
                    "sous_titre": "Brique creuse 10×20×40",
                    "lignes": ["20 m² × 12 = 240 briques", "240 × 2 500 Ar", "= 600 000 Ar"],
                    "note": "+ 3 à 5 % ho an'ny vaky · tsy tafiditra ny fanaterana"},
        "texte": """💰 Rindrina fisarahana (cloison) 20 m² : ohatrinona ?

🧱 Brique creuse 10×20×40, 12 isaky ny m² :
→ 20 m² × 12 = 240 briques
→ 240 × 2 500 Ar = 600 000 Ar

Ohatra : rindrina 7 m ny halavany sy 2,8 m ny haavony → 7 m × 2,8 m = 19,6 m² eo ho eo.
➕ Ampio 3 à 5 % ho an'ny vaky. Tsy tafiditra ny fanaterana.""",
    },
    {
        "date": "2026-10-07", "slug": "aiza-ianao-no-manorina", "cible": "livraison",
        "affiche": {"gabarit": "carte", "badge": "FANONTANIANA", "titre": "Aiza ianao no manorina ?",
                    "sous_titre": "Soraty ao amin'ny commentaire",
                    "lignes": ["Antananarivo ?", "Ambohimanga, Alasora ?", "Imerintsiatosika, Andramasina ?",
                               "Faritra hafa ?"]},
        "texte": """📍 Aiza ianao no manorina na hanorina trano ?

Soraty ao amin'ny commentaire ny faritra misy ny chantier-nao 👇

Manatitra izahay any Antananarivo sy ny manodidina : Ambohimanga, Alasora, Imerintsiatosika, Andramasina. Lavitra kokoa ve ianao ? Soraty ihany : dinihinay tsirairay ny fanaterana.""",
    },
    {
        "date": "2026-10-08", "slug": "fitehirizana-eo-amin-ny-chantier", "cible": "faq",
        "affiche": {"gabarit": "carte", "badge": "TORO-HEVITRA", "titre": "Eo amin'ny chantier",
                    "sous_titre": "Ahoana no hitehirizana ny hourdis ?",
                    "lignes": ["Eo ambonin'ny tohana", "Amin'ny toerana voaaro", "Aza atsipy", "+ 3 à 5 % ho an'ny vaky"]},
        "texte": """🧱 Tonga eo amin'ny chantier ny hourdis : ahoana no hitehirizana azy ?

1️⃣ Aza apetraka mivantana amin'ny tany lena : apetraho eo ambonin'ny tohana (hazo).
2️⃣ Apetraho amin'ny toerana voaaro, lavitry ny lalana fandehanan'ny fiara.
3️⃣ Aza atsipy rehefa ampidinina : apetraho tsikelikely. Ny hourdis tsy tapaka no tsy lany vola.
4️⃣ Ampio 3 à 5 % amin'ny commande ho an'ny vaky tsy azo ihodivirana.

Hourdis voatahiry tsara = plancher tsara.""",
    },
    {
        "date": "2026-10-09", "slug": "nahoana-terre-cuite", "cible": "faq",
        "affiche": {"gabarit": "carte", "badge": "TERRE CUITE", "titre": "Nahoana ny terre cuite ?",
                    "sous_titre": "Tombony 4",
                    "lignes": ["Tsy may", "Miaro amin'ny tabataba", "Miaro amin'ny hafanana", "Tsy miova amin'ny fotoana"]},
        "texte": """🔥 Nahoana no terre cuite no safidianay ?

✅ TSY MAY : efa nandalo afo ao anaty lafaoro izy, ka tsy mirehitra.
✅ MIARO AMIN'NY TABATABA : manalefaka ny feo avy any ivelany sy avy amin'ny rihana ambony.
✅ MIARO AMIN'NY HAFANANA : mangatsiatsiaka kokoa ny ao an-trano.
✅ MAHARITRA : tsy miova endrika amin'ny fotoana.

Vita amin'ny tanimanga malagasy, eto Ambohimanga Rova.""",
    },
    {
        "date": "2026-10-10", "slug": "voambolana-2", "cible": "faq",
        "affiche": {"gabarit": "carte", "badge": "VOAMBOLANA 2", "titre": "Teny 4 hafa",
                    "sous_titre": "amin'ny chantier",
                    "lignes": ["Chaînage", "Étai", "Portée", "Entraxe"]},
        "texte": """📖 VOAMBOLANA 2 — teny 4 hafa amin'ny chantier

⛓️ CHAÎNAGE : béton misy vy manodidina ny rindrina, mampitambatra azy sy mitondra ny plancher.
🪵 ÉTAI : tohana (hazo na vy) mitazona ny poutrelle mandra-pahamafin'ny béton — matetika 21 à 28 andro.
📏 PORTÉE : ny elanelana eo amin'ny tohana roa. Io no mamaritra ny haavon'ny hourdis (12, 15 sa 20).
↔️ ENTRAXE : ny elanelana eo amin'ny afovoan'ny poutrelle roa — 33 cm eo ho eo amin'ny hourdis-nay.""",
    },
    {
        "date": "2026-10-11", "slug": "ao-ambadiky-ny-famokarana", "cible": "production",
        "affiche": {"gabarit": "collage", "badge": "SARY TENA IZY", "titre": "Ny famokarana",
                    "photos": ["p36", "p14", "p19", "p34"]},
        "texte": """📸 Ao ambadiky ny famokarana

Nalaina teto amin'ny toeram-pamokaranay eto Ambohimanga Rova :
1️⃣ Ny milina mamolavola ny tanimanga
2️⃣ Brique creuse an-jatony maina amin'ny masoandro
3️⃣ Brique vao voaforona, andrasana ho maina
4️⃣ Ny lafaoro : ny fandorana, dingana farany

Izany rehetra izany no mahatonga ny famokarana ho eo amin'ny 30 andro : tsy azo hafainganina ny fanamainana sy ny fandorana.""",
    },
    {
        "date": "2026-10-12", "slug": "terre-cuite-sa-beton", "cible": "faq",
        "affiche": {"gabarit": "question", "badge": "NANONTANY IANAREO",
                    "question": "Hourdis terre cuite, béton sa polystyrène ?",
                    "lignes": ["Terre cuite : tsy may, tsy mitabataba", "Béton : matanjaka fa mavesatra",
                               "Polystyrène : maivana fa lafo kokoa"]},
        "texte": """❓ « Hourdis terre cuite, béton sa polystyrène : iza no tsara ? »

🧱 TERRE CUITE (ny anay) : tsy may, miaro tsara amin'ny tabataba sy ny hafanana, tsy miova amin'ny fotoana.
🪨 BÉTON : matanjaka be, fa mavesatra ho entina sy apetraka, ary kely ny fiarovany amin'ny hafanana.
⬜ POLYSTYRÈNE : maivana indrindra sy miaro tsara amin'ny hafanana, fa lafo kokoa ary mora simba rehefa voadona.

Samy manana ny tombony avy : ny ingénieur no manoro izay mety amin'ny tetikasa-nao.""",
    },
    {
        "date": "2026-10-13", "slug": "quiz-tafo-50m2", "cible": "produits",
        "affiche": {"gabarit": "carte", "badge": "QUIZ", "titre": "Tafo 50 m²",
                    "sous_titre": "Firy ny tuile mécanique ?",
                    "lignes": ["A · 500", "B · 750", "C · 1 000"]},
        "texte": """🤔 QUIZ — Tafo 50 m², tuile mécanique : firy ny tuile ilaina ?

🅰️ 500
🅱️ 750
🅲️ 1 000

Soraty ao amin'ny commentaire ny valinao 👇 Ny valiny : rahampitso amin'ny 2 ora tolakandro.

(Fanazavana : 15 tuiles mécaniques isaky ny m².)""",
    },
    {
        "date": "2026-10-14", "slug": "valiny-quiz-tafo", "cible": "produits",
        "affiche": {"gabarit": "carte", "badge": "VALINY", "titre": "B · 750 tuiles",
                    "sous_titre": "50 m² × 15 = 750",
                    "lignes": ["Refeso ny tafo mihitsy", "Ampio ny pente sy ny débord", "+ 3 à 5 % ho an'ny vaky"]},
        "texte": """✅ Valin'ny quiz omaly : 🅱️ 750 tuiles (50 m² × 15 = 750).

Fa tandremo ! Ny surface-n'ny TAFO no raisina, fa tsy ny an'ny trano :
📐 Misy pente ny tafo, ka lehibe kokoa noho ny gorodona ny surface-ny.
📐 Misy débord (ny ampahany mivoaka ivelan'ny rindrina).
➕ Ampio 3 à 5 % ho an'ny vaky sy ny fanapahana.

Anontanio ny chef de chantier-nao ny surface marina, ary kajio ao amin'ny site ny isany sy ny vidiny.""",
    },
    {
        "date": "2026-10-15", "slug": "commande-lehibe", "cible": "devis",
        "affiche": {"gabarit": "carte", "badge": "COMMANDE LEHIBE", "titre": "Commande lehibe ?",
                    "sous_titre": "Miresaha aminay",
                    "lignes": ["Vidiny araka ny isany", "Araka ny vokatra sy ny daty", "Devis maimaim-poana"]},
        "texte": """📦 Commande lehibe ve ? Miresaha aminay.

Ho an'ny commande an-jatony pièces na mihoatra, ny vidiny dia miankina amin'ny :
• habetsahana (isany)
• vokatra (hourdis, brique creuse, tuile)
• daty ilanao azy

Lazao anay ao amin'ny hafatra na ao amin'ny formulaire devis ao amin'ny site ny surface na ny isany : omenay anao devis mazava, maimaim-poana.""",
    },
    {
        "date": "2026-10-16", "slug": "budget-etage-60m2", "cible": "produits",
        "affiche": {"gabarit": "carte", "badge": "BUDGET", "titre": "Étage 60 m²",
                    "sous_titre": "60 m² × 9 = 540 hourdis",
                    "lignes": ["Hourdis 12 : 1 512 000 Ar", "Hourdis 15 : 1 620 000 Ar", "Hourdis 20 : 1 836 000 Ar"],
                    "note": "+ 3 à 5 % ho an'ny vaky · tsy tafiditra ny fanaterana"},
        "texte": """💰 Étage 60 m² : ohatrinona ny hourdis ?

🧱 60 m² × 9 = 540 hourdis

• Hourdis 12 : 540 × 2 800 Ar = 1 512 000 Ar
• Hourdis 15 : 540 × 3 000 Ar = 1 620 000 Ar
• Hourdis 20 : 540 × 3 400 Ar = 1 836 000 Ar

Ny ingénieur na ny chef de chantier no mamaritra ny haavony araka ny portée.
➕ Ampio 3 à 5 % ho an'ny vaky. Tsy tafiditra ny fanaterana. Ny devis an-tsoratra no manan-kery.""",
    },
    {
        "date": "2026-10-17", "slug": "asehoy-ny-chantier-nao", "cible": "accueil",
        "affiche": {"gabarit": "carte", "badge": "CHANTIER-NAREO", "titre": "Asehoy anay !",
                    "sous_titre": "Sary chantier misy ny vokatray",
                    "lignes": ["Plancher hourdis", "Rindrina brique creuse", "Tafo tuile"]},
        "texte": """📷 Nampiasa ny hourdis, brique na tuile-nay ve ianao ?

Asehoy anay ny chantier-nao ! Apetraho ao amin'ny commentaire ny sary : plancher, rindrina, tafo…

Faly izahay mahita ny tranonareo mitsangana 🏡""",
    },
    {
        "date": "2026-10-18", "slug": "zavatra-5-alohan-ny-hanafarana", "cible": "accueil",
        "affiche": {"gabarit": "carte", "badge": "TEHIRIZO", "titre": "Alohan'ny hanafarana",
                    "sous_titre": "Zavatra 5 tokony ho fantatra",
                    "lignes": ["Commande : ≈ 30 andro", "9 hourdis · 12 briques / m²", "+ 3 à 5 % ho an'ny vaky",
                               "Fanaterana : 1 500 Ar / km", "Devis maimaim-poana"]},
        "texte": """📌 Zavatra 5 tokony ho fantatra alohan'ny hanafarana

1️⃣ Amin'ny commande : eo amin'ny 30 andro ny famokarana, 3 à 7 andro ny fanaterana.
2️⃣ 9 hourdis isaky ny m² de plancher, 12 brique creuse isaky ny m² de mur.
3️⃣ Ampio 3 à 5 % ho an'ny vaky sy ny fanapahana.
4️⃣ Fanaterana : 1 500 Ar isaky ny km manomboka eto Ambohimanga Rova.
5️⃣ Devis maimaim-poana : ao amin'ny site, amin'ny hafatra na antso.

Tehirizo ity publication ity 📌, na zarao amin'izay manorina trano.""",
    },
]
