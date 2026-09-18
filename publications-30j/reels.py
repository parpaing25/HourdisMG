# -*- coding: utf-8 -*-
"""reels.py — un reel vertical (1080×1920, ~13 s) par publication de la série.

    python publications-30j/reels.py scenes            # affiche le découpage texte de chaque reel
    python publications-30j/reels.py tout [slug ...]   # scènes PNG + montage → sortie/<post>/reel.mp4
    python publications-30j/reels.py planche           # planche des premières scènes, pour contrôle

Chaque reel = 3 scènes composées (texte intégré à l'image) + une carte de fin commune
(site, téléphone). Le montage (zoom lent, fondus, musique à -14 LUFS) est celui de
l'atelier Fonenako : marketing/atelier/clip.py, importé tel quel, rien n'est recopié.

Zone sûre : le zoom lent de clip.py rogne ~11 % de l'image, et Facebook couvre le haut
(~250 px) et le bas (~420 px) d'un reel. Tout le texte vit entre x 120-960 et y 230-1480.

Musique : bibliothèque Mixkit de l'atelier (licence relue le 04/09/2026, sans
attribution), catégories « annonce » et « confiance », jamais deux jours de suite le
même morceau. Aucune voix : une voix malgache se choisit à l'oreille d'Andry.
"""
from __future__ import annotations

import html
import json
import re
import subprocess
import sys
from pathlib import Path

from PIL import Image

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
from serie import SERIE  # noqa: E402
from reels_scenes import SCENES  # noqa: E402
from fabriquer import (PRODUITS, LOGO, dossier, numero, photos, affectation,  # noqa: E402
                       preparer_photo, CAPTURES)

ATELIER = Path.home() / "Desktop/Fonenako preprod/29031/Fonenako FinAL GITHUB/marketing/atelier"
sys.path.insert(0, str(ATELIER))
import clip  # noqa: E402  (le monteur de l'atelier Fonenako)

W, H = 1080, 1920
DUREE_SCENE = 3.8
# morceaux Mixkit (sans attribution) : annonce 05-08, confiance 09-12
MUSIQUES = sorted((ATELIER / "musique").glob("0[5-9]-*.mp3")) + sorted((ATELIER / "musique").glob("1[0-2]-*.mp3"))

MARQUEURS = ("→", "✅", "❌", "•", "1️⃣", "2️⃣", "3️⃣", "4️⃣", "🅰️", "🅱️", "🅲️", "🅳️")


def points_du_texte(texte: str, n: int = 4) -> list[str]:
    """Les lignes à puces du texte, sans leur puce, coupées à la première flèche."""
    res = []
    for l in texte.split("\n"):
        l = l.strip()
        if not l.startswith(MARQUEURS):
            continue
        for m in MARQUEURS:
            if l.startswith(m):
                l = l[len(m):].strip()
        l = l.split(" → ")[0].strip()
        if l:
            res.append(l)
    return res[:n]


def premiere_phrase(texte: str) -> str:
    l = texte.strip().split("\n")[0]
    return re.sub(r"^[^\w«]+", "", l).strip()


# ------------------------------------------------------------------ découpage
def decoupage(p: dict) -> list[dict]:
    """Les scènes d'un reel : 1 = l'affiche (ou « s1 »), 2 et 3 = reels_scenes.py.
    La grille des prix se génère depuis produits.json : aucun prix recopié à la main."""
    a = p["affiche"]
    g = a["gabarit"]
    if g == "tarifs":
        sc = [{"fond": "terre", "badge": a["badge"], "titre": a["titre"], "sous": a.get("sous_titre", "")}]
        for c in PRODUITS["categories"][:3]:
            sc.append({"fond": "terre", "titre": c["titre"],
                       "lignes": [f"{pr['nom'].replace(' cm', '')} · " + f"{pr['prix']:,} Ar".replace(",", " ")
                                  for pr in c["produits"]]})
        return sc
    ecrit = SCENES[p["slug"]]
    fond = "terre" if g == "capture" else "photo"
    s1 = dict(ecrit.get("s1") or {"badge": a["badge"], "titre": a["titre"], "sous": a.get("sous_titre", "")})
    s1["fond"] = "capture" if g == "capture" else "photo"
    return [s1] + [dict(ecrit[k], fond=fond) for k in ("s2", "s3")]


