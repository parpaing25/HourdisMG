# -*- coding: utf-8 -*-
"""fabriquer.py — fabrique les 30 publications de la page Hourdis Madagascar.

    python publications-30j/fabriquer.py captures   # captures du site LOCAL (build.py --servir)
    python publications-30j/fabriquer.py tout       # textes + affiches, dans sortie/<date>-<slug>/
    python publications-30j/fabriquer.py planche    # planches de contrôle des 30 affiches

Chaque dossier de sortie suit la convention de l'atelier Fonenako (onglets.py peut
le reprendre) : brouillon.txt (le texte exact à publier), fiche.json, affiche-fil.png.

Les captures se font sur la copie locale du site, jamais en ligne : le site compte
ses visites (stat.php), une capture en production y écrirait de fausses visites.
"""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

from PIL import Image, ImageOps

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ICI = Path(__file__).resolve().parent
RACINE = ICI.parent
sys.path.insert(0, str(ICI))
import importlib  # noqa: E402
import os  # noqa: E402

# Deux séries partagent ces outils : « serie » (18:00, reels) et « serie14 » (14:00).
#     HOURDIS_SERIE=serie14 python publications-30j/fabriquer.py tout
_MODULE = importlib.import_module(os.environ.get("HOURDIS_SERIE", "serie"))
SERIE, CIBLES, HEURE = _MODULE.SERIE, _MODULE.CIBLES, _MODULE.HEURE
CAMPAGNE = getattr(_MODULE, "CAMPAGNE", "serie30j")     # utm_campaign
PREFIXE = getattr(_MODULE, "PREFIXE", "j")              # utm_content = j01…j30 / k01…k30
NOM = getattr(_MODULE, "NOM", "")                       # suffixe des planches et du cahier

SORTIE = ICI / getattr(_MODULE, "SORTIE_NOM", "sortie")
CAPTURES = ICI / "captures"
PRODUITS = json.loads((RACINE / "site/data/produits.json").read_text(encoding="utf-8"))
LOGO = RACINE / "site/image/logo.webp"
SITE = "https://hourdis.fonenako.mg"
LOCAL = "http://127.0.0.1:8765"

W, H = 1080, 1350

FIN = """
👉 {libelle} : {lien}
📞 032 47 041 43 · 033 71 063 34 · na hafatra eto amin'ny page
📍 Ambohimanga Rova — manatitra any Antananarivo sy ny manodidina

#HourdisMadagascar #Hourdis #TerreCuite #Fanorenana #Antananarivo"""


def dossier(p: dict) -> Path:
    return SORTIE / f"{p['date']}-{p['slug']}"


def numero(p: dict) -> int:
    return SERIE.index(p) + 1


def lien(p: dict) -> str:
    cible, _ = CIBLES[p["cible"]]
    chemin, ancre = ("faq", "") if cible == "faq" else ("", cible)
    return (f"{SITE}/{chemin}?utm_source=facebook&utm_medium=post&utm_campaign={CAMPAGNE}"
            f"&utm_content={PREFIXE}{numero(p):02d}{ancre}")


def texte_complet(p: dict) -> str:
    _, libelle = CIBLES[p["cible"]]
    return p["texte"].strip() + "\n" + FIN.format(libelle=libelle, lien=lien(p))


# ------------------------------------------------------------------ photos
def photos() -> dict:
    f = ICI / "photos.json"
    return {x["id"]: x for x in json.loads(f.read_text(encoding="utf-8"))} if f.exists() else {}


def affectation() -> dict:
    f = ICI / getattr(_MODULE, "AFFECTATION", "affectation.json")
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


