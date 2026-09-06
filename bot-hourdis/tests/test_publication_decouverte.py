from datetime import datetime, timedelta

from bot import base, planificateur, publication, sources_decouverte


def _gardee(url, auteur_url, genre="video", score=70, auteur="Chaîne X"):
    return base.ajouter_trouvaille({"url": url, "titre": "Pose hourdis", "texte": "x" * 200, "genre": genre,
                                    "auteur": auteur, "auteur_url": auteur_url, "score": score, "statut": "gardee"})


def test_publier_a_blanc_ne_touche_pas_meta(cfg):
    tid = _gardee("https://youtube.com/watch?v=1", "https://www.youtube.com/channel/UC1")
    r = publication.publier(tid, cfg, a_blanc=True)
    assert r["ok"] and r["a_blanc"] and "https://youtube.com/watch?v=1" in r["message"]
    assert base.publications()[0]["a_blanc"] == 1
    assert base.trouvaille(tid)["statut"] == "gardee"


def test_publication_eteinte_refuse(cfg):
    tid = _gardee("https://youtube.com/watch?v=2", "https://www.youtube.com/channel/UC1")
    r = publication.publier(tid, cfg)
    assert not r["ok"] and "éteinte" in r["erreur"]


def test_programmation_hors_fenetre(cfg):
    tid = _gardee("https://youtube.com/watch?v=3", "https://www.youtube.com/channel/UC1")
    r = publication.publier(tid, cfg, quand=datetime.now() + timedelta(minutes=2), a_blanc=True)
    assert not r["ok"] and "10 min" in r["erreur"]


def test_decouverte_propose_chaine_et_site(cfg):
    _gardee("https://youtube.com/watch?v=a", "https://www.youtube.com/channel/UC1")
    _gardee("https://youtube.com/watch?v=b", "https://www.youtube.com/channel/UC1")
    _gardee("https://youtube.com/watch?v=c", "https://www.youtube.com/channel/UC2")   # une seule : pas encore
    _gardee("https://www.batiweb.com/a1", "", genre="article", auteur="Batiweb")
    _gardee("https://www.batiweb.com/a2", "", genre="article", auteur="Batiweb")
    _gardee("https://www.rector.fr/a1", "", genre="article", score=80, auteur="Rector")
    base.ajouter_source("Rector", "https://rector.fr", "site")          # déjà suivi (sans www)
    r = sources_decouverte.decouvrir(cfg)
    cles = {c["cle"]: c for c in base.candidats()}
    assert "https://www.youtube.com/channel/UC1" in cles and "https://www.youtube.com/channel/UC2" not in cles
    assert "https://batiweb.com" in cles and "https://rector.fr" not in cles
    assert r["nouveaux"] == 2
    assert cles["https://batiweb.com"]["note"] >= 55


def test_creneau_du():
    heures = ["08:30", "18:30"]
    assert planificateur.creneau_du(heures, datetime(2026, 9, 6, 7, 0)) == ""
    assert planificateur.creneau_du(heures, datetime(2026, 9, 6, 9, 0)) == "08:30"
    assert planificateur.creneau_du(heures, datetime(2026, 9, 6, 23, 0)) == "18:30"
    assert planificateur.prochain_passage(heures, False) == ""
