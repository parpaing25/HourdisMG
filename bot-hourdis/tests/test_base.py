from bot import base


def test_propre_url_normalise():
    assert base.propre_url("https://www.exemple.fr/a/?utm_source=fb&x=1&fbclid=Z#haut") == "https://exemple.fr/a?x=1"
    assert base.propre_url("https://youtu.be/abc123") == "https://youtube.com/watch?v=abc123"
    assert base.propre_url("https://www.youtube.com/watch?v=abc123&t=12s&feature=share") == "https://youtube.com/watch?v=abc123"
    assert base.propre_url("exemple.fr") == "https://exemple.fr/"


def test_empreinte_texte():
    long_ = "Pose des hourdis en terre cuite : " * 10       # > 220 caractères utiles
    assert base.empreinte_texte(long_) == base.empreinte_texte(long_.upper() + " suite différente")
    assert base.empreinte_texte("court") == ""


def test_trouvailles_doublons_et_compteurs():
    tid = base.ajouter_trouvaille({"url": "https://www.exemple.fr/a?utm_source=x", "titre": "A", "texte": "t" * 200,
                                   "empreinte": base.empreinte_texte("t" * 200), "score": 60, "themes": ["pose"]})
    assert tid
    assert base.existe_url("https://exemple.fr/a")
    assert base.ajouter_trouvaille({"url": "https://exemple.fr/a", "titre": "B"}) is None
    assert base.texte_deja_vu(base.empreinte_texte("t" * 200)) == tid
    base.ajouter_trouvaille({"url": "https://exemple.fr/b", "titre": "B", "statut": "ecartee", "motif_ecart": "score"})
    c = base.compteurs()
    assert c["total"] == 2 and c["nouvelle"] == 1 and c["ecartee"] == 1
    assert base.lister_trouvailles(statut="actives")[0]["id"] == tid
    assert base.lister_trouvailles(theme="pose")[0]["id"] == tid
    assert base.themes_disponibles() == [("pose", 1)]
    base.modifier_trouvaille(tid, {"statut": "gardee", "themes": ["pose", "calcul"]})
    assert base.trouvaille(tid)["themes"] == ["pose", "calcul"]


def test_sources_et_rendement():
    s = base.ajouter_source("Rector", "https://www.rector.fr/", "site")
    assert base.ajouter_source("Rector bis", "https://www.rector.fr/", "site")["id"] == s["id"]
    base.compter_source(s["id"], examines=10, trouvees=3, gardees=3)
    base.compter_source(s["id"], echec="HTTP 403")
    s2 = base.source(s["id"])
    assert s2["nb_examines"] == 10 and s2["echecs"] == 1 and "403" in s2["dernier_echec"]
    base.compter_source(s["id"], examines=1)
    assert base.source(s["id"])["echecs"] == 0


def test_candidats_ecartes_ne_reviennent_pas():
    assert base.ajouter_candidat({"cle": "https://a.fr", "genre": "site", "nom": "A", "url": "https://a.fr", "note": 60})
    assert not base.ajouter_candidat({"cle": "https://a.fr", "genre": "site", "nom": "A", "url": "https://a.fr", "note": 80})
    assert base.candidats()[0]["note"] == 80
    base.decider_candidat("https://a.fr", "ecarte")
    assert not base.ajouter_candidat({"cle": "https://a.fr", "genre": "site", "nom": "A", "url": "https://a.fr", "note": 99})
    assert base.candidats() == []
    assert "https://a.fr" in base.cles_connues()
