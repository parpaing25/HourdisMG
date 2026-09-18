# -*- coding: utf-8 -*-
"""La série de 30 publications de la page Hourdis Madagascar (19/09 → 18/10/2026).

Une entrée = une publication : texte (corps SANS la fin commune), affiche, photo.
La fin commune (appel à l'action, lien du site, numéros, hashtags) est ajoutée par
fabriquer.py, identique partout. Les faits viennent de deux sources et de nulle part
ailleurs, pour que la page et le site ne se contredisent jamais :
  - site/data/produits.json  (prix à la pièce, pièces par m², livraison, délais)
  - site/faq.html            (choix 12/15/20, pose, erreurs à éviter, gaines)
Règle d'Andry du 06/09/2026 : les hourdis sont SUR COMMANDE (≈ 30 jours), jamais
« en stock » ni « misy hatrany ».
"""

HEURE = "18:00"  # heure de Tana, chaque jour

# ancre du site vers laquelle pointe chaque publication, et le libellé de l'appel
CIBLES = {
    "accueil":   ("", "Jereo ny site"),
    "produits":  ("#produits", "Ny vidiny rehetra sy ny kajy"),
    "devis":     ("#contact", "Devis maimaim-poana"),
    "livraison": ("#livraison", "Fanaterana sy délai"),
    "production": ("#production", "Ny famokaranay"),
    "faq":       ("faq", "Fanontaniana mahazatra"),
}

