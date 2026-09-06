import json

from bot import config, rangement


def _t(**extra):
    t = {"id": "abc123def456", "url": "https://exemple.fr/pose-hourdis", "titre": "Pose d'un plancher hourdis : les étapes",
         "texte": "Le texte intégral.\nDeuxième ligne.", "genre": "article", "auteur": "Rector", "source_nom": "Rector",
         "publie_le": "2026-09-04", "date_origine": "meta", "collecte_le": "2026-09-06T05:00:00+00:00",
         "score": 72, "themes": ["pose", "plancher"], "motifs": ["hourdis ×4"], "images": [], "post": "Brouillon."}
    t.update(extra)
    return t


def test_ranger_cree_le_dossier_par_date(cfg):
    relatif = rangement.ranger(_t(), cfg)
    assert relatif == "2026-09-04/pose-d-un-plancher-hourdis-les-etapes--abc123"
    dossier = rangement.racine(cfg) / relatif
    texte = (dossier / "texte.txt").read_text(encoding="utf-8")
    assert texte.startswith("Titre         : Pose d'un plancher hourdis : les étapes\n")
    assert "Publié le     : 2026-09-04" in texte and "TEXTE\nLe texte intégral." in texte
    assert (dossier / "post-facebook.txt").read_text(encoding="utf-8").strip() == "Brouillon."
    fiche = json.loads((dossier / "fiche.json").read_text(encoding="utf-8"))
    assert fiche["score"] == 72 and "texte" not in fiche
    index = (dossier.parent / "INDEX.txt").read_text(encoding="utf-8")
    assert " 72 | Article" in index and "pose-d-un-plancher" in index


def test_sans_date_va_dans_date_inconnue(cfg):
    relatif = rangement.ranger(_t(publie_le="", date_origine=""), cfg)
    assert relatif.startswith("date-inconnue/")
    texte = (rangement.racine(cfg) / relatif / "texte.txt").read_text(encoding="utf-8")
    assert "Publié le     : inconnu" in texte


def test_deplacer_quand_la_date_change(cfg):
    t = _t(publie_le="")
    ancien = rangement.ranger(t, cfg)
    t["publie_le"] = "2025-01-15"
    nouveau = rangement.deplacer(t, ancien, cfg)
    assert nouveau.startswith("2025-01-15/")
    assert not (rangement.racine(cfg) / ancien).exists()
    assert (rangement.racine(cfg) / nouveau / "texte.txt").exists()
    # Le dossier « date-inconnue » vidé disparaît.
    assert not (rangement.racine(cfg) / "date-inconnue").exists()


def test_slug_et_dossier_configurable(tmp_path):
    assert rangement.slug("Étaiement & coffrage : 3 règles !", "zz9999") == "etaiement-coffrage-3-regles--zz9999"
    assert rangement.nom_dossier_date("2026-9-4") == "date-inconnue"
    cfg = config.charger()
    cfg["dossier_collecte"] = str(tmp_path / "ailleurs")
    assert rangement.racine(cfg) == tmp_path / "ailleurs"


def test_supprimer_nettoie(cfg):
    relatif = rangement.ranger(_t(), cfg)
    rangement.supprimer(relatif, cfg)
    assert not (rangement.racine(cfg) / relatif).exists()
