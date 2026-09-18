# -*- coding: utf-8 -*-
"""Écrit photos.json et photos-rejetees.json à partir du tri visuel des planches.

Les numéros (001…058) sont ceux des planches (table.json, produite par planches.py).
Tout ce qui est écrit ici a été VU sur les planches ou sur une vue de détail (planches/vue_*,
detail_*, net_*, bandes_bas_*, verif_recadrage). Ce qui n'était pas lisible est dit comme tel.
"""
import sys, json, collections
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ICI = Path(__file__).resolve().parent
TABLE = json.loads((ICI / "table.json").read_text(encoding="utf-8"))

FILIGRANE_REDMI = "filigrane « REDMI K20 PRO 48MP TRIPLE CAMERA » en bas à gauche"
SANS_FILIGRANE = [0.0, 0.0, 1.0, 0.87]  # vérifié sur planches/verif_recadrage.jpg : plus rien au-dessus de 0,87

# (numéro planche, sujet, détail, qualité, défauts, images du site, recadrage)
# {NNN} dans un texte = renvoi vers l'id retenu de la photo NNN
RETENUES = [
    # --- HOURDIS ---
    ("008", "hourdis (stock, cuits)",
     "Grande pile de hourdis cuits en plein air sur terre rouge, profil à alvéoles et marches bien visibles, arbres et ciel bleu derrière ; hauteur non lisible.",
     "nette", [], ["hero-1920.webp", "hero-960.webp", "hero-640.webp"], None),
    ("009", "hourdis (séchage sur étagères)",
     "Hourdis crus alignés sur des étagères en perches de bois sous le hangar, profil vu de près.",
     "correcte (un peu douce)", [], ["galerie-hourdis-etalage.webp", "galerie-sechage-hourdis.webp"], None),
    ("014", "hourdis (séchage au sol, crus)",
     "Blocs crus à deux rangées d'alvéoles alignés au sol sous le hangar (photo rangée par Andry dans Publication/HOURDIS ; le profil exact n'est pas lisible sur la photo).",
     "nette", ["3 ouvriers au fond en haut à gauche, de dos ou de profil, visages non reconnaissables à la taille de publication"], [], None),
    ("015", "hourdis (séchage sur étagères)",
     "Hourdis crus posés sur des étagères en bois à montants métalliques bleus, profil à talons bien lisible.",
     "nette", [], [], None),
    ("029", "hourdis (gros plan, cuit)",
     "Un hourdis cuit à deux rangées d'alvéoles posé sur un muret de terrasse carrelé, collines boisées et quartier au fond ; fichier nommé « Hourdis 15 2 » (hauteur non lisible sur la photo).",
     "nette (1440x1080)", [FILIGRANE_REDMI], [], SANS_FILIGRANE),
    ("030", "hourdis (gros plan, cuit)",
     "Un hourdis cuit à deux rangées d'alvéoles vu de face sur un muret, immeuble jaune et collines au fond ; le fichier s'appelle « Hourdis 15 » mais le site l'affiche comme hourdis 12 : hauteur à confirmer par Andry.",
     "nette (1440x1080)", [FILIGRANE_REDMI], ["hourdis-12.webp"], SANS_FILIGRANE),
    ("034", "hourdis (séchage sur étagères)",
     "Hourdis crus sur des étagères en perches de bois sous un hangar en tôle, vus en bout de rangée (série du 05/03/2026).",
     "nette", [], [], None),
    ("039", "hourdis (séchage sur étagères)",
     "Étagères chargées de hourdis crus vus de profil sous un hangar à toit de bâche rayée (05/03/2026).",
     "nette", [], [], None),
    ("040", "hourdis (séchage sur étagères)",
     "Allée étroite entre deux étagères de bois chargées de hourdis crus, alvéoles face à l'objectif (05/03/2026).",
     "correcte", [], [], None),
    ("041", "hourdis (stock avant cuisson)",
     "Hourdis secs de teinte beige (pas encore cuits) empilés en escalier sous le hangar, étagères et un vélo au fond (05/03/2026).",
     "nette", [], [], None),
    ("047", "hourdis (gros plan, cuit)",
     "Un hourdis cuit à trois rangées d'alvéoles vu de trois quarts sur un muret, immeuble jaune au fond ; le site l'affiche comme hourdis 20 (hauteur non lisible sur la photo).",
     "correcte mais petite (720x540)",
     ["filigrane REDMI dédoublé et illisible en bas à gauche", "basse résolution 720x540",
      "le recadrage à 0,87 affleure le pied du hourdis"], ["hourdis-20.webp"], SANS_FILIGRANE),
    ("048", "hourdis (gros plan, cuit)",
     "Un hourdis cuit à trois rangées d'alvéoles vu de trois quarts, un second hourdis derrière, immeuble jaune et collines ; le site l'affiche comme hourdis 15 alors qu'une copie s'appelle « Hourdis 20.png » : hauteur à confirmer par Andry.",
     "correcte mais petite (720x540)",
     [FILIGRANE_REDMI, "basse résolution 720x540"], ["hourdis-15.webp"], SANS_FILIGRANE),
    # --- BRIQUE CREUSE ---
    ("001", "brique creuse (stock, cuites)",
     "Pile de briques creuses cuites dans la cour, terre latérite rouge, une autre pile et des arbres au fond, ciel bleu.",
     "nette", [], ["brique-creuse-10.webp", "galerie-briques-seches.webp"], None),
    ("002", "brique creuse (séchage en plein air, crues)",
     "Des centaines de briques creuses crues posées debout au soleil pour sécher, une pile de briques cuites au fond.",
     "nette", [], ["galerie-briques-crues.webp"], None),
    ("003", "brique creuse (séchage sous hangar, crues)",
     "Briques creuses crues à 12 alvéoles alignées au sol sous le hangar, machines bleues au fond.",
     "nette", [], [], None),
    ("004", "brique creuse (séchage sur étagères)",
     "Briques creuses crues rangées sur des étagères en bois sous un hangar couvert de chaume.",
     "nette", [], ["galerie-hangar-briques.webp", "apropos-atelier.webp"], None),
    ("005", "brique creuse (séchage sur étagères)",
     "Briques creuses crues sur des étagères à montants métalliques bleus sous le hangar.",
     "correcte (un peu douce)", [], ["galerie-briques-etalage.webp"], None),
    ("028", "brique creuse (gros plan, cuites)",
     "Deux briques creuses cuites posées sur le muret d'un balcon, alvéoles face à l'objectif, maisons au fond ; fichier nommé « BC 15 ».",
     "nette (1440x1080)", [FILIGRANE_REDMI], ["brique-creuse-15.webp"], SANS_FILIGRANE),
    ("031", "brique creuse (séchage sous hangar, crues)",
     "Briques creuses crues hautes à 9 alvéoles dressées au sol sous le hangar, étagères et machines au fond (modèle différent de {003}).",
     "nette", [], [], None),
    ("042", "brique creuse (stock, cuites)",
     "Pile de briques creuses cuites dans la cour de l'atelier, hangars, four et conteneur rouge au fond, ciel bleu (05/03/2026).",
     "nette", [], [], None),
    ("046", "brique creuse (gros plan, cuites)",
     "Deux briques creuses cuites sur un muret, l'une vue en bout (alvéoles), l'autre en long, immeuble jaune au fond ; le site l'affiche comme brique creuse 20.",
     "correcte mais petite (720x540)", [FILIGRANE_REDMI, "basse résolution 720x540"], ["brique-creuse-20.webp"], SANS_FILIGRANE),
    # --- TUILES ---
    ("013", "tuile mécanique (abri couvert)",
     "Abri en briques couvert de tuiles mécaniques vu de face, cheminée de briques et pins au fond (même abri que {027}, autre angle).",
     "nette", [], [], None),
    ("023", "tuile mécanique (stock)",
     "Tuiles mécaniques cuites rangées sur chant en longues rangées, profil d'emboîtement bien visible.",
     "nette", [], [], None),
    ("024", "tuile mécanique (posée)",
     "Toit de l'abri couvert de tuiles mécaniques vu en biais, cheminée de briques et arbres au fond.",
     "correcte", [], ["tuile-mecanique.webp"], None),
    ("025", "tuile mécanique (posée, gros plan)",
     "Rangs de tuiles mécaniques le long du toit de l'abri, maison en briques et collines au fond (10 s après {024}, cadrage différent).",
     "nette", [], [], None),
    ("026", "tuile écaille",
     "Panneau d'échantillon couvert de tuiles écailles en quinconce, posé en pente sur l'herbe sèche, briques au fond.",
     "nette", [], ["tuile-ecaille.webp"], None),
    ("027", "tuile mécanique (abri couvert)",
     "Abri en briques couvert de tuiles mécaniques vu en diagonale, cheminée de briques et petites cabanes en bois au fond.",
     "nette", [], ["galerie-tuiles.webp"], None),
    # --- PLAQUETTES, BRIQUETTES, BRIQUES PLEINES ---
    ("011", "brique repressée / briquette / plaquette",
     "Plaquette décorative à motif en losanges posée debout sur un lit de plaquettes, pile de briques au fond (type exact non lisible sur la photo).",
     "nette", [], [], None),
    ("018", "tuile mécanique + plaquettes décoratives",
     "Sur une étagère métallique : une tuile mécanique et trois plaquettes à motif en losanges, mur gris.",
     "correcte (légèrement douce, lumière plate)", [], [], None),
    ("019", "brique repressée / briquette / plaquette",
     "Trois plaquettes décoratives à motif en losanges posées sur une pile, cadrage vertical.",
     "nette", [], [], None),
    ("020", "brique repressée / briquette / plaquette (stock)",
     "Stock de plaquettes et de briques empilées à l'intérieur d'un abri en briques, herbes vues par l'ouverture.",
     "nette", [], [], None),
    ("022", "brique repressée / briquette / plaquette",
     "Paquet de plaquettes rainurées dressé sur un sol de plaquettes, pile de briques et herbes sèches au fond.",
     "nette", [], [], None),
    ("045", "briques pleines (stock)",
     "Grand mur de briques pleines empilées sous le hangar, une brique posée au premier plan ; cuites ou non : pas vérifiable sur la photo (05/03/2026).",
     "correcte", [], [], None),
    # --- FABRICATION, SÉCHAGE, CUISSON, ATELIER ---
    ("006", "four / cuisson (fandorana)",
     "Le four : briques crues empilées sur le dessus, fumée qui s'échappe, paroi du four à droite, grand arbre au fond.",
     "nette", [], ["galerie-fandorana-briques.webp"], None),
    ("016", "four / cuisson (fandorana)",
     "Paroi du four en briques noircies par le feu, fumée, briques creuses cuites et cassées au premier plan (même four que {006}, 47 s plus tôt, autre angle).",
     "nette", ["briques cassées au premier plan (peu flatteur pour la vente)"], [], None),
    ("037", "moulage (extrudeuse)",
     "La machine de moulage bleue avec un boudin d'argile sur le tapis, étagères, vélos et vêtements suspendus au fond (05/03/2026).",
     "nette", ["une personne assise au fond, de dos, non reconnaissable", "arrière-plan encombré (vélos, vêtements)"], [], None),
    ("035", "séchage (vue d'ensemble du hangar)",
     "Longues rangées d'étagères de séchage chargées de hourdis crus sous le hangar en tôle, bâche bleue (05/03/2026, 12 s après {034}, plan large).",
     "nette", [], [], None),
    ("036", "atelier (hangar de séchage)",
     "Allée d'un hangar sombre bordée d'étagères presque vides, ciel bleu et bâches bleues au bout (05/03/2026).",
     "sombre", ["sombre, contre-jour", "étagères presque vides : peu de produit visible"], [], None),
]