SERIE = [
    # ------------------------------------------------------------------ semaine 1
    {
        "date": "2026-09-19", "slug": "site-hourdis-an-tserasera", "cible": "accueil",
        "affiche": {"gabarit": "photo", "badge": "VAOVAO", "titre": "hourdis.fonenako.mg",
                    "sous_titre": "Vidiny · Kajy · Devis maimaim-poana"},
        "photo_voulue": "stock ou étalage de hourdis, belle vue d'ensemble",
        "texte": """🧱 Vaovao : manana site ofisialy izahay izao !

hourdis.fonenako.mg — ao no ahitanao ny zava-drehetra momba ny hourdis, ny brique creuse ary ny tuile vita eto Ambohimanga Rova :

✅ Ny vidiny rehetra, isaky ny pièce, tsy misy miafina
✅ Kajy mandeha ho azy : ampidiro ny surface (m²), omeny anao ny isan'ny pièce sy ny budget
✅ Devis maimaim-poana : fenoy ny formulaire, antsoinay ianao
✅ Valin'ny fanontaniana mahazatra : délai, fanaterana, fametrahana

Vita tanimanga malagasy, natao ho an'ny fanorenana maharitra.""",
    },
    {
        "date": "2026-09-20", "slug": "hourdis-20", "cible": "produits",
        "affiche": {"gabarit": "carte", "badge": "HOURDIS 20", "titre": "Hourdis 20×33×33 cm",
                    "sous_titre": "9 isaky ny m² de plancher", "prix": "3 400 Ar",
                    "lignes": ["Portée lava", "Terrasse azo andehanana", "Entana mavesatra"]},
        "photo_voulue": "hourdis 20 vu de face",
        "texte": """🧱 Hourdis 20×33×33 cm — 3 400 Ar ny iray

Ho an'iza ity hourdis ity ?
→ Plancher misy portée lava (elanelana lava eo amin'ny tohana roa)
→ Terrasse azo andehanana
→ Plancher mitondra entana mavesatra

📐 9 pièces isaky ny m². Ohatra : plancher 40 m² → 360 hourdis, ampio 3 à 5 % ho an'ny vaky.

⚠️ Ny haavon'ny hourdis dia manaraka ny poutrelle : ny ingénieur na ny chef de chantier no mamaritra azy araka ny plan-nao.""",
    },
    {
        "date": "2026-09-21", "slug": "avy-amin-ny-tanimanga", "cible": "production",
        "affiche": {"gabarit": "photo", "badge": "ATELIER", "titre": "Avy amin'ny tanimanga",
                    "sous_titre": "Famolavolana, fanamainana, fandorana"},
        "photo_voulue": "fabrication : briques crues, moulage ou argile",
        "texte": """👷 Ahoana no anaovana ny hourdis sy ny biriky eto aminay ?

1️⃣ TANIMANGA — akora voajanahary avy eto an-toerana
2️⃣ FAMOLAVOLANA — omena ny endriny sy ny lavaka ao anatiny
3️⃣ FANAMAINANA — avela ho maina moramora, mba tsy hitriatra
4️⃣ FANDORANA — dorana ao anaty lafaoro mandra-pahamafiny

Tsy azo hafainganina izany rehetra izany : izany no antony anaovanay azy amin'ny commande, eo amin'ny 30 andro eo ho eo.""",
    },
    {
        "date": "2026-09-22", "slug": "kajy-hourdis-9-isaky-ny-m2", "cible": "produits",
        "affiche": {"gabarit": "carte", "badge": "KAJY", "titre": "9 hourdis isaky ny m²",
                    "sous_titre": "Surface × 9 = isan'ny hourdis",
                    "lignes": ["20 m² → 180 pièces", "50 m² → 450 pièces", "100 m² → 900 pièces", "+ 3 à 5 % ho an'ny vaky"]},
        "photo_voulue": "pile de hourdis (petite bande)",
        "texte": """📐 Firy ny hourdis ilainao ? Kajy iray monja.

SURFACE (m²) × 9 = ISAN'NY HOURDIS

• 20 m² → 180 pièces
• 50 m² → 450 pièces
• 100 m² → 900 pièces

Ampio 3 à 5 % ho an'ny vaky sy ny fanapahana amin'ny sisiny.

💡 Tsy te hikajy ve ianao ? Ao amin'ny site, tsindrio « Calculer mes quantités » eo amin'ny hourdis tianao : omeny anao avy hatrany ny isany sy ny vidiny.""",
    },
    {
        "date": "2026-09-23", "slug": "brique-creuse-20", "cible": "produits",
        "affiche": {"gabarit": "carte", "badge": "BRIQUE CREUSE", "titre": "Brique creuse 20×20×40",
                    "sous_titre": "12 isaky ny m² de mur", "prix": "3 500 Ar",
                    "lignes": ["Rindrina mitondra entana", "miaraka amin'ny chaînage"]},
        "photo_voulue": "brique creuse 20",
        "texte": """🧱 Brique creuse 20×20×40 cm — 3 500 Ar ny iray

Ny matevina indrindra amin'ny brique creuse-nay :
→ Rindrina mitondra entana, miaraka amin'ny chaînage
→ Rindrina tianao ho matanjaka sy matevina

📐 12 pièces isaky ny m² de mur. Ohatra : rindrina 30 m² → 360 briques.

Ny lavaka ao anatiny dia manamaivana ny biriky ary miaro amin'ny hafanana sy ny tabataba.""",
    },
    {
        "date": "2026-09-24", "slug": "quiz-plancher-30-m2", "cible": "produits",
        "affiche": {"gabarit": "carte", "badge": "QUIZ", "titre": "Plancher 30 m²",
                    "sous_titre": "Firy ny hourdis ilaina ?",
                    "lignes": ["A · 180", "B · 270", "C · 330"]},
        "photo_voulue": "hourdis rangés (petite bande)",
        "texte": """🤔 QUIZ — Plancher 30 m² : firy ny hourdis ilaina ?

🅰️ 180
🅱️ 270
🅲️ 330

Soraty ao amin'ny commentaire ny valinao 👇
Ny valiny marina : rahampitso eto amin'ity page ity.

(Fanazavana : hourdis 33×33 cm no ampiasainay.)""",
    },
    {
        "date": "2026-09-25", "slug": "commande-30-andro", "cible": "livraison",
        "affiche": {"gabarit": "carte", "badge": "COMMANDE", "titre": "Rahoviana no tonga ?",
                    "sous_titre": "Amin'ny commande no anaovanay azy",
                    "lignes": ["1 · Commande", "2 · Famokarana : ≈ 30 andro", "3 · Fanaterana : 3 à 7 andro"]},
        "photo_voulue": "stock de hourdis prêts",
        "texte": """✅ Valin'ny quiz omaly : 🅱️ 270 hourdis (30 m² × 9). Miaraka amin'ny 3 à 5 % ho an'ny vaky : eo amin'ny 280.

📅 Ary rahoviana no tonga eo amin'ny chantier ?

Amin'ny commande no anaovanay ny hourdis :
1️⃣ Mandefa commande ianao (antso, hafatra na formulaire ao amin'ny site)
2️⃣ Famokarana : eo amin'ny 30 andro eo ho eo
3️⃣ Fanaterana : 3 à 7 andro, arakaraka ny halavirana

💡 Aza miandry ny andro hilana azy vao manafatra. Raha hanao plancher ianao amin'ny volana ho avy, izao no fotoana hanaovana commande.""",
    },
    # ------------------------------------------------------------------ semaine 2
    {
        "date": "2026-09-26", "slug": "tuile-mecanique", "cible": "produits",
        "affiche": {"gabarit": "photo", "badge": "TUILE", "titre": "Tuile mécanique",
                    "sous_titre": "22×33,5 cm · 15 isaky ny m²", "prix": "2 200 Ar"},
        "photo_voulue": "tuile mécanique",
        "texte": """🏠 Tuile mécanique — 2 200 Ar ny iray

→ Tuile terre cuite 22×33,5 cm
→ 15 pièces isaky ny m² de toiture
→ Tsy mafana toy ny tôle rehefa mahamay ny masoandro, ary tsy mitabataba rehefa avy ny orana

📐 Ohatra : tafo 80 m² → 1 200 tuiles.""",
    },
    {
        "date": "2026-09-27", "slug": "hourdis-sa-dalle-pleine", "cible": "faq",
        "affiche": {"gabarit": "carte", "badge": "FAMPITAHANA", "titre": "Hourdis sa dalle pleine ?",
                    "sous_titre": "Ny tena fahasamihafana",
                    "lignes": ["✓ Tsy mila coffrage", "✓ Béton vitsy kokoa", "✓ Maivana kokoa", "✓ Mandalo ao anatiny ny gaine"]},
        "photo_voulue": "hourdis en pile, vue rapprochée",
        "texte": """⚖️ Plancher hourdis sa dalle pleine ?

DALLE PLEINE
❌ Coffrage hazo manontolo eo ambany
❌ Béton be dia be
❌ Mavesatra kokoa ho an'ny rindrina sy ny fondation

PLANCHER HOURDIS
✅ Tsy mila coffrage : apetraka amin'ny tanana eo anelanelan'ny poutrelle roa ny hourdis
✅ Béton vitsy kokoa : dalle de compression 4 à 5 cm ihany no arotsaka eo ambony
✅ Maivana kokoa, ary mandalo ao anaty lavaka ny gaine électrique sy ny tuyau

Ny ingénieur na ny chef de chantier no mamaritra izay mety amin'ny plan-nao.""",
    },
    {
        "date": "2026-09-28", "slug": "fanamainana", "cible": "production",
        "affiche": {"gabarit": "photo", "badge": "ATELIER", "titre": "Fanamainana",
                    "sous_titre": "Ny fotoana no manome ny hamafiny"},
        "photo_voulue": "séchage des hourdis ou briques crues",
        "texte": """☀️ Fanamainana : dingana tsy azo hafainganina

Alohan'ny handorana azy, ny hourdis sy ny biriky vao voaforona dia avela ho maina tsikelikely.
Raha maina haingana loatra izy, dia mety hitriatra. Raha dorana nefa mbola lena, dia mety ho vaky ao anaty lafaoro.

Izany no mahatonga ny famokarana ho eo amin'ny 30 andro : ny fotoana no manome ny hamafiny.""",
    },
    {
        "date": "2026-09-29", "slug": "kajy-ao-amin-ny-site", "cible": "produits",
        "affiche": {"gabarit": "capture", "badge": "SITE", "titre": "Kajio ny budget-nao",
                    "sous_titre": "ao anatin'ny 10 segondra", "capture": "calcul"},
        "photo_voulue": None,
        "texte": """📱 Kajio ny budget-nao ao anatin'ny 10 segondra

Ao amin'ny hourdis.fonenako.mg :
1️⃣ Safidio ny vokatra (hourdis, brique creuse, tuile…)
2️⃣ Tsindrio « Calculer mes quantités »
3️⃣ Ampidiro ny surface (m²)

➡️ Omeny anao avy hatrany ny isan'ny pièce sy ny vidiny rehetra, ary azonao alefa mivantana ho fangatahana devis izany.

Maimaim-poana, tsy mila misoratra anarana.""",
    },
    {
        "date": "2026-09-30", "slug": "brique-creuse-15", "cible": "produits",
        "affiche": {"gabarit": "carte", "badge": "BRIQUE CREUSE", "titre": "Brique creuse 15×20×40",
                    "sous_titre": "12 isaky ny m² de mur", "prix": "3 000 Ar",
                    "lignes": ["Rindrina ivelany sy façade", "Rindrina anatiny matevina"]},
        "photo_voulue": "brique creuse 15",
        "texte": """🧱 Brique creuse 15×20×40 cm — 3 000 Ar ny iray

Ny fampiasa mahazatra azy amin'ny trano fonenana :
→ Rindrina ivelany sy façade
→ Rindrina anatiny tianao ho matevina

📐 12 pièces isaky ny m². Ohatra : rindrina 25 m² → 300 briques.

Terre cuite : tsy may, miaro amin'ny hafanana sy ny tabataba, ary maharitra.""",
    },
    {
        "date": "2026-10-01", "slug": "fanaterana-antananarivo", "cible": "livraison",
        "affiche": {"gabarit": "carte", "badge": "FANATERANA", "titre": "Hatrany amin'ny chantier",
                    "sous_titre": "Antananarivo sy ny manodidina",
                    "lignes": ["1 500 Ar isaky ny km", "manomboka eto Ambohimanga Rova", "3 à 7 andro aorian'ny commande"]},
        "photo_voulue": "chargement, camion ou gros stock",
        "texte": """🚚 Tonga hatrany amin'ny chantier-nao

Manatitra izahay any :
📍 Antananarivo sy ny manodidina : Ambohimanga, Alasora, Imerintsiatosika, Andramasina

💰 1 500 Ar isaky ny kilometatra, manomboka eto amin'ny toeram-pitehirizanay Ambohimanga Rova — voasoratra mazava ao amin'ny devis alohan'ny hanekenao azy.
⏱️ 3 à 7 andro aorian'ny fanamafisana ny commande.
🚛 Afaka tonga maka mivantana amin'ny camion-nao ihany koa ianao.

Lavitra kokoa ve ianao ? Anontanio izahay : dinihinay tsirairay.""",
    },
    {
        "date": "2026-10-02", "slug": "fahadisoana-4-plancher", "cible": "faq",
        "affiche": {"gabarit": "carte", "badge": "TORO-HEVITRA", "titre": "Plancher hourdis",
                    "sous_titre": "4 fahadisoana tokony hialana",
                    "lignes": ["1 · Tsy misy tahiry", "2 · Mandeha eo ambony", "3 · Étais esorina aloha loatra", "4 · Tany lena"]},
        "photo_voulue": "hourdis posés ou pile",
        "texte": """⚠️ Plancher hourdis : fahadisoana 4 tokony hialana

1️⃣ Manafatra tsy misy tahiry → Ampio 3 à 5 % ho an'ny vaky sy ny fanapahana
2️⃣ Mandeha mivantana eo ambonin'ny hourdis alohan'ny coulage → Mandehana amin'ny hazo fisaka apetraka eo ambonin'ny poutrelle
3️⃣ Manala ny étais aloha loatra → Avelao mandra-pahamafin'ny béton, matetika 21 à 28 andro
4️⃣ Mametraka ny hourdis mivantana amin'ny tany lena → Apetraho eo ambonin'ny tohana, amin'ny toerana voaaro""",
    },
    # ------------------------------------------------------------------ semaine 3
    {
        "date": "2026-10-03", "slug": "tuile-ecaille", "cible": "produits",
        "affiche": {"gabarit": "photo", "badge": "TUILE", "titre": "Tuile écaille",
                    "sous_titre": "Ny tafo malagasy nentim-paharazana", "prix": "500 Ar"},
        "photo_voulue": "tuile écaille",
        "texte": """🔶 Tuile écaille — 500 Ar ny iray

Ny tafo malagasy nentim-paharazana : tuile kely boribory tendrony, apetraka mifanindry.

→ 75 pièces isaky ny m² de toiture
→ Terre cuite : tsy mafana, tsy mitabataba rehefa avy ny orana, ary maharitra taona maro

📐 Ohatra : tafo 60 m² → 4 500 tuiles écaille.""",
    },
    {
        "date": "2026-10-04", "slug": "inona-no-manahirana-anao", "cible": "devis",
        "affiche": {"gabarit": "carte", "badge": "FANONTANIANA", "titre": "Inona no manahirana anao ?",
                    "sous_titre": "amin'ny fanorenana trano",
                    "lignes": ["A · Ny vidiny", "B · Ny fotoana", "C · Ny mpanao asa", "D · Ny fitaterana"]},
        "photo_voulue": "chantier ou mur en briques (Madagascar)",
        "texte": """💬 Inona no manahirana anao indrindra amin'ny fanorenana trano ?

🅰️ Ny vidiny
🅱️ Ny fotoana
🅲️ Ny mpanao asa (maçon)
🅳️ Ny fitaterana ny akora

Valio amin'ny litera iray ao amin'ny commentaire 👇
Hovakianay avokoa ny valinareo, ary izany no hanorenanay ny toro-hevitra manaraka.""",
    },
    {
        "date": "2026-10-05", "slug": "hourdis-tsara-kalitao", "cible": "faq",
        "affiche": {"gabarit": "carte", "badge": "TORO-HEVITRA", "titre": "Hourdis tsara kalitao",
                    "sous_titre": "Ahoana no hamantarana azy ?",
                    "lignes": ["1 · Feo madio rehefa dondonina", "2 · Tsy misy triatra", "3 · Loko mitovy", "4 · 33 × 33 cm tsara"]},
        "photo_voulue": "gros plan d'un hourdis cuit",
        "texte": """🔎 Ahoana no hamantarana hourdis tsara kalitao ?

Alohan'ny hividianana, na aiza na aiza :
1️⃣ Dondony moramora : feo madio mikarantsana = voadoro tsara. Feo tsy madio = mety misy triatra ao anatiny.
2️⃣ Jereo ny sisiny : tsy misy triatra, tsy misy sisiny tapaka.
3️⃣ Jereo ny loko : mitovy manontolo. Loko hatsatra loatra = mety tsy ampy fandorana.
4️⃣ Refeso : 33 × 33 cm tsara, mba hifanaraka amin'ny poutrelle.""",
    },
    {
        "date": "2026-10-06", "slug": "hourdis-15", "cible": "produits",
        "affiche": {"gabarit": "carte", "badge": "HOURDIS 15", "titre": "Hourdis 15×33×33 cm",
                    "sous_titre": "9 isaky ny m² de plancher", "prix": "3 000 Ar",
                    "lignes": ["Portée 3 à 4 m eo ho eo", "Plancher étage trano fonenana"]},
        "photo_voulue": "hourdis 15",
        "texte": """🧱 Hourdis 15×33×33 cm — 3 000 Ar ny iray

Ny hourdis mahazatra indrindra amin'ny trano fonenana :
→ Portée 3 à 4 m eo ho eo
→ Plancher étage ho an'ny efitra fatoriana, lasalle, lakozia

📐 9 pièces isaky ny m². Ohatra : étage 60 m² → 540 hourdis, ampio 3 à 5 %.

Ireo dia ordres de grandeur : ny ingénieur na ny chef de chantier no mamaritra ny tena ilaina araka ny plan-nao.""",
    },
    {
        "date": "2026-10-07", "slug": "devis-maimaim-poana", "cible": "devis",
        "affiche": {"gabarit": "capture", "badge": "SITE", "titre": "Devis maimaim-poana",
                    "sous_titre": "tsy mila mivoaka ny trano", "capture": "devis"},
        "photo_voulue": None,
        "texte": """📝 Devis maimaim-poana, tsy mila mivoaka ny trano

Ao amin'ny hourdis.fonenako.mg, fenoy ny formulaire fohy :
• ny anaranao sy ny laharana finday
• ny toerana misy ny chantier
• ny vokatra sy ny surface na ny isany

Antsoinay ianao avy eo : vidiny, fanaterana ary délai, mazava tsara alohan'ny hanapahanao hevitra.""",
    },
    {
        "date": "2026-10-08", "slug": "trano-mangatsiatsiaka", "cible": "faq",
        "affiche": {"gabarit": "photo", "badge": "TORO-HEVITRA", "titre": "Trano mangatsiatsiaka",
                    "sous_titre": "Ny anjaran'ny brique creuse"},
        "photo_voulue": "briques creuses, alvéoles visibles",
        "texte": """🌡️ Manomboka mafana ny andro : ahoana no hahatonga ny trano ho mangatsiatsiaka kokoa ?

Ny rindrina no mandray ny hafanan'ny masoandro mandritra ny andro.
Ny brique creuse terre cuite dia misy rivotra voahidy ao anaty lavaka : mampiadana ny fidiran'ny hafanana izany, ka mangatsiatsiaka kokoa ny ao an-trano.

Ampiarahina amin'ny tafo tuile, dia tsapa ny fahasamihafana amin'ny volana mafana.""",
    },
    {
        "date": "2026-10-09", "slug": "brique-creuse-10", "cible": "produits",
        "affiche": {"gabarit": "carte", "badge": "BRIQUE CREUSE", "titre": "Brique creuse 10×20×40",
                    "sous_titre": "12 isaky ny m² de mur", "prix": "2 500 Ar",
                    "lignes": ["Rindrina fisarahana (cloison)", "Maivana, mora apetraka"]},
        "photo_voulue": "brique creuse 10 ou pile de briques",
        "texte": """🧱 Brique creuse 10×20×40 cm — 2 500 Ar ny iray

Ho an'ny rindrina fisarahana (cloison) ao anatin'ny trano :
→ Maivana, mora apetraka
→ Mahazo toerana kokoa ao amin'ny efitra

📐 12 pièces isaky ny m². Ohatra : cloison 3 m × 2,8 m = 8,4 m² → 101 briques, eo amin'ny 105 miaraka amin'ny tahiry.""",
    },
    # ------------------------------------------------------------------ semaine 4
    {
        "date": "2026-10-10", "slug": "aiza-no-misy-anay", "cible": "accueil",
        "affiche": {"gabarit": "photo", "badge": "AMBOHIMANGA ROVA", "titre": "Aiza no misy anay ?",
                    "sous_titre": "Lalana mandalo an'i Sabotsy Namehana"},
        "photo_voulue": "atelier, hangar ou lieu de production",
        "texte": """📍 Aiza no misy anay ?

Ambohimanga Rova, amin'ny lalana mandalo an'i Sabotsy Namehana.
Eto no anaovanay sy itahirizanay ny hourdis, ny brique creuse ary ny tuile.

Te hijery maso ny vokatra alohan'ny hanaovana commande ve ianao ? Tongava — fa miantsoa aloha, mba hisy olona handray anao.""",
    },
    {
        "date": "2026-10-11", "slug": "marina-sa-diso", "cible": "faq",
        "affiche": {"gabarit": "carte", "badge": "MARINA SA DISO ?", "titre": "« Ny hourdis no mitondra",
                    "sous_titre": "ny lanjan'ny plancher. »",
                    "lignes": ["MARINA", "na", "DISO ?"]},
        "photo_voulue": "hourdis (petite bande)",
        "texte": """🤔 MARINA SA DISO ?

« Ny hourdis no mitondra ny lanjan'ny plancher. »

Inona no hevitrao ? Soraty ao amin'ny commentaire : MARINA na DISO 👇
Ny valiny : rahampitso eto amin'ity page ity.""",
    },
    {
        "date": "2026-10-12", "slug": "fandorana", "cible": "production",
        "affiche": {"gabarit": "photo", "badge": "ATELIER", "titre": "Fandorana",
                    "sous_titre": "Dingana farany, hamafisana sy faharetana"},
        "photo_voulue": "four / cuisson (fandorana)",
        "texte": """✅ Valiny omaly : DISO. Amin'ny ankapobeny, ny poutrelle sy ny dalle de compression (béton misy treillis) no mitondra ny lanjany. Ny hourdis kosa mameno ny elanelana, manolo ny coffrage, ary manamaivana ny plancher.

🔥 Androany : ny fandorana, dingana farany amin'ny famokarana

Aorian'ny fanamainana, dorana ao anaty lafaoro ny hourdis sy ny biriky. Ny fandorana ampy no manome azy :
→ hamafisana
→ loko mitovy
→ faharetana amin'ny orana sy ny fotoana""",
    },
    {
        "date": "2026-10-13", "slug": "biriky-hafa", "cible": "devis",
        "affiche": {"gabarit": "carte", "badge": "VOKATRA HAFA", "titre": "Tsy hourdis ihany",
                    "sous_titre": "Vidiny isaky ny pièce",
                    "lignes": ["Brique repressée · 2 200 Ar", "Tonette · 1 800 Ar", "Plaquette chinois · 700 Ar",
                               "Plaquette · 500 Ar", "Briquette · 500 Ar"]},
        "photo_voulue": "brique pleine, repressée ou plaquette si disponible",
        "texte": """🧱 Tsy hourdis ihany : ireto koa no vitanay

• Brique repressée — 2 200 Ar (42 isaky ny m²)
• Tonette — 1 800 Ar (25 isaky ny m²)
• Plaquette chinois — 700 Ar (50 isaky ny m²)
• Plaquette — 500 Ar (72 isaky ny m²)
• Briquette — 500 Ar (82 isaky ny m²)

Mila sary ve ianao alohan'ny hisafidianana ? Andefaso hafatra izahay : alefanay aminao amin'ny Messenger.""",
    },
    {
        "date": "2026-10-14", "slug": "kajy-brique-creuse-12", "cible": "produits",
        "affiche": {"gabarit": "carte", "badge": "KAJY", "titre": "12 briques isaky ny m²",
                    "sous_titre": "Surface rindrina × 12",
                    "lignes": ["Rindrina 10 m × 2,8 m = 28 m²", "Esory varavarana : − 4 m²", "24 m² × 12 = 288 briques", "+ 3 à 5 % ho an'ny vaky"]},
        "photo_voulue": "mur ou pile de briques creuses",
        "texte": """📐 Firy ny brique creuse ilaina amin'ny rindrina iray ?

SURFACE RINDRINA (m²) × 12 = ISAN'NY BRIQUE

Ohatra : rindrina 10 m ny halavany, 2,8 m ny haavony
→ 28 m²
→ esory ny varavarana sy ny varavarankely (ohatra 4 m²) : 24 m²
→ 24 × 12 = 288 briques, ampio 3 à 5 % ho an'ny vaky

Ao amin'ny site, ny bokotra « Calculer mes quantités » no manao izany ho anao, miaraka amin'ny vidiny.""",
    },
    {
        "date": "2026-10-15", "slug": "alohan-ny-fahavaratra", "cible": "devis",
        "affiche": {"gabarit": "photo", "badge": "COMMANDE", "titre": "Alohan'ny fahavaratra",
                    "sous_titre": "Manafara izao, tonga alohan'ny orana"},
        "photo_voulue": "tuiles ou stock en extérieur",
        "texte": """🌧️ Ho avy tsy ho ela ny fahavaratra : vonona ve ny tafo sy ny plancher-nao ?

Eo amin'ny 30 andro ny famokarana. Raha manafatra izao ianao, dia tonga alohan'ny orana ny hourdis sy ny tuile, ka voaaro ny chantier.

Aza andrasana ny orana voalohany vao mihazakazaka.""",
    },
    {
        "date": "2026-10-16", "slug": "vidiny-rehetra", "cible": "produits",
        "affiche": {"gabarit": "tarifs", "badge": "VIDINY", "titre": "Ny vidiny rehetra",
                    "sous_titre": "isaky ny pièce, tsy tafiditra ny fanaterana"},
        "photo_voulue": None,
        "texte": """📋 Ny vidiny rehetra, amin'ny pejy iray

HOURDIS (9 isaky ny m²)
• 20×33×33 — 3 400 Ar
• 15×33×33 — 3 000 Ar
• 12×33×33 — 2 800 Ar

BRIQUE CREUSE (12 isaky ny m²)
• 20×20×40 — 3 500 Ar
• 15×20×40 — 3 000 Ar
• 10×20×40 — 2 500 Ar

TUILE
• Mécanique — 2 200 Ar (15 isaky ny m²)
• Écaille — 500 Ar (75 isaky ny m²)

Vidiny isaky ny pièce, tsy tafiditra ny fanaterana. Ny devis an-tsoratra no manan-kery. Ho an'ny commande lehibe, miresaha aminay.""",
    },
    {
        "date": "2026-10-17", "slug": "fanontaniana-3-mahazatra", "cible": "faq",
        "affiche": {"gabarit": "carte", "badge": "FANONTANIANA", "titre": "Ireo apetrakareo matetika",
                    "sous_titre": "ary ny valiny",
                    "lignes": ["Misy stock ve ?", "Manatitra ve ianareo ?", "Mandalo ao anatiny ve ny gaine ?"]},
        "photo_voulue": "hourdis 12 ou produit non encore montré",
        "texte": """❓ Fanontaniana 3 apetrakareo matetika

« Misy stock ve ? »
→ Amin'ny commande no anaovanay azy : eo amin'ny 30 andro ny famokarana. Raha misy lot malalaka alohan'izay, antsoinay ianao.

« Manatitra ve ianareo ? »
→ Eny : Antananarivo sy ny manodidina, 1 500 Ar isaky ny km manomboka eto Ambohimanga Rova.

« Mandalo ao anaty hourdis ve ny gaine électrique ? »
→ Eny : mandalo ao anaty lavaka ny gaine sy ny tuyau, tsy mila mandavaka ny béton. Ataovy alohan'ny coulage ny lalana handehanany.""",
    },
    {
        "date": "2026-10-18", "slug": "misaotra-anareo", "cible": "accueil",
        "affiche": {"gabarit": "photo", "badge": "HOURDIS MADAGASCAR", "titre": "Misaotra anareo !",
                    "sous_titre": "Vita tanimanga malagasy, eto Ambohimanga Rova"},
        "photo_voulue": "la plus belle photo restante",
        "texte": """🙏 Misaotra anareo nanaraka anay nandritra ity volana ity !

Hourdis, brique creuse, tuile : vita tanimanga malagasy, eto Ambohimanga Rova.

Manana tetikasa ve ianao — trano vaovao, étage, tafo ? Ao amin'ny hourdis.fonenako.mg ny zava-drehetra : vidiny, kajy, devis maimaim-poana.

Zarao amin'ny namanao manorina trano ity page ity 🤝""",
    },
]
