"""Serveur local du bot : API JSON + interface web, sur 127.0.0.1:8761.

Rien n'est exposé au réseau. Les tâches longues (tournée, connexion Facebook,
relecture, découverte) partent dans un fil et rendent la main ; l'interface suit
l'avancement par /api/etat, interrogé toutes les trois secondes.

Deux tâches ne s'excluent que si elles se disputent la même RESSOURCE (leçon
d'AKORA) : une relecture par le modèle ne bloque pas une tournée, mais deux
tournées ne partent pas ensemble.
"""
from __future__ import annotations

import csv
import io
import threading
import webbrowser
from datetime import datetime
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse, StreamingResponse
from pydantic import BaseModel

from . import analyse_llm, base, facebook, publication, rangement, redaction, sources_decouverte
from . import planificateur as plan
from .collecteur import (
    ajouter_sources_conseillees, analyser_source, collecteur, renoter_tout,
    semer_sources_par_defaut,
)
from .config import PORT, RACINE, charger, enregistrer

WEB = RACINE / "web"
app = FastAPI(title="Bot de veille Hourdis", docs_url=None, redoc_url=None)

tache = {"type": None, "actif": False, "message": "", "detail": "", "cible": ""}
RESSOURCE = {"collecte": "collecte", "import": "collecte", "connexion": "navigateur",
             "relecture": "llm", "decouverte": "reseau", "publication": "publication",
             # La renotation réécrit les mêmes fiches que la collecte : même ressource.
             "renotation": "collecte"}
_prises: dict[str, str] = {}
_verrou_taches = threading.Lock()
_planificateur: plan.Planificateur | None = None


def _lancer(type_tache: str, fonction) -> bool:
    ressource = RESSOURCE.get(type_tache, type_tache)
    with _verrou_taches:
        if ressource in _prises:
            return False
        _prises[ressource] = type_tache
    tache.update({"type": type_tache, "actif": True, "message": "", "detail": ""})

    def enveloppe():
        try:
            fonction()
        except Exception as e:                                # noqa: BLE001
            base.logguer(f"{type_tache} : {type(e).__name__}: {e}", "erreur")
            tache["message"] = str(e)
        finally:
            with _verrou_taches:
                _prises.pop(ressource, None)
                tache["actif"] = bool(_prises)
                tache["type"] = next(iter(_prises.values()), None)
                if not _prises:
                    tache["detail"] = ""
                    tache["cible"] = ""

    threading.Thread(target=enveloppe, daemon=True).start()
    return True


def _occupe() -> bool:
    return "collecte" in _prises or collecteur.etat.get("actif", False)


# ── Modèles d'entrée ────────────────────────────────────────────────────────
class SourceEntree(BaseModel):
    entree: str
    nom: str = ""
    aussi_youtube: bool = True


class SourceModif(BaseModel):
    nom: str | None = None
    actif: bool | None = None
    requete: str | None = None
    url: str | None = None


class UrlEntree(BaseModel):
    url: str


class TrouvailleModif(BaseModel):
    statut: str | None = None
    note: str | None = None
    post: str | None = None
    titre: str | None = None
    publie_le: str | None = None      # 'AAAA-MM-JJ' ou '' (inconnue)


class LotEntree(BaseModel):
    ids: list[str]
    action: str                       # garder | ecarter | programmer | supprimer | nouvelle


class RedigerEntree(BaseModel):
    langue: str = ""


class PublierEntree(BaseModel):
    quand: str | None = None          # ISO local 'AAAA-MM-JJTHH:MM'
    a_blanc: bool = False
    message: str = ""


class UnClicEntree(BaseModel):
    refaire_texte: bool | None = None  # None = réglage `un_clic_refaire_texte`
    avec_video: bool | None = None     # None = réglage `un_clic_video`
    message: str = ""                  # texte imposé (celui du panneau), sinon refait
    a_blanc: bool = False              # tout faire sauf envoyer
    allumer: bool = False              # allume `publication_active` avant d'envoyer


class ConfigEntree(BaseModel):
    config: dict


