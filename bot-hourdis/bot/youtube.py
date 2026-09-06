"""YouTube sans clé d'API : recherche, fiche d'une vidéo, sous-titres — via yt-dlp.

yt-dlp (2026.8.19 sur ce PC) sait chercher (`ytsearchN:requête`), décrire une
vidéo (`--dump-json`) et rapatrier ses sous-titres automatiques. C'est ce qui
donne au bot le TEXTE d'un tuto vidéo : la transcription, rangée en .txt à
côté du titre — sans télécharger la vidéo, jamais.

Budget : la recherche « à plat » coûte UNE requête pour N vidéos, mais ne rend
ni la date ni la description complète. La fiche complète coûte une requête PAR
vidéo, les sous-titres deux ou trois. Le collecteur ne les demande que pour
les vidéos dont le titre note déjà bien (`score.pre_note`), dans des plafonds
réglables — une tournée ne doit pas ressembler à un aspirateur.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from . import dates_web

DELAI_RECHERCHE = 120
DELAI_FICHE = 60
DELAI_SOUS_TITRES = 90


def _commande() -> list[str]:
    binaire = shutil.which("yt-dlp")
    if binaire:
        return [binaire]
    return [sys.executable, "-m", "yt_dlp"]


def _executer(arguments: list[str], delai: int) -> tuple[str, str, int]:
    commande = _commande() + ["--no-warnings", "--ignore-errors", "--socket-timeout", "20",
                              "--no-playlist", "--no-check-certificate"] + arguments
    try:
        fini = subprocess.run(commande, capture_output=True, text=True, timeout=delai,
                              encoding="utf-8", errors="replace",
                              creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except FileNotFoundError:
        return "", "yt-dlp introuvable (pip install yt-dlp)", 127
    except subprocess.TimeoutExpired:
        return "", f"yt-dlp : délai de {delai} s dépassé", 124
    return fini.stdout, fini.stderr, fini.returncode


def _depuis_json(d: dict) -> dict:
    """Une fiche yt-dlp -> le dictionnaire commun du bot."""
    video_id = d.get("id") or ""
    vignettes = d.get("thumbnails") or []
    vignette = d.get("thumbnail") or ""
    if not vignette and vignettes:
        vignette = sorted(vignettes, key=lambda v: (v.get("width") or 0))[-1].get("url", "")
    quand = dates_web.lire_iso(str(d.get("upload_date") or ""))
    if quand is None and d.get("timestamp"):
        quand = dates_web.lire_iso(str(int(d["timestamp"])))
    if quand is None and d.get("release_timestamp"):
        quand = dates_web.lire_iso(str(int(d["release_timestamp"])))
    return {
        "video_id": video_id,
        "url": d.get("webpage_url") or (f"https://www.youtube.com/watch?v={video_id}" if video_id else ""),
        "titre": (d.get("title") or "").strip(),
        "resume": (d.get("description") or "").strip(),
        "duree_s": int(d["duration"]) if d.get("duration") else None,
        "vues": int(d["view_count"]) if d.get("view_count") is not None else None,
        "auteur": (d.get("channel") or d.get("uploader") or "").strip(),
        "chaine_id": d.get("channel_id") or "",
        "auteur_url": d.get("channel_url") or d.get("uploader_url") or "",
        "publie_le": quand,
        "image": vignette,
        "tags": d.get("tags") or [],
        "chapitres": [c.get("title", "") for c in (d.get("chapters") or []) if c.get("title")],
        "langue": d.get("language") or "",
        "en_direct": (d.get("live_status") or "") in ("is_live", "is_upcoming"),
    }


def rechercher(requete: str, n: int = 12) -> tuple[list[dict], str]:
    """Recherche à plat : rend ([fiches sommaires], erreur)."""
    sortie, erreur, code = _executer(
        [f"ytsearch{int(n)}:{requete}", "--flat-playlist", "--dump-json", "--skip-download"],
        DELAI_RECHERCHE)
    fiches = []
    for ligne in sortie.splitlines():
        ligne = ligne.strip()
        if not ligne.startswith("{"):
            continue
        try:
            fiches.append(_depuis_json(json.loads(ligne)))
        except json.JSONDecodeError:
            continue
    if not fiches and code != 0:
        return [], (erreur.strip().splitlines() or ["yt-dlp a échoué"])[-1][:200]
    return fiches, ""


def fiche(url_ou_id: str) -> tuple[dict | None, str]:
    """La fiche complète d'une vidéo (date, description, chapitres, tags)."""
    cible = url_ou_id if url_ou_id.startswith("http") else f"https://www.youtube.com/watch?v={url_ou_id}"
    sortie, erreur, code = _executer([cible, "--dump-json", "--skip-download"], DELAI_FICHE)
    for ligne in sortie.splitlines():
        if ligne.strip().startswith("{"):
            try:
                return _depuis_json(json.loads(ligne)), ""
            except json.JSONDecodeError:
                continue
    return None, (erreur.strip().splitlines() or ["fiche illisible"])[-1][:200]