def preparer_photo(src: Path, dest: Path, largeur: int, hauteur: int,
                   boite=None, foyer=(0.5, 0.5)) -> None:
    """Recadre (boite = zone utile en fractions), puis remplit largeur×hauteur."""
    with Image.open(src) as im:
        im = ImageOps.exif_transpose(im).convert("RGB")
        if boite:
            g, h, d, b = boite
            im = im.crop((int(g * im.width), int(h * im.height), int(d * im.width), int(b * im.height)))
        im.thumbnail((largeur * 3, hauteur * 3))
        im = ImageOps.fit(im, (largeur, hauteur), Image.LANCZOS, centering=foyer)
        im.save(dest, "JPEG", quality=90, optimize=True)


# ------------------------------------------------------------------ gabarits
CSS = """
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:1080px;height:1350px;overflow:hidden}
body{font-family:"Segoe UI",Roboto,Arial,sans-serif;color:#1A1A1A;background:#FFFFFF;position:relative}
.photo{position:absolute;left:0;top:0;width:1080px;object-fit:cover;display:block}
.voile{position:absolute;left:0;top:0;width:1080px;height:190px;background:linear-gradient(rgba(0,0,0,.55),rgba(0,0,0,0))}
.marque{position:absolute;left:48px;top:40px;display:flex;align-items:center;gap:20px;color:#fff;font-weight:700;font-size:36px;text-shadow:0 2px 6px rgba(0,0,0,.4)}
.marque img{width:92px;height:92px;border-radius:50%;border:4px solid #fff;background:#fff}
.badge{display:inline-block;background:#B85C38;color:#fff;font-weight:800;letter-spacing:2px;font-size:30px;padding:12px 26px;border-radius:40px}
.badge.clair{background:#fff;color:#9A4A2B}
.titre{font-weight:800;line-height:1.08}
.sous{color:#495057;font-size:40px;line-height:1.25;margin-top:14px}
.prix{display:inline-flex;align-items:baseline;gap:14px;background:#B85C38;color:#fff;border-radius:18px;padding:14px 30px;margin-top:26px}
.prix b{font-size:66px;font-weight:800}
.prix span{font-size:32px}
.pied{position:absolute;left:0;bottom:0;width:1080px;height:104px;background:#9A4A2B;color:#fff;display:flex;align-items:center;justify-content:space-between;padding:0 48px}
.pied .site{font-size:44px;font-weight:800;letter-spacing:.5px}
.pied .tel{font-size:32px;opacity:.95}
/* gabarit photo */
.g-photo .panneau{position:absolute;left:0;top:860px;width:1080px;height:386px;background:#fff;padding:0 56px}
.g-photo .panneau .badge{position:relative;top:-32px}
.g-photo .titre{font-size:70px;margin-top:-10px}
/* gabarit carte */
.g-carte .tete{position:absolute;left:0;top:0;width:1080px;height:420px;background:#B85C38;color:#fff;padding:56px 56px 0}
.g-carte .tete .marque{position:static;margin-bottom:34px;text-shadow:none}
.g-carte .tete .titre{font-size:76px;margin-top:22px}
.g-carte .tete .sous{color:#F7EAE3;font-size:42px}
.g-carte .corps{position:absolute;left:0;top:420px;width:1080px;background:#fff;padding:44px 56px}
.g-carte .ligne{font-size:50px;font-weight:700;padding:18px 0;border-bottom:3px solid #F7EAE3;line-height:1.15}
.g-carte .ligne:last-child{border-bottom:none}
.g-carte .bande{position:absolute;left:0;width:1080px;object-fit:cover}
.g-carte .note{font-size:32px;color:#6B7280;padding-top:14px}
/* gabarit question */
.g-question .tete{position:absolute;left:0;top:0;width:1080px;height:620px;background:#B85C38;color:#fff;padding:56px 56px 0}
.g-question .tete .marque{position:static;margin-bottom:28px;text-shadow:none}
.bulle{position:relative;background:#fff;color:#1A1A1A;border-radius:36px;padding:30px 44px;font-size:58px;font-weight:700;font-style:italic;line-height:1.18;margin-top:26px}
.bulle:after{content:"";position:absolute;left:90px;bottom:-26px;width:52px;height:52px;background:#fff;transform:rotate(45deg)}
.g-question .corps{position:absolute;left:0;top:660px;width:1080px;padding:26px 56px}
.g-question .ligne{font-size:50px;font-weight:700;padding:18px 0;border-bottom:3px solid #F7EAE3;line-height:1.15}
.g-question .ligne:last-child{border-bottom:none}
.valiny{font-size:32px;font-weight:800;letter-spacing:4px;color:#9A4A2B}
/* gabarit collage */
.g-collage .tete{position:absolute;left:0;top:0;width:1080px;height:372px;background:#B85C38;color:#fff;padding:52px 56px 0}
.g-collage .tete .marque{position:static;margin-bottom:24px;text-shadow:none}
.g-collage .titre{font-size:72px;margin-top:18px}
.grille{position:absolute;left:0;top:372px;width:1080px;display:grid;grid-template-columns:535px 535px;gap:10px}
.case{position:relative;height:432px;overflow:hidden}
.case img{width:535px;height:432px;object-fit:cover;display:block}
.case span{position:absolute;left:18px;top:18px;width:64px;height:64px;border-radius:50%;background:#B85C38;color:#fff;font-size:38px;font-weight:800;display:flex;align-items:center;justify-content:center;border:4px solid #fff}
/* gabarit hauteurs */
.g-hauteurs .tete{position:absolute;left:0;top:0;width:1080px;height:420px;background:#B85C38;color:#fff;padding:56px 56px 0}
.g-hauteurs .tete .marque{position:static;margin-bottom:34px;text-shadow:none}
.g-hauteurs .titre{font-size:76px;margin-top:22px}
.g-hauteurs .sous{color:#F7EAE3;font-size:42px}
.hauteurs{position:absolute;left:56px;right:56px;top:470px;height:560px;display:flex;align-items:flex-end;justify-content:space-between}
.hbloc{width:290px;text-align:center}
.hforme{background:repeating-linear-gradient(90deg,#B85C38 0 58px,#9A4A2B 58px 70px);border-radius:10px;color:#fff;display:flex;align-items:center;justify-content:center}
.hforme b{font-size:52px;font-weight:800;text-shadow:0 2px 6px rgba(0,0,0,.35)}
.hprix{font-size:46px;font-weight:800;margin-top:18px}
.hnote{position:absolute;left:56px;right:56px;top:1110px;font-size:40px;color:#495057;text-align:center}
/* gabarit capture */
.g-capture{background:#B85C38}
.g-capture .tete{position:absolute;left:0;top:0;width:1080px;padding:56px 56px 0;color:#fff}
.g-capture .tete .marque{position:static;margin-bottom:30px;text-shadow:none}
.g-capture .titre{font-size:76px;margin-top:22px}
.g-capture .sous{color:#F7EAE3;font-size:42px}
.g-capture .ecran{position:absolute;left:50%;transform:translateX(-50%);top:520px;width:560px;height:730px;border-radius:44px;border:14px solid #1A1A1A;overflow:hidden;background:#fff;box-shadow:0 20px 50px rgba(0,0,0,.35)}
.g-capture .ecran img{width:100%;display:block}
/* gabarit tarifs */
.g-tarifs .tete{position:absolute;left:0;top:0;width:1080px;height:330px;background:#B85C38;color:#fff;padding:52px 56px 0}
.g-tarifs .tete .marque{position:static;margin-bottom:26px;text-shadow:none}
.g-tarifs .titre{font-size:72px}
.g-tarifs .sous{color:#F7EAE3;font-size:34px;margin-top:6px}
.g-tarifs table{position:absolute;left:56px;top:370px;width:968px;border-collapse:collapse;font-size:42px}
.g-tarifs th{text-align:left;color:#9A4A2B;font-size:30px;letter-spacing:2px;padding:22px 0 8px}
.g-tarifs td{padding:10px 0;border-bottom:2px solid #F7EAE3}
.g-tarifs td.p{text-align:right;font-weight:800}
.g-tarifs td.m{color:#6B7280;font-size:28px;text-align:right;padding-right:26px}
"""

