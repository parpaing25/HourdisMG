"""Ranger ce que le bot trouve : un dossier par DATE DE PUBLICATION, le texte en .txt.

    collecte/
      2026-09-04/
        INDEX.txt                          ← une ligne par fiche du jour
        pose-plancher-hourdis-poutrelles--a1b2c3/
          texte.txt                        ← en-tête + texte intégral (ou transcription)
          fiche.json                       ← tout ce qu'on sait, pour les machines
          post-facebook.txt                ← brouillon de publication prêt à coller
          images/                          ← vignette, photos utiles
      date-inconnue/                       ← quand la page ne dit pas de quand elle date
        ...

⚠ « date-inconnue » n'est pas un échec de rangement, c'est une information :
  on ne date pas du jour ce qu'on n'a pas su dater (règle de `fraicheur.py`).
  La date se corrige à la main dans l'interface, et la fiche DÉMÉNAGE alors
  dans le bon dossier (`deplacer`).

Le nom du sous-dossier porte un suffixe de six caractères tiré de l'identifiant :
deux articles au même titre ne s'écrasent pas.
"""
from __future__ import annotations

import io
import json
import os
import re
import shutil
import unicodedata
from datetime import date, datetime
from pathlib import Path

import requests

from . import config as cfg_mod
from . import youtube

DOSSIER_SANS_DATE = "date-inconnue"
LIBELLES_GENRE = {"article": "Article", "video": "Vidéo", "pdf": "Guide PDF",
                  "actualite": "Actualité", "post_fb": "Publication Facebook"}
LIBELLES_DATE = {"jsonld": "balise de la page", "meta": "balise de la page",
                 "time": "balise <time>", "url": "adresse de la page",
                 "url_mois": "adresse de la page (mois seulement)", "texte": "lue dans le texte",
                 "flux": "flux RSS", "youtube": "YouTube", "facebook": "Facebook",
                 "manuelle": "saisie à la main", "": "inconnue"}


def slug(titre: str, tid: str, longueur: int = 60) -> str:
    reduit = unicodedata.normalize("NFKD", titre or "sans-titre")
    reduit = "".join(c for c in reduit if unicodedata.category(c) != "Mn").lower()
    reduit = re.sub(r"[^a-z0-9]+", "-", reduit).strip("-")[:longueur].rstrip("-")
    return f"{reduit or 'sans-titre'}--{(tid or '')[:6]}"


def nom_dossier_date(quand: str | date | None) -> str:
    if isinstance(quand, date):
        return quand.isoformat()
    quand = (quand or "").strip()
    return quand if re.fullmatch(r"\d{4}-\d{2}-\d{2}", quand) else DOSSIER_SANS_DATE


def racine(cfg: dict | None = None) -> Path:
    return cfg_mod.dossier_collecte(cfg)


def chemin_de(trouvaille: dict, cfg: dict | None = None) -> Path:
    return racine(cfg) / nom_dossier_date(trouvaille.get("publie_le")) / slug(
        trouvaille.get("titre", ""), trouvaille.get("id", ""))


def _ligne(nom: str, valeur) -> str:
    return f"{nom:<14}: {valeur}\n" if valeur not in (None, "", [], 0) else ""