def chaine_id_de(url: str) -> tuple[str, str, str]:
    """(channel_id, nom, url canonique) d'une adresse de chaîne (@nom, /c/, /channel/)."""
    cible = url.rstrip("/")
    if not re.search(r"/(videos|streams|shorts|featured)$", cible):
        cible += "/videos"
    sortie, erreur, code = _executer(
        [cible, "--flat-playlist", "--playlist-end", "1", "--dump-single-json", "--skip-download"],
        DELAI_FICHE)
    for ligne in sortie.splitlines():
        if ligne.strip().startswith("{"):
            try:
                d = json.loads(ligne)
            except json.JSONDecodeError:
                continue
            cid = d.get("channel_id") or d.get("uploader_id") or ""
            if not cid and (d.get("entries") or []):
                cid = (d["entries"][0] or {}).get("channel_id", "")
            nom = d.get("channel") or d.get("uploader") or d.get("title") or ""
            return cid, nom, d.get("channel_url") or url
    return "", "", url


# ── Sous-titres ─────────────────────────────────────────────────────────────
_HORODATAGE_VTT = re.compile(r"^\d{2}:\d{2}:\d{2}[.,]\d{3}\s+-->")
_BALISES = re.compile(r"<[^>]+>")


def vtt_en_texte(contenu: str) -> str:
    """Un fichier WebVTT -> paragraphe lisible, sans répétitions.

    Les sous-titres automatiques de YouTube répètent chaque ligne deux ou
    trois fois (la ligne « en cours » et la ligne « suivante » se chevauchent) :
    on ne garde une ligne que si elle n'est pas contenue dans les deux
    précédentes.
    """
    lignes: list[str] = []
    for brut in contenu.splitlines():
        ligne = _BALISES.sub("", brut).strip()
        if (not ligne or ligne.startswith(("WEBVTT", "Kind:", "Language:", "NOTE"))
                or _HORODATAGE_VTT.match(ligne) or ligne.isdigit()):
            continue
        ligne = re.sub(r"\s+", " ", ligne.replace("&nbsp;", " "))
        if lignes and (ligne in lignes[-1] or (len(lignes) > 1 and ligne in lignes[-2])):
            continue
        if lignes and lignes[-1] in ligne:
            lignes[-1] = ligne
            continue
        lignes.append(ligne)
    texte = " ".join(lignes)
    return re.sub(r"\s+", " ", texte).strip()


def sous_titres(video_id: str, langues: tuple[str, ...] = ("fr", "mg", "en")) -> tuple[str, str]:
    """(texte, langue) des sous-titres — manuels d'abord, automatiques sinon."""
    with tempfile.TemporaryDirectory(prefix="hourdis-st-") as dossier:
        gabarit = str(Path(dossier) / "%(id)s.%(ext)s")
        codes = ",".join(f"{l},{l}-orig,{l}.*" for l in langues)
        _executer([f"https://www.youtube.com/watch?v={video_id}", "--skip-download",
                   "--write-subs", "--write-auto-subs", "--sub-langs", codes,
                   "--sub-format", "vtt", "--convert-subs", "vtt", "-o", gabarit],
                  DELAI_SOUS_TITRES)
        fichiers = sorted(Path(dossier).glob("*.vtt"))
        if not fichiers:
            return "", ""
        # La langue préférée d'abord, puis la première disponible.
        def rang(f: Path) -> int:
            suffixe = f.name[len(video_id) + 1:]
            for i, l in enumerate(langues):
                if suffixe.startswith(l):
                    return i
            return len(langues)
        fichier = sorted(fichiers, key=rang)[0]
        langue = fichier.name[len(video_id) + 1:].split(".")[0][:2]
        try:
            return vtt_en_texte(fichier.read_text(encoding="utf-8", errors="replace")), langue
        except OSError:
            return "", ""


def duree_lisible(secondes: int | None) -> str:
    if not secondes:
        return ""
    m, s = divmod(int(secondes), 60)
    h, m = divmod(m, 60)
    return f"{h} h {m:02d} min" if h else (f"{m} min {s:02d}" if m else f"{s} s")
