"""Trouver de nouvelles sources tout seul — à partir de ce qu'on a déjà gardé.

Les trois bots frères cherchent leurs sources dans la recherche Facebook. Ici la
matière première est différente et meilleure : les trouvailles elles-mêmes.

  - une CHAÎNE YouTube dont on a gardé deux vidéos ou plus vaut la peine d'être
    suivie (son flux Atom, gratuit) ;
  - un SITE dont on a gardé deux articles via Google Actualités ou Bing devient
    une source « site » explorée directement, sans passer par le moteur ;
  - un site cité dans le texte d'une trouvaille (un fabricant, une fédération)
    est un candidat plus faible, noté comme tel.

Rien n'est adopté d'office : les candidats s'affichent dans « Nouvelles
sources », Andry adopte ou écarte. Un écarté ne revient jamais.
"""
from __future__ import annotations

import re
from urllib.parse import urlsplit

from . import base, flux, youtube

HOTES_IGNORES = re.compile(
    r"(youtube\.com|youtu\.be|facebook\.com|fb\.com|instagram\.com|tiktok\.com|twitter\.com|"
    r"x\.com|linkedin\.com|pinterest\.|google\.|bing\.com|wikipedia\.org|amazon\.|"
    r"leboncoin|ebay\.|cdiscount|fnac\.|apple\.com|microsoft\.com)", re.I)


def _hote(url: str) -> str:
    h = urlsplit(url).netloc.lower()
    return h[4:] if h.startswith("www.") else h


def decouvrir(cfg: dict) -> dict:
    """Rend {nouveaux, examines}. N'ajoute que des candidats inconnus."""
    score_min = max(int(cfg.get("score_min", 35)), 45)
    lignes = base.auteurs_des_gardees(score_min)
    sources_actuelles = base.sources()
    hotes_suivis = {_hote(s["url"]) for s in sources_actuelles if s["genre"] == "site" and s["url"]}
    chaines_suivies = {s["url"] for s in sources_actuelles if s["genre"] == "youtube_chaine"}
    connues = base.cles_connues()

    chaines: dict[str, dict] = {}
    sites: dict[str, dict] = {}
    for l in lignes:
        if l["genre"] == "video" and l.get("auteur_url"):
            cle = l["auteur_url"].rstrip("/")
            c = chaines.setdefault(cle, {"nom": l["auteur"] or cle, "n": 0, "scores": []})
            c["n"] += 1
            c["scores"].append(l["score"])
        elif l["genre"] in ("article", "actualite", "pdf") and l.get("url"):
            hote = _hote(l["url"])
            if not hote or HOTES_IGNORES.search(hote) or hote in hotes_suivis:
                continue
            s = sites.setdefault(hote, {"nom": l["auteur"] or hote, "n": 0, "scores": []})
            s["n"] += 1
            s["scores"].append(l["score"])

    nouveaux = 0
    for url, c in chaines.items():
        if url in chaines_suivies or url in connues or c["n"] < 2:
            continue
        note = min(100, 35 + 15 * c["n"] + int(sum(c["scores"]) / len(c["scores"]) / 4))
        if base.ajouter_candidat({
            "cle": url, "genre": "youtube_chaine", "nom": c["nom"], "url": url, "note": note,
            "nb_vues": c["n"],
            "raison": f"{c['n']} vidéos gardées, score moyen {int(sum(c['scores']) / len(c['scores']))}",
        }):
            nouveaux += 1
    for hote, s in sites.items():
        url = f"https://{hote}"
        if url in connues or hote in connues:
            continue
        moyenne = int(sum(s["scores"]) / len(s["scores"]))
        if s["n"] < 2 and moyenne < 70:
            continue
        note = min(100, 30 + 15 * s["n"] + moyenne // 4)
        if base.ajouter_candidat({
            "cle": url, "genre": "site", "nom": s["nom"] if s["nom"] != hote else hote,
            "url": url, "note": note, "nb_vues": s["n"],
            "raison": f"{s['n']} article(s) gardé(s) via les moteurs, score moyen {moyenne}",
        }):
            nouveaux += 1
    return {"nouveaux": nouveaux, "examines": len(lignes)}


def adopter(cle: str) -> dict | None:
    """Un candidat devient une source active."""
    candidat = base.decider_candidat(cle, "adopte")
    if not candidat:
        return None
    genre = candidat["genre"]
    url = candidat["url"]
    if genre == "youtube_chaine":
        # Le flux Atom demande l'identifiant de chaîne ; l'adresse « @nom » ne
        # suffit pas. yt-dlp le rend en une requête.
        cid, nom, canonique = youtube.chaine_id_de(url)
        if cid:
            url = flux.flux_chaine_youtube(cid)
            candidat["nom"] = candidat["nom"] or nom
        genre_source = "youtube_chaine"
    else:
        genre_source = "site"
    return base.ajouter_source(candidat["nom"], url, genre_source)