# ------------------------------------------------------------------ rendu des scènes
CSS = """
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:1080px;height:1920px;overflow:hidden}
body{font-family:"Segoe UI",Roboto,Arial,sans-serif;background:#9A4A2B;position:relative;color:#fff}
.fond{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover}
.voile{position:absolute;inset:0;background:linear-gradient(rgba(0,0,0,.55) 0,rgba(0,0,0,0) 420px,rgba(0,0,0,0) 760px,rgba(0,0,0,.72) 1250px,rgba(0,0,0,.78) 1920px)}
.terre{background:#B85C38}
.marque{position:absolute;left:120px;top:240px;display:flex;align-items:center;gap:22px;font-weight:700;font-size:40px;text-shadow:0 2px 8px rgba(0,0,0,.45)}
.marque img{width:100px;height:100px;border-radius:50%;border:5px solid #fff;background:#fff}
.bloc{position:absolute;left:120px;right:120px;bottom:470px}
.badge{display:inline-block;background:#B85C38;color:#fff;font-weight:800;letter-spacing:3px;font-size:36px;padding:14px 30px;border-radius:44px;margin-bottom:26px}
.terre .badge{background:#fff;color:#9A4A2B}
.titre{font-weight:800;font-size:96px;line-height:1.06;text-shadow:0 3px 12px rgba(0,0,0,.45)}
.sous{font-size:52px;line-height:1.25;margin-top:20px;color:#F7EAE3;text-shadow:0 2px 8px rgba(0,0,0,.5)}
.prix{display:inline-flex;align-items:baseline;gap:18px;background:#B85C38;border-radius:24px;padding:20px 40px;margin-bottom:24px}
.prix b{font-size:110px;font-weight:800}
.prix span{font-size:44px}
.panneau{background:#fff;color:#1A1A1A;border-radius:32px;padding:22px 44px;margin-top:24px;box-shadow:0 12px 40px rgba(0,0,0,.35)}
.ligne{font-size:56px;font-weight:700;line-height:1.18;padding:22px 0;border-bottom:3px solid #F7EAE3}
.ligne:last-child{border-bottom:none}
.ecran{position:absolute;left:50%;transform:translateX(-50%);top:420px;width:620px;height:806px;border-radius:50px;border:16px solid #1A1A1A;overflow:hidden;background:#fff;box-shadow:0 24px 60px rgba(0,0,0,.4)}
.ecran img{width:100%;display:block}
.capture .bloc{top:380px;bottom:auto}
.capture .ecran{top:790px;width:540px;height:702px}
/* carte de fin */
.fin{background:#B85C38;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;gap:26px}
.fin img{width:240px;height:240px;border-radius:50%;border:8px solid #fff;background:#fff}
.fin .nom{font-size:64px;font-weight:800}
.fin .site{font-size:74px;font-weight:800;background:#fff;color:#9A4A2B;border-radius:24px;padding:18px 40px}
.fin .petit{font-size:48px;color:#F7EAE3;line-height:1.35}
"""

AJUSTER = """<script>
document.querySelectorAll('[data-max]').forEach(function (el) {
  var max = +el.dataset.max, t = parseFloat(getComputedStyle(el).fontSize);
  // hauteur ET largeur : « hourdis.fonenako.mg » est un seul mot, il déborde à droite sans jamais passer à la ligne
  while ((el.getBoundingClientRect().height > max || el.scrollWidth > el.clientWidth + 1) && t > 30) { t -= 2; el.style.fontSize = t + 'px'; }
});
document.querySelectorAll('.bloc').forEach(function (b) {   // le bloc ne remonte jamais sous la marque
  var t = b.getBoundingClientRect().top;
  if (t < 380) { var f = b.querySelectorAll('.ligne,.titre,.sous');
    f.forEach(function (e) { e.style.fontSize = (parseFloat(getComputedStyle(e).fontSize) * 0.85) + 'px'; }); }
});
document.body.dataset.pret = '1';
</script>"""


INSECABLE = chr(160)


