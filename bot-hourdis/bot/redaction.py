"""Rédiger un brouillon de publication Facebook depuis une trouvaille — sans modèle.

Le brouillon suit le format de la bible business de la page Hourdis (16/07/2026) :
une accroche d'une ligne, un corps court et aéré, l'attribution à la source, un
appel à l'action, les hashtags. Il est écrit dans `post-facebook.txt` dès le
rangement, pour qu'Andry ait toujours quelque chose à coller — et le modèle,
quand il est allumé, PROPOSE mieux, il ne remplace pas ce filet.

Ce que le brouillon ne fait JAMAIS : citer un prix (ils vivent dans la bible,
pas dans un texte trouvé sur le web), s'approprier le contenu (la source est
nommée et liée), ni dépasser ce que Facebook affiche sans « voir plus »
raisonnable (~1 300 caractères).
"""
from __future__ import annotations

import re

from . import lexique, score, youtube

# ⚠ « hourdis », « tuile », « beton », « polystyrène » GARDENT leurs lettres
#   étrangères ici, et c'est délibéré. La règle « aucun mot hors de l'alphabet
#   malgache » vient des TUTOS VIDÉO : elle protège le moteur de synthèse vocale,
#   qui massacre c, u, q, w, x et ç. Ces textes-ci sont ÉCRITS, personne ne les
#   lit à voix haute, et un maçon de Tana dit « hourdis » — il n'existe pas de
#   mot malgache pour ça. Vérifié le 06/09/2026 : les cinq questions malgaches
#   ci-dessous sont ouvertes (firy, iza, nahoana, inona) ou alternatives (sa),
#   donc aucune ne prend la particule VE ; seule une question fermée l'exige, et
#   c'est le cas du seul appel à l'action fermé (« … ve ianao ? »).
ACCROCHES = {
    "pose": {"fr": ["🧱 Bien poser un plancher hourdis : ce que les pros font, étape par étape",
                    "🔧 Technique de pose : le détail qui change tout sur un plancher hourdis"],
             "mg": ["🧱 Fomba fametrahana hourdis araka ny tokony ho izy — tsy azo atao an-kamehana",
                    "🔧 Torohevitra fametrahana rihana hourdis avy amin'ny matihanina"]},
    "erreurs": {"fr": ["⚠️ Les erreurs qui coûtent cher sur un plancher hourdis",
                       "🚫 À éviter absolument avant de couler votre dalle"],
                "mg": ["⚠️ Hadisoana mahazatra rehefa manao rihana hourdis — ary ny fomba hialana",
                       "🚫 Tsy azo atao alohan'ny handrarahana ny dalle"]},
    "calcul": {"fr": ["📐 Combien de hourdis pour votre plancher ? La méthode simple",
                      "🧮 Calculer son plancher sans se tromper"],
               "mg": ["📐 Firy ny hourdis ilaina amin'ny rihana-nao ? Fomba tsotra",
                      "🧮 Kajy tsotra ho an'ny rihana-nao"]},
    "comparatif": {"fr": ["⚖️ Hourdis ou dalle pleine ? Ce qu'il faut comparer vraiment",
                          "🤔 Terre cuite, béton, polystyrène : le bon choix pour votre plancher"],
                   "mg": ["⚖️ Hourdis sa dalle feno ? Inona no tena tokony hampitahaina",
                          "🤔 Tanimanga, beton, polystyrène : iza no mety ho anao ?"]},
    "isolation": {"fr": ["🌡️ Une maison fraîche à Tana : le rôle de la terre cuite",
                         "🌡️ Isolation : pourquoi la terre cuite garde la maison agréable"],
                  "mg": ["🌡️ Trano mangatsiatsiaka : ny anjara asan'ny tanimanga",
                         "🌡️ Nahoana ny tanimanga no mahatonga ny trano ho mahafinaritra ?"]},
    "toiture": {"fr": ["🏠 Toiture en tuiles terre cuite : les règles d'une pose qui dure",
                       "🏠 Tuiles : ce qu'un bon couvreur vérifie toujours"],
                "mg": ["🏠 Tafo tuile tanimanga : fitsipika ho an'ny tafo maharitra",
                       "🏠 Tuile : inona no jerena foana amin'ny tafo tsara ?"]},
    "murs": {"fr": ["🧱 Monter un mur en brique creuse : les bons gestes",
                    "🧱 Brique creuse : la qualité se voit dès le premier rang"],
             "mg": ["🧱 Manangana rindrina biriky creuse : ny fihetsika marina",
                    "🧱 Biriky : hita amin'ny andalana voalohany ny kalitao"]},
    "fabrication": {"fr": ["🔥 Comment naît une brique : séchage, cuisson, qualité",
                           "🔥 De l'argile à la tuile : la fabrication expliquée"],
                    "mg": ["🔥 Ahoana no fanaovana biriky : fanamainana, fandorana, kalitao",
                           "🔥 Avy amin'ny tanimanga ka hatramin'ny tuile"]},
    "etaiement": {"fr": ["🪜 Étaiement : le geste qui protège votre chantier et vos ouvriers"],
                  "mg": ["🪜 Étaiement : ny fihetsika miaro ny toeram-piasana sy ny mpiasa"]},
    "securite": {"fr": ["🦺 Sécurité sur le chantier : un plancher se pose sans accident"],
                 "mg": ["🦺 Fiarovana eny an-toeram-piasana : rihana apetraka tsy misy loza"]},
    "defaut": {"fr": ["💡 Conseil construction du jour — hourdis et terre cuite",
                      "💡 Le savoir-faire du plancher hourdis, en clair",
                      "🏗️ Construire mieux avec la terre cuite"],
               "mg": ["💡 Torohevitra fanorenana androany — hourdis sy tanimanga",
                      "💡 Fahaizana momba ny rihana hourdis, mazava tsara",
                      "🏗️ Manorina tsara kokoa amin'ny tanimanga"]},
}

