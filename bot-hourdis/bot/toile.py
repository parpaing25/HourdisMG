"""Le web ouvert : lire une page, un site de fabricant, un guide PDF — poliment.

Repris de la toile du bot Diako (celle qui lit les sites d'hôtels), avec ce
qu'elle a appris en production : robots.txt lu une fois par hôte (un robots.txt
injoignable vaut autorisation), deux secondes entre deux pages du même hôte,
décodage sans se fier à l'en-tête, et la RAISON d'un échec rendue au lieu d'être
avalée (« DNS mort » et « 403 » ne se soignent pas pareil).

Ce qui change pour Hourdis : on cherche du CONTENU ÉDITORIAL — un article, un
guide, une fiche technique — pas une grille de tarifs. D'où `contenu_principal`
(le corps d'un article plutôt que son gabarit) et `pages_a_visiter` réglé sur
« conseils / guides / pose / brique / tuile ».
"""
from __future__ import annotations

import html
import io
import re
import threading
import time
import urllib.robotparser
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit, urlunsplit

import requests

AGENT = ("Mozilla/5.0 (compatible; HourdisBot/1.0; +https://hourdis.fonenako.mg) "
         "veille technique terre cuite")
AGENT_NAVIGATEUR = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36")
EN_TETES = {"User-Agent": AGENT, "Accept-Language": "fr,mg;q=0.9,en;q=0.7"}

LIBELLES_ECHEC = {
    "dns": "adresse introuvable (le domaine n'existe plus)",
    "injoignable": "site injoignable",
    "delai": "site injoignable (délai dépassé)",
    "ssl": "certificat HTTPS invalide",
    "403": "accès refusé par le site (HTTP 403)",
    "404": "page absente (HTTP 404)",
    "5xx": "erreur du serveur (HTTP 5xx)",
    "robots": "robots.txt l'interdit",
    "pas_html": "pas une page HTML",
}

OCTETS_MAX = 2_500_000
OCTETS_MAX_PDF = 25_000_000
DELAI_ENTRE_PAGES = 2.0
DELAI = 25

_robots: dict = {}
_verrou_robots = threading.Lock()
_dernier_appel: dict = {}
_verrou_cadence = threading.Lock()


# ── Politesse ───────────────────────────────────────────────────────────────
def _hote(url: str) -> str:
    return urlsplit(url).netloc.lower()


def _sans_www(hote: str) -> str:
    return hote[4:] if hote.startswith("www.") else hote


def robots_autorise(url: str) -> bool:
    decoupe = urlsplit(url)
    cle = (decoupe.scheme, decoupe.netloc.lower())
    with _verrou_robots:
        lecteur = _robots.get(cle)
    if lecteur is None:
        lecteur = _lire_robots(decoupe.scheme, decoupe.netloc)
        with _verrou_robots:
            _robots[cle] = lecteur
    if lecteur is False:
        return True
    try:
        return lecteur.can_fetch("HourdisBot", url)
    except Exception:
        return True


def _lire_robots(scheme: str, hote: str):
    lecteur = urllib.robotparser.RobotFileParser()
    try:
        r = requests.get(f"{scheme}://{hote}/robots.txt", headers=EN_TETES, timeout=10)
    except requests.RequestException:
        return False
    if r.status_code >= 400 or "html" in r.headers.get("Content-Type", "").lower():
        return False
    try:
        lecteur.parse(r.text.splitlines())
    except Exception:
        return False
    return lecteur


def _patienter(url: str) -> None:
    hote = _hote(url)
    with _verrou_cadence:
        precedent = _dernier_appel.get(hote, 0.0)
        attente = DELAI_ENTRE_PAGES - (time.time() - precedent)
        _dernier_appel[hote] = time.time() + max(attente, 0)
    if attente > 0:
        time.sleep(attente)


# ── Récupération ────────────────────────────────────────────────────────────
def _decoder(reponse: requests.Response) -> str:
    octets = reponse.content[:OCTETS_MAX]
    declare = re.search(rb'charset=["\']?\s*([\w-]+)', octets[:4000], re.I)
    for encodage in (
        (declare.group(1).decode("ascii", "ignore") if declare else None),
        reponse.encoding if (reponse.encoding or "").lower() != "iso-8859-1" else None,
        "utf-8",
    ):
        if not encodage:
            continue
        try:
            return octets.decode(encodage, "strict")
        except (LookupError, UnicodeDecodeError):
            continue
    return octets.decode("utf-8", "replace")


