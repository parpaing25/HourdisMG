"""Flux RSS et Atom : la presse du bâtiment, Google Actualités, Bing, YouTube.

Un flux est la source la moins chère qui existe : une requête, vingt titres
datés. Trois usages ici :

  - un flux déclaré tel quel (le blog d'un fabricant, un magazine) ;
  - une RECHERCHE WEB : Google Actualités et Bing rendent chacun un flux RSS
    pour n'importe quelle requête, sans clé ni compte — c'est ce qui remplace
    le moteur de recherche que le bot n'a pas ;
  - le flux Atom d'une CHAÎNE YouTube : ses quinze dernières vidéos, datées,
    sans passer par yt-dlp.

🔴 LES LIENS DE GOOGLE ACTUALITÉS NE SONT PAS DES LIENS. Depuis 2024,
   `news.google.com/rss/articles/CBMi…` ne redirige plus par HTTP : la page
   rendue contient une signature, et c'est un appel `batchexecute` qui donne
   l'adresse réelle (vérifié le 06/09/2026 : un lien Batirama en clair). Sans
   cette résolution, toutes les trouvailles de Google auraient la même
   adresse d'hôte et l'article ne serait jamais lu.
"""
from __future__ import annotations

import html
import json
import re
import xml.etree.ElementTree as ET
from datetime import date
from urllib.parse import quote_plus

import requests

from . import dates_web, toile

NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "media": "http://search.yahoo.com/mrss/",
    "yt": "http://www.youtube.com/xml/schemas/2015",
    "content": "http://purl.org/rss/1.0/modules/content/",
    "dc": "http://purl.org/dc/elements/1.1/",
}


def flux_google_actualites(requete: str, langue: str = "fr") -> str:
    pays = {"fr": "FR:fr", "en": "US:en", "mg": "MG:fr"}.get(langue, "FR:fr")
    hl = {"fr": "fr", "en": "en-US", "mg": "fr"}.get(langue, "fr")
    return (f"https://news.google.com/rss/search?q={quote_plus(requete)}"
            f"&hl={hl}&gl={pays.split(':')[0]}&ceid={pays}")


def flux_bing(requete: str) -> str:
    return f"https://www.bing.com/search?format=rss&q={quote_plus(requete)}"


def flux_chaine_youtube(channel_id: str) -> str:
    return f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"


def _texte(element, chemin: str, ns: dict | None = None) -> str:
    trouve = element.find(chemin, ns or {}) if element is not None else None
    if trouve is None:
        return ""
    return html.unescape((trouve.text or "").strip())


def _sans_balises(code: str) -> str:
    texte = re.sub(r"<[^>]+>", " ", html.unescape(code or ""))
    return re.sub(r"\s+", " ", texte).strip()


# ⚠ LES FLUX DES MOTEURS NE PASSENT PAS PAR robots.txt. Mesuré le 06/09/2026 à la
#   première tournée : news.google.com/robots.txt interdit /rss/search et
#   bing.com/robots.txt interdit /search — aux ROBOTS D'INDEXATION. Un flux RSS
#   est un produit servi aux lecteurs de flux (c'est son seul usage), et un
#   lecteur de flux n'a jamais lu robots.txt. Appliquer la règle ici tuait la
#   recherche web entière (0 examinée) au nom d'une politesse hors de propos.
#   La cadence par hôte, elle, s'applique toujours : une requête, vingt titres.
HOTES_FLUX_SANS_ROBOTS = ("news.google.com", "www.bing.com", "bing.com", "www.youtube.com")


def lire_flux(url: str, session: requests.Session | None = None) -> tuple[list[dict], str]:
    """Rend ([entrées], raison). Une entrée : {titre, url, resume, publie_le, auteur,
    image, video_id, chaine_id, vues, source}."""
    session = session or requests.Session()
    if toile._hote(url) not in HOTES_FLUX_SANS_ROBOTS and not toile.robots_autorise(url):
        return [], "robots"
    toile._patienter(url)
    r, raison = toile._requete(url, session)
    if r is None:
        return [], raison
    try:
        racine = ET.fromstring(r.content)
    except ET.ParseError as e:
        return [], f"flux illisible ({str(e)[:60]})"
    etiquette = racine.tag.lower()
    if etiquette.endswith("feed"):
        return _lire_atom(racine), ""
    return _lire_rss(racine), ""


def _lire_rss(racine) -> list[dict]:
    entrees = []
    for item in racine.iter("item"):
        titre = _texte(item, "title")
        lien = _texte(item, "link")
        if not lien:
            # Certains flux mettent le lien dans <guid isPermaLink="true">
            guid = item.find("guid")
            if guid is not None and (guid.get("isPermaLink") or "true") != "false":
                lien = (guid.text or "").strip()
        if not lien:
            continue
        description = _texte(item, "description") or _texte(item, "content:encoded", NS)
        source_nom = _texte(item, "source")
        # Google Actualités : « Titre - Éditeur ».
        if "news.google.com" in lien and " - " in titre:
            titre, _, editeur = titre.rpartition(" - ")
            source_nom = source_nom or editeur.strip()
        quand = dates_web.lire_iso(_texte(item, "pubDate") or _texte(item, "dc:date", NS))
        image = ""
        media = item.find("media:content", NS)
        if media is None:
            media = item.find("media:thumbnail", NS)
        if media is not None:
            image = media.get("url", "")
        enclosure = item.find("enclosure")
        if not image and enclosure is not None and "image" in (enclosure.get("type") or ""):
            image = enclosure.get("url", "")
        entrees.append({
            "titre": titre, "url": lien.strip(), "resume": _sans_balises(description)[:1500],
            "publie_le": quand, "auteur": _texte(item, "dc:creator", NS) or _texte(item, "author"),
            "image": image, "video_id": "", "chaine_id": "", "vues": None, "source": source_nom,
        })
    return entrees


