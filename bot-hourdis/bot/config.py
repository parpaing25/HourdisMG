"""Configuration du bot de veille Hourdis.

Tout ce qui se règle vit dans data/config.json (créé au premier lancement à
partir des valeurs ci-dessous, et complété à chaque clé nouvelle). Les secrets
ne sont JAMAIS ici : ils se lisent à l'exécution dans ~/.hourdis-secrets/, avec
un repli sur le .env du profil Hermes « hourdis », qui porte déjà le jeton de la
page Facebook et la clé Groq.

Ce bot est le QUATRIÈME bot de collecte de la machine, et le premier tourné
vers le web ouvert plutôt que vers Facebook : il reprend ce que les trois
autres (Fonenako 8756, Diako 8757, AKORA 8758) ont appris — la toile de Diako,
la fraîcheur et le planificateur d'AKORA, la prospection de sources des trois —
et le port suivant, 8761 (le 8760 est le poste de pilotage).
"""
from __future__ import annotations

import json
import os
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent

# Le dossier de travail se déplace par variable d'environnement : un test qui
# tourne contre la VRAIE base a déjà effacé les 32 sources d'Andry chez AKORA
# (23/08/2026). Les tests posent HOURDIS_BOT_DATA sur un dossier jetable.
DOSSIER_DONNEES = Path(os.environ.get("HOURDIS_BOT_DATA") or (RACINE / "data"))
BASE = DOSSIER_DONNEES / "bot.db"
FICHIER_CONFIG = DOSSIER_DONNEES / "config.json"
PROFIL_NAVIGATEUR = DOSSIER_DONNEES / "profil-fb"

SECRETS = Path.home() / ".hourdis-secrets"
FICHIER_FACEBOOK = SECRETS / "facebook.txt"        # FB_PAGE_ID=… / FB_PAGE_TOKEN=…
CLE_ANTHROPIC = SECRETS / "anthropic_key.txt"
CLE_ANTHROPIC_REPLI = Path.home() / ".fonenako-secrets" / "anthropic_key.txt"
CLE_COMPATIBLE = SECRETS / "llm_key.txt"           # Groq, Cerebras… (OpenAI-compatible)
ENV_HERMES = Path.home() / ".hermes" / "profiles" / "hourdis" / ".env"

PORT = 8761
NOM_BOT = "hourdis"          # identifiant pour le verrou navigateur partagé

DEFAUTS = {
    # ── Ce qu'on garde ───────────────────────────────────────────────────
    # En dessous de ce score (0-100, voir score.py), la trouvaille est notée
    # « écartée » : elle reste visible dans l'onglet Trouvailles (filtre
    # « écartées ») pour régler le tri, mais n'entre pas dans les dossiers.
    "score_min": 35,
    # 0 = pas de limite d'âge. Un tuto de pose de 2018 vaut encore ; ce sont
    # les ACTUALITÉS qui vieillissent, et elles passent par `jours_max_actualites`.
    "jours_max": 0,
    "jours_max_actualites": 540,
    "annee_minimum": 2012,
    "langues": ["fr", "mg", "en"],
    "penalite_anglais": 12,
    # Vide = le lexique par défaut (lexique.py). Ce qu'on met ici S'AJOUTE.
    "mots_metier": [],
    "repoussoirs": [],
    "garder_les_ecartees": True,      # en base seulement, jamais en dossier

    # ── Budget par source et par tournée ─────────────────────────────────
    "videos_par_recherche": 12,
    "videos_details_max": 15,         # fiches complètes yt-dlp (1 requête chacune)
    "transcrire_videos": True,
    "transcriptions_max": 8,          # sous-titres lus par tournée
    "articles_par_flux": 20,
    "resultats_par_recherche_web": 15,
    "pages_par_site": 10,
    "lire_les_pdf": True,
    "pdf_pages_max": 12,
    "telecharger_images": True,
    "images_max": 4,
    "largeur_image_min": 400,

    # ── Rangement : un dossier par DATE DE PUBLICATION ────────────────────
    # Vide = data/collecte. Un chemin absolu déplace toute l'arborescence
    # (⚠ sur C:, jamais sur G: pendant une synchronisation Drive).
    "dossier_collecte": "",

    # ── Partie Facebook, volontairement PETITE ────────────────────────────
    # Le web est la source principale. Facebook ne sert qu'à suivre deux ou
    # trois pages de métier : peu de défilements, pauses humaines.
    "facebook_actif": True,
    "scrolls_max_par_source": 6,
    "posts_max_par_source": 15,
    "pause_entre_scrolls": [2.0, 4.0],
    "pause_entre_sources": [10, 25],
    "navigateur_visible": True,
    # 🔴 Sous ce seuil de mémoire engageable (Mo), Chromium ne s'ouvre pas :
    #   le 23/08/2026 la machine est descendue à 189 Mo et a tué trois bots.
    "memoire_mini_mo": 900,
    "largeur_photo_min": 400,
    # La partie WEB (requests, yt-dlp : ~100 Mo) tourne même quand une session
    # Claude est ouverte ; seule la partie Chromium attend (règle du 03/09).
    # Mettre à FAUX pour suspendre toute la tournée automatique.
    "web_pendant_session_claude": True,

    # ── Relecture par un modèle — FACULTATIVE ─────────────────────────────
    # Le tri et le rangement n'en dépendent jamais. Le modèle résume, tire
    # 3 à 5 conseils, et rédige un brouillon de publication FR + MG.
    "llm_actif": False,
    # 'compatible' (Groq, Cerebras… : URL OpenAI + clé) | 'anthropic' | 'passerelle'
    "llm_transport": "compatible",
    "llm_url": "https://api.groq.com/openai/v1",
    "llm_modele": "llama-3.3-70b-versatile",
    "llm_passerelle": "http://127.0.0.1:4000",
    "llm_modele_passerelle": "claude-abo",
    "llm_modele_anthropic": "claude-sonnet-5",
    "llm_delai": 90,
    "llm_relire_auto": False,          # relire les meilleures après chaque tournée
    "llm_relire_max": 6,
    "llm_score_min_pour_relire": 50,

    # ── Publication sur la page Facebook « Hourdis Madagascar » ───────────
    # FAUX : le bot PRÉPARE les publications (post-facebook.txt dans chaque
    # dossier, onglet Publication), mais n'envoie rien. Allumer pour que le
    # bouton « Publier » et la programmation parlent vraiment à Meta.
    "publication_active": False,
    # Quand VRAI : aux heures dites, le planificateur publie la PROCHAINE
    # trouvaille que vous avez passée en « programmée » — jamais une que vous
    # n'avez pas relue.
    "publication_auto_programmee": False,
    "heures_publication": ["07:00", "19:00"],
    "publier_avec_photo": True,
    # ── « Publier en un clic » : refait le texte, importe les médias, envoie ──
    "un_clic_refaire_texte": True,    # réécrit le brouillon à chaque clic (modèle si allumé, sinon gabarit)
    "un_clic_video": True,            # pour une vidéo YouTube : la télécharger et la publier en vidéo native
    "un_clic_photos_max": 4,          # images attachées à une publication (article, PDF, post)
    "video_hauteur_max": 720,         # 720p suffit à Facebook et pèse 4 fois moins que 1080p
    "video_taille_max_mo": 250,
    "video_duree_max_s": 1500,        # au-delà de 25 min, on publie la vignette et le lien
    "langue_post": "mix",             # 'fr' | 'mg' | 'mix'
    "contact_ligne": "📞 032 47 041 43 | 033 71 063 34 · 🌐 https://hourdis.fonenako.mg/",
    "hashtags": "#Hourdis #ConstructionMadagascar #TranoGasy #BriqueMadagascar #TerreCuite",
    "signature_source": True,

    # ── Collectes automatiques ───────────────────────────────────────────
    "collecte_auto": False,
    "heures_collecte": ["08:30", "18:30"],
    "objectif_par_jour": 8,           # trouvailles GARDABLES (score ≥ min) par jour

    # ── Découverte de nouvelles sources ──────────────────────────────────
    "decouverte_auto": False,
    "decouverte_jours": 7,
    "decouverte_note_min": 55,
}