def _requete(url: str, session, stream: bool = False):
    """Une requête GET avec les deux agents et les codes 429/503 respectés.
    Rend (reponse | None, raison)."""
    r = None
    for agent in (AGENT, AGENT_NAVIGATEUR):
        try:
            r = session.get(url, headers={**EN_TETES, "User-Agent": agent}, timeout=DELAI,
                            allow_redirects=True, stream=stream)
        except requests.exceptions.SSLError:
            return None, "ssl"
        except requests.exceptions.Timeout:
            return None, "delai"
        except requests.exceptions.ConnectionError as e:
            texte = str(e)
            if "NameResolution" in texte or "getaddrinfo" in texte or "Name or service" in texte:
                return None, "dns"
            return None, "injoignable"
        except requests.RequestException:
            return None, "injoignable"
        if r.status_code in (429, 503):
            try:
                pause = min(int(r.headers.get("Retry-After") or 5), 20)
            except ValueError:
                pause = 5
            time.sleep(pause)
            continue
        if r.status_code in (401, 403) and agent == AGENT:
            continue
        break
    if r is None:
        return None, "injoignable"
    if not r.ok:
        if r.status_code in (401, 403):
            return None, "403"
        if r.status_code in (404, 410):
            return None, "404"
        if r.status_code >= 500 or r.status_code in (429, 503):
            return None, "5xx"
        return None, f"http_{r.status_code}"
    return r, ""


def recuperer(url: str, session: requests.Session | None = None) -> tuple[str, str, str]:
    """Rend (html, url_finale, raison). `html` vide si la page n'est pas lisible."""
    if not robots_autorise(url):
        return "", url, "robots"
    _patienter(url)
    r, raison = _requete(url, session or requests)
    if r is None:
        return "", url, raison
    if "html" not in r.headers.get("Content-Type", "").lower() and \
            not r.content[:300].lstrip().lower().startswith((b"<!doctype", b"<html")):
        return "", r.url, "pas_html"
    return _decoder(r), r.url, ""


def recuperer_pdf(url: str, session: requests.Session | None = None) -> tuple[bytes, str]:
    """Rend (octets, raison) — vide si ce n'est pas un PDF lisible."""
    if not robots_autorise(url):
        return b"", "robots"
    _patienter(url)
    r, raison = _requete(url, session or requests, stream=True)
    if r is None:
        return b"", raison
    try:
        taille = int(r.headers.get("Content-Length") or 0)
    except ValueError:
        taille = 0
    if taille > OCTETS_MAX_PDF:
        return b"", "pdf trop lourd"
    octets = io.BytesIO()
    for morceau in r.iter_content(65536):
        octets.write(morceau)
        if octets.tell() > OCTETS_MAX_PDF:
            return b"", "pdf trop lourd"
    contenu = octets.getvalue()
    if not contenu.startswith(b"%PDF"):
        return b"", "pas un PDF"
    return contenu, ""


# Un libellé de bouton n'est pas un titre. Mesuré le 06/09/2026 : quatre fiches
# produit de Bouyer Leroux et deux brochures Rector sont entrées sous les titres
# « Télécharger la fiche » et « Afficher le document » — le texte du lien, pas
# celui du document. Le PDF, lui, s'annonce en première page : « Fiche produit
# FIBROCO | Tuile décor fibro L 460 mm ».
_LIGNE_SANS_INTERET = re.compile(
    r"^\s*(?:\d+\s*)?(?:edition|édition|version|page|sommaire|©|www\.|http)", re.I)


def titre_du_pdf(texte: str) -> str:
    """La première ligne du PDF qui ressemble à un titre, ou '' si aucune."""
    for brut in (texte or "").split("\n")[:14]:
        ligne = re.sub(r"\s+", " ", brut).strip(" -–—|·")
        # « 1ÉDITION 04/2026Fiche produit FIBROCO | … » : le numéro de page et la
        # mention d'édition sont collés au titre par l'extracteur.
        ligne = re.sub(r"^\s*\d*\s*(?:ÉDITION|EDITION|VERSION)\s*[\d/.-]*\s*", "", ligne, flags=re.I)
        if _LIGNE_SANS_INTERET.match(ligne) or not (15 <= len(ligne) <= 140):
            continue
        if sum(c.isalpha() for c in ligne) < 10:
            continue
        return ligne
    return ""


