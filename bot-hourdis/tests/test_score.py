from datetime import date

from bot import score

TUTO_FR = """Comment poser un plancher hourdis sur poutrelles précontraintes : les étapes.
Avant de couler la dalle de compression, vérifiez l'étaiement des poutrelles tous les 1,50 m.
Les hourdis en terre cuite se posent à sec entre les poutrelles ; le treillis soudé se place
ensuite, puis le chaînage périphérique. Erreur à éviter : couler sans étais, le plancher fléchit.
Comptez 9 hourdis par m² pour un entraxe de 60 cm."""

ANNONCE_IMMO = """A vendre villa F4 à Ambohimanga, murs en brique, toit en tuile, terrain titré borné.
Prix 250 millions, contact 034 00 000 00. Avendre urgent."""

MG = """Torohevitra : ahoana ny fametrahana hourdis amin'ny rihana ? Ny biriky tanimanga dia
apetraka eo anelanelan'ny poutrelle, ary tsy azo atao ny mandraraka beton raha tsy misy etais.
Isa : 9 hourdis isaky ny metatra toradroa. Fanorenana trano vato any Antananarivo, Madagasikara."""


def test_tuto_francais_note_haut_et_trouve_les_themes():
    r = score.noter("Comment poser un plancher hourdis — tutoriel", TUTO_FR, "article")
    assert not r["hors_sujet"]
    assert r["score"] >= 65, r
    assert "pose" in r["themes"] and "erreurs" in r["themes"] and "calcul" in r["themes"]
    assert r["langue"] == "fr"
    assert any("tutoriel" in m for m in r["motifs"])


def test_annonce_immobiliere_est_hors_sujet():
    r = score.noter("Villa à vendre Ambohimanga", ANNONCE_IMMO, "post_fb")
    assert r["hors_sujet"] is True
    assert "immobili" in r["raison"]


def test_brique_de_lait_est_hors_sujet():
    r = score.noter("Recette : gâteau à la brique de lait", "Prenez une brique de lait et du sucre.", "article")
    assert r["hors_sujet"] is True


def test_aucun_mot_du_metier_ecarte():
    r = score.noter("Le match de ce soir", "Les joueurs ont bien joué au football.", "article")
    assert r["hors_sujet"] is True and r["score"] == 0


def test_malgache_reconnu_et_pertinent():
    r = score.noter("Fametrahana hourdis", MG, "video")
    assert r["langue"] == "mg"
    assert not r["hors_sujet"]
    assert r["score"] >= 55, r
    assert "madagascar" in r["themes"]


def test_anglais_penalise_mais_garde():
    en = ("How to install a beam and block floor with hollow clay blocks. Step by step guide: "
          "place the precast beams, then the clay blocks, then pour the concrete topping.")
    fr = score.noter("Pose plancher hourdis terre cuite étape par étape", TUTO_FR, "article")
    r = score.noter("How to install a beam and block floor", en, "article")
    assert r["langue"] == "en" and not r["hors_sujet"]
    assert r["score"] < fr["score"]
    assert "anglais" in r["motifs"]


def test_repoussoir_attenue_quand_le_coeur_est_fort():
    texte = TUTO_FR + "\nCe plancher hourdis convient aussi à une maison à vendre plus tard."
    r = score.noter("Plancher hourdis : guide de pose", texte, "article")
    assert not r["hors_sujet"]


def test_video_recente_bonus_et_pre_note():
    hier = date.today()
    r1 = score.noter("Pose hourdis", TUTO_FR, "video", publie_le=hier)
    r2 = score.noter("Pose hourdis", TUTO_FR, "article", publie_le=hier)
    assert r1["score"] > r2["score"]
    assert score.pre_note("Comment réaliser un plancher hourdis ?") >= 20
    assert score.pre_note("Mon chat fait du skate") == 0


def test_themes_ordonnes_le_titre_d_abord():
    texte = "On monte le mur en brique. Un défaut classique : l'erreur de niveau. Mur, mur, brique."
    themes = score.themes_de(texte, "Comment bâtir un mur en briques creuses")
    assert themes[0] == "murs"
    assert "erreurs" in themes


def test_mots_metier_supplementaires_de_la_config():
    cfg = {"mots_metier": ["rupteur thermique"]}
    r = score.noter("Rupteur thermique", "Le rupteur thermique se pose en rive de plancher hourdis.", "article", cfg=cfg)
    assert any("rupteur" in m for m in r["motifs"])