# (numéro, raison, garder à la place)
REJETEES = [
    ("007", "quasi-doublon : même pile de hourdis que 008, sous le même angle ; 008 est plus nette (007 est déjà sur le site : galerie-stock-hourdis, galerie-pile-hourdis)", "008"),
    ("010", "quasi-doublon : même sol de séchage que 003, 22 s plus tard ; 003 est plus nette. NB : une copie s'appelle « Hourdis bediabe am tany » mais la photo montre des briques creuses à 12 alvéoles (et Andry l'a rangée dans Publication/Brique creuse)", "003"),
    ("012", "quasi-doublon : même abri à tuiles que 013, 8 s plus tôt, même cadrage", "013"),
    ("017", "document : note manuscrite des produits avec prix de 2023 (brique repressée, briquette, plaquette, tuiles, tomette) — pas une photo de produit, prix périmés", None),
    ("021", "quasi-doublon : même paquet de plaquettes que 022, 16 s plus tôt ; 022 plus lisible et plus nette", "022"),
    ("032", "quasi-doublon : mêmes plaquettes que 011, 4 s plus tard ; 011 montre mieux le motif", "011"),
    ("033", "document : même note manuscrite de prix 2023 que 017 (original non retouché)", None),
    ("038", "quasi-doublon : mêmes étagères de hourdis que 039, 6 s plus tôt ; 039 plus nette", "039"),
    ("043", "quasi-doublon : même mur de briques pleines que 045, même cadrage frontal", "045"),
    ("044", "quasi-doublon : même pile que 045 vue de l'angle, 20 s plus tôt, plus sombre et moins nette", "045"),
    ("049", "quasi-doublon : mêmes briques creuses que 046, petite (720x540) et filigrane REDMI", "046"),
    ("050", "ORIGINE DOUTEUSE : maison européenne à porte de garage sectionnelle et sapins, prise par drone (EXIF : DJI FC220, 24/03/2022), nom de fichier d'un site de fabricant (« 1-Maison-brique-terre-cuite-BGV4G-Vue-generale-Sud-scaled ») — rien de Madagascar", None),
    ("051", "ORIGINE DOUTEUSE : image de catalogue « poutrelles-hourdis » 800x400, aucun indice de lieu, vraisemblablement tirée d'internet", None),
    ("052", "ORIGINE DOUTEUSE : plafond en hourdis vu de dessous avec échafaudage, 512x384 (« unnamed »), aucun indice de Madagascar", None),
    ("053", "ORIGINE DOUTEUSE : image d'un article web (« pourquoi les produits en terre cuite permettent de réduire les ponts thermiques ») : murs en blocs de terre cuite, prairie verte et arbres feuillus d'Europe, engin de levage", None),
    ("054", "montage déjà fait : collage de photos avec liste de prix et numéros de téléphone incrustés (542x728)", None),
    ("055", "illustration / montage : rendus 3D de produits avec logo, pas une photo", None),
    ("056", "document client : bon de commande avec nom et adresse du client et montants", None),
    ("057", "ORIGINE À CONFIRMER : vrai chantier à Antananarivo (collines couvertes de maisons, jerrican jaune) avec hourdis, poutrelles et treillis — MAIS prise avec un autre téléphone (filigrane « honor 7X », alors que toutes les photos retenues viennent d'un Mi 9T Pro (EXIF) ou d'un Redmi K20 Pro (filigrane), le même modèle de téléphone), rien ne prouve que ce soit un chantier livré par Hourdis Madagascar, et un ouvrier accroupi a le visage visible. Rejetée par prudence ; à réintégrer seulement si Andry confirme que c'est un de ses clients (recadrage alors : 0, 0, 1, 0.9 pour le filigrane)", None),
    ("058", "logo, pas une photo", None),
]

