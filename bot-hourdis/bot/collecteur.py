"""La tournée : chaque source à son tour, chaque trouvaille notée, rangée, datée.

Ordre d'une tournée, et pourquoi :

  1. LE WEB D'ABORD — flux, recherches, YouTube, sites. Rien de tout ça n'ouvre
     Chromium : ~100 Mo, pas de session Facebook à entretenir. C'est la partie
     qui tourne même quand la machine est chargée ou qu'une session Claude est
     ouverte (règle du 03/09/2026 : c'est Chromium qui mange la RAM).
  2. FACEBOOK ENSUITE, petit, derrière trois garde-fous : mémoire disponible,
     verrou navigateur partagé avec les trois bots frères (~/bots-hub), et pas
     de tournée AUTOMATIQUE pendant une session Claude.
  3. LA RELECTURE IA en dernier, facultative, plafonnée.

Chaque trouvaille passe par `_traiter` — un seul chemin, quel que soit le genre :
adresse canonique, empreinte du texte (doublons), score, date, dossier. Ce qui
est écarté est COMPTÉ et dit : « 0 trouvaille » sans explication est indiscernable
d'une source tarie.
"""
from __future__ import annotations

import re
import threading
import uuid
from datetime import date
from urllib.parse import urlsplit

import requests

from . import base, dates_web, facebook, flux, rangement, redaction, score, toile, youtube
from . import analyse_llm, session_claude, verrou_navigateur
from .config import NOM_BOT, charger

SOURCES_PAR_DEFAUT = [
    # (nom, url, genre, requête)
    ("Recherche : pose plancher hourdis", "", "recherche_web", "pose plancher hourdis poutrelles"),
    ("Recherche : conseils plancher hourdis", "", "recherche_web", "plancher hourdis conseils erreurs"),
    ("Recherche : brique terre cuite", "", "recherche_web", "brique terre cuite construction technique"),
    ("Recherche : tuile terre cuite", "", "recherche_web", "tuile terre cuite pose toiture conseils"),
    ("Recherche : hourdis Madagascar", "", "recherche_web", "hourdis Madagascar"),
    ("YouTube : pose hourdis", "", "youtube_recherche", "pose hourdis plancher poutrelles"),
    ("YouTube : plancher hourdis étapes", "", "youtube_recherche", "plancher hourdis étapes chantier"),
    ("YouTube : brique creuse", "", "youtube_recherche", "monter mur brique creuse terre cuite"),
    ("YouTube : tuile terre cuite", "", "youtube_recherche", "pose tuile terre cuite toiture"),
    ("YouTube : hourdis Madagascar", "", "youtube_recherche", "hourdis Madagascar trano"),
    ("Batirama", "https://www.batirama.com/", "site", ""),
    ("Wienerberger France", "https://www.wienerberger.fr/", "site", ""),
    ("Bouyer Leroux", "https://www.bouyer-leroux.com/", "site", ""),
    ("Terreal", "https://www.terreal.com/", "site", ""),
    ("Rector (poutrelles, hourdis)", "https://www.rector.fr/", "site", ""),
    ("FFTB — Fédération des tuiles et briques", "https://www.fftb.org/", "site", ""),
    ("bio'bric", "https://www.biobric.com/", "site", ""),
]


def semer_sources_par_defaut() -> int:
    """Au premier démarrage seulement : un jeu de sources qui donne tout de suite."""
    if base.lire_etat("sources_semees") == "1":
        return 0
    n = 0
    if not base.sources():
        for nom, url, genre, requete in SOURCES_PAR_DEFAUT:
            base.ajouter_source(nom, url, genre, requete)
            n += 1
    base.ecrire_etat("sources_semees", "1")
    if n:
        base.logguer(f"{n} sources semées au premier démarrage — modifiez-les dans l'onglet Sources.", "info")
    return n