def texte_fiche(t: dict) -> str:
    """Le contenu de texte.txt : un en-tête lisible, puis le texte intégral."""
    entete = "".join([
        _ligne("Titre", t.get("titre")),
        _ligne("Genre", LIBELLES_GENRE.get(t.get("genre"), t.get("genre"))),
        _ligne("Adresse", t.get("url")),
        _ligne("Auteur", t.get("auteur")),
        _ligne("Chaîne/Site", t.get("auteur_url")),
        _ligne("Source", t.get("source_nom")),
        _ligne("Publié le", t.get("publie_le") or "inconnu"),
        _ligne("Date d'où", LIBELLES_DATE.get(t.get("date_origine", ""), t.get("date_origine"))),
        _ligne("Collecté le", (t.get("collecte_le") or "")[:16].replace("T", " ")),
        _ligne("Langue", t.get("langue")),
        _ligne("Score", f"{t.get('score')}/100" + (f" (IA : {t['score_ia']})" if t.get("score_ia") else "")),
        _ligne("Thèmes", ", ".join(t.get("themes") or [])),
        _ligne("Pourquoi", " · ".join(t.get("motifs") or [])),
        _ligne("Durée", youtube.duree_lisible(t.get("duree_s"))),
        _ligne("Vues", f"{t['vues']:,}".replace(",", " ") if t.get("vues") else ""),
    ])
    corps = []
    if t.get("resume"):
        corps.append("RÉSUMÉ\n" + t["resume"].strip())
    if t.get("conseils"):
        corps.append("CONSEILS RETENUS\n" + "\n".join(f"- {c}" for c in t["conseils"]))
    if t.get("avertissements"):
        corps.append("⚠ À VÉRIFIER\n" + "\n".join(f"- {a}" for a in t["avertissements"]))
    texte = (t.get("texte") or "").strip()
    etiquette = "TRANSCRIPTION" if t.get("genre") == "video" else "TEXTE"
    corps.append(f"{etiquette}\n{texte if texte else '(aucun texte lisible sur cette page)'}")
    return entete + "\n" + "\n\n".join(corps) + "\n"


def ranger(t: dict, cfg: dict | None = None, images_distantes: list[str] | None = None) -> str:
    """Écrit (ou réécrit) le dossier d'une trouvaille. Rend le chemin RELATIF à la racine."""
    cfg = cfg or cfg_mod.charger()
    dossier = chemin_de(t, cfg)
    dossier.mkdir(parents=True, exist_ok=True)
    (dossier / "texte.txt").write_text(texte_fiche(t), encoding="utf-8")
    if t.get("post"):
        (dossier / "post-facebook.txt").write_text(t["post"].strip() + "\n", encoding="utf-8")
    if t.get("post_mg"):
        (dossier / "post-facebook-mg.txt").write_text(t["post_mg"].strip() + "\n", encoding="utf-8")
    images_locales = list(t.get("images") or [])
    if images_distantes and cfg.get("telecharger_images", True):
        nouvelles = telecharger_images(images_distantes, dossier / "images", cfg,
                                       deja=len(images_locales))
        images_locales.extend(n for n in nouvelles if n not in images_locales)
        t["images"] = images_locales
    fiche = {k: v for k, v in t.items() if k not in ("texte", "html")}
    fiche["texte_longueur"] = len(t.get("texte") or "")
    fiche["range_le"] = datetime.now().isoformat(timespec="seconds")
    (dossier / "fiche.json").write_text(json.dumps(fiche, ensure_ascii=False, indent=2, default=str),
                                        encoding="utf-8")
    relatif = dossier.relative_to(racine(cfg)).as_posix()
    reecrire_index(dossier.parent, cfg)
    return relatif


def deplacer(t: dict, ancien_relatif: str, cfg: dict | None = None) -> str:
    """La date a changé : le dossier suit. Rend le nouveau chemin relatif."""
    cfg = cfg or cfg_mod.charger()
    ancien = racine(cfg) / ancien_relatif if ancien_relatif else None
    nouveau = chemin_de(t, cfg)
    if ancien and ancien.exists() and ancien.resolve() != nouveau.resolve():
        nouveau.parent.mkdir(parents=True, exist_ok=True)
        if nouveau.exists():
            shutil.rmtree(nouveau, ignore_errors=True)
        shutil.move(str(ancien), str(nouveau))
        reecrire_index(ancien.parent, cfg)
        _supprimer_si_vide(ancien.parent)
    return ranger(t, cfg)


