"""Base SQLite locale : sources, trouvailles, candidats de sources, journal, état.

Une seule base, un seul fichier (data/bot.db) : facile à sauvegarder, facile à
jeter. L'unité est la TROUVAILLE — un article, une vidéo, un guide PDF, une
publication — identifiée par son adresse normalisée ET par l'empreinte de son
texte : le même tuto repris par trois sites n'entre qu'une fois.
"""
from __future__ import annotations

import json
import re
import sqlite3
import threading
import unicodedata
import uuid
from datetime import date, datetime, timezone
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .config import BASE, DOSSIER_DONNEES

_verrou = threading.Lock()

GENRES_SOURCE = ("site", "flux", "recherche_web", "youtube_recherche",
                 "youtube_chaine", "page_fb", "groupe_fb")
GENRES_TROUVAILLE = ("article", "video", "pdf", "actualite", "post_fb")
STATUTS = ("nouvelle", "gardee", "programmee", "publiee", "ecartee")

SCHEMA = """
CREATE TABLE IF NOT EXISTS sources (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    nom               TEXT NOT NULL,
    url               TEXT NOT NULL DEFAULT '',
    genre             TEXT NOT NULL DEFAULT 'site',
    requete           TEXT NOT NULL DEFAULT '',
    actif             INTEGER NOT NULL DEFAULT 1,
    derniere_collecte TEXT,
    nb_examines       INTEGER NOT NULL DEFAULT 0,
    nb_trouvees       INTEGER NOT NULL DEFAULT 0,
    nb_gardees        INTEGER NOT NULL DEFAULT 0,
    echecs            INTEGER NOT NULL DEFAULT 0,
    dernier_echec     TEXT NOT NULL DEFAULT '',
    cree_le           TEXT NOT NULL,
    UNIQUE(genre, url, requete)
);

CREATE TABLE IF NOT EXISTS trouvailles (
    id             TEXT PRIMARY KEY,
    url            TEXT NOT NULL UNIQUE,
    empreinte      TEXT NOT NULL DEFAULT '',
    titre          TEXT NOT NULL DEFAULT '',
    texte          TEXT NOT NULL DEFAULT '',
    resume         TEXT NOT NULL DEFAULT '',
    genre          TEXT NOT NULL DEFAULT 'article',
    source_id      INTEGER,
    source_nom     TEXT NOT NULL DEFAULT '',
    auteur         TEXT NOT NULL DEFAULT '',
    auteur_url     TEXT NOT NULL DEFAULT '',
    langue         TEXT NOT NULL DEFAULT '',
    publie_le      TEXT NOT NULL DEFAULT '',
    date_origine   TEXT NOT NULL DEFAULT '',
    collecte_le    TEXT NOT NULL,
    score          INTEGER NOT NULL DEFAULT 0,
    score_ia       INTEGER,
    themes         TEXT NOT NULL DEFAULT '[]',
    motifs         TEXT NOT NULL DEFAULT '[]',
    statut         TEXT NOT NULL DEFAULT 'nouvelle',
    motif_ecart    TEXT NOT NULL DEFAULT '',
    dossier        TEXT NOT NULL DEFAULT '',
    images         TEXT NOT NULL DEFAULT '[]',
    duree_s        INTEGER,
    vues           INTEGER,
    conseils       TEXT NOT NULL DEFAULT '[]',
    avertissements TEXT NOT NULL DEFAULT '[]',
    post           TEXT NOT NULL DEFAULT '',
    post_mg        TEXT NOT NULL DEFAULT '',
    relu_le        TEXT NOT NULL DEFAULT '',
    publie_fb_id   TEXT NOT NULL DEFAULT '',
    publie_fb_le   TEXT NOT NULL DEFAULT '',
    note           TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_trouvailles_statut ON trouvailles(statut);
CREATE INDEX IF NOT EXISTS idx_trouvailles_empreinte ON trouvailles(empreinte);
CREATE INDEX IF NOT EXISTS idx_trouvailles_publie ON trouvailles(publie_le);

CREATE TABLE IF NOT EXISTS candidats (
    cle       TEXT PRIMARY KEY,
    genre     TEXT NOT NULL,
    nom       TEXT NOT NULL,
    url       TEXT NOT NULL,
    note      INTEGER NOT NULL DEFAULT 0,
    raison    TEXT NOT NULL DEFAULT '',
    nb_vues   INTEGER NOT NULL DEFAULT 0,
    statut    TEXT NOT NULL DEFAULT 'nouveau',
    vu_le     TEXT NOT NULL,
    decide_le TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS publications (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    trouvaille TEXT NOT NULL,
    fb_id      TEXT NOT NULL DEFAULT '',
    quand      TEXT NOT NULL,
    programme  TEXT NOT NULL DEFAULT '',
    message    TEXT NOT NULL DEFAULT '',
    a_blanc    INTEGER NOT NULL DEFAULT 0,
    resultat   TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS journal (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    ts      TEXT NOT NULL,
    niveau  TEXT NOT NULL,
    message TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS etat (
    cle    TEXT PRIMARY KEY,
    valeur TEXT NOT NULL
);
"""

