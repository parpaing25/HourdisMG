# -*- coding: utf-8 -*-
"""Les scènes des reels, écrites à la main : 13 secondes ne laissent place qu'à des
phrases courtes. La scène 1 reprend l'affiche (badge, titre, sous-titre) sauf si
« s1 » la remplace. Clés d'une scène : badge, titre, sous, prix, lignes.
Les montants et les calculs passent par verifier.py comme les textes."""

SCENES = {
    "site-hourdis-an-tserasera": {
        "s2": {"titre": "Ny vidiny rehetra", "sous": "isaky ny pièce, tsy misy miafina"},
        "s3": {"lignes": ["Kajy mandeha ho azy", "Devis maimaim-poana", "Fanontaniana mahazatra"]},
    },
    "hourdis-20": {
        "s2": {"prix": "3 400 Ar", "sous": "9 isaky ny m² de plancher"},
        "s3": {"lignes": ["Portée lava", "Terrasse azo andehanana", "Entana mavesatra"]},
    },
    "avy-amin-ny-tanimanga": {
        "s2": {"lignes": ["1 · Tanimanga", "2 · Famolavolana"]},
        "s3": {"sous": "Amin'ny commande : ≈ 30 andro", "lignes": ["3 · Fanamainana", "4 · Fandorana"]},
    },
    "kajy-hourdis-9-isaky-ny-m2": {
        "s2": {"titre": "Surface × 9", "lignes": ["20 m² → 180 pièces", "50 m² → 450 pièces", "100 m² → 900 pièces"]},
        "s3": {"titre": "+ 3 à 5 %", "sous": "ho an'ny vaky sy ny fanapahana", "lignes": ["Kajio ao amin'ny site"]},
    },
    "brique-creuse-20": {
        "s2": {"prix": "3 500 Ar", "sous": "12 isaky ny m² de mur"},
        "s3": {"lignes": ["Rindrina mitondra entana", "miaraka amin'ny chaînage", "30 m² → 360 pièces"]},
    },
    "quiz-plancher-30-m2": {
        "s2": {"lignes": ["A · 180", "B · 270", "C · 330"]},
        "s3": {"titre": "Inona no valinao ?", "sous": "Soraty ao amin'ny commentaire 👇 Valiny rahampitso"},
    },
    "commande-30-andro": {
        "s1": {"badge": "VALINY", "titre": "B · 270 hourdis", "sous": "30 m² × 9 = 270, ampio 3 à 5 %"},
        "s2": {"titre": "Rahoviana no tonga ?", "lignes": ["1 · Commande", "2 · Famokarana ≈ 30 andro", "3 · Fanaterana 3 à 7 andro"]},
        "s3": {"titre": "Manafara izao", "sous": "raha hanao plancher ianao amin'ny volana ho avy"},
    },
    "tuile-mecanique": {
        "s2": {"prix": "2 200 Ar", "sous": "15 isaky ny m² de toiture"},
        "s3": {"lignes": ["Tsy mafana toy ny tôle", "Tsy mitabataba rehefa avy ny orana", "80 m² → 1 200 tuiles"]},
    },
    "hourdis-sa-dalle-pleine": {
        "s2": {"titre": "Dalle pleine", "lignes": ["✗ Coffrage hazo manontolo", "✗ Béton be dia be", "✗ Mavesatra kokoa"]},
        "s3": {"titre": "Plancher hourdis", "lignes": ["✓ Tsy mila coffrage", "✓ Béton vitsy kokoa", "✓ Maivana kokoa"]},
    },
    "fanamainana": {
        "s2": {"lignes": ["Maina haingana loatra : mitriatra", "Mbola lena : vaky ao anaty lafaoro"]},
        "s3": {"titre": "Ny fotoana", "sous": "no manome ny hamafiny"},
    },
    "kajy-ao-amin-ny-site": {
        "s2": {"titre": "Ahoana ?", "lignes": ["1 · Safidio ny vokatra", "2 · « Calculer mes quantités »", "3 · Ampidiro ny surface"]},
        "s3": {"titre": "Isany sy vidiny", "sous": "avy hatrany, maimaim-poana", "lignes": ["hourdis.fonenako.mg"]},
    },
    "brique-creuse-15": {
        "s2": {"prix": "3 000 Ar", "sous": "12 isaky ny m² de mur"},
        "s3": {"lignes": ["Rindrina ivelany sy façade", "Rindrina anatiny matevina", "25 m² → 300 pièces"]},
    },
    "fanaterana-antananarivo": {
        "s2": {"titre": "1 500 Ar isaky ny km", "sous": "manomboka eto Ambohimanga Rova"},
        "s3": {"lignes": ["Antananarivo sy ny manodidina", "3 à 7 andro aorian'ny commande", "Afaka tonga maka ihany koa"]},
    },
    "fahadisoana-4-plancher": {
        "s2": {"lignes": ["1 · Tsy misy tahiry 3 à 5 %", "2 · Mandeha eo ambonin'ny hourdis"]},
        "s3": {"lignes": ["3 · Étais esorina aloha loatra", "4 · Hourdis eo amin'ny tany lena"]},
    },
    "tuile-ecaille": {
        "s2": {"prix": "500 Ar", "sous": "75 isaky ny m² de toiture"},
        "s3": {"lignes": ["Tafo malagasy nentim-paharazana", "Tsy mafana, tsy mitabataba", "Maharitra taona maro"]},
    },
    "inona-no-manahirana-anao": {
        "s2": {"lignes": ["A · Ny vidiny", "B · Ny fotoana", "C · Ny mpanao asa", "D · Ny fitaterana"]},
        "s3": {"titre": "Valio amin'ny litera iray", "sous": "ao amin'ny commentaire 👇"},
    },
    "hourdis-tsara-kalitao": {
        "s2": {"lignes": ["1 · Feo madio rehefa dondonina", "2 · Tsy misy triatra"]},
        "s3": {"lignes": ["3 · Loko mitovy manontolo", "4 · 33 × 33 cm tsara"]},
    },
    "hourdis-15": {
        "s2": {"prix": "3 000 Ar", "sous": "9 isaky ny m² de plancher"},
        "s3": {"lignes": ["Portée 3 à 4 m eo ho eo", "Plancher étage trano fonenana", "60 m² → 540 pièces"]},
    },
    "devis-maimaim-poana": {
        "s2": {"titre": "Fenoy ny formulaire", "lignes": ["Anarana sy finday", "Toerana misy ny chantier", "Vokatra sy surface"]},
        "s3": {"titre": "Antsoinay ianao", "sous": "vidiny, fanaterana, délai"},
    },
    "trano-mangatsiatsiaka": {
        "s2": {"titre": "Rivotra voahidy", "sous": "ao anaty lavaky ny brique creuse"},
        "s3": {"lignes": ["Miadana ny fidiran'ny hafanana", "Mangatsiatsiaka kokoa ny ao an-trano"]},
    },
    "brique-creuse-10": {
        "s2": {"prix": "2 500 Ar", "sous": "12 isaky ny m² de mur"},
        "s3": {"lignes": ["Rindrina fisarahana (cloison)", "Maivana, mora apetraka", "8,4 m² → 101 pièces"]},
    },
    "aiza-no-misy-anay": {
        "s2": {"titre": "Ambohimanga Rova", "sous": "lalana mandalo an'i Sabotsy Namehana"},
        "s3": {"titre": "Tongava hijery", "sous": "fa miantsoa aloha : 032 47 041 43"},
    },
    "marina-sa-diso": {
        "s2": {"titre": "MARINA sa DISO ?"},
        "s3": {"titre": "Soraty ao amin'ny commentaire 👇", "sous": "Ny valiny rahampitso"},
    },
    "fandorana": {
        "s1": {"badge": "VALINY", "titre": "DISO !", "sous": "Ny poutrelle sy ny dalle de compression no mitondra ny lanjany"},
        "s2": {"badge": "ATELIER", "titre": "Fandorana", "sous": "dingana farany amin'ny famokarana"},
        "s3": {"lignes": ["Hamafisana", "Loko mitovy", "Faharetana amin'ny orana"]},
    },
    "biriky-hafa": {
        "s2": {"lignes": ["Brique repressée · 2 200 Ar", "Tonette · 1 800 Ar", "Plaquette chinois · 700 Ar"]},
        "s3": {"sous": "Mila sary ve ? Andefaso hafatra", "lignes": ["Plaquette · 500 Ar", "Briquette · 500 Ar"]},
    },
    "kajy-brique-creuse-12": {
        "s2": {"lignes": ["Rindrina 10 m × 2,8 m", "= 28 m²", "Esory varavarana : − 4 m²"]},
        "s3": {"titre": "24 × 12 = 288", "sous": "briques, ampio 3 à 5 %"},
    },
    "alohan-ny-fahavaratra": {
        "s2": {"titre": "≈ 30 andro", "sous": "ny famokarana"},
        "s3": {"titre": "Manafara izao", "sous": "tonga alohan'ny orana ny hourdis sy ny tuile"},
    },
    "fanontaniana-3-mahazatra": {
        "s2": {"titre": "« Misy stock ve ? »", "sous": "Amin'ny commande : ≈ 30 andro"},
        "s3": {"titre": "« Manatitra ve ? »", "sous": "Eny : Antananarivo sy ny manodidina"},
    },
    "misaotra-anareo": {
        "s2": {"titre": "Vita tanimanga malagasy", "sous": "eto Ambohimanga Rova"},
        "s3": {"titre": "Zarao ity page ity", "sous": "amin'ny namanao manorina trano 🤝"},
    },
}
