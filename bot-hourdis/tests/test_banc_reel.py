"""LE BANC DES CAS RÉELS — mesuré le 06/09/2026 sur les 13 premières trouvailles.

🔴 POURQUOI CE FICHIER EXISTE. Les 63 tests d'origine passaient au vert pendant
que le bot gardait « comment maintenir une pression d'eau régulière ? » (37/100)
et « décryptage des normes pour vos gants de protection » (51/100) — deux
articles de BTP générique qui ne nomment jamais un hourdis, une brique, une tuile
ni la terre cuite. Ils passaient parce que le score s'additionnait : 12 points de
métier (« chantiers » ×8, « gros œuvre ») et 30 points de bonus (tutoriel,
thèmes, longueur).

Un banc de cas inventés n'aurait jamais trouvé ça : il faut les VRAIS textes,
avec leur bruit, leur longueur et leurs mots de remplissage. Chaque cas ci-dessous
porte donc le titre réel, l'adresse réelle, et un extrait fidèle de ce que le bot
a effectivement lu.
"""
from __future__ import annotations

import pytest

from bot import score, toile

# ── Ce que le bot doit GARDER : le produit est nommé, le contenu enseigne ──
GARDER = [
    (
        "12g. RENOVATION! Comment bâtir un mur en briques creuses au mortier de chaux.",
        "video",
        "Bonjour, aujourd'hui je vous montre comment j'ai maçonné les murs porteurs servant de "
        "cloisons séparatives dans notre futur gîte. Ce sont des briques de 15 cm. On pose les "
        "briques creuses au mortier de chaux, mortier pas trop mouillé pas trop sec parce que la "
        "brique absorbe énormément l'eau du mortier. On vérifie le niveau à chaque rang, on croise "
        "les joints, et on laisse le mur reposer avant de charger. " * 4,
    ),
    (
        "Les nouvelles tuiles à emboîtement",
        "article",
        "Les tuiles à emboîtement en terre cuite se posent sur liteaux avec un recouvrement "
        "réglable. La pente minimale dépend de la zone et de la longueur de rampant. Le pureau "
        "varie selon le modèle de tuile. La fixation des tuiles de rive et de faîtage se fait par "
        "crochet ou par vis. La terre cuite garde son aspect des décennies durant. " * 5,
    ),
    (
        "Comment monter une cloison en brique",
        "video",
        "Dans ce tutoriel nous allons découvrir comment monter une cloison en brique. La "
        "construction d'une cloison en brique demande précision et méthode : tracer l'implantation, "
        "poser le premier rang au mortier, vérifier l'aplomb, croiser les joints. " * 3,
    ),
    (
        "La liste des DTU (Documents Techniques Unifiés) à jour",
        "article",
        "Le DTU 20.1 traite des ouvrages en maçonnerie de petits éléments : parois et murs en "
        "briques et en blocs. Le DTU 23.1 concerne les murs en béton banché. Le DTU 40.21 fixe la "
        "pose des tuiles en terre cuite à emboîtement. Le DTU 21 traite de l'exécution des ouvrages "
        "en béton, dont les planchers à poutrelles et hourdis. " * 5,
    ),
]

# ── Ce que le bot doit JETER : du BTP, mais pas notre métier ──
JETER = [
    (
        "Sécurité : décryptage des normes pour sélectionner vos gants de protection professionnels",
        "article",
        "La norme EN 388 mesure la résistance des gants aux agressions mécaniques : abrasion, "
        "coupure, déchirure, perforation. Sur un chantier de gros œuvre, le choix du gant dépend du "
        "poste. Le maçon, le ferrailleur et le coffreur n'ont pas les mêmes besoins. L'isolation "
        "thermique du gant compte aussi pour les travaux d'hiver. " * 6,
    ),
    (
        "Habitat collectif : comment maintenir une pression d'eau régulière ?",
        "article",
        "Dans un immeuble collectif, la pression d'eau peut chuter lorsque plusieurs logements "
        "sollicitent le réseau au même moment. Le surpresseur compense la perte de charge liée à la "
        "hauteur. Le dimensionnement se fait selon le nombre de points de puisage. Sur un chantier "
        "neuf, le plombier règle la pression après les essais. " * 6,
    ),
    (
        "Recette : le gâteau à la brique de lait",
        "article",
        "Prenez une brique de lait entier, du sucre et trois œufs. Faites chauffer le lait sans le "
        "faire bouillir. La brique de lait se conserve au frais après ouverture. " * 6,
    ),
]


