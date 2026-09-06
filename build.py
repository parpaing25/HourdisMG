"""Construit le site statique : site/ → dist/, prêt pour le déploiement atomique.

    python build.py            # construit et vérifie ; code de sortie 1 si un garde-fou tombe
    python build.py --servir   # construit puis sert dist/ sur http://127.0.0.1:8765 pour regarder

Ce que fait le build, dans l'ordre :
  1. injecte les partiels (_partials/header.html, footer.html) et la date dans chaque page ;
  2. génère les cartes produits, le tableau, les offres JSON-LD et le tableau de prix de la FAQ
     depuis site/data/produits.json — UNE source pour tous les prix ;
  3. fabrique le JSON-LD FAQPage à partir des <details> de faq.html ;
  4. hache main.css et main.js en assets/index-<hash>.css|js et réécrit les références
     (le cache navigateur est « immutable, 1 an » sur ces noms : sans hash, une correction
     resterait invisible pendant un an aux visiteurs revenus) ;
  5. écrit sitemap.xml ;
  6. VÉRIFIE : aucun style en ligne (CSP), aucun lien interne cassé, une seule <h1> par page,
     alt sur chaque image, titres et descriptions dans les bornes, aucun marqueur oublié,
     aucune photo de banque d'images, budget de poids de la première vue.

Aucune dépendance hors bibliothèque standard : ni npm, ni Vite. Le dépôt garde package.json
uniquement pour l'historique ; il ne sert plus au site.
"""
from __future__ import annotations

import hashlib
import html
import json
import re
import shutil
import sys
from datetime import date
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RACINE = Path(__file__).resolve().parent
SITE = RACINE / "site"
DIST = RACINE / "dist"
PAGES = ["index.html", "faq.html", "mentions-legales.html", "confidentialite.html", "merci.html", "404.html"]
INDEXABLES = {"index.html": "/", "faq.html": "/faq", "mentions-legales.html": "/mentions-legales", "confidentialite.html": "/confidentialite"}
HOTE = "https://hourdis.fonenako.mg"
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]

erreurs: list[str] = []


def erreur(msg: str) -> None:
    erreurs.append(msg)
    print("  ✗", msg)


def fmt_prix(n: int) -> str:
    return f"{n:,}".replace(",", " ")


# ── 2. Produits ──────────────────────────────────────────────────────────────
def rendre_produits(data: dict) -> tuple[str, str, str, str]:
    cartes, tableau, offres, faq = [], [], [], []
    for cat in data["categories"]:
        pcs_cat = cat.get("pcs_m2")
        if cat.get("tableau"):
            lignes = []
            for p in cat["produits"]:
                lignes.append(
                    f'<tr><th scope="row">{html.escape(p["nom"])}</th><td>{html.escape(p["dims"])}</td>'
                    f'<td class="num">{fmt_prix(p["prix"])} Ar</td><td class="num">{p["pcs_m2"]} / m²</td>'
                    f'<td><button type="button" class="btn btn-outline calculator-btn" data-price="{p["prix"]}" data-pcs="{p["pcs_m2"]}" data-name="{html.escape(p["nom"])}">Calculer</button></td></tr>'
                )
            tableau.append(
                f'<div class="product-category"><h3 class="category-title">{html.escape(cat["titre"])}</h3>'
                f'<p class="category-sub">{html.escape(cat["sous_titre"])}</p>'
                f'<div class="table-wrap"><table class="table-produits"><caption class="sr-only">{html.escape(cat["titre"])} : dimensions, prix à la pièce, pièces par m²</caption>'
                f'<thead><tr><th scope="col">Produit</th><th scope="col">Dimensions</th><th scope="col" class="num">Prix / pièce</th><th scope="col" class="num">Pièces / m²</th><th scope="col"><span class="sr-only">Calculer</span></th></tr></thead>'
                f'<tbody>{"".join(lignes)}</tbody></table></div></div>'
            )
        else:
            items = []
            for p in cat["produits"]:
                pcs = p.get("pcs_m2", pcs_cat)
                items.append(
                    f'<article class="product-card reveal" id="{p["id"]}"><div class="product-image">'
                    f'<img src="/image/{p["image"]}" alt="{html.escape(p["alt"])}" width="720" height="540" loading="lazy" decoding="async"></div>'
                    f'<div class="product-info"><h4>{html.escape(p["nom"])}</h4><p class="product-dims">{html.escape(p["dims"])}</p>'
                    f'<p class="product-price">{fmt_prix(p["prix"])} Ar <small>/ pièce</small></p>'
                    f'<p class="product-yield">{pcs} pièces par m²</p>'
                    f'<button type="button" class="btn btn-outline calculator-btn" data-price="{p["prix"]}" data-pcs="{pcs}" data-name="{html.escape(p["nom"])}">Calculer mes quantités</button></div></article>'
                )
            cartes.append(
                f'<div class="product-category"><h3 class="category-title">{html.escape(cat["titre"])}</h3>'
                f'<p class="category-sub">{html.escape(cat["sous_titre"])}</p><div class="products-grid">{"".join(items)}</div></div>'
            )
        for p in cat["produits"]:
            pcs = p.get("pcs_m2", pcs_cat)
            offre = {
                "@type": "Offer",
                "itemOffered": {"@type": "Product", "name": p["nom"], "description": f'{p["nom"]} en terre cuite, {pcs} pièces par m².',
                                **({"image": f'{HOTE}/image/{p["image"]}'} if p.get("image") else {})},
                "price": p["prix"], "priceCurrency": "MGA", "availability": "https://schema.org/PreOrder",
                "url": f'{HOTE}/#{p["id"]}' if p.get("image") else f'{HOTE}/#produits',
            }
            offres.append(offre)
            faq.append(f'<tr><th scope="row">{html.escape(p["nom"])}</th><td class="num">{fmt_prix(p["prix"])} Ar</td><td class="num">{pcs} / m²</td></tr>')
    faq_html = ('<div class="table-wrap"><table class="table-produits"><thead><tr><th scope="col">Produit</th><th scope="col" class="num">Prix / pièce</th><th scope="col" class="num">Pièces / m²</th></tr></thead>'
                f'<tbody>{"".join(faq)}</tbody></table></div>')
    return "\n".join(cartes), "\n".join(tableau), json.dumps(offres, ensure_ascii=False), faq_html