class ChoixEntree(BaseModel):
    cles: list[str]


class DossierEntree(BaseModel):
    chemin: str = ""


# ── Interface ───────────────────────────────────────────────────────────────
@app.get("/")
def accueil():
    page = (WEB / "index.html").read_text(encoding="utf-8")
    for fichier in ("style.css", "app.js"):
        empreinte = int((WEB / fichier).stat().st_mtime)
        page = page.replace(f"/static/{fichier}", f"/static/{fichier}?v={empreinte}")
    return HTMLResponse(page)


@app.get("/static/{fichier}")
def statique(fichier: str):
    chemin = (WEB / Path(fichier).name).resolve()
    if not chemin.is_file() or WEB.resolve() not in chemin.parents:
        raise HTTPException(404, "Fichier inconnu")
    return FileResponse(chemin)


@app.get("/media/{tid}/{fichier}")
def media(tid: str, fichier: str):
    t = base.trouvaille(tid)
    if not t or not t.get("dossier"):
        raise HTTPException(404, "Trouvaille inconnue")
    racine = rangement.racine(charger()).resolve()
    chemin = (racine / t["dossier"] / "images" / Path(fichier).name).resolve()
    if not chemin.is_file() or racine not in chemin.parents:
        raise HTTPException(404, "Image introuvable")
    return FileResponse(chemin)


# ── État ────────────────────────────────────────────────────────────────────
@app.get("/api/etat")
def etat():
    cfg = charger()
    compteurs = base.compteurs()
    return {
        "compteurs": compteurs,
        "collecte": collecteur.etat,
        "tache": tache,
        "journal": base.lire_journal(40),
        "session_fb": base.lire_etat(facebook.CLE_SESSION) == "1",
        "sources_actives": len(base.sources(actives_seulement=True)),
        "candidats": base.compter_candidats().get("nouveau", 0),
        "planning": plan.bilan_du_jour(cfg),
        "publication": {"active": bool(cfg.get("publication_active")),
                        "en_file": compteurs["gardee"] + compteurs["programmee"],
                        "programmees": compteurs["programmee"]},
        "llm_actif": bool(cfg.get("llm_actif")),
        "dossier_collecte": str(rangement.racine(cfg)),
        "port": PORT,
    }


@app.get("/api/journal")
def journal(limite: int = 200, niveau: str = ""):
    return base.lire_journal(limite, niveau)


# ── Sources ─────────────────────────────────────────────────────────────────
@app.get("/api/sources")
def lister_sources():
    return base.sources()


@app.post("/api/sources")
def ajouter_source(entree: SourceEntree):
    try:
        analyse = analyser_source(entree.entree)
    except ValueError as e:
        raise HTTPException(400, str(e))
    nom = entree.nom.strip() or analyse["nom"]
    creees = []
    if analyse["genre"] == "recherche":
        creees.append(base.ajouter_source(nom, "", "recherche_web", analyse["requete"]))
        if entree.aussi_youtube:
            creees.append(base.ajouter_source(nom.replace("Recherche", "YouTube", 1), "",
                                              "youtube_recherche", analyse["requete"]))
    elif analyse["genre"] in ("import_video", "import_page"):
        raise HTTPException(400, "C'est l'adresse d'un contenu précis, pas d'une source : "
                                 "utilisez « Importer une adresse ».")
    else:
        creees.append(base.ajouter_source(nom, analyse["url"], analyse["genre"]))
    base.logguer("Source(s) ajoutée(s) : " + ", ".join(f"« {s['nom']} »" for s in creees), "info")
    return {"sources": creees}


@app.patch("/api/sources/{sid}")
def modifier_source(sid: int, entree: SourceModif):
    champs = {k: v for k, v in entree.model_dump().items() if v is not None}
    if "actif" in champs:
        champs["actif"] = int(champs["actif"])
    base.modifier_source(sid, **champs)
    return base.source(sid)


@app.post("/api/sources/conseillees")
def sources_conseillees():
    """Ajoute les sources conseillées manquantes. Ne supprime ni ne modifie rien."""
    return ajouter_sources_conseillees()