@pytest.mark.parametrize("titre,genre,texte", GARDER, ids=[c[0][:34] for c in GARDER])
def test_le_bon_contenu_est_garde(titre, genre, texte):
    r = score.noter(titre, texte, genre)
    assert not r["hors_sujet"], f"{titre} : rejeté — {r['raison']}"
    assert r["score"] >= 35, f"{titre} : {r['score']}/100, sous le seuil"


@pytest.mark.parametrize("titre,genre,texte", JETER, ids=[c[0][:34] for c in JETER])
def test_le_btp_generique_est_jete(titre, genre, texte):
    r = score.noter(titre, texte, genre)
    assert r["hors_sujet"] or r["score"] < 35, (
        f"{titre} : gardé avec {r['score']}/100 — motifs {r['motifs']}")


def test_le_produit_doit_etre_nomme():
    """La porte qui manquait : sans le produit, les bonus ne suffisent plus."""
    generique = ("Sur un chantier de gros œuvre, le maçon coule le béton et vérifie le ferraillage. "
                 "Comment éviter les erreurs ? Voici les étapes et les conseils du chantier. " * 8)
    r = score.noter("Les étapes d'un chantier réussi", generique, "article")
    assert r["hors_sujet"] and "jamais nommé" in " ".join(r["motifs"])
    # Le même texte, avec le produit nommé une seule fois dans le titre, entre.
    r2 = score.noter("Poser un plancher hourdis : les étapes", generique, "article")
    assert not r2["hors_sujet"]


def test_les_bonus_ne_portent_pas_un_article_a_eux_seuls():
    """Le score ne peut pas plus que doubler grâce aux bonus."""
    maigre = ("Le mur en brique du voisin est joli. Comment faire ? Voici un guide, des conseils, "
              "des étapes, des erreurs à éviter, le calcul, le prix, l'isolation, la toiture. " * 10)
    r = score.noter("Comment bien faire ? Guide, étapes et erreurs", maigre, "video")
    assert r["score"] <= 2 * min(58, r["score"]), "les bonus doivent être plafonnés par le cœur"


def test_le_mur_anti_robot_n_est_pas_un_article():
    assert toile.est_sans_contenu(
        "Chargement… anubis n'a pas réussi à charger son code javascript. "
        "Le serveur est peut-être surchargé. Veuillez recharger la page.")
    assert toile.est_sans_contenu("Veuillez activer JavaScript pour continuer.")
    assert toile.est_sans_contenu("Article réservé aux abonnés. Connectez-vous pour lire la suite.")
    assert not toile.est_sans_contenu("Pose des hourdis en terre cuite entre poutrelles. " * 20)


def test_javascript_ne_rejette_plus_un_article_de_terre_cuite():
    """« javascript » est de l'ossature de page, pas un sujet.

    Un article universitaire sur les tuiles et les briques au Moyen Âge était
    rejeté comme « informatique » à cause du bandeau de sa page."""
    texte = ("Les tuiles et les briques au Moyen Âge en Pays de la Loire : un état de la question. "
             "Les tuileries médiévales produisaient des tuiles plates et des briques de terre cuite "
             "cuites au bois. L'étude des pâtes et des dimensions permet de dater la production. " * 5
             + " Ce site utilise du javascript pour l'affichage des figures.")
    r = score.noter("Les tuiles et les briques au Moyen Âge en Pays de la Loire", texte, "article")
    assert not r["hors_sujet"], f"rejeté à tort — {r['raison']}"