CHAMPS_JSON = ("themes", "motifs", "images", "conseils", "avertissements")


def connexion() -> sqlite3.Connection:
    DOSSIER_DONNEES.mkdir(parents=True, exist_ok=True)
    cx = sqlite3.connect(BASE, timeout=30)
    cx.row_factory = sqlite3.Row
    return cx


def initialiser() -> None:
    with _verrou, connexion() as cx:
        cx.executescript(SCHEMA)


def maintenant() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _sortir(ligne: sqlite3.Row | None) -> dict | None:
    if ligne is None:
        return None
    valeurs = dict(ligne)
    for champ in CHAMPS_JSON:
        if isinstance(valeurs.get(champ), str):
            try:
                valeurs[champ] = json.loads(valeurs[champ])
            except json.JSONDecodeError:
                valeurs[champ] = []
    return valeurs


def _entrer(champs: dict) -> dict:
    valeurs = dict(champs)
    for champ in CHAMPS_JSON:
        if champ in valeurs and not isinstance(valeurs[champ], str):
            valeurs[champ] = json.dumps(valeurs[champ], ensure_ascii=False)
    return valeurs


# ── Journal et état ─────────────────────────────────────────────────────────
def logguer(message: str, niveau: str = "info") -> None:
    with _verrou, connexion() as cx:
        cx.execute("INSERT INTO journal (ts, niveau, message) VALUES (?, ?, ?)",
                   (maintenant(), niveau, message))
        cx.execute("DELETE FROM journal WHERE id NOT IN "
                   "(SELECT id FROM journal ORDER BY id DESC LIMIT 3000)")
    try:
        print(f"[{niveau}] {message}", flush=True)
    except (UnicodeEncodeError, OSError):
        pass          # console cp1252 : un emoji ne doit pas tuer le bot


def lire_journal(limite: int = 60, niveau: str = "") -> list[dict]:
    with _verrou, connexion() as cx:
        if niveau:
            lignes = cx.execute(
                "SELECT ts, niveau, message FROM journal WHERE niveau = ? "
                "ORDER BY id DESC LIMIT ?", (niveau, limite)).fetchall()
        else:
            lignes = cx.execute(
                "SELECT ts, niveau, message FROM journal ORDER BY id DESC LIMIT ?",
                (limite,)).fetchall()
    return [dict(l) for l in lignes]


def ecrire_etat(cle: str, valeur: str) -> None:
    with _verrou, connexion() as cx:
        cx.execute("INSERT INTO etat (cle, valeur) VALUES (?, ?) "
                   "ON CONFLICT(cle) DO UPDATE SET valeur = excluded.valeur",
                   (cle, valeur))


def lire_etat(cle: str, defaut: str = "") -> str:
    with _verrou, connexion() as cx:
        ligne = cx.execute("SELECT valeur FROM etat WHERE cle = ?", (cle,)).fetchone()
    return ligne["valeur"] if ligne else defaut


# ── Adresses et empreintes ──────────────────────────────────────────────────
PARAMETRES_PISTAGE = re.compile(
    r"^(utm_|fbclid|gclid|mc_|ref|source|igshid|si|feature|pp|_ga|yclid|msclkid)", re.I
)