@app.delete("/api/sources/{sid}")
def supprimer_source(sid: int):
    base.supprimer_source(sid)
    return {"ok": True}


@app.post("/api/sources/{sid}/collecter")
def collecter_source(sid: int):
    if not base.source(sid):
        raise HTTPException(404, "Source inconnue")
    if not _lancer("collecte", lambda: collecteur.collecter_une(sid)):
        raise HTTPException(409, "Une tournée est déjà en cours.")
    return {"lancee": True}


# ── Collecte ────────────────────────────────────────────────────────────────
@app.post("/api/collecte")
def lancer_collecte():
    if not _lancer("collecte", lambda: collecteur.collecter()):
        raise HTTPException(409, "Une tournée est déjà en cours.")
    return {"lancee": True}


@app.post("/api/collecte/arret")
def arreter_collecte():
    collecteur.stop.set()
    base.logguer("Arrêt demandé — la tournée s'interrompt à la prochaine étape.", "avert")
    return {"ok": True}


@app.post("/api/importer")
def importer(entree: UrlEntree):
    url = entree.url.strip()
    if not url.startswith("http"):
        raise HTTPException(400, "Collez l'adresse complète (https://…).")
    resultat: dict = {}

    def travail():
        resultat.update(collecteur.importer(url))
        if resultat.get("erreur"):
            base.logguer(f"Import refusé : {resultat['erreur']}", "erreur")
        elif resultat.get("statut") == "doublon":
            base.logguer("Import : cette adresse (ou ce texte) est déjà en base.", "avert")

    if not _lancer("import", travail):
        raise HTTPException(409, "Une tournée est déjà en cours.")
    return {"lancee": True}


# ── Trouvailles ─────────────────────────────────────────────────────────────
@app.get("/api/trouvailles")
def lister_trouvailles(statut: str = "actives", genre: str = "", theme: str = "",
                       source_id: int = 0, q: str = "", tri: str = "score", limite: int = 200,
                       date_pub: str = ""):
    return {"trouvailles": base.lister_trouvailles(statut, genre, theme, source_id, q, tri, limite, date_pub),
            "themes": base.themes_disponibles()}


@app.get("/api/trouvailles/{tid}")
def lire_trouvaille(tid: str):
    t = base.trouvaille(tid)
    if not t:
        raise HTTPException(404, "Trouvaille inconnue")
    return t


@app.get("/api/trouvailles/{tid}/texte", response_class=PlainTextResponse)
def texte_trouvaille(tid: str):
    t = base.trouvaille(tid)
    if not t:
        raise HTTPException(404, "Trouvaille inconnue")
    return rangement.texte_fiche(t)