def supprimer(relatif: str, cfg: dict | None = None) -> None:
    cfg = cfg or cfg_mod.charger()
    if not relatif:
        return
    dossier = (racine(cfg) / relatif).resolve()
    if racine(cfg).resolve() in dossier.parents and dossier.exists():
        shutil.rmtree(dossier, ignore_errors=True)
        reecrire_index(dossier.parent, cfg)
        _supprimer_si_vide(dossier.parent)


def _supprimer_si_vide(dossier: Path) -> None:
    try:
        restes = [p for p in dossier.iterdir() if p.name != "INDEX.txt"]
        if not restes:
            shutil.rmtree(dossier, ignore_errors=True)
    except OSError:
        pass


def reecrire_index(dossier_date: Path, cfg: dict | None = None) -> None:
    """INDEX.txt du jour : score | genre | titre | adresse — trié par score."""
    if not dossier_date.exists():
        return
    lignes = []
    for sous in sorted(dossier_date.iterdir()):
        fiche = sous / "fiche.json"
        if not fiche.is_file():
            continue
        try:
            f = json.loads(fiche.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        lignes.append((int(f.get("score") or 0), LIBELLES_GENRE.get(f.get("genre"), f.get("genre", "")),
                       f.get("titre", ""), f.get("url", ""), sous.name))
    lignes.sort(key=lambda l: -l[0])
    contenu = [f"# {dossier_date.name} — {len(lignes)} fiche(s), réécrit le "
               f"{datetime.now():%Y-%m-%d %H:%M}", ""]
    for score, genre, titre, url, nom in lignes:
        contenu.append(f"{score:>3} | {genre:<21} | {titre[:90]:<90} | {url}\n"
                       f"    └ {nom}/")
    try:
        (dossier_date / "INDEX.txt").write_text("\n".join(contenu) + "\n", encoding="utf-8")
    except OSError:
        pass


# ── Images ──────────────────────────────────────────────────────────────────
def telecharger_images(urls: list[str], dossier: Path, cfg: dict, deja: int = 0) -> list[str]:
    """Rapatrie jusqu'à `images_max` images assez larges. Rend les noms de fichiers."""
    try:
        from PIL import Image
    except ImportError:
        return []
    maximum = int(cfg.get("images_max", 4))
    largeur_min = int(cfg.get("largeur_image_min", 400))
    noms: list[str] = []
    for url in urls:
        if len(noms) + deja >= maximum:
            break
        try:
            r = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (HourdisBot)"},
                             timeout=20, stream=True)
            if not r.ok:
                continue
            octets = r.raw.read(8_000_000, decode_content=True)
        except (requests.RequestException, OSError):
            continue
        try:
            image = Image.open(io.BytesIO(octets))
            image.load()
        except Exception:
            continue
        if image.width < largeur_min:
            continue
        dossier.mkdir(parents=True, exist_ok=True)
        extension = {"JPEG": "jpg", "PNG": "png", "WEBP": "webp"}.get(image.format or "", "jpg")
        nom = f"image-{deja + len(noms) + 1}.{extension}"
        try:
            if image.mode not in ("RGB", "RGBA", "L"):
                image = image.convert("RGB")
            if image.width > 1600:
                image = image.resize((1600, int(image.height * 1600 / image.width)))
            if extension == "jpg" and image.mode == "RGBA":
                image = image.convert("RGB")
            image.save(dossier / nom, quality=88)
        except Exception:
            continue
        noms.append(f"images/{nom}")
    return noms


def ouvrir_dans_explorateur(relatif: str = "", cfg: dict | None = None) -> str:
    """Ouvre le dossier (Windows) — rend le chemin ouvert."""
    cfg = cfg or cfg_mod.charger()
    cible = (racine(cfg) / relatif) if relatif else racine(cfg)
    cible.mkdir(parents=True, exist_ok=True)
    try:
        os.startfile(str(cible))          # type: ignore[attr-defined]
    except (AttributeError, OSError):
        pass
    return str(cible)
