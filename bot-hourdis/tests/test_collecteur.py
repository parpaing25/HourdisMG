from datetime import date

from bot import base, collecteur, rangement

TUTO = ("Comment poser un plancher hourdis sur poutrelles : vérifiez l'étaiement avant de couler la dalle "
        "de compression. Les hourdis terre cuite se posent à sec. Erreur à éviter : oublier le chaînage. "
        "Comptez 9 hourdis par m².") * 2


def _item(**extra):
    item = {"url": "https://www.exemple.fr/pose-hourdis?utm_source=x", "titre": "Pose plancher hourdis : le guide",
            "texte": TUTO, "resume": TUTO[:200], "genre": "article", "auteur": "Rector",
            "auteur_url": "https://exemple.fr", "publie_le": date(2026, 9, 1), "date_origine": "meta", "images": []}
    item.update(extra)
    return item


def test_traiter_range_puis_refuse_le_doublon(cfg):
    c = collecteur.Collecteur()
    source = {"id": 1, "nom": "Test"}
    statut, tid = c._traiter(_item(), source, cfg)
    assert statut == "nouvelle" and tid
    t = base.trouvaille(tid)
    assert t["url"] == "https://exemple.fr/pose-hourdis"
    assert t["dossier"].startswith("2026-09-01/") and t["post"]
    assert (rangement.racine(cfg) / t["dossier"] / "texte.txt").exists()
    assert c.etat["trouvees"] == 1 and c.etat["rangees"] == 1
    # Même adresse (variante) → doublon ; même texte ailleurs → doublon.
    assert c._traiter(_item(url="https://exemple.fr/pose-hourdis/"), source, cfg)[0] == "doublon"
    assert c._traiter(_item(url="https://autre.fr/copie"), source, cfg)[0] == "doublon"
    assert c.etat["ecartees_doublons"] == 2


def test_hors_sujet_est_ecarte_sans_dossier(cfg):
    c = collecteur.Collecteur()
    statut, tid = c._traiter(_item(url="https://x.fr/villa", titre="Villa à vendre",
                                   texte="A vendre villa en brique, terrain titré, 250 millions. Avendre."), {"id": 1, "nom": "T"}, cfg)
    assert statut == "ecartee"
    t = base.trouvaille(tid)
    assert t["statut"] == "ecartee" and t["dossier"] == "" and "immobili" in t["motif_ecart"]
    assert c.etat["ecartees_hors_sujet"] == 1


def test_trop_ancien_selon_le_genre(cfg):
    c = collecteur.Collecteur()
    cfg["jours_max_actualites"] = 30
    statut, _ = c._traiter(_item(url="https://x.fr/news", genre="actualite", publie_le=date(2024, 1, 1)), {"id": 1, "nom": "T"}, cfg)
    assert statut == "ecartee" and c.etat["ecartees_anciennes"] == 1
    # Un autre texte (le premier est déjà en base, écarté, et bloquerait par empreinte).
    autre = TUTO.replace("Comment poser", "Guide complet pour poser").replace("9 hourdis", "neuf hourdis")
    statut, _ = c._traiter(_item(url="https://x.fr/tuto", genre="article", texte=autre,
                                 publie_le=date(2016, 1, 1)), {"id": 1, "nom": "T"}, cfg)
    assert statut == "nouvelle"          # jours_max = 0 : un tuto ne vieillit pas


def test_sans_date_va_dans_date_inconnue(cfg):
    c = collecteur.Collecteur()
    statut, tid = c._traiter(_item(url="https://x.fr/sans-date", publie_le=None, date_origine=""), {"id": 1, "nom": "T"}, cfg)
    assert statut == "nouvelle"
    assert base.trouvaille(tid)["dossier"].startswith("date-inconnue/")


def test_analyser_source():
    a = collecteur.analyser_source
    assert a("pose hourdis")["genre"] == "recherche"
    assert a("https://www.youtube.com/@Rector/videos")["genre"] == "youtube_chaine"
    assert a("https://www.youtube.com/watch?v=abc")["genre"] == "import_video"
    assert a("https://youtu.be/abc")["genre"] == "import_video"
    assert a("https://www.facebook.com/groups/12345/")["genre"] == "groupe_fb"
    assert a("https://www.facebook.com/HourdisMadagascar")["genre"] == "page_fb"
    assert a("https://www.batirama.com/rss/actualites.xml")["genre"] == "flux"
    assert a("https://www.rector.fr/")["genre"] == "site"
    assert a("rector.fr")["genre"] == "site"
    assert a("https://www.rector.fr/conseils/poser-un-plancher-hourdis-en-5-etapes")["genre"] == "import_page"
    assert a("https://www.rector.fr/docs/guide-pose.pdf")["genre"] == "import_page"


def test_semer_une_seule_fois():
    assert collecteur.semer_sources_par_defaut() == len(collecteur.SOURCES_PAR_DEFAUT)
    assert collecteur.semer_sources_par_defaut() == 0
    base.supprimer_source(base.sources()[0]["id"])
    assert collecteur.semer_sources_par_defaut() == 0      # l'utilisateur a la main