@app.patch("/api/trouvailles/{tid}")
def modifier_trouvaille(tid: str, entree: TrouvailleModif):
    t = base.trouvaille(tid)
    if not t:
        raise HTTPException(404, "Trouvaille inconnue")
    champs = {k: v for k, v in entree.model_dump().items() if v is not None}
    if "statut" in champs and champs["statut"] not in base.STATUTS:
        raise HTTPException(400, "statut inconnu")
    cfg = charger()
    ancien_dossier = t.get("dossier", "")
    date_change = "publie_le" in champs and champs["publie_le"] != t.get("publie_le", "")
    if date_change:
        valeur = champs["publie_le"].strip()
        if valeur:
            try:
                datetime.strptime(valeur, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(400, "date attendue : AAAA-MM-JJ")
        champs["date_origine"] = "manuelle" if valeur else ""
    base.modifier_trouvaille(tid, champs)
    t = base.trouvaille(tid)
    # Une trouvaille écartée qui revient reçoit son dossier ; une gardée dont la
    # date change déménage ; un post modifié se réécrit.
    if t["statut"] != "ecartee":
        try:
            if date_change:
                t["dossier"] = rangement.deplacer(t, ancien_dossier, cfg)
            else:
                t["dossier"] = rangement.ranger(t, cfg)
            base.modifier_trouvaille(tid, {"dossier": t["dossier"]})
        except OSError as e:
            base.logguer(f"Dossier non réécrit : {e}", "avert")
    elif ancien_dossier and "statut" in champs:
        rangement.supprimer(ancien_dossier, cfg)
        base.modifier_trouvaille(tid, {"dossier": ""})
        t["dossier"] = ""
    return t


@app.delete("/api/trouvailles/{tid}")
def supprimer_trouvaille(tid: str):
    t = base.trouvaille(tid)
    if t and t.get("dossier"):
        rangement.supprimer(t["dossier"], charger())
    base.supprimer_trouvaille(tid)
    return {"ok": True}


@app.post("/api/trouvailles/renoter")
def renoter(tout: bool = False):
    """Recalcule les notes du stock avec les règles d'aujourd'hui.

    Par défaut ne touche que la pile « à trier ». `tout=true` renote aussi les
    notes des gardées et des écartées — sans jamais changer le statut de ce
    qu'Andry a lui-même gardé.
    """
    resultat: dict = {}

    def travail():
        resultat.update(renoter_tout(charger(), seulement_a_trier=not tout))

    if not _lancer("renotation", travail):
        raise HTTPException(409, "Une renotation est déjà en cours.")
    return {"lancee": True}


@app.post("/api/trouvailles/lot")
def lot_trouvailles(entree: LotEntree):
    statuts = {"garder": "gardee", "ecarter": "ecartee", "programmer": "programmee", "nouvelle": "nouvelle"}
    n = 0
    for tid in entree.ids:
        if entree.action == "supprimer":
            supprimer_trouvaille(tid)
            n += 1
        elif entree.action in statuts:
            try:
                modifier_trouvaille(tid, TrouvailleModif(statut=statuts[entree.action]))
                n += 1
            except HTTPException:
                continue
    base.logguer(f"Lot : {n} trouvaille(s) → {entree.action}.", "info")
    return {"n": n}


@app.post("/api/trouvailles/{tid}/rediger")
def rediger_trouvaille(tid: str, entree: RedigerEntree):
    t = base.trouvaille(tid)
    if not t:
        raise HTTPException(404, "Trouvaille inconnue")
    cfg = charger()
    post = redaction.rediger(t, cfg, entree.langue)
    base.modifier_trouvaille(tid, {"post": post})
    t["post"] = post
    if t.get("statut") != "ecartee":
        rangement.ranger(t, cfg)
    return {"post": post}


@app.post("/api/trouvailles/{tid}/relire")
def relire_trouvaille(tid: str):
    t = base.trouvaille(tid)
    if not t:
        raise HTTPException(404, "Trouvaille inconnue")
    cfg = charger()
    if not cfg.get("llm_actif"):
        raise HTTPException(409, "Le modèle est éteint (Réglages → Relecture par un modèle).")

    def travail():
        try:
            lecture = analyse_llm.relire(t, cfg)
        except analyse_llm.LLMIndisponible as e:
            base.logguer(f"Relecture impossible : {e}", "erreur")
            tache["message"] = str(e)
            return
        analyse_llm.appliquer(tid, lecture, cfg)
        base.logguer(f"Relue par le modèle ({lecture['score_ia']}/100) : « {t['titre'][:60]} »", "succes")

    if not _lancer("relecture", travail):
        raise HTTPException(409, "Une relecture est déjà en cours.")
    return {"lancee": True}


@app.post("/api/trouvailles/{tid}/ouvrir")
def ouvrir_trouvaille(tid: str):
    t = base.trouvaille(tid)
    if not t or not t.get("dossier"):
        raise HTTPException(404, "Pas de dossier pour cette trouvaille")
    return {"chemin": rangement.ouvrir_dans_explorateur(t["dossier"], charger())}


# ── Dossiers ────────────────────────────────────────────────────────────────
@app.get("/api/dossiers")
def dossiers():
    cfg = charger()
    return {"racine": str(rangement.racine(cfg)), "dates": base.dates_de_publication()}


@app.post("/api/dossiers/ouvrir")
def ouvrir_dossier(entree: DossierEntree):
    return {"chemin": rangement.ouvrir_dans_explorateur(entree.chemin, charger())}


# ── Publication ─────────────────────────────────────────────────────────────
@app.get("/api/publication")
def etat_publication(page: bool = False):
    cfg = charger()
    return {"active": bool(cfg.get("publication_active")),
            "auto": bool(cfg.get("publication_auto_programmee")),
            "un_clic": {"refaire_texte": bool(cfg.get("un_clic_refaire_texte", True)),
                        "video": bool(cfg.get("un_clic_video", True)),
                        "llm": bool(cfg.get("llm_actif"))},
            "file": publication.file_attente(),
            "historique": base.publications(40),
            "page": publication.etat_page() if page else None}


@app.post("/api/publication/{tid}")
def publier(tid: str, entree: PublierEntree):
    cfg = charger()
    quand = None
    if entree.quand:
        try:
            quand = datetime.fromisoformat(entree.quand)
        except ValueError:
            raise HTTPException(400, "date/heure illisible")
    resultat = publication.publier(tid, cfg, quand, entree.a_blanc, entree.message)
    if not resultat.get("ok"):
        raise HTTPException(409, resultat.get("erreur", "refus"))
    return resultat


@app.post("/api/publication/{tid}/un-clic")
def publier_un_clic(tid: str, entree: UnClicEntree):
    """Texte refait + médias importés + envoi, dans un fil de fond.

    Le refus « publication éteinte » tombe ICI, avant tout travail, pour que le
    bouton puisse proposer d'allumer et de recommencer. `allumer` le fait en un
    seul aller-retour, parce que c'est Andry qui vient de cliquer.
    """
    t = base.trouvaille(tid)
    if not t:
        raise HTTPException(404, "Trouvaille inconnue")
    cfg = charger()
    if entree.allumer and not cfg.get("publication_active"):
        cfg["publication_active"] = True
        enregistrer(cfg)
        base.logguer("Publication allumée depuis le bouton « Publier en un clic ».", "avert")
    if not entree.a_blanc and not cfg.get("publication_active"):
        raise HTTPException(409, publication.REFUS_ETEINT)
    if t.get("statut") == "publiee" and not entree.a_blanc:
        raise HTTPException(409, "Déjà publiée sur la page.")

    def progression(message: str) -> None:
        tache["detail"] = message
        base.logguer(f"[{t['titre'][:40]}] {message}", "info")

    resultat: dict = {}

    def travail():
        resultat.update(publication.publier_en_un_clic(
            tid, cfg, progression, entree.refaire_texte, entree.avec_video, entree.message, entree.a_blanc))
        if not resultat.get("ok"):
            tache["message"] = resultat.get("erreur", "échec")

    if not _lancer("publication", travail):
        raise HTTPException(409, "Une publication est déjà en cours — attendez qu'elle finisse.")
    tache["cible"] = tid
    return {"lancee": True, "a_blanc": entree.a_blanc}


@app.get("/api/publication/{tid}/apercu")
def apercu_publication(tid: str):
    t = base.trouvaille(tid)
    if not t:
        raise HTTPException(404, "Trouvaille inconnue")
    return publication.preparer(t, charger())


# ── Nouvelles sources ───────────────────────────────────────────────────────
@app.get("/api/candidats")
def lister_candidats(statut: str = "nouveau"):
    cfg = charger()
    seuil = int(cfg.get("decouverte_note_min", 55))
    tous = base.candidats(statut)
    return {"candidats": tous if statut != "nouveau" else [c for c in tous if c["note"] >= seuil],
            "sous_le_seuil": len([c for c in tous if c["note"] < seuil]) if statut == "nouveau" else 0,
            "compteurs": base.compter_candidats(), "seuil": seuil}


@app.post("/api/candidats/decouvrir")
def decouvrir():
    def travail():
        r = sources_decouverte.decouvrir(charger())
        base.ecrire_etat(plan.CLE_DECOUVERTE, datetime.now().date().isoformat())
        base.logguer(f"Découverte : {r['nouveaux']} candidat(s) nouveau(x) sur {r['examines']} "
                     "trouvailles gardées.", "info")

    if not _lancer("decouverte", travail):
        raise HTTPException(409, "Une découverte est déjà en cours.")
    return {"lancee": True}


@app.post("/api/candidats/{decision}")
def decider_candidats(decision: str, entree: ChoixEntree):
    if decision not in ("adopter", "ecarter"):
        raise HTTPException(400, "décision inconnue")
    n = 0
    for cle in entree.cles:
        if decision == "adopter":
            if sources_decouverte.adopter(cle):
                n += 1
        else:
            base.decider_candidat(cle, "ecarte")
            n += 1
    base.logguer(f"{n} candidat(s) {'adopté(s)' if decision == 'adopter' else 'écarté(s)'}.", "info")
    return {"n": n}


# ── Réglages, Facebook, modèle ──────────────────────────────────────────────
@app.get("/api/config")
def lire_config():
    return charger()


@app.put("/api/config")
def ecrire_config(entree: ConfigEntree):
    cfg = charger()
    interdits = {k for k in entree.config if k not in cfg}
    if interdits:
        raise HTTPException(400, f"clés inconnues : {', '.join(sorted(interdits))}")
    cfg.update(entree.config)
    enregistrer(cfg)
    base.logguer("Réglages enregistrés.", "info")
    return cfg


@app.post("/api/llm/test")
def tester_llm():
    return analyse_llm.tester(charger())


@app.get("/api/facebook/page")
def page_facebook(force: bool = False):
    return publication.etat_page(force)


@app.post("/api/facebook/connexion")
def connexion_facebook():
    if not _lancer("connexion", lambda: facebook.ouvrir_connexion(collecteur.stop)):
        raise HTTPException(409, "Le navigateur est déjà occupé.")
    return {"lancee": True}


@app.post("/api/facebook/oublier")
def oublier_facebook():
    facebook.oublier_session()
    return {"ok": True}


# ── Export ──────────────────────────────────────────────────────────────────
@app.get("/api/export.csv")
def export_csv(statut: str = ""):
    lignes = base.lister_trouvailles(statut=statut, limite=5000, tri="date")
    tampon = io.StringIO()
    tampon.write("﻿")
    w = csv.writer(tampon, delimiter=";")
    w.writerow(["publie_le", "score", "genre", "statut", "titre", "auteur", "url", "themes",
                "source", "dossier", "collecte_le"])
    for t in lignes:
        w.writerow([t["publie_le"], t["score"], t["genre"], t["statut"], t["titre"], t["auteur"],
                    t["url"], " ".join(t["themes"] or []), t["source_nom"], t["dossier"],
                    t["collecte_le"][:16]])
    return StreamingResponse(iter([tampon.getvalue()]), media_type="text/csv",
                             headers={"Content-Disposition": "attachment; filename=trouvailles-hourdis.csv"})


# ── Démarrage ───────────────────────────────────────────────────────────────
@app.on_event("startup")
def au_demarrage():
    global _planificateur
    base.logguer("Bot de veille Hourdis démarré.", "info")
    semer_sources_par_defaut()
    threading.Thread(target=facebook.session_enregistree, daemon=True).start()

    def collecte_planifiee(apres=None) -> bool:
        def travail():
            try:
                collecteur.collecter(automatique=True)
            finally:
                if apres:
                    try:
                        apres()
                    except Exception as e:                    # noqa: BLE001
                        base.logguer(f"Tâches du jour : {e}", "erreur")
        return _lancer("collecte", travail)

    _planificateur = plan.Planificateur(lancer_collecte=collecte_planifiee, est_occupe=_occupe)


@app.on_event("shutdown")
def a_l_arret():
    if _planificateur:
        _planificateur.fermer()


def demarrer(port: int = PORT, ouvrir: bool = True) -> None:
    if ouvrir:
        threading.Timer(1.2, lambda: webbrowser.open(f"http://127.0.0.1:{port}")).start()
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")