AT = "\\sary vaovao\\Apres traitement\\"
AT_PS = "\\sary vaovao\\Apres traitement\\Pour site\\"


def meilleur_chemin(num):
    t = TABLE[num]
    tous = [t["chemin"]] + t["copies"]
    # série retouchée : préférer la copie directe de « Apres traitement » (même image, même taille)
    for c in tous:
        if AT in c and AT_PS not in c:
            return c
    return t["chemin"]


def orientation(num):
    w, h = TABLE[num]["w"], TABLE[num]["h"]
    if abs(w - h) <= 0.05 * max(w, h):
        return "carre"
    return "paysage" if w > h else "portrait"


def main():
    vus, photos = set(), []
    for k, (num, sujet, detail, qualite, defauts, site, recad) in enumerate(RETENUES, 1):
        assert num in TABLE, num
        assert num not in vus, f"doublon {num}"
        vus.add(num)
        ch = meilleur_chemin(num)
        assert Path(ch).exists(), ch
        photos.append({
            "id": f"p{k:02d}", "chemin": ch, "sujet": sujet, "detail": detail, "qualite": qualite,
            "orientation": orientation(num), "defauts": defauts, "sur_le_site": bool(site),
            "recadrage_conseille": recad,
            "images_site": site, "dimensions": f"{TABLE[num]['w']}x{TABLE[num]['h']}",
            "ref_planche": num, "nb_copies_dans_les_dossiers": 1 + len(TABLE[num]["copies"]),
        })
    ids = {p["ref_planche"]: p["id"] for p in photos}
    for p in photos:
        for num, pid in ids.items():
            p["detail"] = p["detail"].replace("{" + num + "}", pid)
        assert "{" not in p["detail"], p["detail"]
    rejetees = []
    for num, raison, garder in REJETEES:
        assert num in TABLE and num not in vus, num
        vus.add(num)
        t = TABLE[num]
        e = {"chemin": t["chemin"], "raison": raison, "ref_planche": num, "dimensions": f"{t['w']}x{t['h']}"}
        if garder:
            e["garder_a_la_place"] = ids[garder]
        if raison.startswith("ORIGINE"):
            e["toutes_les_copies"] = [t["chemin"]] + t["copies"]
        rejetees.append(e)
    manquants = sorted(set(TABLE) - vus)
    assert not manquants, f"photos non classées : {manquants}"
    assert len({p["chemin"] for p in photos}) == len(photos)
    (ICI / "photos.json").write_text(json.dumps(photos, ensure_ascii=False, indent=1), encoding="utf-8")
    (ICI / "photos-rejetees.json").write_text(json.dumps(rejetees, ensure_ascii=False, indent=1), encoding="utf-8")
    c = collections.Counter(p["sujet"].split(" (")[0] for p in photos)
    print(len(photos), "retenues,", len(rejetees), "rejetées,", len(TABLE), "photos distinctes au total")
    for k, v in c.most_common():
        print(f"  {v:2d}  {k}")
    print("sur le site :", sum(p["sur_le_site"] for p in photos), "; avec défaut :", sum(bool(p["defauts"]) for p in photos))


if __name__ == "__main__":
    main()