def propre_url(url: str) -> str:
    """Adresse canonique : sans pistage, sans ancre, sans « www. » ni « / » final.

    Deux adresses du même article (avec et sans `utm_source=facebook`) sont la
    même trouvaille ; sans cette normalisation, la deuxième collecte dupliquait
    la première. YouTube : on ne garde que `v=`.
    """
    url = (url or "").strip()
    if not url:
        return ""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    d = urlsplit(url)
    hote = d.netloc.lower()
    if hote.startswith("www."):
        hote = hote[4:]
    if hote in ("youtu.be",):
        return f"https://youtube.com/watch?v={d.path.strip('/').split('/')[0]}"
    if hote.endswith("youtube.com") and d.path == "/watch":
        v = dict(parse_qsl(d.query)).get("v", "")
        return f"https://youtube.com/watch?v={v}" if v else url
    if hote.startswith("m.") and hote.endswith("youtube.com"):
        hote = "youtube.com"
    params = [(k, v) for k, v in parse_qsl(d.query, keep_blank_values=True)
              if not PARAMETRES_PISTAGE.match(k)]
    chemin = d.path.rstrip("/") or "/"
    return urlunsplit(("https", hote, chemin, urlencode(params), ""))


def empreinte_texte(texte: str, longueur: int = 220) -> str:
    """Les 220 premiers caractères utiles, sans accents ni ponctuation.

    Le même texte repris mot pour mot ailleurs a la même empreinte ; un texte
    trop court (< 100 caractères utiles) n'en a pas — deux légendes de photo
    différentes se ressembleraient trop.
    """
    reduit = unicodedata.normalize("NFKD", texte or "")
    reduit = "".join(c for c in reduit if unicodedata.category(c) != "Mn")
    reduit = re.sub(r"[^a-z0-9]+", " ", reduit.lower()).strip()
    if len(reduit) < 100:
        return ""
    return reduit[:longueur]


# ── Sources ─────────────────────────────────────────────────────────────────
def sources(actives_seulement: bool = False) -> list[dict]:
    requete = "SELECT * FROM sources"
    if actives_seulement:
        requete += " WHERE actif = 1"
    requete += " ORDER BY genre, nom COLLATE NOCASE"
    with _verrou, connexion() as cx:
        return [dict(l) for l in cx.execute(requete).fetchall()]


def source(sid: int) -> dict | None:
    with _verrou, connexion() as cx:
        ligne = cx.execute("SELECT * FROM sources WHERE id = ?", (sid,)).fetchone()
    return dict(ligne) if ligne else None


def ajouter_source(nom: str, url: str, genre: str, requete: str = "") -> dict:
    if genre not in GENRES_SOURCE:
        raise ValueError(f"genre de source inconnu : {genre}")
    with _verrou, connexion() as cx:
        existante = cx.execute(
            "SELECT * FROM sources WHERE genre = ? AND url = ? AND requete = ?",
            (genre, url, requete)).fetchone()
        if existante:
            return dict(existante)
        cx.execute(
            "INSERT INTO sources (nom, url, genre, requete, cree_le) VALUES (?, ?, ?, ?, ?)",
            (nom.strip() or url or requete, url, genre, requete, maintenant()))
        ligne = cx.execute("SELECT * FROM sources WHERE id = last_insert_rowid()").fetchone()
    return dict(ligne)


def modifier_source(sid: int, **champs) -> None:
    permis = {"nom", "url", "actif", "requete", "derniere_collecte", "nb_examines",
              "nb_trouvees", "nb_gardees", "echecs", "dernier_echec"}
    champs = {k: v for k, v in champs.items() if k in permis}
    if not champs:
        return
    with _verrou, connexion() as cx:
        cx.execute(
            "UPDATE sources SET " + ", ".join(f"{k} = ?" for k in champs) + " WHERE id = ?",
            (*champs.values(), sid))


def compter_source(sid: int, examines: int = 0, trouvees: int = 0, gardees: int = 0,
                   echec: str | None = None) -> None:
    """Met à jour le rendement d'une source après un passage."""
    with _verrou, connexion() as cx:
        if echec is None:
            cx.execute(
                "UPDATE sources SET derniere_collecte = ?, nb_examines = nb_examines + ?, "
                "nb_trouvees = nb_trouvees + ?, nb_gardees = nb_gardees + ?, echecs = 0, "
                "dernier_echec = '' WHERE id = ?",
                (maintenant(), examines, trouvees, gardees, sid))
        else:
            cx.execute(
                "UPDATE sources SET derniere_collecte = ?, echecs = echecs + 1, "
                "dernier_echec = ? WHERE id = ?", (maintenant(), echec[:200], sid))