CTA = {
    "fr": "👉 Une question sur votre plancher ou vos briques ? Écrivez-nous en MP, on vous conseille.",
    "mg": "👉 Manana fanontaniana momba ny rihana-nao sa ny biriky-nao ve ianao ? Manorata aty amin'ny MP, manoro hevitra izahay.",
}
LOHARANO = {"fr": "📌 Source", "mg": "📌 Loharano"}

_METIER = [(re.compile(rf"\b(?:{m})\b"), p) for m, p in lexique.MOTS_METIER]
_TUTO = re.compile(lexique.TUTORIEL)
_FIN_PHRASE = re.compile(r"(?<=[.!?…])\s+|\n+")
_BRUIT = re.compile(r"http|www\.|amzn|@|cookie|abonn|inscri|cliquez|newsletter|copyright|©|lien[s]? (ci|affili)|"
                    r"commission|merci pour|n'oubliez pas|like|partag|s'abonner|\[musique\]|\[applaud|"
                    r"salut a tous|bonjour a tous|cette video|la video|regarder|chaine youtube|"
                    r"\bon va voir ensemble\b|\bpour de la brique on va\b", re.I)
FENETRE_MOTS = 22


def _decouper(texte: str) -> list[str]:
    """Phrases — ou, quand le texte n'a pas de ponctuation (sous-titres
    automatiques de YouTube), des fenêtres de ~22 mots. Mesuré le 06/09/2026 :
    une transcription de 17 minutes ne rendait AUCUNE phrase, et le brouillon
    retombait sur la description brute, liens d'affiliation compris."""
    brut = re.sub(r"[ \t]+", " ", (texte or "").replace("\r", "\n")).strip()
    morceaux = []
    for segment in _FIN_PHRASE.split(brut):
        segment = (segment or "").strip(" -•·\t")
        if not segment:
            continue
        if len(segment) <= 230:
            morceaux.append(segment)
            continue
        mots = segment.split(" ")
        for i in range(0, len(mots), FENETRE_MOTS):
            fenetre = " ".join(mots[i:i + FENETRE_MOTS + 6]).strip()
            if fenetre:
                morceaux.append(fenetre)
    return morceaux