def analyser_source(entree: str) -> dict:
    """Ce qu'on a collé -> {nom, url, genre, requete}. `genre` peut valoir 'recherche'
    (à décliner en web + YouTube) ou 'import_video' / 'import_page' (une adresse unique)."""
    e = (entree or "").strip()
    if not e:
        raise ValueError("Rien à ajouter.")
    if not e.startswith(("http://", "https://")) and not re.match(r"^[\w.-]+\.[a-z]{2,}(/|$)", e, re.I):
        return {"nom": f"Recherche : {e[:60]}", "url": "", "genre": "recherche", "requete": e}
    url = e if e.startswith("http") else "https://" + e
    d = urlsplit(url)
    hote = d.netloc.lower().replace("www.", "")
    chemin = d.path.lower()
    if hote in ("youtube.com", "m.youtube.com", "youtu.be"):
        if chemin == "/watch" or hote == "youtu.be" or chemin.startswith("/shorts/"):
            return {"nom": "Vidéo YouTube", "url": url, "genre": "import_video", "requete": ""}
        if "feeds/videos.xml" in chemin:
            return {"nom": "Chaîne YouTube", "url": url, "genre": "youtube_chaine", "requete": ""}
        if chemin.startswith(("/@", "/channel/", "/c/", "/user/")):
            nom = chemin.split("/")[1].lstrip("@") if chemin.count("/") >= 1 else hote
            return {"nom": f"Chaîne YouTube : {nom}", "url": url.split("/videos")[0].rstrip("/"),
                    "genre": "youtube_chaine", "requete": ""}
        return {"nom": "YouTube", "url": url, "genre": "import_page", "requete": ""}
    if hote in ("facebook.com", "m.facebook.com", "fb.com", "web.facebook.com"):
        if "/groups/" in chemin:
            nom = chemin.split("/groups/")[1].split("/")[0]
            return {"nom": f"Groupe FB : {nom}", "url": f"https://www.facebook.com/groups/{nom}",
                    "genre": "groupe_fb", "requete": ""}
        segments = [s for s in chemin.split("/") if s]
        if segments and segments[0] not in ("posts", "photo", "watch", "reel", "share", "story.php"):
            nom = segments[0]
            return {"nom": f"Page FB : {nom}", "url": f"https://www.facebook.com/{nom}",
                    "genre": "page_fb", "requete": ""}
        return {"nom": "Publication Facebook", "url": url, "genre": "import_page", "requete": ""}
    if re.search(r"\.(xml|rss|atom)$|/feed/?$|/rss/?$|/feeds?/", chemin) or \
            re.search(r"(^|&)(feed|format)=(rss|atom|rss2)?", d.query.lower()):
        return {"nom": f"Flux : {hote}", "url": url, "genre": "flux", "requete": ""}
    if chemin.endswith(".pdf"):
        return {"nom": f"PDF : {hote}", "url": url, "genre": "import_page", "requete": ""}
    # Une adresse profonde (un article précis) s'importe ; une racine ou une
    # rubrique devient un site à explorer.
    if chemin.count("/") >= 2 and len(chemin) > 25 and not chemin.endswith("/"):
        return {"nom": f"Page : {hote}", "url": url, "genre": "import_page", "requete": ""}
    return {"nom": hote, "url": url, "genre": "site", "requete": ""}