def supprimer_source(sid: int) -> None:
    with _verrou, connexion() as cx:
        cx.execute("DELETE FROM sources WHERE id = ?", (sid,))


# ── Trouvailles ─────────────────────────────────────────────────────────────
def existe_url(url: str) -> bool:
    with _verrou, connexion() as cx:
        return cx.execute("SELECT 1 FROM trouvailles WHERE url = ?",
                          (propre_url(url),)).fetchone() is not None


def texte_deja_vu(empreinte: str) -> str | None:
    """L'id de la trouvaille qui porte déjà ce texte, ou None."""
    if not empreinte:
        return None
    with _verrou, connexion() as cx:
        ligne = cx.execute("SELECT id FROM trouvailles WHERE empreinte = ?",
                           (empreinte,)).fetchone()
    return ligne["id"] if ligne else None


def ajouter_trouvaille(champs: dict) -> str | None:
    """Insère une trouvaille ; rend son id, ou None si l'adresse existe déjà."""
    valeurs = _entrer(champs)
    valeurs.setdefault("id", uuid.uuid4().hex[:12])
    valeurs["url"] = propre_url(valeurs.get("url", ""))
    valeurs.setdefault("collecte_le", maintenant())
    if isinstance(valeurs.get("publie_le"), date):
        valeurs["publie_le"] = valeurs["publie_le"].isoformat()
    valeurs["publie_le"] = valeurs.get("publie_le") or ""
    colonnes = ", ".join(valeurs)
    marques = ", ".join("?" for _ in valeurs)
    with _verrou, connexion() as cx:
        try:
            cx.execute(f"INSERT INTO trouvailles ({colonnes}) VALUES ({marques})",
                       tuple(valeurs.values()))
        except sqlite3.IntegrityError:
            return None
    return valeurs["id"]


def trouvaille(tid: str) -> dict | None:
    with _verrou, connexion() as cx:
        return _sortir(cx.execute("SELECT * FROM trouvailles WHERE id = ?", (tid,)).fetchone())


def modifier_trouvaille(tid: str, champs: dict) -> None:
    valeurs = _entrer(champs)
    if isinstance(valeurs.get("publie_le"), date):
        valeurs["publie_le"] = valeurs["publie_le"].isoformat()
    valeurs.pop("id", None)
    if not valeurs:
        return
    with _verrou, connexion() as cx:
        cx.execute(
            "UPDATE trouvailles SET " + ", ".join(f"{k} = ?" for k in valeurs) + " WHERE id = ?",
            (*valeurs.values(), tid))


def supprimer_trouvaille(tid: str) -> None:
    with _verrou, connexion() as cx:
        cx.execute("DELETE FROM trouvailles WHERE id = ?", (tid,))


COLONNES_LISTE = (
    "id, url, titre, resume, genre, source_id, source_nom, auteur, auteur_url, langue, "
    "publie_le, date_origine, collecte_le, score, score_ia, themes, motifs, statut, "
    "motif_ecart, dossier, images, duree_s, vues, conseils, avertissements, "
    "CASE WHEN post <> '' THEN 1 ELSE 0 END AS a_post, relu_le, publie_fb_id, "
    "publie_fb_le, note, length(texte) AS longueur"
)


