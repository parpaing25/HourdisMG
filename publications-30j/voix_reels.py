# -*- coding: utf-8 -*-
"""voix_reels.py — les reels Hourdis EXPLIQUÉS par la voix malgache Abidi (serie_voix.py).

    python publications-30j/voix_reels.py verifier            # textes : alphabet, chiffres, scènes
    python publications-30j/voix_reels.py essai               # essai de prononciation de « hourdis »
    python publications-30j/voix_reels.py tout [slug ...]     # scènes + voix + montage
    python publications-30j/voix_reels.py planche             # une image par scène, pour contrôle
    python publications-30j/voix_reels.py cahier              # cahier-voix.html : narration + légende

La chaîne est celle qu'Andry a validée à l'oreille, importée telle quelle, jamais recopiée :
voix = tools/tutos-video/voix.py `narration()` (réglage N3 du 04/09/2026 : Abidi phrase par
phrase, restauration sur le VPS, pièce de 0,80 s) ; montage = marketing/atelier/film.py
(musique 0.22 en side-chain, −14 LUFS). Deux ajouts seulement, faits ICI à l'exécution :
- le lexique de prononciation de « hourdis » (le mot porte un u, hors alphabet malgache) ;
  il se choisit À L'OREILLE dans prononciation.json, après l'essai ;
- la couleur des sous-titres (terre cuite Hourdis au lieu du bleu Fonenako).
Les nombres s'écrivent {n:3400} dans serie_voix.py : la voix les dit en toutes lettres,
les sous-titres et la légende les écrivent en chiffres.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

os.environ.setdefault("HOURDIS_SERIE", "serie_voix")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
import fabriquer as F  # noqa: E402
import reels as R  # noqa: E402

DEPOT = Path.home() / "Desktop/Fonenako preprod/29031/Fonenako FinAL GITHUB"
ATELIER, TUTOS = DEPOT / "marketing/atelier", DEPOT / "tools/tutos-video"
sys.path[:0] = [str(ATELIER), str(TUTOS)]
import clip  # noqa: E402
import film  # noqa: E402
import voix  # noqa: E402
import reel_cartes  # noqa: E402

SERIE = F.SERIE
FICHIER_PRONONCIATION = ICI / "prononciation.json"
VARIANTES = ["hourdis", "ordy", "hordy", "ordisy"]      # l'essai ; Andry choisit à l'oreille
MUSIQUES = sorted((ATELIER / "musique").glob("0[1-4]-tuto-*.mp3"))

# Sous-titres : terre cuite #9A4A2B (ASS = &HAABBGGRR), cartouche à 25 % de transparence
TERRE_CONTOUR, TERRE_FOND = "&H002B4A9A", "&H402B4A9A"


# ------------------------------------------------------------------ les nombres
UNITES = ["", "iray", "roa", "telo", "efatra", "dimy", "enina", "fito", "valo", "sivy"]
DIZAINES = ["", "folo", "roapolo", "telopolo", "efapolo", "dimampolo", "enimpolo", "fitopolo", "valopolo", "sivifolo"]
CENTAINES = ["", "zato", "roanjato", "telonjato", "efajato", "dimanjato", "eninjato", "fitonjato", "valonjato", "sivinjato"]


def _moins_de_cent(n: int) -> str:
    if n < 10:
        return UNITES[n]
    if n == 10:
        return "folo"
    if n < 20:
        return ("iraika" if n == 11 else UNITES[n - 10]) + " ambin'ny folo"
    d, u = divmod(n, 10)
    return DIZAINES[d] + (" sy " + UNITES[u] if u else "")


def mg_nombre(n: int) -> str:
    """Du plus grand au plus petit, joints par « sy » — la forme de la narration validée
    (« roa ambin'ny folo tapitrisa sy dimy hetsy », « iray hetsy sy roa alina »)."""
    if n <= 0:
        return "aotra"
    parts = []
    for val, nom in ((1_000_000, "tapitrisa"), (100_000, "hetsy"), (10_000, "alina"), (1000, "arivo")):
        q, n = divmod(n, val)
        if q:
            parts.append("arivo" if (nom == "arivo" and q == 1) else f"{_moins_de_cent(q)} {nom}")
    q, n = divmod(n, 100)
    if q:
        parts.append(CENTAINES[q])
    if n:
        parts.append(_moins_de_cent(n))
    return " sy ".join(parts)


NOMBRE = re.compile(r"\{n:(\d+)\}")


def parler(phrase: str) -> str:
    return NOMBRE.sub(lambda m: mg_nombre(int(m.group(1))), phrase)


def afficher(phrase: str) -> str:
    return NOMBRE.sub(lambda m: f"{int(m.group(1)):,}".replace(",", " "), phrase)


def prononciation() -> dict:
    if FICHIER_PRONONCIATION.exists():
        return json.loads(FICHIER_PRONONCIATION.read_text(encoding="utf-8"))
    return {"hourdis": "ordy", "_statut": "PAR DÉFAUT, non validé à l'oreille"}


def poser_lexique(lex: dict) -> None:
    voix.LEXIQUE_ABIDI.clear()
    for mot, dit in lex.items():
        if not mot.startswith("_") and dit != mot:
            voix.LEXIQUE_ABIDI[mot] = dit


# ------------------------------------------------------------------ contrôle
ALPHABET = set("abdefghijklmnoprstvyzàìòôỳ")
INTERROGATIFS = re.compile(r"\b(firy|inona|ahoana|aiza|iza|nahoana|ohatrinona|rahoviana|sa|ve)\b", re.I)
PRIX = {pr["prix"] for c in F.PRODUITS["categories"] for pr in c["produits"]} | {1500}
NB = r"\d{1,3}(?:[  ]\d{3})*(?:,\d+)?"


def _n(s: str) -> float:
    return float(re.sub(r"[  ]", "", s).replace(",", "."))


def verifier() -> int:
    erreurs, avis, photos_vues = [], [], {}
    lex = prononciation()
    for i, p in enumerate(SERIE, 1):
        nom = f"{i:02d} {p['slug']}"
        n = len(p["voix"])
        couvertes = [k for s in p["scenes"] for k in s["phrases"]]
        if couvertes != list(range(n)):
            erreurs.append(f"{nom} : les scènes couvrent {couvertes}, attendu 0..{n - 1} dans l'ordre")
        for ph in p["voix"]:
            dit = parler(ph)
            nettoye = re.sub(r"(?i)\b(" + "|".join(k for k in lex if not k.startswith("_")) + r")\b", "", dit)
            etrangeres = sorted({c for c in nettoye.lower() if c.isalpha() and c not in ALPHABET})
            if etrangeres:
                erreurs.append(f"{nom} : lettres hors alphabet malgache {etrangeres} dans « {dit[:60]} »")
            if "?" in ph and not INTERROGATIFS.search(ph):
                avis.append(f"{nom} : question sans interrogatif ni « ve » : {ph[:60]}")
            if len(voix.decouper_en_souffles(dit)) != len(voix.decouper_en_souffles(afficher(ph))):
                erreurs.append(f"{nom} : la voix et les sous-titres ne se coupent pas pareil : {ph[:50]}")
        mots = sum(len(parler(x).split()) for x in p["voix"])
        if mots / 2.13 > 38:
            avis.append(f"{nom} : {mots} mots ≈ {mots / 2.13:.0f} s de voix, long pour un reel")
        for s in p["scenes"]:
            ecran = " ".join([s.get("titre", ""), s.get("sous", ""), s.get("prix", "")] + s.get("lignes", []))
            admis = set(PRIX)
            for m in re.finditer(rf"({NB})\s*(?:Ar)?\s*×\s*({NB})\s*(?:Ar)?\s*=\s*({NB})", ecran):
                a, b, c = _n(m.group(1)), _n(m.group(2)), _n(m.group(3))
                if abs(a * b - c) > 0.51:
                    erreurs.append(f"{nom} : calcul faux {m.group(0)!r}")
                admis.add(int(c))
            for m in re.finditer(r"(\d{1,3}(?:[  ]\d{3})*)\s*Ar\b", ecran):
                if int(re.sub(r"\D", "", m.group(1))) not in admis:
                    erreurs.append(f"{nom} : montant {m.group(0)!r} hors catalogue")
            for m in re.finditer(r"(\d+)\s*m²\s*→\s*(\d[\d  ]*)\s*pièces", ecran):
                if not any(abs(int(re.sub(r"\D", "", m.group(2))) - int(m.group(1)) * r) < 1 for r in (9, 12, 15, 75)):
                    erreurs.append(f"{nom} : exemple faux {m.group(0)!r}")
        # les nombres dits se retrouvent-ils dans ce qui est montré ? (un prix dit ≠ prix affiché)
        for ph in p["voix"]:
            for m in re.finditer(r"\{n:(\d+)\}\s*ariary", ph):
                if int(m.group(1)) not in PRIX | {2160000}:
                    erreurs.append(f"{nom} : montant dit {m.group(1)} Ar hors catalogue")
        if p.get("photo"):
            if p["photo"] in photos_vues:
                erreurs.append(f"{nom} : photo {p['photo']} déjà prise par {photos_vues[p['photo']]}")
            photos_vues[p["photo"]] = nom
    for a in avis:
        print("⚠", a)
    for e in erreurs:
        print("❌", e)
    print(f"\n{len(SERIE)} reels · prononciation de « hourdis » : {lex.get('hourdis')} ({lex.get('_statut', 'validée')})")
    print(f"{'VERDICT ok' if not erreurs else 'VERDICT REFUSÉ'} — {len(erreurs)} erreur(s), {len(avis)} avertissement(s)")
    return 0 if not erreurs else 1


# ------------------------------------------------------------------ rendu
def _css_voix() -> None:
    """Le texte des scènes remonte : les sous-titres occupent le bas (jusqu'à 3 lignes)."""
    R.CSS = (R.CSS.replace(".bloc{position:absolute;left:120px;right:120px;bottom:470px}",
                           ".bloc{position:absolute;left:120px;right:120px;bottom:640px}")
                  .replace(".capture .ecran{top:790px;width:540px;height:702px}",
                           ".capture .ecran{top:720px;width:470px;height:611px}"))
    assert "bottom:640px" in R.CSS, "gabarit des reels modifié : revoir _css_voix"


_sous_titres_origine = clip.sous_titres


def _sous_titres_terre(*a, **k):
    f = _sous_titres_origine(*a, **k)
    t = f.read_text(encoding="utf-8").replace("&H00502A14", TERRE_CONTOUR).replace("&HA0502A14", TERRE_FOND)
    f.write_text(t, encoding="utf-8")
    return f


clip.sous_titres = _sous_titres_terre      # film.py appelle clip.sous_titres : même module


def scenes_png(page, p: dict, d: Path) -> list[Path]:
    from PIL import Image
    with Image.open(F.LOGO) as im:
        im.convert("RGB").save(d / "logo.png")
    ph = F.photos()
    if p.get("photo"):
        info = ph[p["photo"]]
        F.preparer_photo(Path(info["chemin"]), d / "photo-reel.jpg", R.W, R.H,
                         boite=info.get("recadrage_conseille"), foyer=tuple(info.get("foyer", (0.5, 0.5))))
    if p.get("capture"):
        (d / "capture.png").write_bytes((F.CAPTURES / f"{p['capture']}.png").read_bytes())
    fond = "photo" if p.get("photo") else "terre"
    pngs = []
    for i, s in enumerate(p["scenes"], 1):
        sc = {k: v for k, v in s.items() if k != "phrases"}
        sc["fond"] = "capture" if (p.get("capture") and i == 1) else fond
        pngs.append(R.rendre(page, R.html_scene(sc), d, f"scene-{i}"))
    R.rendre(page, R.html_fin(), d, "fin")
    return pngs


def construire(p: dict, page) -> dict:
    d = F.dossier(p)
    d.mkdir(parents=True, exist_ok=True)
    scenes_png(page, p, d)
    dites = [parler(x) for x in p["voix"]]
    montrees = [afficher(x) for x in p["voix"]]
    # post.md : ## VOIX = ce qui est dit, ## MG = ce que montrent les sous-titres (chiffres)
    (d / "post.md").write_text("## VOIX\n" + "\n".join(dites) + "\n\n## MG\n" + "\n".join(montrees) + "\n",
                               encoding="utf-8")
    poser_lexique(prononciation())
    wav = d / "voix-mg.wav"
    voix.narration("\n".join(dites), wav)
    souffles = json.loads((d / "voix-mg.souffles.json").read_text(encoding="utf-8"))
    groupes = reel_cartes.souffles_par_phrase(dites, souffles)
    scenes = []
    for i, s in enumerate(p["scenes"], 1):
        idx = sum((groupes[k] for k in s["phrases"]), [])
        sc = {"image": f"scene-{i}.png", "effet": "zoom" if p.get("photo") else "fixe", "souffles": idx}
        if i > 1:
            sc["sfx"] = "whoosh-doux"
        scenes.append(sc)
    musique = MUSIQUES[(F.numero(p) - 1) % len(MUSIQUES)]
    (d / "scenario.json").write_text(json.dumps({
        "format": "story", "musique": str(musique), "avance": 0.8, "scenes": scenes,
        "fin": {"image": "fin.png", "duree": 2.5}}, ensure_ascii=False, indent=1), encoding="utf-8")
    film.realiser(d, d / "reel.mp4")
    # la légende : le titre, puis la narration en chiffres, puis la fin commune (site, téléphones)
    p["texte"] = f"🎙️ {p['titre']}\n\n" + "\n".join(montrees)
    (d / "brouillon.txt").write_text(F.texte_complet(p), encoding="utf-8")
    info = R.sonde(d / "reel.mp4")
    info.update(lufs=R.volume(d / "reel.mp4"), voix_s=round(souffles[-1]["fin"], 1), musique=musique.name,
                prononciation=prononciation())
    (d / "fiche.json").write_text(json.dumps({"date": p["date"], "heure": F.HEURE, "slug": p["slug"],
                                              "photo": p.get("photo"), **info}, ensure_ascii=False, indent=1),
                                  encoding="utf-8")
    return info


def cmd_tout(seuls: list[str]) -> int:
    from playwright.sync_api import sync_playwright
    if verifier():
        return 1
    _css_voix()
    lot = [p for p in SERIE if not seuls or p["slug"] in seuls or p["date"] in seuls]
    echecs = 0
    with sync_playwright() as pw:
        nav = pw.chromium.launch()
        page = nav.new_page(viewport={"width": R.W, "height": R.H})
        for p in lot:
            try:
                i = construire(p, page)
                print(f"🎙️ {F.numero(p):02d} {p['slug']} → {i['duree']:.1f} s (voix {i['voix_s']} s) · "
                      f"{i['video']}/{i['audio']} · {i['octets'] // 1024} Ko · {i['lufs']} LUFS · {i['musique']}", flush=True)
            except Exception as e:     # un reel raté ne doit pas arrêter les 29 autres
                echecs += 1
                print(f"❌ {F.numero(p):02d} {p['slug']} : {type(e).__name__}: {str(e)[:300]}", flush=True)
        nav.close()
    print(f"\n{len(lot) - echecs}/{len(lot)} reels fabriqués.")
    return 0 if not echecs else 2


def cmd_essai(_a) -> int:
    """Une même phrase, « hourdis » dit de quatre façons : Andry choisit à l'oreille."""
    dossier = ICI / "essai-prononciation"
    dossier.mkdir(exist_ok=True)
    phrase = "Ity ny hourdis vita eto Ambohimanga Rova. Hourdis tsara, hourdis mateza."
    liste = []
    for k, v in enumerate(VARIANTES, 1):
        poser_lexique({"hourdis": v})
        wav = dossier / f"{k}-{v}.wav"
        voix.narration(phrase, wav)
        mp3 = dossier / f"{k}-{v}.mp3"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav), "-af", "loudnorm=I=-16",
                        "-b:a", "160k", str(mp3)], check=True)
        liste.append(mp3)
        print(f"   {k} · écrit « {v} » → {mp3.name} ({R.volume(mp3)} LUFS)")
    # un seul fichier : 1, silence, 2, silence…
    silence = dossier / "_silence.mp3"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "anullsrc=r=22050:cl=mono",
                    "-t", "1.5", "-b:a", "160k", str(silence)], check=True)
    concat = dossier / "_liste.txt"
    concat.write_text("".join(f"file '{f.name}'\nfile '{silence.name}'\n" for f in liste), encoding="utf-8")
    tout = dossier / "ESSAI-hourdis-1-2-3-4.mp3"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(concat),
                    "-ar", "44100", "-b:a", "160k", str(tout)], check=True, cwd=dossier)
    print(tout)
    return 0


