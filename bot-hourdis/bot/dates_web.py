"""De quand date une PAGE WEB ? — la date de publication, ou `None`, jamais aujourd'hui.

Le rangement du bot repose sur cette date : un dossier par jour de publication.
La règle héritée de `fraicheur.py` (AKORA, 24/08/2026) s'applique telle quelle :
**on ne remplace pas une date inconnue par la date du jour**. Une fiche datée du
jour alors qu'elle vient d'un article de 2019 est un mensonge rangé.

Les pistes, du plus sûr au plus douteux — la première qui parle gagne, et
l'ORIGINE est rendue avec la date pour que la fiche dise d'où elle la tient :

  1. `jsonld`  — datePublished / uploadDate dans <script type="application/ld+json">
  2. `meta`    — article:published_time, name=date|pubdate|publish_date, DC.date…
  3. `time`    — <time datetime="…"> (pubdate ou premier de la page)
  4. `url`     — /2024/03/12/ ou 2024-03-12 dans le chemin
  5. `texte`   — « Publié le 12 mars 2024 » dans les 800 premiers caractères
  6. `url_mois`— /2024/03/ : le 1er du mois, marqué comme approximatif

Une date dans le futur ou avant 2000 est refusée : c'est une date de scénario,
d'événement ou de copyright, pas une date de publication.
"""
from __future__ import annotations

import html as _html
import json
import re
from datetime import date, datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

from . import fraicheur

_JSONLD = re.compile(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
                     re.I | re.S)
_CLES_JSONLD = ("datePublished", "uploadDate", "dateCreated", "datePosted")
_META = re.compile(r"<meta\b[^>]*>", re.I)
_ATTR = re.compile(r'([a-zA-Z_:.-]+)\s*=\s*(?:"([^"]*)"|\'([^\']*)\'|([^\s>]+))')
_NOMS_META = {
    "article:published_time", "og:article:published_time", "article:published",
    "datepublished", "date", "pubdate", "publishdate", "publish_date", "publish-date",
    "publication_date", "dc.date", "dc.date.issued", "dcterms.created", "dcterms.issued",
    "sailthru.date", "parsely-pub-date", "citation_publication_date", "og:pubdate",
    "uploaddate", "video:release_date",
}
_TIME = re.compile(r"<time\b([^>]*)>", re.I)
_URL_JOUR = re.compile(r"/(20\d{2})[/-](0?[1-9]|1[0-2])[/-](0?[1-9]|[12]\d|3[01])(?:/|-|\.|$)")
_URL_ISO = re.compile(r"(20\d{2})-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])")
_URL_MOIS = re.compile(r"/(20\d{2})/(0?[1-9]|1[0-2])/")
_ANCRE_TEXTE = re.compile(
    r"(publie le|publiee le|mis a jour le|mise a jour le|date de publication|posted on|"
    r"published on|published|updated|le )\s*:?\s*([^\n]{6,40})")


def _plausible(quand: date | None, aujourdhui: date) -> date | None:
    if quand is None:
        return None
    if quand.year < 2000 or quand > aujourdhui + timedelta(days=1):
        return None
    return quand


def lire_iso(valeur: str, aujourdhui: date | None = None) -> date | None:
    """« 2024-03-12T10:00:00+01:00 », « 2024-03-12 », « Tue, 12 Mar 2024 07:00:00 GMT »,
    « 20240312 » (yt-dlp) — ou None."""
    aujourdhui = aujourdhui or date.today()
    texte = _html.unescape((valeur or "").strip())
    if not texte:
        return None
    if re.fullmatch(r"20\d{6}", texte):
        try:
            return _plausible(datetime.strptime(texte, "%Y%m%d").date(), aujourdhui)
        except ValueError:
            return None
    trouve = _URL_ISO.search(texte)
    if trouve:
        try:
            return _plausible(date(int(trouve[1]), int(trouve[2]), int(trouve[3])), aujourdhui)
        except ValueError:
            return None
    try:
        return _plausible(parsedate_to_datetime(texte).date(), aujourdhui)
    except (TypeError, ValueError, IndexError):
        pass
    if re.fullmatch(r"\d{9,11}", texte):          # horodatage Unix
        try:
            return _plausible(datetime.fromtimestamp(int(texte), timezone.utc).date(), aujourdhui)
        except (ValueError, OverflowError, OSError):
            return None
    return None


def _chercher_jsonld(objet, profondeur: int = 0) -> str:
    if profondeur > 6:
        return ""
    if isinstance(objet, dict):
        for cle in _CLES_JSONLD:
            if isinstance(objet.get(cle), str) and objet[cle].strip():
                return objet[cle]
        for valeur in objet.values():
            trouve = _chercher_jsonld(valeur, profondeur + 1)
            if trouve:
                return trouve
    elif isinstance(objet, list):
        for valeur in objet:
            trouve = _chercher_jsonld(valeur, profondeur + 1)
            if trouve:
                return trouve
    return ""


