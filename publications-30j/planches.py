# -*- coding: utf-8 -*-
"""Planches contact des photos hourdis (lecture seule sur les sources).

1. vignettes en cache (decodage JPEG reduit par draft, jamais l'original en pleine taille)
2. empreintes dHash 8x8 et 16x16 -> regroupement des copies d'une MEME photo
   (la meme image recopiee dans H, H2, Publication, Pour site...)
3. un representant par groupe, choisi par priorite de dossier puis resolution
4. planches 4x3 de vignettes 300 px, numero + nom court sous chaque vignette
5. table numero -> chemin complet dans table.json (et TABLE ci-dessous apres execution)

Usage : python planches.py            (tout)
        python planches.py zoom N...  (vues 600 px de photos precises pour verifier un detail)
"""
import sys, json, re, collections
from pathlib import Path
from PIL import Image, ImageOps, ImageDraw, ImageFont

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RACINE = Path(r"C:/Users/ANDRIANIRINA/Desktop/ASA/SERA ORDI KELY/sera/hourdis")
SITE_IMG = Path(r"C:/Users/ANDRIANIRINA/Desktop/Site Hourdis/site/image")
ICI = Path(__file__).resolve().parent
PLANCHES = ICI / "planches"
CACHE = ICI / "planches" / "_cache"
EXT = {".jpg", ".jpeg", ".png", ".webp"}
IGNORE = {"Claude 2026", "Tsy ilaina", "Hourdis Facture"}

# priorite des dossiers (plus petit = prefere comme representant)
PRIORITE = [
    ("sary vaovao/Apres traitement/Pour site", 1),
    ("sary vaovao/Apres traitement", 1),
    ("sary vaovao/Publication", 2),
    ("sary vaovao/sary vaovao ce 0904/Maivana", 3),
    ("sary vaovao/sary vaovao ce 0904", 2),
    ("Pour site/Nouveau dossier", 2),
    ("sary vaovao/Pour site", 2),
    ("sary vaovao", 2),
    ("Nouveau dossier/2-Mardi HOURDIS", 3),
    ("Nouveau dossier/4-Jeudi Tuiles", 3),
    ("Nouveau dossier/6-Samedi Brique creuse", 3),
    ("Nouveau dossier/H2", 4),
    ("Nouveau dossier/H", 4),
    ("Nouveau dossier", 4),
    ("", 5),
]

VIGN_W, VIGN_H, TXT_H, MARGE = 300, 225, 36, 6
COLS, LIGNES = 4, 3


def prio(rel):
    r = rel.replace("\\", "/")
    for pref, p in PRIORITE:
        if pref == "" or r.startswith(pref + "/"):
            return p
    return 9


def police(t):
    for f in ("C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/arial.ttf"):
        try:
            return ImageFont.truetype(f, t)
        except Exception:
            pass
    return ImageFont.load_default()


def ouvrir_reduit(p, cible=900):
    im = Image.open(p)
    if im.format == "JPEG":
        im.draft("RGB", (cible, cible))
    im.load()
    im = ImageOps.exif_transpose(im)
    return im.convert("RGB")


def dhash(im, n):
    g = im.convert("L").resize((n + 1, n), Image.LANCZOS)
    px = g.tobytes()
    bits = 0
    for y in range(n):
        for x in range(n):
            bits = (bits << 1) | (px[y * (n + 1) + x] > px[y * (n + 1) + x + 1])
    return bits


def ham(a, b):
    return bin(a ^ b).count("1")


def cle_cache(rel):
    return re.sub(r"[^A-Za-z0-9]+", "_", rel)[-120:] + ".jpg"


def charger():
    CACHE.mkdir(parents=True, exist_ok=True)
    photos = []
    for p in sorted(RACINE.rglob("*")):
        if not p.is_file() or p.suffix.lower() not in EXT:
            continue
        rel = str(p.relative_to(RACINE))
        if Path(rel).parts[0] in IGNORE:
            continue
        c = CACHE / cle_cache(rel)
        with Image.open(p) as im0:
            w, h = im0.size
            try:
                ori = im0.getexif().get(274, 1)
            except Exception:
                ori = 1
        if ori in (5, 6, 7, 8):
            w, h = h, w
        if not c.exists():
            im = ouvrir_reduit(p)
            im.thumbnail((600, 600), Image.LANCZOS)
            im.save(c, "JPEG", quality=88)
        im = Image.open(c)
        photos.append({"chemin": str(p), "rel": rel, "w": w, "h": h, "octets": p.stat().st_size,
                       "prio": prio(rel), "cache": str(c),
                       "h8": dhash(im, 8), "h16": dhash(im, 16)})
    return photos