def texte_du_pdf(octets: bytes, pages_max: int = 12) -> tuple[str, str]:
    """(texte, titre) des premières pages d'un PDF. Vide si pypdf manque."""
    try:
        from pypdf import PdfReader
    except ImportError:
        return "", ""
    try:
        lecteur = PdfReader(io.BytesIO(octets))
        titre = ""
        try:
            titre = (lecteur.metadata.title or "").strip() if lecteur.metadata else ""
        except Exception:
            titre = ""
        morceaux = []
        for page in lecteur.pages[:pages_max]:
            try:
                morceaux.append(page.extract_text() or "")
            except Exception:
                continue
        texte = re.sub(r"[ \t\xa0]+", " ", "\n".join(morceaux))
        texte = re.sub(r"\n{3,}", "\n\n", texte).strip()
        return texte, titre[:160]
    except Exception:
        return "", ""


# ── HTML -> texte ───────────────────────────────────────────────────────────
BLOCS = {"p", "div", "br", "li", "tr", "td", "th", "h1", "h2", "h3", "h4", "h5", "h6",
         "section", "article", "header", "footer", "table", "ul", "ol", "blockquote", "pre",
         "figcaption", "dd", "dt"}
MUETS = {"script", "style", "noscript", "svg", "head", "iframe", "form", "nav", "button",
         "select", "option", "template"}