def charger() -> dict:
    """Lit data/config.json, le crée au besoin, et y réécrit toute clé manquante.

    Une clé neuve ajoutée au code doit apparaître dans le fichier : un réglage
    qu'on ne peut pas lire n'est pas un réglage, c'est une constante cachée.
    """
    DOSSIER_DONNEES.mkdir(parents=True, exist_ok=True)
    config = dict(DEFAUTS)
    if FICHIER_CONFIG.exists():
        try:
            sur_disque = json.loads(FICHIER_CONFIG.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            sur_disque = {}
        config.update(sur_disque)
        if set(DEFAUTS) - set(sur_disque):
            try:
                enregistrer(config)
            except OSError:
                pass
    else:
        enregistrer(config)
    return config


def enregistrer(config: dict) -> None:
    DOSSIER_DONNEES.mkdir(parents=True, exist_ok=True)
    FICHIER_CONFIG.write_text(
        json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def dossier_collecte(config: dict | None = None) -> Path:
    config = config or charger()
    chemin = (config.get("dossier_collecte") or "").strip()
    return Path(chemin) if chemin else DOSSIER_DONNEES / "collecte"


def lire_env(chemin: Path) -> dict:
    """Lit un fichier `clé=valeur` (BOM toléré). Ne jamais logguer le retour."""
    valeurs: dict[str, str] = {}
    if not chemin.exists():
        return valeurs
    for ligne in chemin.read_text(encoding="utf-8-sig").splitlines():
        ligne = ligne.strip().strip("﻿")
        if not ligne or ligne.startswith("#") or "=" not in ligne:
            continue
        cle, _, valeur = ligne.partition("=")
        valeurs[cle.strip()] = valeur.strip().strip('"').strip("'")
    return valeurs


def secrets_facebook() -> tuple[str, str]:
    """(identifiant de la page, jeton). Vide si rien n'est configuré.

    D'abord ~/.hourdis-secrets/facebook.txt, sinon le .env du profil Hermes
    « hourdis » — c'est là que le jeton de la page a été posé le 16/07/2026.
    """
    for chemin in (FICHIER_FACEBOOK, ENV_HERMES):
        env = lire_env(chemin)
        page, jeton = env.get("FB_PAGE_ID", ""), env.get("FB_PAGE_TOKEN", "")
        if page and jeton:
            return page, jeton
    return "", ""


def cle_llm_compatible() -> str:
    """Clé du fournisseur OpenAI-compatible (Groq par défaut)."""
    if CLE_COMPATIBLE.exists():
        valeur = CLE_COMPATIBLE.read_text(encoding="utf-8-sig").strip()
        if valeur:
            return valeur
    return lire_env(ENV_HERMES).get("GROQ_API_KEY", "")


def cle_anthropic() -> str:
    for chemin in (CLE_ANTHROPIC, CLE_ANTHROPIC_REPLI):
        if chemin.exists():
            valeur = chemin.read_text(encoding="utf-8-sig").strip()
            if valeur:
                return valeur
    return ""
