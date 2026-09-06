"""Noter une trouvaille de 0 à 100 — déterministe, sans modèle.

Le score répond à UNE question : « est-ce que ça mérite d'être lu par quelqu'un
qui vend et pose des hourdis et de la terre cuite à Madagascar ? ». Il se lit
avec ses MOTIFS (« hourdis ×4 dans le texte », « tutoriel », « vidéo ») : un
chiffre seul ne se corrige pas, un chiffre expliqué se règle.

Ce qui écarte d'office (`hors_sujet`) :
  - aucun mot du métier ni dans le titre ni dans le texte ;
  - un repoussoir (annonce immobilière, brique de lait, Lego…) sans un cœur de
    métier assez fort pour le contredire.

Tout le reste est une NUANCE, jamais un couperet : c'est `score_min` (réglable)
qui tranche, et les écartées restent visibles pour régler le tri.
"""
from __future__ import annotations

import re
import unicodedata
from datetime import date

from . import lexique


def sans_accents(texte: str) -> str:
    reduit = unicodedata.normalize("NFKD", texte or "")
    reduit = "".join(c for c in reduit if unicodedata.category(c) != "Mn")
    reduit = reduit.replace("’", "'").replace("`", "'")
    return re.sub(r"\s+", " ", reduit.lower()).strip()


def _compiler(cfg: dict | None) -> list[tuple[re.Pattern, int]]:
    mots = list(lexique.MOTS_METIER)
    for mot in (cfg or {}).get("mots_metier") or []:
        mot = sans_accents(str(mot))
        if mot:
            mots.append((re.escape(mot), 6))
    return [(re.compile(rf"\b(?:{motif})\b"), poids) for motif, poids in mots]


def _repoussoirs(cfg: dict | None) -> list[tuple[str, re.Pattern]]:
    liste = [(nom, re.compile(motif)) for nom, motif in lexique.REPOUSSOIRS]
    for mot in (cfg or {}).get("repoussoirs") or []:
        mot = sans_accents(str(mot))
        if mot:
            liste.append((f"repoussoir « {mot} »", re.compile(rf"\b{re.escape(mot)}\b")))
    return liste


_TUTORIEL = re.compile(lexique.TUTORIEL)
_THEMES = {nom: re.compile(motif) for nom, motif in lexique.THEMES.items()}


def langue_probable(texte: str) -> str:
    """'fr', 'mg', 'en' ou '' — au vote des mots vides, sur les 3 000 premiers caractères."""
    mots = re.findall(r"[a-z']+", sans_accents(texte)[:3000])
    if len(mots) < 8:
        return ""
    scores = {langue: 0 for langue in lexique.LANGUES}
    for mot in mots:
        for langue, vides in lexique.LANGUES.items():
            if mot in vides:
                scores[langue] += 1
    meilleure = max(scores, key=scores.get)
    if scores[meilleure] < 3:
        return ""
    return meilleure


def themes_de(texte: str, titre: str = "") -> list[str]:
    """Les thèmes présents, DU PLUS PRÉSENT AU MOINS PRÉSENT.

    Un thème dans le titre pèse comme cinq mentions dans le texte : une vidéo
    « bâtir un mur en briques » dont la transcription dit deux fois « défaut »
    est une vidéo sur les MURS, pas sur les erreurs — et c'est le premier
    thème qui choisit l'accroche du brouillon (mesuré le 06/09/2026).
    """
    reduit = sans_accents(texte)[:20000]
    t_titre = sans_accents(titre)
    poids: dict[str, int] = {}
    for nom, motif in _THEMES.items():
        n = len(motif.findall(reduit)) + 5 * len(motif.findall(t_titre))
        if n:
            poids[nom] = n
    return sorted(poids, key=lambda nom: -poids[nom])


def pre_note(titre: str, description: str = "", cfg: dict | None = None) -> int:
    """Note rapide sur le titre (et une courte description) — pour décider si
    une vidéo vaut une requête de plus. Même échelle, jamais d'écart."""
    return noter(titre, description[:600], "video", cfg=cfg)["score"]


def noter(titre: str, texte: str, genre: str = "article", langue: str = "",
          publie_le: date | None = None, cfg: dict | None = None) -> dict:
    """Rend {score, themes, motifs, hors_sujet, raison, langue}."""
    cfg = cfg or {}
    t_titre = sans_accents(titre)
    t_texte = sans_accents(texte)[:40000]
    langue = langue or langue_probable(texte or titre)
    motifs: list[str] = []

    # ── Le cœur : les mots du métier ──
    points = 0
    dans_titre = 0
    for motif, poids in _compiler(cfg):
        n_titre = len(motif.findall(t_titre))
        n_texte = len(motif.findall(t_texte))
        if n_titre:
            points += 3 * poids * min(n_titre, 2)
            dans_titre += 1
        if n_texte:
            points += poids * min(n_texte, 4)
        if (n_titre or n_texte) and poids >= 6:
            exemple = re.sub(r"^\\b\(\?:|\)\\b$", "", motif.pattern).split("|")[0]
            exemple = re.sub(r"[\\()\[\]?*+]", "", exemple).strip()
            motifs.append(f"{exemple} ×{n_titre + n_texte}")
    if points == 0:
        return {"score": 0, "themes": [], "motifs": ["aucun mot du métier"],
                "hors_sujet": True, "raison": "aucun mot du métier", "langue": langue}
    coeur = min(58, round(points * 0.55))

    # ── Repoussoirs ──
    for nom, motif in _repoussoirs(cfg):
        if motif.search(t_titre) or motif.search(t_texte[:4000]):
            if coeur < 30:
                return {"score": 0, "themes": [], "motifs": motifs + [f"repoussoir : {nom}"],
                        "hors_sujet": True, "raison": nom, "langue": langue}
            coeur -= 18
            motifs.append(f"repoussoir atténué : {nom}")
            break

    score = coeur

    # ── Signal « ça enseigne » ──
    if _TUTORIEL.search(t_titre) or _TUTORIEL.search(t_texte[:600]):
        score += 12
        motifs.append("tutoriel / conseil")
    if dans_titre:
        score += 6
        motifs.append("sujet dans le titre")

    # ── Thèmes ──
    themes = themes_de(texte, titre)
    score += min(12, 3 * len([t for t in themes if t not in ("prix", "madagascar")]))
    if "madagascar" in themes:
        score += 6
        motifs.append("Madagascar")

    # ── Genre, longueur, langue ──
    score += lexique.BONUS_GENRE.get(genre, 0)
    longueur = len(t_texte)
    if longueur >= 1500:
        score += 6
    elif longueur >= 600:
        score += 3
    elif longueur < 150 and genre not in ("video", "post_fb"):
        score -= 12
        motifs.append("texte très court")
    if langue == "en":
        score -= int(cfg.get("penalite_anglais", 12))
        motifs.append("anglais")
    if langue and langue not in (cfg.get("langues") or ["fr", "mg", "en"]):
        score -= 25
        motifs.append(f"langue non suivie : {langue}")

    # ── Fraîcheur : un léger bonus au récent, jamais de couperet ici ──
    if publie_le:
        age = (date.today() - publie_le).days
        if age <= 90:
            score += 4
        elif age > 6 * 365:
            score -= 6
            motifs.append("plus de six ans")

    score = max(0, min(100, int(round(score))))
    return {"score": score, "themes": themes, "motifs": motifs, "hors_sujet": False,
            "raison": "", "langue": langue}