class Collecteur:
    """Une tournée à la fois (verrou de classe). L'état est lu par /api/etat."""

    _en_cours = threading.Lock()

    def __init__(self) -> None:
        self.stop = threading.Event()
        self.etat = self._etat_vierge()
        self._compteurs = threading.Lock()
        self.session = requests.Session()
        self._budget = {"details": 0, "transcriptions": 0}
        self.config = charger()

    @staticmethod
    def _etat_vierge() -> dict:
        return {"actif": False, "source": None, "examines": 0, "trouvees": 0, "rangees": 0,
                "ecartees_hors_sujet": 0, "ecartees_score": 0, "ecartees_doublons": 0,
                "ecartees_anciennes": 0, "relues_ia": 0, "debut": "", "fin": "",
                "automatique": False, "facebook": ""}

    def _compter(self, cle: str, n: int = 1) -> None:
        with self._compteurs:
            self.etat[cle] = self.etat.get(cle, 0) + n

    # ── Entrées ──────────────────────────────────────────────────────────────
    def collecter(self, sources: list[dict] | None = None, reglages: dict | None = None,
                  automatique: bool = False) -> dict:
        if not Collecteur._en_cours.acquire(blocking=False):
            return {"erreur": "Une collecte est déjà en cours."}
        try:
            return self._collecter(sources, reglages, automatique)
        finally:
            self.etat["actif"] = False
            self.etat["fin"] = base.maintenant()
            Collecteur._en_cours.release()

    def collecter_une(self, sid: int) -> dict:
        source = base.source(sid)
        if not source:
            return {"erreur": "source inconnue"}
        return self.collecter([source])

    def importer(self, url: str) -> dict:
        """Avale UNE adresse (page, PDF ou vidéo) hors de toute source."""
        cfg = self.config = charger()
        self._budget = {"details": 0, "transcriptions": 0}
        analyse = analyser_source(url)
        pseudo = {"id": None, "nom": "Import manuel", "genre": analyse["genre"]}
        if analyse["genre"] == "import_video":
            item = self._item_video({"url": analyse["url"], "video_id": "", "titre": "", "resume": ""},
                                    cfg, forcer_details=True)
        elif analyse["url"].lower().split("?")[0].endswith(".pdf"):
            item = self._item_pdf(analyse["url"], "", cfg)
        else:
            item = self._item_page(analyse["url"], cfg)
        if not item:
            return {"erreur": "adresse illisible"}
        statut, tid = self._traiter(item, pseudo, cfg)
        return {"statut": statut, "id": tid}

    # ── La tournée ───────────────────────────────────────────────────────────
    def _collecter(self, sources, reglages, automatique) -> dict:
        self.config = charger()
        if reglages:
            self.config.update(reglages)
        cfg = self.config
        self.stop.clear()
        self.etat = self._etat_vierge()
        self.etat.update(actif=True, debut=base.maintenant(), automatique=automatique)
        self._budget = {"details": 0, "transcriptions": 0}
        sources = sources or base.sources(actives_seulement=True)
        if not sources:
            base.logguer("Aucune source active — ajoutez une recherche, un site, une chaîne "
                         "YouTube ou un flux dans l'onglet Sources.", "avert")
            return self.etat

        web = [s for s in sources if s["genre"] not in ("page_fb", "groupe_fb")]
        fb = [s for s in sources if s["genre"] in ("page_fb", "groupe_fb")]
        par_genre: dict[str, int] = {}
        for s in sources:
            par_genre[s["genre"]] = par_genre.get(s["genre"], 0) + 1
        base.logguer("Tournée lancée : " + ", ".join(f"{n} {g}" for g, n in sorted(par_genre.items()))
                     + (" (automatique)" if automatique else ""), "info")

        for rang, source in enumerate(web):
            if self.stop.is_set():
                break
            self.etat["source"] = f"{source['nom']} ({rang + 1}/{len(web)})"
            examines = trouvees = gardees = 0
            try:
                examines, trouvees, gardees = self._collecter_source(source, cfg)
                base.compter_source(source["id"], examines, trouvees, gardees)
            except toile.requests.RequestException as e:
                base.compter_source(source["id"], echec=str(e))
                base.logguer(f"« {source['nom']} » : réseau — {str(e)[:120]}", "erreur")
            except Exception as e:                            # noqa: BLE001
                base.compter_source(source["id"], echec=f"{type(e).__name__}: {e}")
                base.logguer(f"« {source['nom']} » : {type(e).__name__}: {str(e)[:160]}", "erreur")

        if fb and cfg.get("facebook_actif", True) and not self.stop.is_set():
            self._tournee_facebook(fb, cfg, automatique)

        if cfg.get("llm_actif") and cfg.get("llm_relire_auto") and not self.stop.is_set():
            self.etat["source"] = "relecture par le modèle"
            self._relire_auto(cfg)

        self.etat["source"] = None
        e = self.etat
        base.logguer(
            f"Tournée terminée : {e['examines']} examinée(s), {e['trouvees']} gardable(s), "
            f"{e['ecartees_hors_sujet']} hors sujet, {e['ecartees_score']} sous le score, "
            f"{e['ecartees_doublons']} doublon(s), {e['ecartees_anciennes']} trop ancienne(s)"
            + (f", {e['relues_ia']} relue(s) par le modèle" if e["relues_ia"] else "") + ".",
            "succes" if e["trouvees"] else "info")
        return self.etat

    def _collecter_source(self, source: dict, cfg: dict) -> tuple[int, int, int]:
        genre = source["genre"]
        if genre == "recherche_web":
            return self._source_recherche_web(source, cfg)
        if genre == "youtube_recherche":
            return self._source_youtube_recherche(source, cfg)
        if genre == "youtube_chaine":
            return self._source_youtube_chaine(source, cfg)
        if genre == "flux":
            return self._source_flux(source, cfg)
        if genre == "site":
            return self._source_site(source, cfg)
        base.logguer(f"Genre de source inconnu : {genre}", "avert")
        return 0, 0, 0

    # ── Sources web ──────────────────────────────────────────────────────────
    def _source_recherche_web(self, source, cfg) -> tuple[int, int, int]:
        entrees, raisons = flux.entrees_recherche_web(
            source["requete"], "fr", int(cfg.get("resultats_par_recherche_web", 15)), self.session)
        for r in raisons:
            base.logguer(f"« {source['nom']} » : {r}", "avert")
        if not entrees and raisons:
            raise RuntimeError(" ; ".join(raisons))
        examines = trouvees = gardees = 0
        for e in entrees[:int(cfg.get("resultats_par_recherche_web", 15)) * 2]:
            if self.stop.is_set() or examines >= int(cfg.get("resultats_par_recherche_web", 15)):
                break
            url = flux.resoudre_lien_google(e["url"], self.session) if "news.google.com" in e["url"] \
                else e["url"]
            if base.existe_url(url):
                self._compter("ecartees_doublons")
                continue
            # Le titre seul dit déjà beaucoup : une actualité « Lego brique »
            # ne mérite pas une page chargée.
            if score.pre_note(e["titre"], e.get("resume", ""), cfg) < 12:
                self._compter("ecartees_hors_sujet")
                self._compter("examines")
                examines += 1
                continue
            examines += 1
            item = self._item_page(url, cfg, e) if "news.google.com" not in url else None
            if not item:
                item = {"url": url, "titre": e["titre"], "texte": e.get("resume", ""),
                        "resume": e.get("resume", ""), "genre": "actualite",
                        "auteur": e.get("source") or e.get("auteur", ""), "auteur_url": "",
                        "publie_le": e.get("publie_le"), "date_origine": "flux" if e.get("publie_le") else "",
                        "images": [e["image"]] if e.get("image") else []}
            if e.get("moteur") == "Google Actualités":
                item["genre"] = "actualite"
            statut, _ = self._traiter(item, source, cfg)
            trouvees += statut in ("nouvelle",)
            gardees += statut in ("nouvelle",)
        return examines, trouvees, gardees

    def _source_flux(self, source, cfg) -> tuple[int, int, int]:
        entrees, raison = flux.lire_flux(source["url"], self.session)
        if raison:
            raise RuntimeError(toile.LIBELLES_ECHEC.get(raison, raison))
        examines = trouvees = 0
        for e in entrees[:int(cfg.get("articles_par_flux", 20))]:
            if self.stop.is_set():
                break
            if base.existe_url(e["url"]):
                self._compter("ecartees_doublons")
                continue
            examines += 1
            if e.get("video_id"):
                item = self._item_video(e, cfg)
            else:
                item = self._item_page(e["url"], cfg, e)
            if not item:
                continue
            statut, _ = self._traiter(item, source, cfg)
            trouvees += statut == "nouvelle"
        return examines, trouvees, trouvees

    def _source_youtube_recherche(self, source, cfg) -> tuple[int, int, int]:
        fiches, erreur = youtube.rechercher(source["requete"], int(cfg.get("videos_par_recherche", 12)))
        if erreur and not fiches:
            raise RuntimeError(erreur)
        return self._traiter_videos(fiches, source, cfg)

    def _source_youtube_chaine(self, source, cfg) -> tuple[int, int, int]:
        url = source["url"]
        if "feeds/videos.xml" not in url:
            cid, nom, _ = youtube.chaine_id_de(url)
            if not cid:
                raise RuntimeError("identifiant de chaîne introuvable (yt-dlp)")
            url = flux.flux_chaine_youtube(cid)
            base.modifier_source(source["id"], url=url,
                                 nom=source["nom"] if source["nom"] else f"Chaîne : {nom}")
            base.logguer(f"Chaîne « {source['nom']} » : flux Atom retrouvé ({cid}).", "info")
        entrees, raison = flux.lire_flux(url, self.session)
        if raison:
            raise RuntimeError(toile.LIBELLES_ECHEC.get(raison, raison))
        fiches = [{"video_id": e["video_id"], "url": e["url"], "titre": e["titre"],
                   "resume": e["resume"], "publie_le": e["publie_le"], "auteur": e["auteur"],
                   "auteur_url": e.get("auteur_url", ""), "chaine_id": e["chaine_id"],
                   "image": e["image"], "vues": e["vues"], "duree_s": None, "en_direct": False}
                  for e in entrees]
        return self._traiter_videos(fiches, source, cfg)

    def _traiter_videos(self, fiches: list[dict], source, cfg) -> tuple[int, int, int]:
        examines = trouvees = 0
        for f in fiches:
            if self.stop.is_set():
                break
            if f.get("en_direct") or not f.get("url"):
                continue
            if base.existe_url(f["url"]):
                self._compter("ecartees_doublons")
                continue
            examines += 1
            if score.pre_note(f["titre"], f.get("resume", ""), cfg) < 15:
                self._compter("examines")
                self._compter("ecartees_hors_sujet")
                continue
            item = self._item_video(f, cfg)
            if not item:
                continue
            statut, _ = self._traiter(item, source, cfg)
            trouvees += statut == "nouvelle"
        return examines, trouvees, trouvees

    def _source_site(self, source, cfg) -> tuple[int, int, int]:
        budget = int(cfg.get("pages_par_site", 10))
        exploration = toile.explorer_site(source["url"], budget, set(), self.session)
        if exploration["refuse"]:
            raise RuntimeError(exploration["refuse"])
        examines = trouvees = requetes = 0
        file = list(exploration["articles"])
        vues: set[str] = set(file)
        # 🔴 UNE RUBRIQUE N'EST PAS UN ARTICLE. Mesuré à la première tournée
        #   (Batirama, 06/09/2026) : « Technique et mise en œuvre 4-1 » — une
        #   liste de quatre-vingts accroches, 28 000 caractères pleins de mots
        #   du métier — est entrée avec 82/100 et une date lue au hasard dans
        #   la liste. Une LISTE ne se garde pas : on suit ses liens
        #   (`toile.ressemble_a_une_liste`, critère mesuré, pas deviné).
        # Le budget compte les REQUÊTES : `budget` articles lus au plus, et
        # jusqu'à deux fois plus de pages ouvertes au total (listes, échecs).
        while file and examines < budget and requetes < 3 * budget and not self.stop.is_set():
            url = file.pop(0)
            if base.existe_url(url):
                continue
            requetes += 1
            page = toile.lire_page(url, self.session)
            if not page["texte"]:
                continue
            liens_articles = [(n, l) for n, l in toile.pages_a_visiter(page["liens"], page["url"], vues) if n >= 12]
            if toile.ressemble_a_une_liste(page, len(liens_articles)):
                ajoutes = 0
                for lien in toile.trier_pour_suivre(liens_articles):
                    if ajoutes >= budget * 2:
                        break
                    if lien not in vues and not base.existe_url(lien):
                        vues.add(lien)
                        file.insert(ajoutes, lien)        # devant les autres listes en attente
                        ajoutes += 1
                base.logguer(f"Rubrique suivie ({len(liens_articles)} liens, {ajoutes} articles retenus) : "
                             f"{url[:80]}", "info")
                continue
            examines += 1
            item = self._item_page_lue(page, url, cfg)
            if not item:
                continue
            statut, _ = self._traiter(item, source, cfg)
            trouvees += statut == "nouvelle"
        if cfg.get("lire_les_pdf", True):
            for url, libelle in exploration["pdf"][:4]:
                if self.stop.is_set() or base.existe_url(url):
                    continue
                examines += 1
                item = self._item_pdf(url, libelle, cfg)
                if item:
                    statut, _ = self._traiter(item, source, cfg)
                    trouvees += statut == "nouvelle"
        return examines, trouvees, trouvees

    # ── Fabriquer un « item » commun ─────────────────────────────────────────
    def _item_page(self, url: str, cfg: dict, entree: dict | None = None) -> dict | None:
        if url.lower().split("?")[0].endswith(".pdf"):
            return self._item_pdf(url, (entree or {}).get("titre", ""), cfg)
        return self._item_page_lue(toile.lire_page(url, self.session), url, cfg, entree)

    def _item_page_lue(self, page: dict, url: str, cfg: dict, entree: dict | None = None) -> dict | None:
        entree = entree or {}
        if not page["texte"] and not entree.get("resume"):
            base.logguer(f"Page illisible ({page['refuse']}) : {url[:90]}", "info")
            return None
        quand, origine = None, ""
        if entree.get("publie_le"):
            quand, origine = entree["publie_le"], "flux"
        if quand is None and page["html"]:
            quand, origine = dates_web.date_de_page(page["html"], page["url"], page["texte"])
        images = list(page["images"])
        if entree.get("image"):
            images.insert(0, entree["image"])
        return {
            "url": page["url"] or url,
            "titre": (entree.get("titre") or page["titre"] or url)[:200],
            "texte": page["texte"] or entree.get("resume", ""),
            "resume": (page["description"] or entree.get("resume", ""))[:1500],
            "genre": "article",
            "auteur": entree.get("source") or entree.get("auteur") or _nom_de_site(page["url"] or url),
            "auteur_url": f"https://{urlsplit(page['url'] or url).netloc}",
            "publie_le": quand, "date_origine": origine, "images": images,
        }

    def _item_pdf(self, url: str, libelle: str, cfg: dict) -> dict | None:
        octets, raison = toile.recuperer_pdf(url, self.session)
        if not octets:
            base.logguer(f"PDF non lu ({raison}) : {url[:90]}", "info")
            return None
        texte, titre = toile.texte_du_pdf(octets, int(cfg.get("pdf_pages_max", 12)))
        if len(texte) < 200:
            return None
        quand = dates_web.date_dans_texte(texte[:3000])
        origine = "texte" if quand else ""
        if quand is None:
            quand, origine = dates_web.date_de_page("", url, "")
        nom = titre or libelle or url.rsplit("/", 1)[-1].replace("-", " ").replace("_", " ")[:-4]
        return {"url": url, "titre": nom[:200], "texte": texte, "resume": texte[:600],
                "genre": "pdf", "auteur": _nom_de_site(url),
                "auteur_url": f"https://{urlsplit(url).netloc}", "publie_le": quand,
                "date_origine": origine, "images": []}

    def _item_video(self, f: dict, cfg: dict, forcer_details: bool = False) -> dict | None:
        """Une fiche sommaire -> un item complet, dans les plafonds de la tournée."""
        fiche = dict(f)
        manque_date = fiche.get("publie_le") is None
        if (forcer_details or manque_date or not fiche.get("resume")) and \
                (forcer_details or self._budget["details"] < int(cfg.get("videos_details_max", 15))):
            self._budget["details"] += 1
            complete, erreur = youtube.fiche(fiche.get("url") or fiche.get("video_id", ""))
            if complete:
                for cle, valeur in complete.items():
                    if valeur not in (None, "", [], 0) or cle not in fiche:
                        fiche[cle] = valeur
            elif erreur:
                base.logguer(f"Fiche YouTube non lue : {erreur}", "info")
        if not fiche.get("titre"):
            return None
        texte = (fiche.get("resume") or "").strip()
        if fiche.get("chapitres"):
            texte += "\n\nCHAPITRES\n" + "\n".join(f"- {c}" for c in fiche["chapitres"])
        transcription = ""
        if cfg.get("transcrire_videos", True) and fiche.get("video_id") and \
                self._budget["transcriptions"] < int(cfg.get("transcriptions_max", 8)) and \
                score.pre_note(fiche["titre"], texte, cfg) >= 25:
            self._budget["transcriptions"] += 1
            transcription, langue_st = youtube.sous_titres(fiche["video_id"])
            if transcription:
                texte += f"\n\nTRANSCRIPTION ({langue_st or '?'})\n" + transcription
        return {
            "url": fiche["url"], "titre": fiche["titre"][:200], "texte": texte,
            "resume": (fiche.get("resume") or "")[:1500], "genre": "video",
            "auteur": fiche.get("auteur", ""), "auteur_url": fiche.get("auteur_url", ""),
            "publie_le": fiche.get("publie_le"),
            "date_origine": "youtube" if fiche.get("publie_le") else "",
            "images": [fiche["image"]] if fiche.get("image") else [],
            "duree_s": fiche.get("duree_s"), "vues": fiche.get("vues"),
            "langue": (fiche.get("langue") or "")[:2],
        }

    # ── Facebook ─────────────────────────────────────────────────────────────
    def _tournee_facebook(self, fb: list[dict], cfg: dict, automatique: bool) -> None:
        if automatique:
            session = session_claude.active()
            if session:
                self.etat["facebook"] = "suspendue (session Claude)"
                base.logguer(f"Partie Facebook suspendue — {session} (règle du 03/09). "
                             "La partie web a tourné normalement.", "info")
                return
        if not facebook.session_enregistree():
            self.etat["facebook"] = "pas de session"
            base.logguer("Partie Facebook sautée : aucun compte connecté (onglet Réglages).", "avert")
            return
        libre = facebook.memoire_libre_mo()
        seuil = int(cfg.get("memoire_mini_mo", 900))
        if libre is not None and libre < seuil:
            self.etat["facebook"] = f"sautée ({libre} Mo libres)"
            base.logguer(f"Partie Facebook sautée : {libre} Mo de mémoire disponible, il en faut "
                         f"{seuil} pour Chromium.", "erreur")
            return
        with verrou_navigateur.verrou_navigateur(NOM_BOT) as pris:
            if not pris:
                occupant = verrou_navigateur.qui() or "un autre bot"
                self.etat["facebook"] = f"sautée ({occupant} a le navigateur)"
                base.logguer(f"Partie Facebook sautée : « {occupant} » occupe le navigateur. "
                             "Elle repassera au prochain créneau.", "avert")
                return
            self.etat["facebook"] = "en cours"
            self.etat["source"] = f"Facebook ({len(fb)} source(s))"

            def sur_publication(pub: dict, source: dict) -> bool:
                if not pub.get("permalien"):
                    return False
                if base.existe_url(pub["permalien"]):
                    self._compter("ecartees_doublons")
                    return False
                item = {"url": pub["permalien"], "titre": (pub["texte"].split("\n")[0] or "Publication")[:120],
                        "texte": pub["texte"], "resume": pub["texte"][:600], "genre": "post_fb",
                        "auteur": pub.get("auteur") or source["nom"], "auteur_url": source["url"],
                        "publie_le": pub.get("publie_le"),
                        "date_origine": "facebook" if pub.get("publie_le") else "",
                        "images": pub.get("images") or []}
                statut, _ = self._traiter(item, source, cfg)
                return statut == "nouvelle"

            def sur_source_finie(source, examines, retenues, erreur):
                if erreur:
                    base.compter_source(source["id"], echec=erreur)
                else:
                    base.compter_source(source["id"], examines, retenues, retenues)

            facebook.parcourir_sources(fb, cfg, self.stop, sur_publication, sur_source_finie,
                                       lambda: verrou_navigateur.toucher(NOM_BOT))
            self.etat["facebook"] = "terminée"

    # ── Le chemin unique ─────────────────────────────────────────────────────
    def _traiter(self, item: dict, source: dict, cfg: dict) -> tuple[str, str | None]:
        """Rend (statut, id). Statuts : nouvelle | ecartee | doublon | ''."""
        url = base.propre_url(item.get("url", ""))
        if not url:
            return "", None
        self._compter("examines")
        if base.existe_url(url):
            self._compter("ecartees_doublons")
            return "doublon", None
        texte = (item.get("texte") or item.get("resume") or "").strip()
        empreinte = base.empreinte_texte(texte)
        if empreinte and base.texte_deja_vu(empreinte):
            self._compter("ecartees_doublons")
            base.logguer(f"Texte déjà collecté mot pour mot : « {item.get('titre', '')[:60]} »", "info")
            return "doublon", None

        genre = item.get("genre", "article")
        publie_le = item.get("publie_le")
        if isinstance(publie_le, str):
            publie_le = dates_web.lire_iso(publie_le)
        langue = item.get("langue") or ""
        note = score.noter(item.get("titre", ""), texte, genre, langue, publie_le, cfg)
        statut, motif = "nouvelle", ""
        if note["hors_sujet"]:
            statut, motif = "ecartee", note["raison"]
            self._compter("ecartees_hors_sujet")
        elif note["score"] < int(cfg.get("score_min", 35)):
            statut, motif = "ecartee", f"score {note['score']} sous le minimum {cfg.get('score_min', 35)}"
            self._compter("ecartees_score")
        if statut == "nouvelle" and publie_le:
            jours_max = int(cfg.get("jours_max_actualites", 540) if genre == "actualite"
                            else cfg.get("jours_max", 0))
            age = (date.today() - publie_le).days
            if publie_le.year < int(cfg.get("annee_minimum", 2012)):
                statut, motif = "ecartee", f"publiée en {publie_le.year}, avant {cfg.get('annee_minimum')}"
                self._compter("ecartees_anciennes")
            elif jours_max > 0 and age > jours_max:
                statut, motif = "ecartee", f"vieille de {age} jours (maximum {jours_max})"
                self._compter("ecartees_anciennes")
        if statut == "ecartee" and not cfg.get("garder_les_ecartees", True):
            return "ecartee", None

        t = {
            "id": uuid.uuid4().hex[:12], "url": url, "empreinte": empreinte,
            "titre": (item.get("titre") or url)[:200], "texte": texte[:150_000],
            # Le résumé affiché est NETTOYÉ (liens, appels à s'abonner) ; le texte
            # brut, lui, reste intégral dans texte.txt.
            "resume": redaction.resume_propre(item.get("resume") or texte, 600), "genre": genre,
            "source_id": source.get("id"), "source_nom": source.get("nom", ""),
            "auteur": (item.get("auteur") or "")[:120], "auteur_url": item.get("auteur_url", ""),
            "langue": note["langue"], "publie_le": publie_le.isoformat() if publie_le else "",
            "date_origine": item.get("date_origine", "") if publie_le else "",
            "score": note["score"], "themes": note["themes"], "motifs": note["motifs"],
            "statut": statut, "motif_ecart": motif, "images": [],
            "duree_s": item.get("duree_s"), "vues": item.get("vues"),
        }
        if statut == "nouvelle":
            t["post"] = redaction.rediger(t, cfg)
            try:
                t["dossier"] = rangement.ranger(t, cfg, item.get("images") or [])
            except OSError as e:
                base.logguer(f"Dossier non écrit ({e}) : « {t['titre'][:60]} »", "erreur")
                t["dossier"] = ""
        tid = base.ajouter_trouvaille(t)
        if tid is None:
            self._compter("ecartees_doublons")
            if t.get("dossier"):
                rangement.supprimer(t["dossier"], cfg)
            return "doublon", None
        if statut == "nouvelle":
            self._compter("trouvees")
            if t.get("dossier"):
                self._compter("rangees")
            base.logguer(f"Gardée ({t['score']}/100, {rangement.LIBELLES_GENRE.get(genre, genre)}"
                         f"{', ' + t['publie_le'] if t['publie_le'] else ', date inconnue'}) : "
                         f"« {t['titre'][:70]} »", "succes")
        return statut, tid

    # ── Relecture automatique ────────────────────────────────────────────────
    def _relire_auto(self, cfg: dict) -> None:
        a_relire = base.trouvailles_a_relire(int(cfg.get("llm_score_min_pour_relire", 50)),
                                             int(cfg.get("llm_relire_max", 6)))
        for t in a_relire:
            if self.stop.is_set():
                break
            try:
                lecture = analyse_llm.relire(t, cfg)
            except analyse_llm.LLMIndisponible as e:
                base.logguer(f"Relecture arrêtée : {e}", "avert")
                break
            analyse_llm.appliquer(t["id"], lecture, cfg)
            self._compter("relues_ia")


def _nom_de_site(url: str) -> str:
    hote = urlsplit(url).netloc.lower()
    return hote[4:] if hote.startswith("www.") else hote


collecteur = Collecteur()