def lister_trouvailles(statut: str = "", genre: str = "", theme: str = "",
                       source_id: int = 0, recherche: str = "", tri: str = "score",
                       limite: int = 200, date_pub: str = "") -> list[dict]:
    clauses, params = [], []
    if statut:
        if statut == "actives":
            clauses.append("statut IN ('nouvelle','gardee','programmee')")
        else:
            clauses.append("statut = ?")
            params.append(statut)
    if genre:
        clauses.append("genre = ?")
        params.append(genre)
    if theme:
        clauses.append("themes LIKE ?")
        params.append(f'%"{theme}"%')
    if source_id:
        clauses.append("source_id = ?")
        params.append(source_id)
    if date_pub:
        clauses.append("publie_le = ?" if date_pub != "inconnue" else "publie_le = ''")
        if date_pub != "inconnue":
            params.append(date_pub)
    if recherche:
        clauses.append("(titre LIKE ? OR texte LIKE ? OR auteur LIKE ? OR source_nom LIKE ?)")
        motif = f"%{recherche}%"
        params += [motif, motif, motif, motif]
    ordre = {
        "score": "score DESC, collecte_le DESC",
        "date": "publie_le DESC, collecte_le DESC",
        "collecte": "collecte_le DESC",
        "vues": "COALESCE(vues, 0) DESC, score DESC",
    }.get(tri, "score DESC, collecte_le DESC")
    requete = f"SELECT {COLONNES_LISTE} FROM trouvailles"
    if clauses:
        requete += " WHERE " + " AND ".join(clauses)
    requete += f" ORDER BY {ordre} LIMIT ?"
    params.append(int(limite))
    with _verrou, connexion() as cx:
        return [_sortir(l) for l in cx.execute(requete, params).fetchall()]


def trouvailles_a_relire(score_min: int, limite: int) -> list[dict]:
    with _verrou, connexion() as cx:
        lignes = cx.execute(
            "SELECT * FROM trouvailles WHERE relu_le = '' AND statut IN ('nouvelle','gardee') "
            "AND score >= ? ORDER BY score DESC LIMIT ?", (score_min, limite)).fetchall()
    return [_sortir(l) for l in lignes]


def compteurs() -> dict:
    with _verrou, connexion() as cx:
        par_statut = {l["statut"]: l["n"] for l in cx.execute(
            "SELECT statut, COUNT(*) AS n FROM trouvailles GROUP BY statut").fetchall()}
        par_genre = {l["genre"]: l["n"] for l in cx.execute(
            "SELECT genre, COUNT(*) AS n FROM trouvailles WHERE statut <> 'ecartee' "
            "GROUP BY genre").fetchall()}
        total = cx.execute("SELECT COUNT(*) AS n FROM trouvailles").fetchone()["n"]
        dates = cx.execute(
            "SELECT COUNT(DISTINCT publie_le) AS n FROM trouvailles "
            "WHERE statut <> 'ecartee' AND publie_le <> ''").fetchone()["n"]
        sans_date = cx.execute(
            "SELECT COUNT(*) AS n FROM trouvailles WHERE statut <> 'ecartee' "
            "AND publie_le = ''").fetchone()["n"]
    return {
        "total": total,
        "nouvelle": par_statut.get("nouvelle", 0),
        "gardee": par_statut.get("gardee", 0),
        "programmee": par_statut.get("programmee", 0),
        "publiee": par_statut.get("publiee", 0),
        "ecartee": par_statut.get("ecartee", 0),
        "a_trier": par_statut.get("nouvelle", 0),
        "videos": par_genre.get("video", 0),
        "articles": par_genre.get("article", 0) + par_genre.get("actualite", 0),
        "pdf": par_genre.get("pdf", 0),
        "posts_fb": par_genre.get("post_fb", 0),
        "dates": dates,
        "sans_date": sans_date,
    }


def _minuit_utc() -> str:
    minuit_ici = datetime.now().astimezone().replace(hour=0, minute=0, second=0, microsecond=0)
    return minuit_ici.astimezone(timezone.utc).isoformat(timespec="seconds")


def gardables_aujourdhui() -> int:
    """Trouvailles au-dessus du score minimum collectées depuis minuit (heure locale)."""
    with _verrou, connexion() as cx:
        return cx.execute(
            "SELECT COUNT(*) AS n FROM trouvailles WHERE collecte_le >= ? "
            "AND statut <> 'ecartee'", (_minuit_utc(),)).fetchone()["n"]


def themes_disponibles() -> list[tuple[str, int]]:
    """(thème, nombre) sur les trouvailles non écartées."""
    comptes: dict[str, int] = {}
    with _verrou, connexion() as cx:
        for ligne in cx.execute(
                "SELECT themes FROM trouvailles WHERE statut <> 'ecartee'").fetchall():
            try:
                for t in json.loads(ligne["themes"] or "[]"):
                    comptes[t] = comptes.get(t, 0) + 1
            except json.JSONDecodeError:
                continue
    return sorted(comptes.items(), key=lambda kv: -kv[1])