def e(s) -> str:
    """Échappe, et colle ce qui ne doit jamais se séparer en fin de ligne : les tranches d'un
    nombre (« 3 / 500 Ar » vu le 18/09 sur la grille des prix), « Ar », « ? », « ! », « : »
    et les guillemets (un « ? » seul sur sa ligne sur trois reels)."""
    s = s or ""
    for _ in range(2):   # 1 200 000 : deux passes pour les millions
        s = re.sub(r"(\d) (\d{3})\b", lambda m: m.group(1) + INSECABLE + m.group(2), s)
    for avant, apres in ((" Ar", INSECABLE + "Ar"), (" ?", INSECABLE + "?"), (" !", INSECABLE + "!"),
                         (" :", INSECABLE + ":"), (" »", INSECABLE + "»"), ("« ", "«" + INSECABLE)):
        s = s.replace(avant, apres)
    return html.escape(s)


def html_scene(sc: dict) -> str:
    fond = sc["fond"]
    if fond == "photo":
        tete = '<img class="fond" src="photo-reel.jpg" alt=""><div class="voile"></div>'
        classe = ""
    elif fond == "capture":
        tete = '<div class="ecran"><img src="capture.png" alt=""></div>'
        classe = "terre capture"
    else:
        tete, classe = "", "terre"
    marque = '<div class="marque"><img src="logo.png" alt=""><span>Hourdis Madagascar</span></div>'
    parts = []
    if sc.get("badge"):
        parts.append(f'<span class="badge">{e(sc["badge"])}</span>')
    if sc.get("prix"):
        parts.append(f'<div><div class="prix"><b>{e(sc["prix"])}</b><span>ny iray</span></div></div>')
    if sc.get("titre"):
        parts.append(f'<div class="titre" data-max="330">{e(sc["titre"])}</div>')
    if sc.get("sous"):
        parts.append(f'<div class="sous" data-max="200">{e(sc["sous"])}</div>')
    if sc.get("lignes"):
        parts.append('<div class="panneau">' + "".join(f'<div class="ligne">{e(l)}</div>' for l in sc["lignes"]) + "</div>")
    return (f'<!doctype html><html lang="mg"><head><meta charset="utf-8"><style>{CSS}</style></head>'
            f'<body class="{classe}">{tete}{marque}<div class="bloc">{"".join(parts)}</div>{AJUSTER}</body></html>')


def html_fin() -> str:
    return (f'<!doctype html><html lang="mg"><head><meta charset="utf-8"><style>{CSS}</style></head>'
            '<body class="fin"><img src="logo.png" alt=""><div class="nom">Hourdis Madagascar</div>'
            '<div class="site">hourdis.fonenako.mg</div>'
            '<div class="petit">Vidiny · Kajy · Devis maimaim-poana<br>📞 032 47 041 43 · 033 71 063 34<br>📍 Ambohimanga Rova</div>'
            '<script>document.body.dataset.pret="1"</script></body></html>')


def rendre(page, html_txt: str, d: Path, nom: str) -> Path:
    f = d / f"{nom}.html"
    f.write_text(html_txt, encoding="utf-8")
    page.goto(f.as_uri())
    page.wait_for_selector("body[data-pret='1']")
    page.wait_for_timeout(250)
    png = d / f"{nom}.png"
    page.screenshot(path=str(png))
    return png


def cmd_scenes(_a) -> int:
    for p in SERIE:
        print(f"\n{numero(p):02d} {p['slug']}")
        for i, sc in enumerate(decoupage(p), 1):
            print(f"   {i}. " + " | ".join(f"{k}={v}" for k, v in sc.items() if k != "fond" and v))
    return 0