def _lire_atom(racine) -> list[dict]:
    entrees = []
    for entry in racine.findall("atom:entry", NS):
        titre = _texte(entry, "atom:title", NS)
        lien = ""
        for l in entry.findall("atom:link", NS):
            if (l.get("rel") or "alternate") == "alternate":
                lien = l.get("href", "")
                break
        video_id = _texte(entry, "yt:videoId", NS)
        chaine_id = _texte(entry, "yt:channelId", NS)
        if video_id and not lien:
            lien = f"https://www.youtube.com/watch?v={video_id}"
        if not lien:
            continue
        groupe = entry.find("media:group", NS)
        resume = _texte(groupe, "media:description", NS) if groupe is not None else ""
        resume = resume or _sans_balises(_texte(entry, "atom:summary", NS)
                                         or _texte(entry, "atom:content", NS))
        image = ""
        vues = None
        if groupe is not None:
            vignette = groupe.find("media:thumbnail", NS)
            image = vignette.get("url", "") if vignette is not None else ""
            stats = groupe.find("media:community/media:statistics", NS)
            if stats is not None and stats.get("views"):
                try:
                    vues = int(stats.get("views"))
                except ValueError:
                    vues = None
        quand = dates_web.lire_iso(_texte(entry, "atom:published", NS)
                                   or _texte(entry, "atom:updated", NS))
        auteur = _texte(entry, "atom:author/atom:name", NS)
        auteur_url = _texte(entry, "atom:author/atom:uri", NS)
        entrees.append({
            "titre": titre, "url": lien, "resume": resume[:1500], "publie_le": quand,
            "auteur": auteur, "auteur_url": auteur_url, "image": image, "video_id": video_id,
            "chaine_id": chaine_id, "vues": vues, "source": "",
        })
    return entrees


# ── Google Actualités : retrouver l'adresse réelle ─────────────────────────
_SIGNATURE = re.compile(r'data-n-a-sg="([^"]+)"')
_HORODATAGE = re.compile(r'data-n-a-ts="([^"]+)"')
_URL_DANS_REPONSE = re.compile(r'https?://(?!news\.google|www\.google)[^"\\\]\s]+')


def resoudre_lien_google(url: str, session: requests.Session | None = None) -> str:
    """L'adresse réelle derrière un lien `news.google.com/rss/articles/…`.

    Trois essais : la redirection HTTP (anciens liens), le décodage base64 de
    l'identifiant (format 2023), puis `batchexecute` (format actuel). En cas
    d'échec, on rend le lien Google lui-même — la trouvaille garde son titre et
    son éditeur, elle n'a simplement pas de texte.
    """
    if "news.google.com" not in url:
        return url
    session = session or requests.Session()
    en_tetes = {"User-Agent": toile.AGENT_NAVIGATEUR, "Accept-Language": "fr"}
    try:
        r = session.get(url, headers=en_tetes, timeout=20, allow_redirects=True)
    except requests.RequestException:
        return url
    if "news.google.com" not in r.url:
        return r.url
    identifiant = url.split("/articles/")[-1].split("?")[0]
    # Format 2023 : l'adresse en clair dans le base64.
    try:
        import base64
        brut = base64.urlsafe_b64decode(identifiant + "=" * (-len(identifiant) % 4))
        trouve = re.search(rb"https?://[\x21-\x7e]{8,}", brut)
        if trouve:
            return trouve.group(0).decode("ascii", "ignore").rstrip("\x01\x02\x03")
    except Exception:
        pass
    signature, horodatage = _SIGNATURE.search(r.text), _HORODATAGE.search(r.text)
    if not (signature and horodatage):
        return url
    requete = [["Fbv4je", json.dumps([
        "garturlreq",
        [["X", "X", ["X", "X"], None, None, 1, 1, "US:en", None, 1, None, None, None, None,
          None, 0, 1], "X", "X", 1, [1, 1, 1], 1, 1, None, 0, 0, None, 0],
        identifiant, horodatage.group(1), signature.group(1)]), None, "generic"]]
    try:
        r2 = session.post(
            "https://news.google.com/_/DotsSplashUi/data/batchexecute",
            data={"f.req": json.dumps([requete])},
            headers={**en_tetes, "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"},
            timeout=20)
    except requests.RequestException:
        return url
    trouve = _URL_DANS_REPONSE.search(r2.text)
    if not trouve:
        return url
    return trouve.group(0).replace("\\u003d", "=").replace("\\u0026", "&")


def entrees_recherche_web(requete: str, langue: str, limite: int,
                          session: requests.Session | None = None) -> tuple[list[dict], list[str]]:
    """Google Actualités + Bing pour une requête : entrées dédoublonnées, raisons d'échec."""
    session = session or requests.Session()
    entrees: list[dict] = []
    raisons: list[str] = []
    vues: set[str] = set()
    for nom, adresse in (("Google Actualités", flux_google_actualites(requete, langue)),
                         ("Bing", flux_bing(requete))):
        lot, raison = lire_flux(adresse, session)
        if raison:
            raisons.append(f"{nom} : {toile.LIBELLES_ECHEC.get(raison, raison)}")
            continue
        for e in lot:
            e["moteur"] = nom
            if e["url"] in vues:
                continue
            vues.add(e["url"])
            entrees.append(e)
    return entrees[:limite * 2], raisons


def est_recent(quand: date | None, jours_max: int) -> bool:
    return quand is None or jours_max <= 0 or (date.today() - quand).days <= jours_max