def grouper(photos):
    n = len(photos)
    par = list(range(n))

    def f(i):
        while par[i] != i:
            par[i] = par[par[i]]
            i = par[i]
        return i

    for i in range(n):
        for j in range(i + 1, n):
            a, b = photos[i], photos[j]
            # meme photo : dHash 8 tres proche ET dHash 16 proche (evite de fusionner deux piles semblables)
            if ham(a["h8"], b["h8"]) <= 6 and ham(a["h16"], b["h16"]) <= 40:
                par[f(i)] = f(j)
    g = collections.defaultdict(list)
    for i in range(n):
        g[f(i)].append(photos[i])
    groupes = []
    for v in g.values():
        v.sort(key=lambda x: (x["prio"], -(x["w"] * x["h"]), x["rel"]))
        groupes.append(v)
    groupes.sort(key=lambda v: (v[0]["prio"], v[0]["rel"]))
    return groupes


def vignette(chemin_cache):
    im = Image.open(chemin_cache).convert("RGB")
    im.thumbnail((VIGN_W, VIGN_H), Image.LANCZOS)
    return im


def planche(items, fichier, titre):
    """items : liste de (numero, chemin_image_cache, ligne1, ligne2)"""
    W = COLS * VIGN_W + (COLS + 1) * MARGE
    H = 28 + LIGNES * (VIGN_H + TXT_H + MARGE) + MARGE
    fond = Image.new("RGB", (W, H), (245, 245, 240))
    d = ImageDraw.Draw(fond)
    f1, f2, ft = police(14), police(12), police(15)
    d.text((MARGE, 6), titre, fill=(20, 20, 20), font=ft)
    for k, (num, cache, l1, l2) in enumerate(items):
        c, r = k % COLS, k // COLS
        x = MARGE + c * (VIGN_W + MARGE)
        y = 28 + r * (VIGN_H + TXT_H + MARGE)
        im = vignette(cache)
        fond.paste(im, (x + (VIGN_W - im.width) // 2, y + (VIGN_H - im.height) // 2))
        d.rectangle([x, y + VIGN_H, x + VIGN_W, y + VIGN_H + TXT_H], fill=(255, 255, 255))
        d.text((x + 3, y + VIGN_H + 2), f"{num}  {l1}"[:44], fill=(160, 0, 0), font=f1)
        d.text((x + 3, y + VIGN_H + 19), l2[:50], fill=(40, 40, 40), font=f2)
    q = 80
    while True:
        fond.save(fichier, "JPEG", quality=q, optimize=True)
        if fichier.stat().st_size <= 280_000 or q <= 40:
            break
        q -= 5


def court(rel):
    p = Path(rel)
    nom = p.stem
    if len(nom) > 22:
        nom = nom[:10] + "~" + nom[-8:]
    return nom


def abrege(rel):
    r = str(Path(rel).parent).replace("\\", "/")
    r = (r.replace("sary vaovao/", "sv/").replace("Nouveau dossier/", "ND/")
          .replace("Apres traitement", "AT").replace("Publication", "Pub")
          .replace("sary vaovao ce 0904", "0904").replace("Pour site", "PS")
          .replace("Brique creuse", "BC").replace("Samedi", "Sam").replace("Jeudi", "Jeu")
          .replace("Mardi", "Mar"))
    return r


def site_hashes():
    s = []
    for p in sorted(SITE_IMG.glob("*.webp")):
        im = ouvrir_reduit(p)
        s.append({"nom": p.name, "chemin": str(p), "h8": dhash(im, 8), "h16": dhash(im, 16), "im": p})
    return s


def main():
    PLANCHES.mkdir(parents=True, exist_ok=True)
    photos = charger()
    groupes = grouper(photos)
    site = site_hashes()
    table = {}
    items = []
    for i, g in enumerate(groupes, 1):
        rep = g[0]
        num = f"{i:03d}"
        proche = min(site, key=lambda s: ham(s["h8"], rep["h8"]))
        table[num] = {"chemin": rep["chemin"], "rel": rep["rel"], "w": rep["w"], "h": rep["h"],
                      "octets": rep["octets"], "copies": [x["chemin"] for x in g[1:]],
                      "site_proche": proche["nom"], "site_dist8": ham(proche["h8"], rep["h8"])}
        l2 = f"{abrege(rep['rel'])} {rep['w']}x{rep['h']} x{len(g)}"
        items.append((num, rep["cache"], court(rep["rel"]), l2))
    (ICI / "table.json").write_text(json.dumps(table, ensure_ascii=False, indent=1), encoding="utf-8")
    par = COLS * LIGNES
    for k in range(0, len(items), par):
        lot = items[k:k + par]
        fic = PLANCHES / f"planche_{k // par + 1:02d}.jpg"
        planche(lot, fic, f"Planche {k // par + 1:02d} - photos {lot[0][0]} a {lot[-1][0]}")
    # planche du site
    CACHE.mkdir(parents=True, exist_ok=True)
    sitems = []
    for j, s in enumerate(site, 1):
        c = CACHE / ("site_" + s["nom"] + ".jpg")
        im = ouvrir_reduit(s["im"])
        im.thumbnail((600, 600))
        im.save(c, "JPEG", quality=88)
        sitems.append((f"S{j:02d}", str(c), s["nom"].replace(".webp", "")[:26], "site/image"))
    for k in range(0, len(sitems), par):
        lot = sitems[k:k + par]
        planche(lot, PLANCHES / f"site_{k // par + 1:02d}.jpg", f"Images du site {k // par + 1}")
    print(len(photos), "photos ->", len(groupes), "photos distinctes ;", (len(items) + par - 1) // par, "planches")


def zoom(nums, colonnes=2):
    """Vues 600 px (2 par ligne) de photos precises, pour lire un filigrane ou juger la nettete."""
    table = json.loads((ICI / "table.json").read_text(encoding="utf-8"))
    ims = []
    for n in nums:
        t = table[n.zfill(3)] if not n.startswith("c:") else None
        im = ouvrir_reduit(Path(t["chemin"]), 1400)
        im.thumbnail((600, 600), Image.LANCZOS)
        ims.append((n, im))
    lignes = (len(ims) + colonnes - 1) // colonnes
    W = colonnes * 610 + 10
    H = lignes * 470 + 10
    fond = Image.new("RGB", (W, H), (245, 245, 240))
    d = ImageDraw.Draw(fond)
    for k, (n, im) in enumerate(ims):
        x, y = 10 + (k % colonnes) * 610, 10 + (k // colonnes) * 470
        fond.paste(im, (x, y))
        d.text((x + 4, y + 4), n, fill=(255, 0, 0), font=police(22))
    fic = PLANCHES / f"zoom_{'_'.join(nums)}.jpg"
    q = 82
    while True:
        fond.save(fic, "JPEG", quality=q, optimize=True)
        if fic.stat().st_size <= 280_000 or q <= 40:
            break
        q -= 5
    print(fic, fic.stat().st_size)


def recadre(num, boite, taille=1000):
    """Extrait une zone (fractions g,h,d,b) d'une photo, en haute resolution, pour lire un detail."""
    table = json.loads((ICI / "table.json").read_text(encoding="utf-8"))
    t = table[num.zfill(3)]
    im = ouvrir_reduit(Path(t["chemin"]), 3000)
    W, H = im.size
    g, h, dr, b = boite
    z = im.crop((int(g * W), int(h * H), int(dr * W), int(b * H)))
    z.thumbnail((taille, taille), Image.LANCZOS)
    fic = PLANCHES / f"detail_{num}.jpg"
    z.save(fic, "JPEG", quality=80)
    print(fic, z.size, fic.stat().st_size)


# --- TABLE numero -> chemin complet (ecrite apres execution, 18/09/2026) ---
TABLE_PLANCHES = {
    "001": "C:\\Users\\ANDRIANIRINA\\Desktop\\ASA\\SERA ORDI KELY\\sera\\hourdis\\sary vaovao\\Apres traitement\\Brique creuse maina Betsaka profil.jpg",
    "002": "C:\\Users\\ANDRIANIRINA\\Desktop\\ASA\\SERA ORDI KELY\\sera\\hourdis\\sary vaovao\\Apres traitement\\Brique creuse mando am tany ivelany .jpg",
    "003": "C:\\Users\\ANDRIANIRINA\\Desktop\\ASA\\SERA ORDI KELY\\sera\\hourdis\\sary vaovao\\Apres traitement\\Brique creuse mando am tany.jpg",
    "004": "C:\\Users\\ANDRIANIRINA\\Desktop\\ASA\\SERA ORDI KELY\\sera\\hourdis\\sary vaovao\\Apres traitement\\Brique creuse mando sur etalage 2.jpg",
    "005": "C:\\Users\\ANDRIANIRINA\\Desktop\\ASA\\SERA ORDI KELY\\sera\\hourdis\\sary vaovao\\Apres traitement\\Brique creuse mando sur etalage.jpg",
    "006": "C:\\Users\\ANDRIANIRINA\\Desktop\\ASA\\SERA ORDI KELY\\sera\\hourdis\\sary vaovao\\Apres traitement\\Fandorana brique creuse.jpg",
    "007": "C:\\Users\\ANDRIANIRINA\\Desktop\\ASA\\SERA ORDI KELY\\sera\\hourdis\\sary vaovao\\Apres traitement\\Hourdis maina betsaka 2.jpg",
    "008": "C:\\Users\\ANDRIANIRINA\\Desktop\\ASA\\SERA ORDI KELY\\sera\\hourdis\\sary vaovao\\Apres traitement\\Hourdis maina betsaka.jpg",
    "009": "C:\\Users\\ANDRIANIRINA\\Desktop\\ASA\\SERA ORDI KELY\\sera\\hourdis\\sary vaovao\\Apres traitement\\Hourdis mando sur etalage.jpg",
    "010": "C:\\Users\\ANDRIANIRINA\\Desktop\\ASA\\SERA ORDI KELY\\sera\\hourdis\\sary vaovao\\Apres traitement\\IMG_20230807_120451.jpg",
    "011": "C:\\Users\\ANDRIANIRINA\\Desktop\\ASA\\SERA ORDI KELY\\sera\\hourdis\\sary vaovao\\Apres traitement\\IMG_20230807_123559.jpg",
    "012": "C:\\Users\\ANDRIANIRINA\\Desktop\\ASA\\SERA ORDI KELY\\sera\\hourdis\\sary vaovao\\Apres traitement\\IMG_20230807_123643.jpg",
    "013": "C:\\Users\\ANDRIANIRINA\\Desktop\\ASA\\SERA ORDI KELY\\sera\\hourdis\\sary vaovao\\Apres traitement\\IMG_20230807_123651.jpg",
    "014": "C:\\Users\\ANDRIANIRINA\\Desktop\\ASA\\SERA ORDI KELY\\sera\\hourdis\\sary vaovao\\Apres traitement\\IMG_20230807_123847.jpg",
    "015": "C:\\Users\\ANDRIANIRINA\\Desktop\\ASA\\SERA ORDI KELY\\sera\\hourdis\\sary vaovao\\Apres traitement\\IMG_20230807_123937.jpg",
    "016": "C:\\Users\\ANDRIANIRINA\\Desktop\\ASA\\SERA ORDI KELY\\sera\\hourdis\\sary vaovao\\Apres traitement\\IMG_20230807_124106.jpg",
    "017": "C:\\Users\\ANDRIANIRINA\\Desktop\\ASA\\SERA ORDI KELY\\sera\\hourdis\\sary vaovao\\Apres traitement\\IMG_20230807_124814.jpg",
    "018": "C:\\Users\\ANDRIANIRINA\\Desktop\\ASA\\SERA ORDI KELY\\sera\\hourdis\\sary vaovao\\Apres traitement\\IMG_20230807_125653.jpg",
    "019": "C:\\Users\\ANDRIANIRINA\\Desktop\\ASA\\SERA ORDI KELY\\sera\\hourdis\\sary vaovao\\Apres traitement\\IMG_20230807_125732.jpg",
    "020": "C:\\Users\\ANDRIANIRINA\\Desktop\\ASA\\SERA ORDI KELY\\sera\\hourdis\\sary vaovao\\Apres traitement\\IMG_20230807_125743.jpg",
    "021": "C:\\Users\\ANDRIANIRINA\\Desktop\\ASA\\SERA ORDI KELY\\sera\\hourdis\\sary vaovao\\Apres traitement\\IMG_20230807_125754.jpg",
    "022": "C:\\Users\\ANDRIANIRINA\\Desktop\\ASA\\SERA ORDI KELY\\sera\\hourdis\\sary vaovao\\Apres traitement\\IMG_20230807_125810.jpg",
    "023": "C:\\Users\\ANDRIANIRINA\\Desktop\\ASA\\SERA ORDI KELY\\sera\\hourdis\\sary vaovao\\Apres traitement\\IMG_20230807_125824.jpg",
    "024": "C:\\Users\\ANDRIANIRINA\\Desktop\\ASA\\SERA ORDI KELY\\sera\\hourdis\\sary vaovao\\Apres traitement\\IMG_20230807_125850.jpg",
    "025": "C:\\Users\\ANDRIANIRINA\\Desktop\\ASA\\SERA ORDI KELY\\sera\\hourdis\\sary vaovao\\Apres traitement\\IMG_20230807_125900.jpg",
    "026": "C:\\Users\\ANDRIANIRINA\\Desktop\\ASA\\SERA ORDI KELY\\sera\\hourdis\\sary vaovao\\Apres traitement\\Pour site\\Tuile exaille .jpg",
    "027": "C:\\Users\\ANDRIANIRINA\\Desktop\\ASA\\SERA ORDI KELY\\sera\\hourdis\\sary vaovao\\Apres traitement\\Pour site\\Tuile.jpg",
    "028": "C:\\Users\\ANDRIANIRINA\\Desktop\\ASA\\SERA ORDI KELY\\sera\\hourdis\\Pour site\\Nouveau dossier\\BC 15.png",
    "029": "C:\\Users\\ANDRIANIRINA\\Desktop\\ASA\\SERA ORDI KELY\\sera\\hourdis\\Pour site\\Nouveau dossier\\Hourdis 15 2.png",
    "030": "C:\\Users\\ANDRIANIRINA\\Desktop\\ASA\\SERA ORDI KELY\\sera\\hourdis\\Pour site\\Nouveau dossier\\Hourdis 15.png",
    "031": "C:\\Users\\ANDRIANIRINA\\Desktop\\ASA\\SERA ORDI KELY\\sera\\hourdis\\sary vaovao\\IMG_20230807_120335.jpg",
    "032": "C:\\Users\\ANDRIANIRINA\\Desktop\\ASA\\SERA ORDI KELY\\sera\\hourdis\\sary vaovao\\IMG_20230807_123603.jpg",
    "033": "C:\\Users\\ANDRIANIRINA\\Desktop\\ASA\\SERA ORDI KELY\\sera\\hourdis\\sary vaovao\\IMG_20230807_124814.jpg",
    "034": "C:\\Users\\ANDRIANIRINA\\Desktop\\ASA\\SERA ORDI KELY\\sera\\hourdis\\sary vaovao\\sary vaovao ce 0904\\IMG_20260305_121649.jpg",
    "035": "C:\\Users\\ANDRIANIRINA\\Desktop\\ASA\\SERA ORDI KELY\\sera\\hourdis\\sary vaovao\\sary vaovao ce 0904\\IMG_20260305_121701.jpg",
    "036": "C:\\Users\\ANDRIANIRINA\\Desktop\\ASA\\SERA ORDI KELY\\sera\\hourdis\\sary vaovao\\sary vaovao ce 0904\\IMG_20260305_121714.jpg",
    "037": "C:\\Users\\ANDRIANIRINA\\Desktop\\ASA\\SERA ORDI KELY\\sera\\hourdis\\sary vaovao\\sary vaovao ce 0904\\IMG_20260305_121723.jpg",
    "038": "C:\\Users\\ANDRIANIRINA\\Desktop\\ASA\\SERA ORDI KELY\\sera\\hourdis\\sary vaovao\\sary vaovao ce 0904\\IMG_20260305_121743.jpg",
    "039": "C:\\Users\\ANDRIANIRINA\\Desktop\\ASA\\SERA ORDI KELY\\sera\\hourdis\\sary vaovao\\sary vaovao ce 0904\\IMG_20260305_121749.jpg",
    "040": "C:\\Users\\ANDRIANIRINA\\Desktop\\ASA\\SERA ORDI KELY\\sera\\hourdis\\sary vaovao\\sary vaovao ce 0904\\IMG_20260305_121817.jpg",
    "041": "C:\\Users\\ANDRIANIRINA\\Desktop\\ASA\\SERA ORDI KELY\\sera\\hourdis\\sary vaovao\\sary vaovao ce 0904\\IMG_20260305_121830.jpg",
    "042": "C:\\Users\\ANDRIANIRINA\\Desktop\\ASA\\SERA ORDI KELY\\sera\\hourdis\\sary vaovao\\sary vaovao ce 0904\\IMG_20260305_121907.jpg",
    "043": "C:\\Users\\ANDRIANIRINA\\Desktop\\ASA\\SERA ORDI KELY\\sera\\hourdis\\sary vaovao\\sary vaovao ce 0904\\IMG_20260305_121942.jpg",
    "044": "C:\\Users\\ANDRIANIRINA\\Desktop\\ASA\\SERA ORDI KELY\\sera\\hourdis\\sary vaovao\\sary vaovao ce 0904\\IMG_20260305_121955.jpg",
    "045": "C:\\Users\\ANDRIANIRINA\\Desktop\\ASA\\SERA ORDI KELY\\sera\\hourdis\\sary vaovao\\sary vaovao ce 0904\\IMG_20260305_122015.jpg",
    "046": "C:\\Users\\ANDRIANIRINA\\Desktop\\ASA\\SERA ORDI KELY\\sera\\hourdis\\Nouveau dossier\\1-Lundi\\272687838_316063163787066_1797550773836676255_n.jpg",
    "047": "C:\\Users\\ANDRIANIRINA\\Desktop\\ASA\\SERA ORDI KELY\\sera\\hourdis\\Nouveau dossier\\1-Lundi\\4.jpg",
    "048": "C:\\Users\\ANDRIANIRINA\\Desktop\\ASA\\SERA ORDI KELY\\sera\\hourdis\\Nouveau dossier\\3-Mercredi\\3.jpg",
    "049": "C:\\Users\\ANDRIANIRINA\\Desktop\\ASA\\SERA ORDI KELY\\sera\\hourdis\\Nouveau dossier\\3-Mercredi\\6.jpg",
    "050": "C:\\Users\\ANDRIANIRINA\\Desktop\\ASA\\SERA ORDI KELY\\sera\\hourdis\\Nouveau dossier\\H2\\19\\1-Maison-brique-terre-cuite-BGV4G-Vue-generale-Sud-scaled.jpg",
    "051": "C:\\Users\\ANDRIANIRINA\\Desktop\\ASA\\SERA ORDI KELY\\sera\\hourdis\\Nouveau dossier\\H2\\19\\poutrelles-hourdis.jpg",
    "052": "C:\\Users\\ANDRIANIRINA\\Desktop\\ASA\\SERA ORDI KELY\\sera\\hourdis\\Nouveau dossier\\H2\\19\\unnamed.jpg",
    "053": "C:\\Users\\ANDRIANIRINA\\Desktop\\ASA\\SERA ORDI KELY\\sera\\hourdis\\Nouveau dossier\\H2\\8\\41237-pourquoi-les-produits-en-terre-cuite-permettent-de-reduire-les-ponts-thermiques.jpg",
    "054": "C:\\Users\\ANDRIANIRINA\\Desktop\\ASA\\SERA ORDI KELY\\sera\\hourdis\\1.jpg",
    "055": "C:\\Users\\ANDRIANIRINA\\Desktop\\ASA\\SERA ORDI KELY\\sera\\hourdis\\292507777_378484357602744_4411009844905828115_n.jpg",
    "056": "C:\\Users\\ANDRIANIRINA\\Desktop\\ASA\\SERA ORDI KELY\\sera\\hourdis\\Facture vrai.jpg",
    "057": "C:\\Users\\ANDRIANIRINA\\Desktop\\ASA\\SERA ORDI KELY\\sera\\hourdis\\armaturehourdis.jpg",
    "058": "C:\\Users\\ANDRIANIRINA\\Desktop\\ASA\\SERA ORDI KELY\\sera\\hourdis\\logo.jpg",
}
# --- fin TABLE ---


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "zoom":
        zoom(sys.argv[2:])
    elif len(sys.argv) > 1 and sys.argv[1] == "detail":
        recadre(sys.argv[2], tuple(float(x) for x in sys.argv[3:7]))
    else:
        main()