def resume_propre(texte: str, longueur: int = 320) -> str:
    """Un résumé sans liens, sans appels à s'abonner : les premières phrases
    utiles, coupées à une fin de phrase."""
    lignes = []
    for ligne in (texte or "").replace("\r", "\n").split("\n"):
        ligne = ligne.strip()
        if not ligne or _BRUIT.search(ligne) or ligne.upper() == ligne and len(ligne) > 12:
            continue
        if re.fullmatch(r"[\W\d_]+", ligne):
            continue
        lignes.append(ligne)
        if sum(len(l) for l in lignes) > longueur * 2:
            break
    propre = re.sub(r"\s+", " ", " ".join(lignes)).strip()
    if len(propre) <= longueur:
        return propre
    coupe = propre[:longueur]
    fin = max(coupe.rfind(". "), coupe.rfind("! "), coupe.rfind("? "))
    return (coupe[:fin + 1] if fin > longueur // 2 else coupe.rstrip() + "…").strip()


def phrases_cles(texte: str, n: int = 3) -> list[str]:
    """Les phrases qui portent le plus de métier ET d'enseignement — dans l'ordre du texte."""
    phrases = _decouper(texte)
    notees = []
    for rang, phrase in enumerate(phrases):
        if not (45 <= len(phrase) <= 260):
            continue
        reduit = score.sans_accents(phrase)
        if _BRUIT.search(reduit):
            continue
        # Bourrage de mots-clés (« monter cloison brique, monter cloison brique
        # creuse, monter cloison brique de verre… ») : beaucoup de virgules,
        # peu de mots distincts. Mesuré le 06/09/2026 sur une description
        # YouTube qui a battu la transcription à ce jeu.
        mots = re.findall(r"[a-z0-9']+", reduit)        # sans la ponctuation collée
        if phrase.count(",") >= 4 or (len(mots) >= 8 and len(set(mots)) < 0.65 * len(mots)):
            continue
        points = sum(poids * len(m.findall(reduit)) for m, poids in _METIER)
        if points == 0:
            continue
        if _TUTO.search(reduit):
            points += 8
        if re.search(r"\d", phrase):
            points += 2
        notees.append((points, rang, phrase))
    notees.sort(key=lambda x: -x[0])
    choisies = sorted(notees[:n], key=lambda x: x[1])
    vues: set[str] = set()
    resultat = []
    for _, _, phrase in choisies:
        cle = score.sans_accents(phrase)[:60]
        if cle in vues:
            continue
        vues.add(cle)
        phrase = phrase.rstrip(" ,;:")
        if not phrase.endswith((".", "!", "?", "…")):
            phrase += "…" if len(phrase.split()) >= FENETRE_MOTS else "."
        resultat.append(phrase[0].upper() + phrase[1:])
    return resultat


def _accroche(themes: list[str], langue: str, graine: str) -> str:
    for theme in ("erreurs", "pose", "calcul", "comparatif", "toiture", "murs", "isolation",
                  "fabrication", "etaiement", "securite"):
        if theme in themes:
            choix = ACCROCHES[theme][langue]
            break
    else:
        choix = ACCROCHES["defaut"][langue]
    return choix[sum(ord(c) for c in graine) % len(choix)]


def rediger(t: dict, cfg: dict, langue: str = "") -> str:
    """Le brouillon complet. `langue` : 'fr', 'mg' ou 'mix' (accroche+CTA dans les deux)."""
    langue = (langue or cfg.get("langue_post") or "mix").lower()
    themes = list(t.get("themes") or [])
    graine = t.get("id") or t.get("url") or ""
    langues = ["mg", "fr"] if langue == "mix" else [langue if langue in ("fr", "mg") else "fr"]

    blocs: list[str] = []
    blocs.append("\n".join(_accroche(themes, l, graine) for l in langues))

    corps: list[str] = []
    conseils = list(t.get("conseils") or [])[:4]
    if not conseils:
        conseils = phrases_cles(t.get("texte") or t.get("resume") or "", 3)
    if conseils:
        corps.append("\n".join(f"✅ {c}" if c.endswith(("!", "?", ".", "…")) else f"✅ {c}."
                               for c in conseils))
    elif t.get("resume") or t.get("texte"):
        corps.append(resume_propre(t.get("resume") or t.get("texte") or ""))
    if t.get("genre") == "video":
        duree = youtube.duree_lisible(t.get("duree_s"))
        libelle = {"fr": "🎥 Vidéo", "mg": "🎥 Horonan-tsary"}[langues[0]]
        corps.append(f"{libelle} : {t.get('titre', '').strip()}" + (f" ({duree})" if duree else ""))
    if corps:
        blocs.append("\n\n".join(corps))

    if cfg.get("signature_source", True) and t.get("url"):
        auteur = (t.get("auteur") or t.get("source_nom") or "").strip()
        blocs.append(f"{LOHARANO[langues[0]]} : {auteur + ' — ' if auteur else ''}{t['url']}")

    blocs.append("\n".join(CTA[l] for l in langues))
    contact = (cfg.get("contact_ligne") or "").strip()
    if contact:
        blocs.append(contact)
    hashtags = (cfg.get("hashtags") or "").strip()
    if hashtags:
        blocs.append(hashtags)

    texte = "\n\n".join(b for b in blocs if b.strip())
    return texte[:1900]


def assembler_depuis_ia(post_ia: str, t: dict, cfg: dict, langue: str) -> str:
    """Un post rédigé par le modèle reçoit la source, le contact et les hashtags du bot."""
    blocs = [post_ia.strip()]
    if cfg.get("signature_source", True) and t.get("url") and t["url"] not in post_ia:
        auteur = (t.get("auteur") or t.get("source_nom") or "").strip()
        blocs.append(f"{LOHARANO.get(langue, LOHARANO['fr'])} : {auteur + ' — ' if auteur else ''}{t['url']}")
    for cle in ("contact_ligne", "hashtags"):
        valeur = (cfg.get(cle) or "").strip()
        if valeur and valeur not in post_ia:
            blocs.append(valeur)
    return "\n\n".join(blocs)[:1900]