def cmd_planche(_a) -> int:
    from PIL import Image
    lots = [p for p in SERIE if (F.dossier(p) / "scene-1.png").exists()]
    tw, th = 120, 213
    for n in range(0, len(lots), 5):
        lot = lots[n:n + 5]
        pl = Image.new("RGB", (4 * tw + 5 * 4, len(lot) * (th + 4) + 4), "#333")
        for r, p in enumerate(lot):
            for c, nom in enumerate(["scene-1", "scene-2", "scene-3", "fin"]):
                f = F.dossier(p) / f"{nom}.png"
                if f.exists():
                    with Image.open(f) as im:
                        pl.paste(im.convert("RGB").resize((tw, th), Image.LANCZOS), (4 + c * (tw + 4), 4 + r * (th + 4)))
        out = ICI / f"planche-voix-{n // 5 + 1}.jpg"
        pl.save(out, "JPEG", quality=82)
        print(out)
    return 0


def cmd_cahier(_a) -> int:
    import html as h
    blocs = []
    for p in SERIE:
        d = F.dossier(p)
        dit = "<br>".join(h.escape(parler(x)) for x in p["voix"])
        leg = h.escape((d / "brouillon.txt").read_text(encoding="utf-8")) if (d / "brouillon.txt").exists() else "(pas encore fabriqué)"
        blocs.append(f"<article><h2>{F.numero(p):02d} · {p['date'][8:10]}/{p['date'][5:7]} · {F.HEURE} — {h.escape(p['titre'])}</h2>"
                     f"<h3>Ce que dit la voix</h3><p>{dit}</p><h3>Légende de la publication</h3><pre>{leg}</pre></article>")
    (ICI / "cahier-voix.html").write_text(
        "<!doctype html><html lang='fr'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<title>Hourdis — 30 reels expliqués</title><style>body{font-family:'Segoe UI',Arial,sans-serif;max-width:900px;margin:0 auto;"
        "padding:16px;background:#F8F9FA;color:#1A1A1A}article{background:#fff;border-radius:10px;padding:16px;margin:14px 0;"
        "box-shadow:0 1px 4px rgba(0,0,0,.08)}h2{color:#B85C38;font-size:18px;margin:0 0 8px}h3{font-size:13px;color:#6B7280;"
        "text-transform:uppercase;letter-spacing:1px;margin:14px 0 4px}p{font-size:17px;line-height:1.55;margin:0}"
        "pre{white-space:pre-wrap;font-family:inherit;font-size:14px;margin:0}</style></head><body>"
        f"<h1 style='color:#9A4A2B'>Hourdis — 30 reels expliqués, {SERIE[0]['date'][8:10]}/{SERIE[0]['date'][5:7]} → "
        f"{SERIE[-1]['date'][8:10]}/{SERIE[-1]['date'][5:7]}, chaque jour à {F.HEURE}</h1>"
        "<p>Relis ce que dit la voix : c'est le texte exact envoyé à Abidi.</p>" + "".join(blocs) + "</body></html>",
        encoding="utf-8")
    print(ICI / "cahier-voix.html")
    return 0


if __name__ == "__main__":
    c = sys.argv[1] if len(sys.argv) > 1 else ""
    cmds = {"verifier": lambda a: verifier(), "essai": cmd_essai, "tout": cmd_tout,
            "planche": cmd_planche, "cahier": cmd_cahier}
    if c not in cmds:
        raise SystemExit(__doc__)
    sys.exit(cmds[c](sys.argv[2:]))