def _attributs(balise: str) -> dict:
    return {m[1].lower(): _html.unescape(m[2] or m[3] or m[4] or "") for m in _ATTR.finditer(balise)}


def date_dans_texte(texte: str, aujourdhui: date | None = None) -> date | None:
    """Une date ABSOLUE AVEC ANNÉE dans un texte, ou None. Les formes sans année
    (« 12 mars ») sont refusées ici : sur une page web, elles désignent aussi
    bien un événement à venir qu'une publication."""
    aujourdhui = aujourdhui or date.today()
    reduit = fraicheur.sans_accents(fraicheur._propre(texte))
    for _, morceau in _ANCRE_TEXTE.findall(reduit):
        quand = _absolue_avec_annee(morceau, aujourdhui)
        if quand:
            return quand
    return _absolue_avec_annee(reduit, aujourdhui)


def _absolue_avec_annee(reduit: str, aujourdhui: date) -> date | None:
    trouve = fraicheur._RE_ISO.search(reduit)
    if trouve:
        return _plausible(fraicheur._construire(int(trouve[1]), int(trouve[2]), int(trouve[3])),
                          aujourdhui)
    trouve = fraicheur._RE_JOUR_MOIS.search(reduit)
    if trouve and trouve[3]:
        return _plausible(fraicheur._construire(int(trouve[3]), fraicheur.MOIS[trouve[2]],
                                                int(trouve[1])), aujourdhui)
    trouve = fraicheur._RE_MOIS_JOUR.search(reduit)
    if trouve and trouve[3]:
        return _plausible(fraicheur._construire(int(trouve[3]), fraicheur.MOIS[trouve[1]],
                                                int(trouve[2])), aujourdhui)
    trouve = fraicheur._RE_NUMERIQUE.search(reduit)
    if trouve:
        premier, second, annee = int(trouve[1]), int(trouve[2]), int(trouve[3])
        if annee < 100:
            annee += 2000
        if premier <= 12 < second:
            mois, jour = premier, second
        else:
            jour, mois = premier, second
        return _plausible(fraicheur._construire(annee, mois, jour), aujourdhui)
    return None


def date_de_page(code: str, url: str = "", texte: str = "",
                 aujourdhui: date | None = None) -> tuple[date | None, str]:
    """Rend (date, origine). `origine` vaut '' quand la date est inconnue."""
    aujourdhui = aujourdhui or date.today()
    code = code or ""

    # 1. JSON-LD
    for bloc in _JSONLD.findall(code)[:6]:
        try:
            objet = json.loads(bloc.strip())
        except json.JSONDecodeError:
            # Beaucoup de sites collent deux objets ou une virgule de trop : on
            # rattrape la valeur à la main plutôt que de perdre la piste.
            trouve = re.search(r'"(?:datePublished|uploadDate|dateCreated)"\s*:\s*"([^"]+)"', bloc)
            objet = {"datePublished": trouve[1]} if trouve else None
        quand = lire_iso(_chercher_jsonld(objet), aujourdhui) if objet else None
        if quand:
            return quand, "jsonld"

    # 2. <meta>
    for balise in _META.findall(code[:200_000]):
        attrs = _attributs(balise)
        nom = (attrs.get("property") or attrs.get("name") or attrs.get("itemprop") or "").lower()
        if nom in _NOMS_META and attrs.get("content"):
            quand = lire_iso(attrs["content"], aujourdhui)
            if quand:
                return quand, "meta"

    # 3. <time datetime>
    premier = None
    for balise in _TIME.findall(code[:300_000]):
        attrs = _attributs(balise)
        valeur = attrs.get("datetime") or attrs.get("content") or ""
        quand = lire_iso(valeur, aujourdhui)
        if not quand:
            continue
        piste = (attrs.get("class", "") + " " + attrs.get("itemprop", "") + " " +
                 ("pubdate" if "pubdate" in attrs else "")).lower()
        if re.search(r"publi|pubdate|date-?published|posted|entry-date", piste):
            return quand, "time"
        premier = premier or quand
    if premier:
        return premier, "time"

    # 4. L'adresse
    chemin = url or ""
    trouve = _URL_JOUR.search(chemin) or _URL_ISO.search(chemin)
    if trouve:
        quand = _plausible(fraicheur._construire(int(trouve[1]), int(trouve[2]), int(trouve[3])),
                           aujourdhui)
        if quand:
            return quand, "url"

    # 5. Le texte
    if texte:
        quand = date_dans_texte(texte[:800], aujourdhui)
        if quand:
            return quand, "texte"

    # 6. Le mois dans l'adresse — approximatif, dit comme tel
    trouve = _URL_MOIS.search(chemin)
    if trouve:
        quand = _plausible(fraicheur._construire(int(trouve[1]), int(trouve[2]), 1), aujourdhui)
        if quand:
            return quand, "url_mois"

    return None, ""
