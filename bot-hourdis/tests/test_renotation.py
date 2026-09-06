"""La renotation applique les règles d'aujourd'hui au stock d'hier.

🔴 POURQUOI. Le 06/09/2026, après avoir fermé la porte qui laissait passer le BTP
générique, « comment maintenir une pression d'eau régulière ? » était toujours
dans la pile à trier d'Andry, à 41/100 : une correction du tri ne vaut que pour
ce qui arrive après elle. Et l'inverse compte autant — quand une règle
s'assouplit, ce qui avait été jeté à tort doit revenir.
"""
from __future__ import annotations

from bot import base, collecteur, rangement

PLOMBERIE = ("Dans un immeuble collectif, la pression d'eau peut chuter lorsque plusieurs logements "
             "sollicitent le réseau. Le surpresseur compense la perte de charge. Sur un chantier de "
             "gros œuvre, le plombier règle la pression après les essais. " * 8)
TUTO = ("Pose d'un plancher hourdis sur poutrelles : vérifier l'étaiement tous les 1,50 m avant de "
        "couler la dalle de compression. Les hourdis en terre cuite se posent à sec. " * 8)


def test_renotation_ecarte_ce_qui_ne_passerait_plus(cfg):
    """Un faux positif d'hier quitte la pile à trier, et son dossier disparaît."""
    c = collecteur.Collecteur()
    tid = base.ajouter_trouvaille({
        "url": "https://x.fr/pression", "titre": "Comment maintenir une pression d'eau régulière ?",
        "texte": PLOMBERIE, "genre": "article", "score": 41, "statut": "nouvelle",
        "dossier": "", "themes": ["calcul"], "motifs": ["ancien barème"]})
    t = base.trouvaille(tid)
    t["dossier"] = rangement.ranger(t, cfg)
    base.modifier_trouvaille(tid, {"dossier": t["dossier"]})
    assert (rangement.racine(cfg) / t["dossier"]).exists()

    bilan = collecteur.renoter_tout(cfg)

    apres = base.trouvaille(tid)
    assert apres["statut"] == "ecartee" and apres["score"] == 0
    assert "ni hourdis" in apres["motif_ecart"]
    assert apres["dossier"] == "" and not (rangement.racine(cfg) / t["dossier"]).exists()
    assert bilan["relues"] == 1 and bilan["ecartees"] == 1


def test_renotation_reprend_ce_qui_avait_ete_jete_a_tort(cfg):
    """Une règle assouplie rend sa chance à une trouvaille écartée."""
    tid = base.ajouter_trouvaille({
        "url": "https://x.fr/dtu", "titre": "Poser un plancher hourdis : les étapes",
        "texte": TUTO, "genre": "article", "score": 0, "statut": "ecartee",
        "motif_ecart": "publiée en 2011, avant 2012"})
    bilan = collecteur.renoter_tout(cfg, seulement_a_trier=False)
    apres = base.trouvaille(tid)
    assert apres["statut"] == "nouvelle" and apres["motif_ecart"] == ""
    assert apres["score"] >= 35 and apres["dossier"]
    assert bilan["reprises"] == 1


def test_renotation_ne_touche_jamais_ce_qu_andry_a_garde(cfg):
    """Son avis prime sur le barème : le statut d'une gardée ne bouge pas."""
    tid = base.ajouter_trouvaille({
        "url": "https://x.fr/gardee", "titre": "Un article que le barème n'aime plus",
        "texte": PLOMBERIE, "genre": "article", "score": 60, "statut": "gardee"})
    collecteur.renoter_tout(cfg, seulement_a_trier=False)
    apres = base.trouvaille(tid)
    assert apres["statut"] == "gardee", "une trouvaille gardée par Andry ne se dégarde pas toute seule"
    assert apres["score"] == 0, "sa note, elle, est bien remise à jour pour le classement"


def test_renotation_applique_aussi_les_regles_hors_bareme(cfg):
    """🔴 Un garde-fou se pose à CHAQUE bout du chemin qu'il protège.

    Quatre fiches « Télécharger la fiche » (le libellé du lien, pas le titre du
    PDF) étaient entrées avant que la règle n'existe. Une renotation qui ne
    recalcule que le barème les aurait laissées dans la pile pour toujours."""
    tid = base.ajouter_trouvaille({
        "url": "https://x.fr/fiche.pdf", "titre": "Télécharger la fiche",
        "texte": TUTO, "genre": "pdf", "score": 48, "statut": "nouvelle"})
    collecteur.renoter_tout(cfg)
    apres = base.trouvaille(tid)
    assert apres["statut"] == "ecartee" and "libellé d'interface" in apres["motif_ecart"]


def test_renotation_par_defaut_ignore_les_ecartees(cfg):
    base.ajouter_trouvaille({"url": "https://x.fr/e", "titre": "Poser un plancher hourdis",
                             "texte": TUTO, "genre": "article", "score": 0, "statut": "ecartee",
                             "motif_ecart": "vieux"})
    bilan = collecteur.renoter_tout(cfg)          # seulement_a_trier=True par défaut
    assert bilan["relues"] == 0 and bilan["reprises"] == 0
    assert base.trouvaille(base.lister_trouvailles(statut="ecartee")[0]["id"])["statut"] == "ecartee"
