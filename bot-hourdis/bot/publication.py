"""Publier sur la page Facebook « Hourdis Madagascar » — par l'API Graph, à la main.

La règle qui commande tout : **le bot prépare, l'humain appuie.** Rien ne part
vers Meta tant que `publication_active` est faux ; et même allumé, une trouvaille
n'est publiée que si Andry l'a relue (bouton « Publier », ou statut « programmée »
posé par lui pour la publication aux heures dites).

Ce module reprend les appels du connecteur `social_post.py` du profil Hermes
hourdis (le même jeton de page, lu dans son .env) : `/{page}/feed` pour un
texte + lien, `/{page}/photos` pour une photo avec légende,
`scheduled_publish_time` pour programmer côté Facebook.

⚠ UN SEUL RÉPONDEUR PAR PAGE (règle du 04/09/2026) : ce bot PUBLIE, il ne répond
  à aucun message ni commentaire — c'est le rôle du profil Hermes hourdis.
"""
from __future__ import annotations

import time
from datetime import datetime, timedelta
from pathlib import Path

import requests

from . import base, config, rangement, redaction

GRAPH = "https://graph.facebook.com/v21.0"
DELAI = 60
_cache_page: dict = {"quand": 0.0, "valeur": None}

REFUS_ETEINT = ("La publication est éteinte (Réglages → « Publication active »). Le brouillon "
                "est prêt dans le dossier de la trouvaille : copiez-le, ou allumez la publication.")


def jeton() -> tuple[str, str]:
    return config.secrets_facebook()


def etat_page(force: bool = False) -> dict:
    """Nom et abonnés de la page — dit si le jeton vit encore. Mis en cache 10 min."""
    if not force and _cache_page["valeur"] and time.time() - _cache_page["quand"] < 600:
        return _cache_page["valeur"]
    page, tok = jeton()
    if not (page and tok):
        valeur = {"ok": False, "erreur": "aucun jeton de page (voir LISEZ-MOI, § Secrets)"}
    else:
        try:
            r = requests.get(f"{GRAPH}/{page}", params={
                "fields": "name,fan_count,followers_count,link", "access_token": tok}, timeout=DELAI)
            d = r.json()
            if r.ok and "name" in d:
                valeur = {"ok": True, "nom": d["name"], "abonnes": d.get("followers_count") or d.get("fan_count"),
                          "lien": d.get("link", ""), "page_id": page}
            else:
                valeur = {"ok": False, "erreur": (d.get("error") or {}).get("message", r.text[:160])}
        except (requests.RequestException, ValueError) as e:
            valeur = {"ok": False, "erreur": str(e)[:160]}
    _cache_page.update(quand=time.time(), valeur=valeur)
    return valeur


def preparer(t: dict, cfg: dict) -> dict:
    """Ce qui partirait : {message, lien, photo (chemin local ou ''), programme}."""
    message = (t.get("post") or "").strip() or redaction.rediger(t, cfg)
    photo = ""
    if cfg.get("publier_avec_photo", True) and t.get("images") and t.get("dossier"):
        candidate = rangement.racine(cfg) / t["dossier"] / t["images"][0]
        if candidate.is_file():
            photo = str(candidate)
    return {"message": message, "lien": t.get("url", ""), "photo": photo}


def _erreur_graph(r: requests.Response) -> str:
    try:
        e = r.json().get("error") or {}
        return f"{e.get('message', '')} (code {e.get('code', '?')}, sous-code {e.get('error_subcode', '-')})"
    except ValueError:
        return r.text[:200]


def publier(tid: str, cfg: dict, quand: datetime | None = None, a_blanc: bool = False,
            message: str = "") -> dict:
    """Publie (ou programme) UNE trouvaille. `a_blanc` rend la charge sans rien envoyer."""
    t = base.trouvaille(tid)
    if not t:
        return {"ok": False, "erreur": "trouvaille inconnue"}
    charge = preparer(t, cfg)
    if message.strip():
        charge["message"] = message.strip()
    programme = ""
    if quand is not None:
        # Facebook exige entre 10 minutes et 30 jours d'avance.
        delta = quand - datetime.now()
        if delta < timedelta(minutes=10) or delta > timedelta(days=30):
            return {"ok": False, "erreur": "la programmation doit tomber entre 10 min et 30 jours d'ici"}
        programme = quand.isoformat(timespec="minutes")
    if a_blanc:
        base.enregistrer_publication(tid, "", charge["message"], programme, a_blanc=True,
                                     resultat="à blanc")
        return {"ok": True, "a_blanc": True, **charge, "programme": programme}
    if not cfg.get("publication_active"):
        return {"ok": False, "erreur": REFUS_ETEINT, **charge}
    page, tok = jeton()
    if not (page and tok):
        return {"ok": False, "erreur": "aucun jeton de page configuré"}

    commun = {"access_token": tok}
    if quand is not None:
        commun.update(published="false", scheduled_publish_time=str(int(quand.timestamp())))
    try:
        if charge["photo"]:
            with open(charge["photo"], "rb") as f:
                legende = charge["message"]
                if charge["lien"] and charge["lien"] not in legende:
                    legende += f"\n\n{charge['lien']}"
                r = requests.post(f"{GRAPH}/{page}/photos", data={"caption": legende, **commun},
                                  files={"source": (Path(charge["photo"]).name, f)}, timeout=DELAI)
        else:
            donnees = {"message": charge["message"], **commun}
            if charge["lien"]:
                donnees["link"] = charge["lien"]
            r = requests.post(f"{GRAPH}/{page}/feed", data=donnees, timeout=DELAI)
    except (requests.RequestException, OSError) as e:
        base.enregistrer_publication(tid, "", charge["message"], programme, resultat=f"erreur : {e}")
        return {"ok": False, "erreur": str(e)[:200]}
    if not r.ok:
        erreur = _erreur_graph(r)
        base.enregistrer_publication(tid, "", charge["message"], programme, resultat=f"refus : {erreur}")
        base.logguer(f"Facebook a refusé la publication : {erreur}", "erreur")
        return {"ok": False, "erreur": erreur}
    fb_id = (r.json().get("post_id") or r.json().get("id") or "")
    base.enregistrer_publication(tid, fb_id, charge["message"], programme, resultat="ok")
    base.modifier_trouvaille(tid, {
        "statut": "programmee" if quand is not None else "publiee",
        "publie_fb_id": fb_id,
        "publie_fb_le": programme or base.maintenant(),
        "post": charge["message"],
    })
    base.logguer(f"{'Programmée sur' if quand else 'Publiée sur'} la page : « {t.get('titre', '')[:70]} »"
                 f" ({fb_id}).", "succes")
    return {"ok": True, "fb_id": fb_id, "programme": programme}


def file_attente(limite: int = 100) -> list[dict]:
    """Ce qui attend : gardées (avec ou sans brouillon) puis programmées."""
    return (base.lister_trouvailles(statut="programmee", tri="score", limite=limite)
            + base.lister_trouvailles(statut="gardee", tri="score", limite=limite))


def prochaine_a_publier() -> dict | None:
    """La prochaine trouvaille passée en « programmée » par Andry — pour le planificateur."""
    liste = base.lister_trouvailles(statut="programmee", tri="score", limite=1)
    return liste[0] if liste else None