AJUSTER = """
<script>
// réduit la taille d'un texte tant qu'il déborde de sa boîte : un titre long ne doit
// jamais sortir de l'affiche ni passer sous le pied de page
document.querySelectorAll('[data-max]').forEach(function (el) {
  var max = +el.dataset.max, t = parseFloat(getComputedStyle(el).fontSize);
  while ((el.scrollWidth > el.clientWidth + 1 || (el.dataset.bloc && el.scrollHeight > el.clientHeight + 1) || el.getBoundingClientRect().height > max) && t > 24) {
    t -= 2; el.style.fontSize = t + 'px';
  }
});
document.body.dataset.pret = '1';
</script>"""


def marque() -> str:
    return f'<div class="marque"><img src="logo.png" alt=""><span>Hourdis Madagascar</span></div>'


def pied() -> str:
    return '<div class="pied"><span class="site">hourdis.fonenako.mg</span><span class="tel">032 47 041 43</span></div>'


def esc(s: str) -> str:
    return html.escape(s or "")


def html_affiche(p: dict, a: dict, photo: bool) -> str:
    g = a["gabarit"]
    if g == "photo":
        prix = (f'<div class="prix"><b>{esc(a["prix"])}</b><span>ny iray</span></div>'
                if a.get("prix") else "")
        corps = f"""<img class="photo" src="photo.jpg" style="height:860px" alt="">
<div class="voile"></div>{marque()}
<div class="panneau"><span class="badge">{esc(a['badge'])}</span>
<div class="titre" data-max="{170 if prix else 180}">{esc(a['titre'])}</div>
<div class="sous" data-max="110">{esc(a.get('sous_titre'))}</div>{prix}</div>{pied()}"""
    elif g == "carte":
        lignes = "".join(f'<div class="ligne">{esc(l)}</div>' for l in a.get("lignes", []))
        if a.get("prix"):
            lignes = (f'<div class="prix" style="margin:0 0 18px"><b>{esc(a["prix"])}</b>'
                      f'<span>ny iray</span></div>') + lignes
        # la bande photo prend la place que les lignes laissent libre (ligne ≈ 86 px,
        # bloc prix ≈ 130 px, marges 88 px), entre 200 et 430 px
        if a.get("note"):
            lignes += f'<div class="note">{esc(a["note"])}</div>'
        besoin = 88 + (130 if a.get("prix") else 0) + 86 * len(a.get("lignes", [])) + (70 if a.get("note") else 0)
        bande_h = max(200, min(430, H - 420 - 104 - besoin - 10)) if photo else 0
        corps_h = H - 420 - 104 - bande_h
        bande = (f'<img class="bande" src="photo.jpg" style="top:{H - 104 - bande_h}px;height:{bande_h}px" alt="">'
                 if photo else "")
        corps = f"""<div class="tete">{marque()}<span class="badge clair">{esc(a['badge'])}</span>
<div class="titre" data-max="92" style="white-space:nowrap">{esc(a['titre'])}</div><div class="sous" data-max="56" style="white-space:nowrap">{esc(a.get('sous_titre'))}</div></div>
<div class="corps" style="height:{corps_h}px" data-max="{corps_h}" data-bloc="1">{lignes}</div>{bande}{pied()}"""
    elif g == "question":
        # la question d'un client (reformulée, jamais son nom) dans une bulle, la réponse dessous
        lignes = "".join(f'<div class="ligne">✓ {esc(l)}</div>' for l in a.get("lignes", []))
        corps = f"""<div class="tete">{marque()}<span class="badge clair">{esc(a['badge'])}</span>
<div class="bulle" data-max="330">« {esc(a['question'])} »</div></div>
<div class="corps" style="height:{H - 660 - 104}px" data-max="{H - 660 - 104}" data-bloc="1"><div class="valiny">VALINY</div>{lignes}</div>{pied()}"""
    elif g == "collage":
        cases = "".join(f'<div class="case"><img src="photo-{i}.jpg" alt=""><span>{i}</span></div>'
                        for i in range(1, len(a["photos"]) + 1))
        corps = f"""<div class="tete">{marque()}<span class="badge clair">{esc(a['badge'])}</span>
<div class="titre" data-max="92" style="white-space:nowrap">{esc(a['titre'])}</div></div>
<div class="grille">{cases}</div>{pied()}"""
    elif g == "hauteurs":
        # schéma à l'échelle : les trois hourdis ne diffèrent QUE par la hauteur (33 × 33 cm)
        cat = next(c for c in PRODUITS["categories"] if c["id"] == "hourdis")
        blocs = []
        for pr in sorted(cat["produits"], key=lambda x: x["prix"]):
            h_cm = int(re.match(r"Hourdis (\d+)", pr["nom"]).group(1))
            prix = f"{pr['prix']:,}".replace(",", " ")
            blocs.append(f'<div class="hbloc"><div class="hforme" style="height:{h_cm * 16}px"><b>{h_cm} cm</b></div>'
                         f'<div class="hprix">{prix} Ar</div></div>')
        corps = f"""<div class="tete">{marque()}<span class="badge clair">{esc(a['badge'])}</span>
<div class="titre" data-max="92" style="white-space:nowrap">{esc(a['titre'])}</div><div class="sous" data-max="56" style="white-space:nowrap">{esc(a.get('sous_titre'))}</div></div>
<div class="hauteurs">{''.join(blocs)}</div><div class="hnote">{esc(a.get('note'))}</div>{pied()}"""
    elif g == "capture":
        corps = f"""<div class="tete">{marque()}<span class="badge clair">{esc(a['badge'])}</span>
<div class="titre" data-max="92" style="white-space:nowrap">{esc(a['titre'])}</div><div class="sous" data-max="56" style="white-space:nowrap">{esc(a.get('sous_titre'))}</div></div>
<div class="ecran"><img src="capture.png" alt=""></div>{pied()}"""
    elif g == "tarifs":
        lignes = []
        for c in PRODUITS["categories"][:3]:
            m = f"{c['pcs_m2']} isaky ny m²" if c.get("pcs_m2") else ""
            lignes.append(f'<tr><th colspan="2">{esc(c["titre"].upper())}</th><td class="m">{esc(m)}</td><td></td></tr>')
            for pr in c["produits"]:
                nom = pr["nom"].replace(" cm", "")
                mm = f"{pr['pcs_m2']} / m²" if pr.get("pcs_m2") and not c.get("pcs_m2") else ""
                prix = f"{pr['prix']:,}".replace(",", " ")   # séparateur des milliers SEUL : « 22×33,5 » garde sa virgule
                lignes.append(f'<tr><td colspan="2">{esc(nom)}</td><td class="m">{esc(mm)}</td>'
                              f'<td class="p">{prix} Ar</td></tr>')
        corps = f"""<div class="tete">{marque()}<div class="titre">{esc(a['titre'])}</div>
<div class="sous">{esc(a.get('sous_titre'))}</div></div><table>{''.join(lignes)}</table>{pied()}"""
    else:
        raise ValueError(g)
    return (f'<!doctype html><html lang="mg"><head><meta charset="utf-8"><style>{CSS}</style></head>'
            f'<body class="g-{g}">{corps}{AJUSTER}</body></html>')