def dates_de_publication() -> list[dict]:
    """Pour l'onglet Dossiers : une ligne par date, avec le nombre de fiches."""
    with _verrou, connexion() as cx:
        lignes = cx.execute(
            "SELECT publie_le AS date, COUNT(*) AS n, MAX(score) AS meilleur "
            "FROM trouvailles WHERE statut <> 'ecartee' AND dossier <> '' "
            "GROUP BY publie_le ORDER BY publie_le DESC").fetchall()
    return [dict(l) for l in lignes]


def auteurs_des_gardees(score_min: int) -> list[dict]:
    """Pour la découverte de sources : qui produit ce qu'on garde."""
    with _verrou, connexion() as cx:
        lignes = cx.execute(
            "SELECT url, auteur, auteur_url, genre, score, source_id FROM trouvailles "
            "WHERE statut <> 'ecartee' AND score >= ?", (score_min,)).fetchall()
    return [dict(l) for l in lignes]


# ── Candidats de sources ────────────────────────────────────────────────────
def ajouter_candidat(c: dict) -> bool:
    """Ajoute ou rafraîchit un candidat. Un candidat ÉCARTÉ ne revient jamais."""
    with _verrou, connexion() as cx:
        existant = cx.execute("SELECT statut FROM candidats WHERE cle = ?",
                              (c["cle"],)).fetchone()
        if existant:
            if existant["statut"] != "nouveau":
                return False
            cx.execute(
                "UPDATE candidats SET note = ?, raison = ?, nb_vues = ?, vu_le = ? WHERE cle = ?",
                (int(c.get("note", 0)), c.get("raison", ""), int(c.get("nb_vues", 0)),
                 maintenant(), c["cle"]))
            return False
        cx.execute(
            "INSERT INTO candidats (cle, genre, nom, url, note, raison, nb_vues, vu_le) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (c["cle"], c["genre"], c["nom"], c["url"], int(c.get("note", 0)),
             c.get("raison", ""), int(c.get("nb_vues", 0)), maintenant()))
    return True


def candidats(statut: str = "nouveau", limite: int = 300) -> list[dict]:
    with _verrou, connexion() as cx:
        lignes = cx.execute(
            "SELECT * FROM candidats WHERE statut = ? ORDER BY note DESC, nb_vues DESC LIMIT ?",
            (statut, limite)).fetchall()
    return [dict(l) for l in lignes]


def decider_candidat(cle: str, statut: str) -> dict | None:
    with _verrou, connexion() as cx:
        cx.execute("UPDATE candidats SET statut = ?, decide_le = ? WHERE cle = ?",
                   (statut, maintenant(), cle))
        ligne = cx.execute("SELECT * FROM candidats WHERE cle = ?", (cle,)).fetchone()
    return dict(ligne) if ligne else None


def compter_candidats() -> dict:
    with _verrou, connexion() as cx:
        return {l["statut"]: l["n"] for l in cx.execute(
            "SELECT statut, COUNT(*) AS n FROM candidats GROUP BY statut").fetchall()}


def cles_connues() -> set[str]:
    """Clés déjà candidates (tout statut) + adresses déjà sources."""
    with _verrou, connexion() as cx:
        cles = {l["cle"] for l in cx.execute("SELECT cle FROM candidats").fetchall()}
        cles |= {l["url"] for l in cx.execute("SELECT url FROM sources").fetchall()}
    return cles


# ── Publications ────────────────────────────────────────────────────────────
def enregistrer_publication(tid: str, fb_id: str, message: str, programme: str = "",
                            a_blanc: bool = False, resultat: str = "") -> None:
    with _verrou, connexion() as cx:
        cx.execute(
            "INSERT INTO publications (trouvaille, fb_id, quand, programme, message, a_blanc, "
            "resultat) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (tid, fb_id, maintenant(), programme, message, int(a_blanc), resultat[:500]))


def publications(limite: int = 50) -> list[dict]:
    with _verrou, connexion() as cx:
        lignes = cx.execute(
            "SELECT p.*, t.titre, t.url FROM publications p "
            "LEFT JOIN trouvailles t ON t.id = p.trouvaille "
            "ORDER BY p.id DESC LIMIT ?", (limite,)).fetchall()
    return [dict(l) for l in lignes]


initialiser()
