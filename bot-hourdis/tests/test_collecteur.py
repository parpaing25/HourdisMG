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


ANNONCE = ("A vendre villa F5 à Ambohimanga, murs en brique, toit en tuile, terrain titré borné de "
           "500 m². Prix 250 millions Ariary à débattre, contact 034 00 000 00. Avendre urgent, "
           "belle vue, quartier calme, proche école et marché. Visite sur rendez-vous uniquement. ") * 3


def test_hors_sujet_est_ecarte_sans_dossier(cfg):
    c = collecteur.Collecteur()
    statut, tid = c._traiter(_item(url="https://x.fr/villa", titre="Villa à vendre", texte=ANNONCE),
                             {"id": 1, "nom": "T"}, cfg)
    assert statut == "ecartee"
    t = base.trouvaille(tid)
    assert t["statut"] == "ecartee" and t["dossier"] == "" and "immobili" in t["motif_ecart"]
    assert c.etat["ecartees_hors_sujet"] == 1


def test_mur_anti_robot_n_entre_pas_en_base(cfg):
    """🔴 Un serveur qui rend 200 n'a pas forcément servi son contenu.

    Le 06/09/2026, journals.openedition.org a servi une page de blocage
    (« anubis n'a pas réussi à charger son code javascript ») et le bot en a
    fait une fiche complète de 529 caractères."""
    c = collecteur.Collecteur()
    mur = ("Chargement… anubis n'a pas réussi à charger son code javascript. Le serveur est "
           "peut-être surchargé. Veuillez recharger la page pour réessayer.")
    statut, tid = c._traiter(_item(url="https://x.fr/mur", titre="Les tuiles au Moyen Âge", texte=mur),
                             {"id": 1, "nom": "T"}, cfg)
    assert statut == "sans_contenu" and tid is None
    assert base.lister_trouvailles(statut="") == []
    assert c.etat["ecartees_sans_contenu"] == 1


def test_page_presque_vide_refusee_mais_pas_une_video(cfg):
    c = collecteur.Collecteur()
    assert c._traiter(_item(url="https://x.fr/court", texte="Hourdis."), {"id": 1, "nom": "T"}, cfg)[0] == "sans_contenu"
    # Une vidéo n'a pas de corps de texte : elle n'est jamais refusée pour ça.
    statut, _ = c._traiter(_item(url="https://youtube.com/watch?v=zz", genre="video",
                                 titre="Pose d'un plancher hourdis", texte="Les étapes."),
                           {"id": 1, "nom": "T"}, cfg)
    assert statut == "nouvelle"


def test_trop_ancien_selon_le_genre(cfg):
    c = collecteur.Collecteur()
    cfg["jours_max_actualites"] = 30
    statut, _ = c._traiter(_item(url="https://x.fr/news", genre="actualite", publie_le=date(2024, 1, 1)), {"id": 1, "nom": "T"}, cfg)
    assert statut == "ecartee" and c.etat["ecartees_anciennes"] == 1
    # 🔴 Une TECHNIQUE ne se périme pas : « La liste des DTU à jour » (88/100),
    #    publiée en 2011, était jetée par annee_minimum avant le 06/09/2026.
    autre = TUTO.replace("Comment poser", "Tout savoir sur la pose d'")
    statut, tid = c._traiter(_item(url="https://x.fr/dtu", genre="article", texte=autre,
                                   publie_le=date(2011, 3, 10)), {"id": 1, "nom": "T"}, cfg)
    assert statut == "nouvelle", "un contenu technique de 2011 doit rester"
    assert base.trouvaille(tid)["dossier"].startswith("2011-03-10/")
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
