"""Génère les artboards de la maquette mobile depuis la SOURCE du site.

    python design/generer.py

Les prix, les quantités par m² et les noms viennent de `site/data/produits.json` : la maquette ne
peut pas dériver du site. Les artboards écrits ici sont ensuite semés dans le canvas Claude Design.
Écrit : Produits.dc.html, Sections.dc.html. (Main.dc.html et HeroCourt.dc.html sont écrits à la main :
ils portent la composition, pas des données.)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RACINE = Path(__file__).resolve().parent.parent
ICI = Path(__file__).resolve().parent
PRODUITS = json.loads((RACINE / "site/data/produits.json").read_text(encoding="utf-8"))

# jetons repris tels quels de site/src/styles/main.css
PRIMAIRE, PRIMAIRE_F, PRIMAIRE_DOUX = "#B85C38", "#9A4A2B", "#F7EAE3"
ENCRE, ENCRE_DOUX, ENCRE_GRIS = "#1A1A1A", "#495057", "#6B7280"
LIGNE, SURFACE2 = "#E5E7EB", "#F8F9FA"

ENTETE = """<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <script src="./support.js"></script>
</head>
<body>
<x-dc>
<helmet>
  <style>
    body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; }
    a { color: #9A4A2B; text-decoration: none; } a:hover { color: #B85C38; }
    * { box-sizing: border-box; }
  </style>
</helmet>
"""
PIED = """</x-dc>
<script data-dc-script data-props='{"$preview":{"width":390,"height":%d}}'>
class Component extends DCLogic {}
</script>
</body>
</html>
"""

IMAGES = {
    "hourdis-20.webp": "p-hourdis-20.webp", "hourdis-15.webp": "p-hourdis-15.webp",
    "hourdis-12.webp": "p-hourdis-12.webp", "brique-creuse-20.webp": "p-brique-20.webp",
    "brique-creuse-15.webp": "p-brique-15.webp", "brique-creuse-10.webp": "p-brique-10.webp",
    "tuile-mecanique.webp": "p-tuile-meca.webp", "tuile-ecaille.webp": "p-tuile-ecaille.webp",
}


def ar(n: int) -> str:
    return f"{n:,}".replace(",", " ") + " Ar"


def carte(p: dict) -> str:
    """Une carte produit de la grille 2 colonnes : ~250 px de haut au lieu de 501."""
    nom = p["nom"].replace(" cm", "").replace("×33×33", "×33×33").replace(" 22×33,5", " 22×33,5")
    img = IMAGES.get(p.get("image", ""), "")
    return f"""      <div style="display: flex; flex-direction: column; background: #FFFFFF; border: 1px solid {LIGNE}; border-radius: 10px; overflow: hidden">
        <img src="{img}" alt="" style="width: 100%; aspect-ratio: 4 / 3; object-fit: cover; display: block">
        <div style="display: flex; flex-direction: column; gap: 3px; padding: 9px 10px 10px">
          <span style="font-size: 13px; font-weight: 700; line-height: 1.25">{nom}</span>
          <span style="font-size: 17px; font-weight: 800; color: {PRIMAIRE_F}">{ar(p['prix'])}</span>
          <a href="#calc" style="display: flex; align-items: center; justify-content: center; min-height: 34px; margin-top: 3px; border: 1.5px solid {PRIMAIRE}; border-radius: 7px; font-size: 12px; font-weight: 600">Calculer</a>
        </div>
      </div>"""


def produits() -> tuple[str, int]:
    blocs, hauteur = [], 90
    for cat in PRODUITS["categories"]:
        if cat.get("tableau"):
            lignes = "".join(
                f"""        <tr>
          <td style="padding: 8px 10px; border-bottom: 1px solid {LIGNE}; font-size: 13px">{p['nom']}<br><span style="color: {ENCRE_GRIS}; font-size: 11px">{p['dims']}</span></td>
          <td style="padding: 8px 10px; border-bottom: 1px solid {LIGNE}; font-size: 13px; text-align: right; white-space: nowrap; font-weight: 700; color: {PRIMAIRE_F}">{ar(p['prix'])}</td>
          <td style="padding: 8px 10px; border-bottom: 1px solid {LIGNE}; font-size: 12px; text-align: right; color: {ENCRE_DOUX}; white-space: nowrap">{p['pcs_m2']}/m²</td>
        </tr>"""
                for p in cat["produits"])
            blocs.append(f"""    <h3 style="margin: 22px 0 2px; font-size: 15px; font-weight: 700; color: {PRIMAIRE_F}">{cat['titre']}</h3>
    <p style="margin: 0 0 10px; font-size: 12px; color: {ENCRE_GRIS}; line-height: 1.35">Demandez-nous des photos par Messenger.</p>
    <table style="width: 100%; border-collapse: collapse; background: #FFFFFF; border: 1px solid {LIGNE}; border-radius: 10px; overflow: hidden">
      <tbody>
{lignes}
      </tbody>
    </table>""")
            hauteur += 60 + 52 * len(cat["produits"])
        else:
            cartes = "\n".join(carte(p) for p in cat["produits"])
            blocs.append(f"""    <h3 style="margin: 22px 0 2px; font-size: 15px; font-weight: 700; color: {PRIMAIRE_F}">{cat['titre']}</h3>
    <p style="margin: 0 0 10px; font-size: 12px; color: {ENCRE_GRIS}">{cat['sous_titre']}</p>
    <div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px">
{cartes}
    </div>""")
            hauteur += 60 + 262 * ((len(cat["produits"]) + 1) // 2)
    corps = "\n".join(blocs)
    html = f"""{ENTETE}
<div style="width: 390px; background: #FFFFFF; color: {ENCRE}">
  <section style="padding: 20px 16px 24px">
    <h2 style="margin: 0 0 4px; font-size: 22px; font-weight: 800">Nos produits et prix</h2>
    <p style="margin: 0 0 4px; font-size: 13px; color: {ENCRE_DOUX}; line-height: 1.4">Prix par pièce, hors livraison. Les 13 produits tiennent sur deux écrans au lieu de six.</p>
{corps}
    <p style="margin: 18px 0 0; padding: 12px; background: {SURFACE2}; border-radius: 8px; font-size: 12px; color: {ENCRE_DOUX}; line-height: 1.45; text-align: center">Prix indicatifs. Le devis écrit fait foi. Production sur commande : comptez environ 30 jours.</p>
  </section>
</div>
{PIED % hauteur}"""
    return html, hauteur


def sections() -> tuple[str, int]:
    """Production (grille 2 colonnes), livraison (2 colonnes), choisir (accordéon)."""
    photos = [("g-sechage.webp", "Séchage des hourdis sous abri"), ("g-stock.webp", "Hourdis cuits, prêts à livrer"),
              ("g-briques.webp", "Briques creuses sur étalage"), ("g-tuiles.webp", "Tuiles en terre cuite")]
    vignettes = "\n".join(
        f"""      <figure style="margin: 0; border-radius: 10px; overflow: hidden; background: {SURFACE2}">
        <img src="{f}" alt="" style="width: 100%; aspect-ratio: 4 / 3; object-fit: cover; display: block">
        <figcaption style="padding: 6px 8px; font-size: 11px; color: {ENCRE_DOUX}; line-height: 1.3">{leg}</figcaption>
      </figure>""" for f, leg in photos)

    liv = [("Zones", "Antananarivo et périphérie : Ambohimanga, Alasora, Imerintsiatosika, Andramasina"),
           ("Tarif", "1 500 Ar le kilomètre depuis Ambohimanga Rova"),
           ("Délai de livraison", "3 à 7 jours après la commande"),
           ("Délai de production", "environ 30 jours ; le stock part vite")]
    cartes_liv = "\n".join(
        f"""      <div style="padding: 10px 12px; background: #FFFFFF; border: 1px solid {LIGNE}; border-radius: 10px">
        <div style="font-size: 12px; font-weight: 700; color: {PRIMAIRE_F}; margin-bottom: 2px">{t}</div>
        <div style="font-size: 12px; color: {ENCRE_DOUX}; line-height: 1.4">{d}</div>
      </div>""" for t, d in liv)

    choisir = [("Selon la charge", "Habitation, terrasse ou stockage : plus la charge est forte, plus l'épaisseur monte (12, 15 ou 20 cm)."),
               ("Selon la portée", "La distance entre deux appuis dicte la hauteur de poutrelle, donc celle de l'hourdis. Au-delà de 4 m, voyez votre ingénieur."),
               ("Selon l'isolation", "La terre cuite garde la fraîcheur et amortit les bruits entre étages."),
               ("Terre cuite, béton ou polystyrène ?", "La terre cuite ne brûle pas et isole bien ; le béton porte plus mais pèse ; le polystyrène isole mieux mais coûte plus cher.")]
    accordeon = "\n".join(
        f"""      <details style="background: #FFFFFF; border: 1px solid {LIGNE}; border-radius: 10px"{' open' if i == 0 else ''}>
        <summary style="display: flex; justify-content: space-between; align-items: center; gap: 12px; min-height: 44px; padding: 10px 12px; font-size: 13px; font-weight: 700; cursor: pointer; list-style: none">{t}
          <span style="flex-shrink: 0; width: 22px; height: 22px; display: flex; align-items: center; justify-content: center; border-radius: 50%; background: {PRIMAIRE_DOUX}; color: {PRIMAIRE_F}; font-weight: 800">+</span>
        </summary>
        <div style="padding: 0 12px 12px; font-size: 12px; color: {ENCRE_DOUX}; line-height: 1.5">{d}</div>
      </details>""" for i, (t, d) in enumerate(choisir))

    html = f"""{ENTETE}
<div style="width: 390px; background: #FFFFFF; color: {ENCRE}">

  <section style="padding: 20px 16px; background: {SURFACE2}">
    <h2 style="margin: 0 0 3px; font-size: 20px; font-weight: 800">Notre production</h2>
    <p style="margin: 0 0 12px; font-size: 12px; color: {ENCRE_DOUX}; line-height: 1.4">Séchage, cuisson et stockage à Ambohimanga Rova. Ce sont nos ateliers, pas des images d'illustration.</p>
    <div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px">
{vignettes}
    </div>
  </section>

  <section style="padding: 20px 16px">
    <h2 style="margin: 0 0 3px; font-size: 20px; font-weight: 800">Livraison et délais</h2>
    <p style="margin: 0 0 12px; font-size: 12px; color: {ENCRE_DOUX}">Ce que vous pouvez attendre, avant de commander.</p>
    <div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px">
{cartes_liv}
    </div>
  </section>

  <section style="padding: 20px 16px; background: {SURFACE2}">
    <h2 style="margin: 0 0 3px; font-size: 20px; font-weight: 800">Comment choisir</h2>
    <p style="margin: 0 0 12px; font-size: 12px; color: {ENCRE_DOUX}">Quatre questions, repliées : on ouvre celle qui nous concerne.</p>
    <div style="display: flex; flex-direction: column; gap: 8px">
{accordeon}
    </div>
  </section>

  <section style="padding: 22px 16px; background: {PRIMAIRE}; color: #FFFFFF; text-align: center">
    <h2 style="margin: 0 0 6px; font-size: 20px; font-weight: 800; color: #FFFFFF">Votre chantier, votre devis</h2>
    <p style="margin: 0 auto 14px; font-size: 13px; color: #FBE9E1; line-height: 1.45; max-width: 30ch">Donnez-nous la surface et le lieu : nous rappelons avec le prix, la livraison et le délai.</p>
    <a href="#contact" style="display: flex; align-items: center; justify-content: center; min-height: 48px; background: #FFFFFF; color: {PRIMAIRE_F}; border-radius: 8px; font-size: 16px; font-weight: 700">Demander un devis gratuit</a>
  </section>

</div>
{PIED % 1450}"""
    return html, 1450


for nom, (contenu, h) in (("Produits.dc.html", produits()), ("Sections.dc.html", sections())):
    (ICI / nom).write_text(contenu, encoding="utf-8", newline="\n")
    print(f"  {nom:<22} {h:>5} px de haut, {len(contenu)//1024} Ko")
print("prix repris de site/data/produits.json :",
      ", ".join(f"{p['nom'].split()[0].lower()} {p['prix']}" for c in PRODUITS["categories"][:1] for p in c["produits"]))