# ── 3. FAQPage depuis les <details> ──────────────────────────────────────────
def faq_jsonld(page: str) -> str:
    qa = []
    for m in re.finditer(r'<details class="faq-item"[^>]*>\s*<summary>(.*?)</summary>\s*<div class="faq-answer">(.*?)</div>\s*</details>', page, re.S):
        q = html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip()
        a = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", m.group(2)))).strip()
        a = re.sub(r"À COMPLÉTER.*?\.", "", a).strip()
        qa.append({"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}})
    d = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": qa}
    return f'<script type="application/ld+json">{json.dumps(d, ensure_ascii=False)}</script>'


# ── 4. Hachage des ressources ────────────────────────────────────────────────
def hacher(src: Path, ext: str) -> str:
    h = hashlib.sha256(src.read_bytes()).hexdigest()[:8]
    nom = f"assets/index-{h}.{ext}"
    (DIST / "assets").mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, DIST / nom)
    return "/" + nom


# ── 6. Vérifications ─────────────────────────────────────────────────────────
def verifier(pages: dict[str, str]) -> None:
    print("— Vérifications —")
    ids_index = set(re.findall(r'\sid="([^"]+)"', pages["index.html"]))
    for nom, page in pages.items():
        if "<!-- @" in page:
            erreur(f"{nom} : marqueur non remplacé : {re.findall(r'<!-- @[a-z-]+ -->', page)}")
        if re.search(r'\sstyle="', page):
            erreur(f"{nom} : attribut style= en ligne (interdit par la CSP)")
        if "pexels" in page.lower() or "unsplash" in page.lower():
            erreur(f"{nom} : photo de banque d'images")
        if len(re.findall(r"<h1[\s>]", page)) != 1:
            erreur(f"{nom} : {len(re.findall(r'<h1[\s>]', page))} balise(s) h1, il en faut exactement une")
        for img in re.findall(r"<img\b[^>]*>", page):
            if ' alt=' not in img:
                erreur(f"{nom} : image sans alt : {img[:80]}")
        t = re.search(r"<title>(.*?)</title>", page, re.S)
        if not t or not (20 <= len(t.group(1).strip()) <= 65):
            erreur(f"{nom} : titre absent ou hors bornes 20-65 : {t.group(1) if t else None}")
        d = re.search(r'<meta name="description" content="([^"]*)"', page)
        if nom in INDEXABLES and (not d or not (100 <= len(d.group(1)) <= 165)):
            erreur(f"{nom} : meta description hors bornes 100-165 ({len(d.group(1)) if d else 0})")
        if '<html lang="fr">' not in page:
            erreur(f"{nom} : lang manquant")
        for lien in set(re.findall(r'(?:href|src|imagesrcset)="([^"]+)"', page)):
            for cible in [c.strip().split(" ")[0] for c in lien.split(",")]:
                if not cible or cible.startswith(("http", "mailto:", "tel:", "data:")):
                    continue
                chemin, _, ancre = cible.partition("#")
                if chemin in ("", "/"):
                    if ancre and ancre not in ids_index:
                        erreur(f"{nom} : ancre #{ancre} introuvable dans index.html")
                    continue
                if chemin.startswith("/"):
                    fichier = DIST / chemin.lstrip("/")
                    if not fichier.exists() and not (fichier.with_suffix(".html")).exists():
                        erreur(f"{nom} : lien interne cassé : {cible}")
    # budget de la première vue mobile : index + css + js + bandeau 960 + logo + favicon
    css = next(DIST.glob("assets/index-*.css")); js = next(DIST.glob("assets/index-*.js"))
    poids = sum(p.stat().st_size for p in [DIST / "index.html", css, js, DIST / "image/hero-960.webp", DIST / "image/logo.webp"])
    print(f"  première vue mobile ≈ {poids // 1024} Ko (index {(DIST / 'index.html').stat().st_size // 1024} + css {css.stat().st_size // 1024} + js {js.stat().st_size // 1024} + bandeau 960 {(DIST / 'image/hero-960.webp').stat().st_size // 1024})")
    if poids > 500 * 1024:
        erreur(f"première vue > 500 Ko ({poids // 1024} Ko)")
    if not (DIST / ".htaccess").exists() or not (DIST / "contact.php").exists():
        erreur(".htaccess ou contact.php absent de dist/")


def construire() -> None:
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    aujourdhui = date.today()
    date_fr = f"{aujourdhui.day} {MOIS[aujourdhui.month - 1]} {aujourdhui.year}"

    # fichiers copiés tels quels
    for p in SITE.iterdir():
        if p.name in ("_partials", "data") or p.name.endswith(".html") or p.name in ("src",):
            continue
        if p.is_dir():
            shutil.copytree(p, DIST / p.name)
        else:
            shutil.copy2(p, DIST / p.name)

    css = hacher(SITE / "src/styles/main.css", "css")
    js = hacher(SITE / "src/js/main.js", "js")
    print(f"— Ressources hachées : {css}  {js}")

    data = json.loads((SITE / "data/produits.json").read_text(encoding="utf-8"))
    cartes, tableau, offres, faq_prix = rendre_produits(data)
    header = (SITE / "_partials/header.html").read_text(encoding="utf-8")
    footer = (SITE / "_partials/footer.html").read_text(encoding="utf-8")

    pages: dict[str, str] = {}
    for nom in PAGES:
        page = (SITE / nom).read_text(encoding="utf-8")
        page = page.replace("<!-- @header -->", header).replace("<!-- @footer -->", footer).replace("<!-- @date -->", date_fr)
        page = page.replace("<!-- @produits -->", cartes).replace("<!-- @tableau -->", tableau).replace("<!-- @jsonld-offres -->", offres)
        page = page.replace("<!-- @faq-prix -->", faq_prix)
        if "<!-- @faq-jsonld -->" in page:
            page = page.replace("<!-- @faq-jsonld -->", faq_jsonld(page))
        page = page.replace('href="/src/styles/main.css"', f'href="{css}"').replace('src="/src/js/main.js"', f'src="{js}"')
        (DIST / nom).write_text(page, encoding="utf-8", newline="\n")
        pages[nom] = page
        print(f"  {nom:<24} {len(page.encode()) // 1024:>3} Ko")

    lastmod = aujourdhui.isoformat()
    urls = "".join(f"  <url><loc>{HOTE}{chemin}</loc><lastmod>{lastmod}</lastmod><changefreq>{'weekly' if chemin == '/' else 'monthly'}</changefreq><priority>{'1.0' if chemin == '/' else '0.6'}</priority></url>\n" for chemin in INDEXABLES.values())
    (DIST / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}</urlset>\n', encoding="utf-8")

    verifier(pages)
    total = sum(p.stat().st_size for p in DIST.rglob("*") if p.is_file())
    n = sum(1 for p in DIST.rglob("*") if p.is_file())
    if erreurs:
        print(f"\nBUILD REFUSÉ : {len(erreurs)} problème(s) ci-dessus.")
        sys.exit(1)
    print(f"\nBUILD OK : {n} fichiers, {total // 1024} Ko dans dist/")


if __name__ == "__main__":
    construire()
    if "--servir" in sys.argv:
        import http.server

        class Serveur(http.server.SimpleHTTPRequestHandler):
            """Imite les deux règles du .htaccess : /faq → faq.html, page absente → 404.html."""
            extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map, ".webp": "image/webp", ".webmanifest": "application/manifest+json"}

            def __init__(self, *a, **k):
                super().__init__(*a, directory=str(DIST), **k)

            def do_GET(self):
                chemin = self.path.split("?")[0].split("#")[0]
                if re.fullmatch(r"/[a-z0-9-]+", chemin) and (DIST / (chemin[1:] + ".html")).exists():
                    self.path = chemin + ".html"
                elif chemin != "/" and not (DIST / chemin.lstrip("/")).exists():
                    self.send_response(404); self.send_header("Content-Type", "text/html; charset=utf-8"); self.end_headers()
                    self.wfile.write((DIST / "404.html").read_bytes()); return
                super().do_GET()

            def do_POST(self):  # contact.php / stat.php : le PHP ne tourne pas ici, on simule la réponse
                self.rfile.read(int(self.headers.get("Content-Length", 0) or 0))
                if self.path.startswith("/contact.php"):
                    self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(b'{"ok":true}')
                else:
                    self.send_response(204); self.end_headers()

            def log_message(self, *a):
                pass

        print("http://127.0.0.1:8765  (Ctrl+C pour arrêter)")
        http.server.ThreadingHTTPServer(("127.0.0.1", 8765), Serveur).serve_forever()