def cmd_tout(seulement: list[str]) -> int:
    from playwright.sync_api import sync_playwright
    ph, aff = photos(), affectation()
    fait = []
    with sync_playwright() as pw:
        nav = pw.chromium.launch()
        page = nav.new_page(viewport={"width": W, "height": H})
        for p in SERIE:
            if seulement and p["slug"] not in seulement and p["date"] not in seulement:
                continue
            d = dossier(p) / "reel"
            d.mkdir(parents=True, exist_ok=True)
            with Image.open(LOGO) as im:
                im.convert("RGB").save(d / "logo.png")
            pid = aff.get(p["slug"])
            if pid:
                info = ph[pid]
                preparer_photo(Path(info["chemin"]), d / "photo-reel.jpg", W, H,
                               boite=info.get("recadrage_conseille"), foyer=tuple(info.get("foyer", (0.5, 0.5))))
            if p["affiche"]["gabarit"] == "capture":
                (d / "capture.png").write_bytes((CAPTURES / f"{p['affiche']['capture']}.png").read_bytes())
            scenes = []
            for i, sc in enumerate(decoupage(p), 1):
                if sc["fond"] == "photo" and not pid:
                    sc["fond"] = "terre"
                scenes.append(rendre(page, html_scene(sc), d, f"scene-{i}"))
            fin = rendre(page, html_fin(), d, "fin")
            fait.append((p, scenes, fin))
        nav.close()
    for p, scenes, fin in fait:
        musique = MUSIQUES[(numero(p) - 1) % len(MUSIQUES)]
        sortie = dossier(p) / "reel.mp4"
        brut = dossier(p) / "reel" / "reel-brut.mp4"
        clip.fabriquer(scenes, [""] * len(scenes), "story", brut, musique=musique,
                       duree_photo=DUREE_SCENE, carte_fin=fin)
        # Sans voix, clip.py laisse la musique à 0.22 — le niveau prévu pour passer SOUS
        # une voix — et ne normalise pas : -27,5 LUFS mesurés le 18/09, inaudible au
        # téléphone. On ramène le reel à -14 LUFS (la cible de clip.py pour les vidéos à
        # voix), sans toucher à clip.py, validé et partagé avec Fonenako.
        clip._ff(["-i", str(brut), "-c:v", "copy", "-af", "loudnorm=I=-14:TP=-1.5:LRA=9,aresample=48000",
                  "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(sortie)])
        brut.unlink()
        info = sonde(sortie)
        info["lufs"] = volume(sortie)
        (dossier(p) / "reel" / "reel.json").write_text(json.dumps(
            {"musique": musique.name, **info}, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"🎬 {numero(p):02d} {p['slug']} → {info['duree']:.1f} s · {info['largeur']}x{info['hauteur']} · "
              f"{info['video']}/{info['audio']} · {info["octets"] // 1024} Ko · {info["lufs"]} LUFS · {musique.name}", flush=True)
    return 0


def sonde(f: Path) -> dict:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "format=duration,size:stream=codec_type,codec_name,width,height,sample_rate",
                        "-of", "json", str(f)], capture_output=True, text=True, check=True)
    j = json.loads(r.stdout)
    v = next(s for s in j["streams"] if s["codec_type"] == "video")
    a = next((s for s in j["streams"] if s["codec_type"] == "audio"), {})
    return {"duree": float(j["format"]["duration"]), "octets": int(j["format"]["size"]),
            "largeur": v["width"], "hauteur": v["height"], "video": v["codec_name"],
            "audio": a.get("codec_name", "AUCUN"), "echantillonnage": a.get("sample_rate")}


def volume(f: Path) -> float:
    """Sonie intégrée mesurée (EBU R128), en LUFS."""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(f), "-af", "ebur128", "-f", "null", "-"],
                       capture_output=True, text=True)
    m = re.findall(r"I:\s+(-?\d+(?:\.\d+)?) LUFS", r.stderr)
    return float(m[-1]) if m else 0.0


def cmd_planche(_a) -> int:
    """Pour chaque reel : ses 3 scènes et la fin, en vignettes, 5 reels par planche."""
    lots = [p for p in SERIE if (dossier(p) / "reel" / "scene-1.png").exists()]
    tw, th = 120, 213
    for n in range(0, len(lots), 5):
        lot = lots[n:n + 5]
        pl = Image.new("RGB", (4 * tw + 5 * 4, len(lot) * (th + 4) + 4), "#333")
        for r, p in enumerate(lot):
            d = dossier(p) / "reel"
            for c, nom in enumerate(["scene-1", "scene-2", "scene-3", "fin"]):
                f = d / f"{nom}.png"
                if f.exists():
                    with Image.open(f) as im:
                        pl.paste(im.convert("RGB").resize((tw, th), Image.LANCZOS), (4 + c * (tw + 4), 4 + r * (th + 4)))
        f = ICI / f"planche-reels-{n // 5 + 1}.jpg"
        pl.save(f, "JPEG", quality=82)
        print(f)
    return 0


if __name__ == "__main__":
    c = sys.argv[1] if len(sys.argv) > 1 else ""
    cmds = {"scenes": cmd_scenes, "tout": cmd_tout, "planche": cmd_planche}
    if c not in cmds:
        raise SystemExit(__doc__)
    sys.exit(cmds[c](sys.argv[2:]))
