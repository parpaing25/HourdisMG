"""Publier sur la page Facebook « Hourdis Madagascar » — par l'API Graph, à la main.

La règle qui commande tout : **le bot prépare, l'humain appuie.** Rien ne part
vers Meta tant que `publication_active` est faux ; et même allumé, une trouvaille
n'est publiée que si Andry l'a relue (bouton « Publier », ou statut « programmée »
posé par lui pour la publication aux heures dites).

Deux chemins :

  - `publier` — le texte du brouillon, avec la première photo ou le lien ;
    peut être PROGRAMMÉ côté Facebook (10 min à 30 jours).
  - `publier_en_un_clic` — refait le texte (modèle si allumé, sinon gabarit),
    IMPORTE les médias (images de l'article, vignette et VIDÉO YouTube), puis
    envoie la publication avec le contenu attaché : vidéo native, ou album de
    photos, ou texte + lien. Demandé par Andry le 06/09/2026.

Ce module reprend les appels du connecteur `social_post.py` du profil Hermes
hourdis (le même jeton de page, lu dans son .env) : `/{page}/feed`,
`/{page}/photos`, `graph-video.facebook.com/{page}/videos`.

⚠ UN SEUL RÉPONDEUR PAR PAGE (règle du 04/09/2026) : ce bot PUBLIE, il ne répond
  à aucun message ni commentaire — c'est le rôle du profil Hermes hourdis.
⚠ Une vidéo republiée reste celle de son auteur : la source est TOUJOURS citée
  dans la description (`signature_source`), et c'est Andry qui décide, vidéo par
  vidéo, en appuyant.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timedelta
from pathlib import Path

import requests

from . import analyse_llm, base, config, rangement, redaction, toile, youtube

GRAPH = "https://graph.facebook.com/v21.0"
GRAPH_VIDEO = "https://graph-video.facebook.com/v21.0"
DELAI = 60
DELAI_VIDEO = 900
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


# ── Publier en un clic : texte refait + médias importés + envoi ─────────────
def _dossier_de(t: dict, cfg: dict) -> Path:
    if not t.get("dossier"):
        t["dossier"] = rangement.ranger(t, cfg)
        base.modifier_trouvaille(t["id"], {"dossier": t["dossier"]})
    return rangement.racine(cfg) / t["dossier"]


def refaire_le_texte(t: dict, cfg: dict, progression) -> str:
    """Le modèle réécrit (résumé, conseils, post FR + MG) s'il est allumé ; sinon
    le gabarit refait le brouillon depuis le texte. Le résultat est enregistré."""
    if cfg.get("llm_actif"):
        progression("Réécriture du texte par le modèle…")
        try:
            lecture = analyse_llm.relire(t, cfg)
            t.update(analyse_llm.appliquer(t["id"], lecture, cfg) or {})
            if t.get("post"):
                return t["post"]
            progression("Le modèle n'a pas rendu de texte — gabarit.")
        except analyse_llm.LLMIndisponible as e:
            progression(f"Modèle indisponible ({str(e)[:80]}) — texte par gabarit.")
    else:
        progression("Rédaction du texte (gabarit)…")
    texte = redaction.rediger(t, cfg)
    base.modifier_trouvaille(t["id"], {"post": texte})
    t["post"] = texte
    return texte


def importer_les_medias(t: dict, cfg: dict, progression, avec_video: bool = True) -> dict:
    """Rend {video: Path|None, photos: [Path], detail: str}. Écrit dans le dossier de la fiche."""
    dossier = _dossier_de(t, cfg)
    resultat = {"video": None, "photos": [], "detail": ""}
    video_id = youtube.video_id_de(t.get("url", "")) if t.get("genre") == "video" else ""

    # Images : celles déjà rangées, sinon on va les chercher.
    photos = [dossier / p for p in (t.get("images") or []) if (dossier / p).is_file()]
    if not photos:
        progression("Récupération des images…")
        distantes: list[str] = []
        if video_id:
            distantes = youtube.vignettes(video_id)
        elif t.get("url") and t.get("genre") in ("article", "actualite", "post_fb"):
            page = toile.lire_page(t["url"])
            distantes = page.get("images") or []
        noms = rangement.telecharger_images(distantes, dossier / "images", cfg)
        if noms:
            t["images"] = list(t.get("images") or []) + noms
            base.modifier_trouvaille(t["id"], {"images": t["images"]})
            photos = [dossier / p for p in noms]
    resultat["photos"] = photos[:int(cfg.get("un_clic_photos_max", 4))]

    # Vidéo : téléchargée en MP4, dans les bornes de durée et de poids.
    if video_id and avec_video and cfg.get("un_clic_video", True):
        duree = int(t.get("duree_s") or 0)
        limite = int(cfg.get("video_duree_max_s", 1500))
        if duree and duree > limite:
            resultat["detail"] = f"vidéo de {youtube.duree_lisible(duree)}, au-delà de la limite — vignette et lien"
            progression(resultat["detail"])
        else:
            progression("Téléchargement de la vidéo…")
            chemin, erreur = youtube.telecharger_video(
                video_id, dossier / "media", int(cfg.get("video_hauteur_max", 720)),
                int(cfg.get("video_taille_max_mo", 250)))
            if chemin:
                resultat["video"] = chemin
                progression(f"Vidéo prête ({chemin.stat().st_size // (1024 * 1024)} Mo).")
            else:
                resultat["detail"] = f"vidéo non récupérée ({erreur}) — vignette et lien"
                progression(resultat["detail"])
    return resultat


def _envoyer_video(page: str, tok: str, video: Path, texte: str, titre: str) -> tuple[str, str]:
    """POST graph-video /{page}/videos. Rend (id, erreur)."""
    try:
        with open(video, "rb") as f:
            r = requests.post(f"{GRAPH_VIDEO}/{page}/videos",
                              data={"access_token": tok, "description": texte, "title": titre[:100]},
                              files={"source": (video.name, f, "video/mp4")}, timeout=DELAI_VIDEO)
    except (requests.RequestException, OSError) as e:
        return "", str(e)[:200]
    if not r.ok:
        return "", _erreur_graph(r)
    return str(r.json().get("id") or ""), ""


def _envoyer_photos(page: str, tok: str, photos: list[Path], texte: str, lien: str) -> tuple[str, str]:
    """Album : chaque photo envoyée non publiée, puis UNE publication qui les attache."""
    identifiants = []
    for photo in photos:
        try:
            with open(photo, "rb") as f:
                r = requests.post(f"{GRAPH}/{page}/photos", data={"access_token": tok, "published": "false"},
                                  files={"source": (photo.name, f)}, timeout=DELAI * 2)
        except (requests.RequestException, OSError) as e:
            return "", str(e)[:200]
        if not r.ok:
            return "", _erreur_graph(r)
        identifiants.append(str(r.json().get("id")))
    donnees = {"access_token": tok, "message": texte if lien in texte or not lien else f"{texte}\n\n{lien}"}
    for i, mid in enumerate(identifiants):
        donnees[f"attached_media[{i}]"] = json.dumps({"media_fbid": mid})
    try:
        r = requests.post(f"{GRAPH}/{page}/feed", data=donnees, timeout=DELAI)
    except requests.RequestException as e:
        return "", str(e)[:200]
    if not r.ok:
        return "", _erreur_graph(r)
    return str(r.json().get("id") or ""), ""


def _envoyer_texte(page: str, tok: str, texte: str, lien: str) -> tuple[str, str]:
    donnees = {"access_token": tok, "message": texte}
    if lien:
        donnees["link"] = lien
    try:
        r = requests.post(f"{GRAPH}/{page}/feed", data=donnees, timeout=DELAI)
    except requests.RequestException as e:
        return "", str(e)[:200]
    if not r.ok:
        return "", _erreur_graph(r)
    return str(r.json().get("id") or ""), ""


def publier_en_un_clic(tid: str, cfg: dict, progression=None, refaire_texte: bool | None = None,
                       avec_video: bool | None = None, message: str = "", a_blanc: bool = False) -> dict:
    """Texte refait + médias importés + envoi. Rend {ok, mode, fb_id|erreur, message, medias}."""
    progression = progression or (lambda m: base.logguer(m, "info"))
    t = base.trouvaille(tid)
    if not t:
        return {"ok": False, "erreur": "trouvaille inconnue"}
    if t.get("statut") == "publiee" and not a_blanc:
        return {"ok": False, "erreur": "déjà publiée sur la page"}
    if not a_blanc and not cfg.get("publication_active"):
        return {"ok": False, "erreur": REFUS_ETEINT}
    refaire = cfg.get("un_clic_refaire_texte", True) if refaire_texte is None else refaire_texte
    avec_video = cfg.get("un_clic_video", True) if avec_video is None else avec_video

    # 1. Le texte
    if message.strip():
        texte = message.strip()
        base.modifier_trouvaille(tid, {"post": texte})
    elif refaire or not t.get("post"):
        texte = refaire_le_texte(t, cfg, progression)
    else:
        texte = t["post"]

    # 2. Les médias
    medias = importer_les_medias(t, cfg, progression, avec_video)
    mode = "video" if medias["video"] else ("photos" if medias["photos"] else "lien")
    charge = {"message": texte, "mode": mode, "video": str(medias["video"] or ""),
              "photos": [str(p) for p in medias["photos"]], "lien": t.get("url", ""),
              "detail": medias["detail"]}
    if a_blanc:
        base.enregistrer_publication(tid, "", texte, a_blanc=True, resultat=f"à blanc ({mode})")
        progression(f"À blanc : publication en mode {mode}, rien envoyé.")
        return {"ok": True, "a_blanc": True, **charge}

    # 3. L'envoi
    page, tok = jeton()
    if not (page and tok):
        return {"ok": False, "erreur": "aucun jeton de page configuré", **charge}
    progression({"video": "Envoi de la vidéo sur la page…", "photos": "Envoi des photos sur la page…",
                 "lien": "Envoi du texte et du lien…"}[mode])
    if mode == "video":
        fb_id, erreur = _envoyer_video(page, tok, medias["video"], texte, t.get("titre", ""))
        if erreur:
            # Une vidéo refusée (droits, poids, jeton sans publish_video) ne doit
            # pas faire perdre la publication : on retombe sur l'album/le lien.
            progression(f"Vidéo refusée par Facebook ({erreur}) — publication avec les photos et le lien.")
            mode = "photos" if medias["photos"] else "lien"
            charge["mode"], charge["detail"] = mode, f"vidéo refusée : {erreur}"
            fb_id, erreur = ("", "")
    if mode == "photos":
        fb_id, erreur = _envoyer_photos(page, tok, medias["photos"], texte, t.get("url", ""))
    elif mode == "lien":
        fb_id, erreur = _envoyer_texte(page, tok, texte, t.get("url", ""))
    if erreur:
        base.enregistrer_publication(tid, "", texte, resultat=f"refus ({mode}) : {erreur}")
        base.logguer(f"Facebook a refusé la publication ({mode}) : {erreur}", "erreur")
        return {"ok": False, "erreur": erreur, **charge}

    # 4. La trace
    base.enregistrer_publication(tid, fb_id, texte, resultat=f"ok ({mode})")
    base.modifier_trouvaille(tid, {"statut": "publiee", "publie_fb_id": fb_id,
                                   "publie_fb_le": base.maintenant(), "post": texte})
    t = base.trouvaille(tid) or t
    try:
        rangement.ranger(t, cfg)
    except OSError:
        pass
    base.logguer(f"Publiée en un clic ({mode}) : « {t.get('titre', '')[:70]} » ({fb_id}).", "succes")
    return {"ok": True, "fb_id": fb_id, **charge, "mode": mode}


def file_attente(limite: int = 100) -> list[dict]:
    """Ce qui attend : gardées (avec ou sans brouillon) puis programmées."""
    return (base.lister_trouvailles(statut="programmee", tri="score", limite=limite)
            + base.lister_trouvailles(statut="gardee", tri="score", limite=limite))


def prochaine_a_publier() -> dict | None:
    """La prochaine trouvaille passée en « programmée » par Andry — pour le planificateur."""
    liste = base.lister_trouvailles(statut="programmee", tri="score", limite=1)
    return liste[0] if liste else None