# ------------------------------------------------------------------ commandes
def cmd_tout(seulement: list[str]) -> int:
    from playwright.sync_api import sync_playwright
    ph, aff = photos(), affectation()
    manquantes = []
    with sync_playwright() as pw:
        nav = pw.chromium.launch()
        page = nav.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        for p in SERIE:
            if seulement and p["slug"] not in seulement and p["date"] not in seulement:
                continue
            d = dossier(p)
            d.mkdir(parents=True, exist_ok=True)
            a = p["affiche"]
            with Image.open(LOGO) as im:
                im.convert("RGB").save(d / "logo.png")
            # la photo
            pid = aff.get(p["slug"])
            photo = False
            if a["gabarit"] in ("photo", "carte") and pid:
                info = ph[pid]
                # bande de carte : préparée à sa hauteur MAXIMALE (430), jamais agrandie par le navigateur
                haut = 860 if a["gabarit"] == "photo" else 430
                preparer_photo(Path(info["chemin"]), d / "photo.jpg", W, haut,
                               boite=info.get("recadrage_conseille"),
                               foyer=tuple(info.get("foyer", (0.5, 0.5))))
                photo = True
            elif a["gabarit"] == "collage":
                for i, cid in enumerate(a["photos"], 1):
                    info = ph[cid]
                    preparer_photo(Path(info["chemin"]), d / f"photo-{i}.jpg", 535, 448,
                                   boite=info.get("recadrage_conseille"),
                                   foyer=tuple(info.get("foyer", (0.5, 0.5))))
                pid = ",".join(a["photos"])
                photo = True
            elif a["gabarit"] == "photo":
                manquantes.append(p["slug"])
                Image.new("RGB", (W, 860), "#D9B8A8").save(d / "photo.jpg")
            if a["gabarit"] == "capture":
                src = CAPTURES / f"{a['capture']}.png"
                if not src.exists():
                    raise SystemExit(f"capture absente : {src} — lancer d'abord « captures »")
                (d / "capture.png").write_bytes(src.read_bytes())
            (d / "affiche.html").write_text(html_affiche(p, a, photo), encoding="utf-8")
            page.goto((d / "affiche.html").as_uri())
            page.wait_for_selector("body[data-pret='1']")
            page.wait_for_timeout(300)
            page.screenshot(path=str(d / "affiche-fil.png"), full_page=False)
            texte = texte_complet(p)
            (d / "brouillon.txt").write_text(texte, encoding="utf-8")
            (d / "fiche.json").write_text(json.dumps({
                "numero": numero(p), "date": p["date"], "heure": HEURE, "slug": p["slug"],
                "page": "Hourdis Madagascar (470850726774233)", "lien": lien(p),
                "photo": pid, "photo_chemin": ph.get(pid, {}).get("chemin") if pid and pid in ph else None,
                "gabarit": a["gabarit"], "caracteres": len(texte),
            }, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"✅ {numero(p):02d} {d.name}  ({len(texte)} car.)" + ("" if photo or a["gabarit"] in ("capture", "tarifs") else "  ⚠ SANS PHOTO"))
        nav.close()
    if manquantes:
        print("⚠ photo non affectée :", ", ".join(manquantes))
    return 0


def cmd_captures(_args) -> int:
    """Calculatrice (hourdis 15, 40 m²) et formulaire de devis, à 390 px, site LOCAL."""
    from playwright.sync_api import sync_playwright
    CAPTURES.mkdir(exist_ok=True)
    with sync_playwright() as pw:
        nav = pw.chromium.launch()
        ctx = nav.new_context(viewport={"width": 390, "height": 507}, device_scale_factor=2,
                              is_mobile=True, has_touch=True)
        page = ctx.new_page()
        page.goto(LOCAL + "/", wait_until="networkidle")
        # calculatrice : le bouton du hourdis 15, 40 m²
        btn = page.locator(".calculator-btn[data-name*='15']").first
        btn.scroll_into_view_if_needed()
        btn.click()
        page.fill("#calcSurface", "40")
        page.dispatch_event("#calcSurface", "input")
        page.wait_for_selector("#calculatorResult.is-visible")
        page.wait_for_timeout(500)
        page.screenshot(path=str(CAPTURES / "calcul.png"))
        page.keyboard.press("Escape")
        # formulaire de devis, vide
        page.goto(LOCAL + "/#contact", wait_until="networkidle")
        page.locator("#titre-formulaire").scroll_into_view_if_needed()
        page.evaluate("window.scrollBy(0, -12)")
        page.wait_for_timeout(500)
        page.screenshot(path=str(CAPTURES / "devis.png"))
        nav.close()
    print("captures :", ", ".join(f.name for f in CAPTURES.glob("*.png")))
    return 0


def cmd_planche(_args) -> int:
    """Deux planches de 15 affiches, pour regarder la série d'un coup d'œil."""
    dossiers = [dossier(p) for p in SERIE if (dossier(p) / "affiche-fil.png").exists()]
    for n in range(0, len(dossiers), 15):
        lot = dossiers[n:n + 15]
        tw, th = 240, 300
        planche = Image.new("RGB", (5 * tw + 6 * 8, 3 * th + 4 * 8), "#333")
        for i, d in enumerate(lot):
            with Image.open(d / "affiche-fil.png") as im:
                im = im.convert("RGB").resize((tw, th), Image.LANCZOS)
            planche.paste(im, (8 + (i % 5) * (tw + 8), 8 + (i // 5) * (th + 8)))
        f = ICI / f"planche{NOM}-{n // 15 + 1}.jpg"
        planche.save(f, "JPEG", quality=80)
        print(f, f.stat().st_size // 1024, "Ko")
    return 0


JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]


def cmd_cahier(_args) -> int:
    """cahier.html : chaque jour, l'affiche et le texte EXACT qui partira — pour relire."""
    from datetime import date
    blocs = []
    for p in SERIE:
        d = dossier(p)
        j = date.fromisoformat(p["date"])
        texte = (d / "brouillon.txt").read_text(encoding="utf-8") if (d / "brouillon.txt").exists() else "(non fabriqué)"
        blocs.append(f"""<article><img src="sortie/{d.name}/affiche-fil.png" alt="">
<div><h2>{numero(p):02d} · {JOURS[j.weekday()]} {j:%d/%m} · {HEURE}</h2><pre>{esc(texte)}</pre></div></article>""")
    (ICI / f"cahier{NOM}.html").write_text(f"""<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Hourdis — 30 publications</title>
<style>body{{font-family:"Segoe UI",Arial,sans-serif;margin:0 auto;max-width:1000px;padding:16px;background:#F8F9FA;color:#1A1A1A}}
h1{{color:#9A4A2B}}article{{display:flex;flex-wrap:wrap;gap:20px;background:#fff;border-radius:10px;padding:16px;margin:16px 0;box-shadow:0 1px 4px rgba(0,0,0,.08)}}
article img{{width:270px;max-width:100%;border-radius:6px}}article div{{flex:1;min-width:260px}}
h2{{font-size:18px;margin:0 0 8px;color:#B85C38}}pre{{white-space:pre-wrap;font-family:inherit;font-size:15px;line-height:1.5;margin:0}}</style></head>
<body><h1>Hourdis Madagascar — 30 publications, 19/09 → 18/10/2026</h1>
<p>Une publication par jour à {HEURE} (heure de Tana). Le texte ci-dessous est exactement celui qui partira.</p>
{''.join(blocs)}</body></html>""", encoding="utf-8")
    print(ICI / f"cahier{NOM}.html")
    return 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "cahier":
        sys.exit(cmd_cahier(sys.argv[2:]))
    if cmd == "tout":
        sys.exit(cmd_tout(sys.argv[2:]))
    if cmd == "captures":
        sys.exit(cmd_captures(sys.argv[2:]))
    if cmd == "planche":
        sys.exit(cmd_planche(sys.argv[2:]))
    raise SystemExit(__doc__)