class _Texte(HTMLParser):
    """HTML -> texte en lignes, plus les liens, les images et le titre."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.morceaux: list[str] = []
        self.liens: list[tuple[str, str]] = []
        self.images: list[str] = []
        self.titre = ""
        self.description = ""
        self._dans_titre = False
        self._muet = 0
        self._lien: str | None = None
        self._libelle: list[str] = []

    def handle_starttag(self, tag, attrs):
        attributs = dict(attrs)
        if tag in MUETS:
            self._muet += 1
        elif tag in BLOCS:
            self.morceaux.append("\n")
        elif tag == "title":
            self._dans_titre = True
        elif tag == "a":
            self._lien = attributs.get("href")
            self._libelle = []
        elif tag == "img":
            source = (attributs.get("data-src") or attributs.get("data-lazy-src")
                      or attributs.get("data-original") or attributs.get("src"))
            if source:
                self.images.append(source)
        elif tag == "meta":
            prop = (attributs.get("property") or attributs.get("name") or "").lower()
            contenu = attributs.get("content") or ""
            if prop in ("og:image", "twitter:image", "twitter:image:src") and contenu:
                self.images.insert(0, contenu)
            elif prop in ("og:title",) and contenu and not self.titre:
                self.titre = contenu.strip()
            elif prop in ("description", "og:description") and contenu and not self.description:
                self.description = contenu.strip()

    def handle_endtag(self, tag):
        if tag in MUETS:
            self._muet = max(0, self._muet - 1)
        elif tag in BLOCS:
            self.morceaux.append("\n")
        elif tag == "title":
            self._dans_titre = False
        elif tag == "a":
            if self._lien:
                self.liens.append((self._lien, " ".join(self._libelle).strip()))
            self._lien, self._libelle = None, []

    def handle_data(self, data):
        if self._dans_titre:
            if not self.titre:
                self.titre = re.sub(r"\s+", " ", data).strip()
            return
        if self._muet:
            return
        self.morceaux.append(data)
        if self._lien is not None:
            self._libelle.append(data.strip())


def mettre_a_plat(code: str) -> dict:
    """Rend {texte, liens, images, titre, description}."""
    lecteur = _Texte()
    try:
        lecteur.feed(code)
    except Exception:
        pass
    texte = html.unescape("".join(lecteur.morceaux))
    texte = re.sub(r"[ \t\xa0]+", " ", texte)
    texte = re.sub(r" *\n *", "\n", texte)
    texte = re.sub(r"\n{3,}", "\n\n", texte).strip()
    return {"texte": texte, "liens": lecteur.liens, "images": lecteur.images,
            "titre": html.unescape(lecteur.titre)[:200],
            "description": html.unescape(lecteur.description)[:500]}


_ARTICLE = re.compile(r"<(article|main)\b[^>]*>(.*?)</\1>", re.I | re.S)
_CORPS = re.compile(
    r'<(div|section)\b[^>]*(?:class|id)=["\'][^"\']*(?:post-content|entry-content|'
    r'article-content|article-body|article__body|content-body|post-body|td-post-content|'
    r'single-content|blog-content|node__content|field--name-body|rich-text|wysiwyg)'
    r'[^"\']*["\'][^>]*>(.*?)</\1>', re.I | re.S)


def contenu_principal(code: str) -> str:
    """Le corps de l'article, quand la page le balise ; sinon toute la page.

    Un gabarit de site pèse souvent plus lourd que l'article (menus, pieds de
    page, « articles liés ») : sans ce tri, l'empreinte de texte de deux
    articles du même site serait la même — celle du menu — et le second
    passerait pour un doublon du premier.
    """
    meilleur = ""
    for motif in (_ARTICLE, _CORPS):
        for trouve in motif.finditer(code):
            interieur = trouve.group(2)
            if len(interieur) > len(meilleur):
                meilleur = interieur
        if meilleur and len(mettre_a_plat(meilleur)["texte"]) >= 400:
            return meilleur
        meilleur = ""
    return code


# 🔴 CE QUI N'EST PAS UN ARTICLE, MÊME QUAND LE SERVEUR REND 200.
#
# MESURÉ LE 06/09/2026 : le bot a range une fiche complete pour
# journals.openedition.org/rao/3510 dont tout le texte tenait en 529 caracteres
# — « Chargement… anubis n'a pas reussi a charger son code javascript. Le
# serveur est peut-etre surcharge. » C'etait un mur anti-robot, pas un article.
# Meme famille que la page de blocage o2switch (le tigre, HTTP 429) qui a fausse
# un audit d'accessibilite entier le 05/09/2026 : un serveur qui repond 200 ne
# prouve pas qu'il a servi le contenu.
MURS = re.compile(
    r"anubis|just a moment|checking your browser|verification que vous n|"
    r"cloudflare|captcha|are you a robot|acces refuse|access denied|"
    r"activez javascript|enable javascript|javascript est desactive|"
    r"veuillez recharger la page|le serveur est peut-etre surcharge|"
    r"page (?:introuvable|non trouvee)|erreur 40[034]|404 not found|"
    r"cookies? (?:pour continuer|avant de continuer)|"
    r"connectez-vous pour|abonnez-vous pour lire|article reserve aux abonnes|"
    r"contenu reserve aux abonnes|log in to continue", re.I)

# Sous cette longueur, une page qui se dit article n'a pas servi son contenu :
# un mur, une redirection, un resume vide, un gabarit. Mesure sur les pages
# reellement collectees : les vrais articles font 5 000 a 30 000 caracteres.
LONGUEUR_ARTICLE_MIN = 400


def est_sans_contenu(texte: str, genre: str = "article") -> str:
    """Rend la RAISON pour laquelle ce n'est pas un article, ou '' si ça en est un.

    Une video ou une publication Facebook n'ont pas de corps de texte : elles
    sont exemptees de la longueur minimale, jamais du mur.
    """
    reduit = (texte or "").strip()
    trouve = MURS.search(reduit[:3000])
    if trouve and len(reduit) < 4000:
        return f"mur ou page de service (« {trouve.group(0)[:40]} »)"
    if genre in ("video", "post_fb"):
        return ""
    if len(reduit) < LONGUEUR_ARTICLE_MIN:
        return f"page presque vide ({len(reduit)} caractères de texte)"
    return ""


_H1 = re.compile(r"<h1[^>]*>(.*?)</h1>", re.I | re.S)
# « Titre de l'article | Nom du site », « … - Nom du site », « … — Nom du site ».
_QUEUE_SITE = re.compile(r"\s*[|·—–]\s*[^|·—–]{2,40}$")


def titre_de_page(code: str, plat: dict, corps: dict) -> str:
    """Le vrai titre de l'article : le <h1> d'abord, la balise <title> ensuite.

    🔴 MESURÉ LE 06/09/2026. Batirama sert dans sa PROPRE balise <title> et dans
    son og:title un titre abîmé — « Ddécryptage des normes pourvos gants de
    protection professionnels » — alors que son <h1> est intact : « Sécurité :
    décryptage des normes pour sélectionner vos gants de protection
    professionnels ». Une fiche est rangée sous ce titre, et c'est lui qui part
    dans le brouillon de publication : un titre casse se voit sur la page.
    Deuxième cas mesuré sur le même site : « Les nouvelles tuiles à emboîtement
    Solutions Charpente-Couverture » — la rubrique collée au titre, sans
    séparateur ; le <h1> rend « Les nouvelles tuiles à emboîtement ».

    Le <h1> n'est retenu que s'il ressemble à un titre d'article (12 à 200
    caractères) : sur une page d'accueil c'est un slogan, et ces pages-là ne
    sont de toute façon pas gardées comme articles.
    """
    for source in (corps.get("html_corps") or "", code or ""):
        trouve = _H1.search(source)
        if not trouve:
            continue
        texte = mettre_a_plat(trouve.group(0))["texte"]
        texte = re.sub(r"\s+", " ", texte).strip(" -–—|·:")
        if 12 <= len(texte) <= 200:
            return texte
    titre = (plat.get("titre") or corps.get("titre") or "").strip()
    # « Pose d'un plancher hourdis | Rector » -> « Pose d'un plancher hourdis ».
    court = _QUEUE_SITE.sub("", titre).strip()
    return court if len(court) >= 12 else titre


IMAGES_REFUSEES = re.compile(
    r"logo|icon|favicon|sprite|pixel|spacer|placeholder|avatar|flag|drapeau|banner-?ad|"
    r"wp-content/plugins|/emoji|badge|button|arrow|fleche|gravatar|share|partage|\.svg", re.I)


def images_utiles(sources: list[str], base_url: str) -> list[str]:
    gardees, vues = [], set()
    for source in sources:
        if not source or source.startswith("data:"):
            continue
        absolu = urljoin(base_url, source.split("?")[0])
        if not re.search(r"\.(jpe?g|png|webp)$", absolu, re.I) and "ytimg" not in absolu \
                and "googleusercontent" not in absolu:
            continue
        if IMAGES_REFUSEES.search(absolu) or absolu in vues:
            continue
        vues.add(absolu)
        gardees.append(absolu)
    return gardees


# ── Lire UNE page ───────────────────────────────────────────────────────────
def lire_page(url: str, session: requests.Session | None = None) -> dict:
    """Rend {texte, titre, description, images, liens, html, url, raison, refuse}."""
    session = session or requests.Session()
    depart = url if url.startswith(("http://", "https://")) else "https://" + url
    code, finale, raison = recuperer(depart, session)
    if not code and raison not in ("robots", "404", "403"):
        autre = ("http://" + depart[8:]) if depart.startswith("https://") else ("https://" + depart[7:])
        code2, finale2, raison2 = recuperer(autre, session)
        if code2:
            code, finale, raison = code2, finale2, ""
    if not code:
        return {"texte": "", "titre": "", "description": "", "images": [], "liens": [],
                "html": "", "url": finale, "raison": raison,
                "refuse": LIBELLES_ECHEC.get(raison, raison or "page illisible")}
    entier = mettre_a_plat(code)
    html_corps = contenu_principal(code)
    corps = mettre_a_plat(html_corps)
    corps["html_corps"] = html_corps
    texte = corps["texte"] if len(corps["texte"]) >= 400 else entier["texte"]
    return {
        "texte": texte[:120_000],
        "titre": titre_de_page(code, entier, corps),
        "description": entier["description"],
        "images": images_utiles(corps["images"] + entier["images"], finale)[:20],
        "liens": entier["liens"],
        "html": code,
        "url": finale,
        "raison": "",
        "refuse": "",
    }


# ── Quelles pages d'un site valent le détour ────────────────────────────────
MOTS_PAGES = (
    (14, r"hourdis|entrevous|poutrelle|plancher|terre-?cuite|brique|tuile|monomur"),
    (12, r"conseil|guide|tuto|astuce|comment|pose|mise-en-oeuvre|technique|fiche|dtu|faq"),
    (8, r"blog|actualit|article|dossier|magazine|news|ressource|documentation|savoir"),
    (5, r"produit|solution|gamme|systeme|système|catalogue"),
)
# Les PDF ne sont pas des pages à visiter : `pdf_trouves` les signale à part.
EXTENSIONS_REFUSEES = re.compile(
    r"\.(jpe?g|png|gif|webp|svg|zip|docx?|xlsx?|pptx?|mp4|mp3|avi|css|js|ico|xml|pdf)(\?|$)", re.I)
NAVIGATION = re.compile(
    r"sitemenu|menu[-_]?(nav|bar|principal)|(?:main|top|left|nav)[-_]?menu|/tag/|/tags/|"
    r"/author/|/auteur/|/page/\d+|[-_/]page[-_]?\d+\.|[?&]page=\d+|/category/|/categorie/|"
    r"/search|/recherche|/login|/panier|/cart|/compte|/account|mentions-legales|cookies|"
    r"politique|cgv|cgu|/rss|/feed|/wp-json|/wp-admin|#|"
    # Lettres d'information et archives : ce sont des CONDENSÉS, pas des articles.
    r"/emailing|newsletter|/archives?/|/sitemap|/plan-du-site", re.I)

# Ce qui, dans une adresse, dit « une liste » (rubrique, catégorie, thème) ou
# « un article » (un slug long, une date, /article/). Sert à choisir quels
# liens suivre depuis une liste : les articles d'abord, jamais une autre liste.
_URL_LISTE = re.compile(r"rubrique|categor|/theme|/dossiers?/?$|/blog/?$|/actualites?/?$|/conseils?/?$|/guides?/?$", re.I)
_URL_ARTICLE = re.compile(r"/article/|/actualite/|/actualites/.|/conseils?/.|/guides?/.|/blog/.|/\d{4}/\d{2}/|/\d{2,}-[a-z]", re.I)


def trier_pour_suivre(liens: list[tuple[int, str]]) -> list[str]:
    """Depuis une page de liste : les adresses d'articles probables d'abord,
    les listes écartées. Mesuré sur Batirama (06/09/2026) : en suivant les liens
    les mieux notés, le bot rouvrait cinq rubriques et zéro article."""
    articles, autres = [], []
    for _, url in liens:
        chemin = urlsplit(url).path
        if _URL_LISTE.search(chemin):
            continue
        slug = chemin.rstrip("/").rsplit("/", 1)[-1]
        if _URL_ARTICLE.search(chemin) or len(slug) > 30:
            articles.append(url)
        else:
            autres.append(url)
    return articles + autres
LANGUES_ETRANGERES = re.compile(
    r"[-_/](ita|eng|deu|esp|nld|rus|chi|jpn|it|de|es|nl|ru|zh|ja|pt|pl|tr|ar|sv|da|no|fi|cs)"
    r"(\.(htm|html|php|asp)|/|$)", re.I)


def _propre(url: str) -> str:
    d = urlsplit(url)
    return urlunsplit((d.scheme, d.netloc, d.path, d.query, ""))


def pages_a_visiter(liens, base_url: str, deja: set[str]) -> list[tuple[int, str]]:
    """Les liens internes qui ressemblent à du contenu, du plus prometteur au moins."""
    hote = _sans_www(_hote(base_url))
    notes: dict[str, int] = {}
    for href, libelle in liens:
        if not href or href.startswith(("mailto:", "tel:", "javascript:", "#")):
            continue
        absolu = _propre(urljoin(base_url, href))
        if _sans_www(_hote(absolu)) != hote or absolu in deja:
            continue
        if EXTENSIONS_REFUSEES.search(absolu) or NAVIGATION.search(absolu):
            continue
        if LANGUES_ETRANGERES.search(absolu):
            continue
        piste = (absolu + " " + (libelle or "")).lower()
        note = sum(poids for poids, motif in MOTS_PAGES if re.search(motif, piste))
        # Un chemin profond (/conseils/poser-un-plancher-hourdis) est un
        # article ; la racine d'une rubrique (/conseils/) est une liste.
        if absolu.count("/") >= 5 and note:
            note += 3
        if note and note > notes.get(absolu, 0):
            notes[absolu] = note
    return sorted(((n, u) for u, n in notes.items()), reverse=True)


_TITRES_H = re.compile(r"<h[23]\b", re.I)


def ressemble_a_une_liste(page: dict, nb_liens_articles: int) -> bool:
    """Une page de RUBRIQUE (liste d'accroches) plutôt qu'un article.

    🔴 MESURÉ SUR BATIRAMA LE 06/09/2026, parce que le premier critère (texte
    par lien) ne séparait rien : 466 caractères par lien pour une rubrique,
    450 pour un article. Ce qui sépare :

        rubrique  : 82-96 titres <h2>/<h3>, 5 paragraphes ≥ 300 caractères,
                    81 blocs moyens (120-300), 58-83 liens d'articles
        article   : 7-14 titres, 15-24 paragraphes longs, 11-17 blocs moyens

    Une liste, c'est beaucoup de titres et d'accroches, peu de paragraphes.
    Un long guide structuré a des titres AUSSI, mais ses paragraphes sont
    longs et nombreux — d'où le plafond `longs <= 8`.
    """
    # ⚠ LA TAILLE SE JUGE AVANT LE NOMBRE DE LIENS. « La sélection quotidienne
    #   de l'actu du BTP » (batirama.com/emailing/…, 82 092 caractères) est
    #   entrée le 06/09/2026 avec 80/100 : c'est une lettre d'information qui
    #   condense vingt articles, et elle ne portait pas dix liens d'articles
    #   reconnus — le garde-fou de taille était donc hors de portée, place
    #   derrière celui des liens. Un article n'a jamais cette taille.
    if len(page.get("texte") or "") > 60_000:
        return True
    if nb_liens_articles < 10:
        return False
    blocs = [b.strip() for b in (page.get("texte") or "").split("\n") if b.strip()]
    longs = sum(1 for b in blocs if len(b) >= 300)
    moyens_courts = sum(1 for b in blocs if 15 <= len(b) < 300)
    titres = len(_TITRES_H.findall(page.get("html") or ""))
    return longs <= 8 and (titres >= 25 or moyens_courts >= 6 * max(longs, 1))


def pdf_trouves(liens, base_url: str) -> list[tuple[str, str]]:
    """Les PDF qui ressemblent à un guide de pose ou une fiche technique : (url, libellé)."""
    interessants = []
    for href, libelle in liens:
        absolu = urljoin(base_url, href or "")
        if not absolu.lower().split("?")[0].endswith(".pdf"):
            continue
        piste = (absolu + " " + (libelle or "")).lower()
        if re.search(r"guide|pose|technique|fiche|notice|mise|oeuvre|hourdis|plancher|brique|"
                     r"tuile|dtu|catalogue|documentation|prescription", piste):
            interessants.append((absolu, (libelle or "").strip()[:120]))
    return interessants[:8]


def explorer_site(url: str, pages_max: int, deja_connues: set[str],
                  session: requests.Session | None = None) -> dict:
    """Parcourt l'accueil (et ses rubriques) d'un site et rend les adresses
    d'articles à lire, avec les PDF repérés.

    Rend {articles: [url], pdf: [(url, libellé)], raison, refuse}. On ne lit
    PAS les articles ici : c'est le collecteur qui les lit et les note, un par
    un, dans le budget `pages_par_site`.
    """
    session = session or requests.Session()
    accueil = lire_page(url, session)
    if not accueil["texte"] and not accueil["liens"]:
        return {"articles": [], "pdf": [], "raison": accueil["raison"], "refuse": accueil["refuse"]}
    vues = {_propre(accueil["url"])}
    candidats = pages_a_visiter(accueil["liens"], accueil["url"], vues)
    pdf = pdf_trouves(accueil["liens"], accueil["url"])
    articles: list[str] = []
    rubriques_lues = 0
    # Les rubriques (blog, conseils…) ouvrent les articles : on en lit jusqu'à
    # trois, chacune ajoute ses liens. Le reste est présumé article.
    for note, lien in list(candidats):
        if lien in deja_connues:
            continue
        est_rubrique = lien.count("/") <= 4 and note < 20
        if est_rubrique and rubriques_lues < 3:
            rubriques_lues += 1
            vues.add(lien)
            page = lire_page(lien, session)
            if page["liens"]:
                for n2, l2 in pages_a_visiter(page["liens"], page["url"], vues):
                    if l2 not in deja_connues and l2 not in articles and n2 >= 12:
                        articles.append(l2)
                pdf.extend(p for p in pdf_trouves(page["liens"], page["url"]) if p not in pdf)
        elif lien not in articles:
            articles.append(lien)
        if len(articles) >= pages_max * 3:
            break
    return {"articles": articles[:pages_max * 3], "pdf": pdf[:8], "raison": "", "refuse": ""}
