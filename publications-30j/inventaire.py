# -*- coding: utf-8 -*-
"""Inventaire des photos hourdis : chemin, poids, dimensions, date EXIF, empreinte dHash.
Lecture seule sur les sources. Ecrit inventaire.json a cote de ce script."""
import sys, json, hashlib
from pathlib import Path
from PIL import Image, ExifTags

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RACINE = Path(r"C:/Users/ANDRIANIRINA/Desktop/ASA/SERA ORDI KELY/sera/hourdis")
SITE_IMG = Path(r"C:/Users/ANDRIANIRINA/Desktop/Site Hourdis/site/image")
SORTIE = Path(__file__).with_name("inventaire.json")
EXT = {".jpg", ".jpeg", ".png", ".webp", ".heic"}
IGNORE = {"Claude 2026", "Tsy ilaina", "Hourdis Facture"}


def dhash(im, n=8):
    g = im.convert("L").resize((n + 1, n), Image.LANCZOS)
    px = list(g.getdata())
    bits = 0
    for y in range(n):
        for x in range(n):
            bits = (bits << 1) | (px[y * (n + 1) + x] > px[y * (n + 1) + x + 1])
    return f"{bits:016x}"


def date_exif(im):
    try:
        ex = im.getexif()
        d = ex.get(36867) or ex.get(306)
        if not d:
            sub = ex.get_ifd(0x8769)
            d = sub.get(36867)
        return d
    except Exception:
        return None


def modele(im):
    try:
        ex = im.getexif()
        return ex.get(272)
    except Exception:
        return None


def ouvrir_petit(p):
    im = Image.open(p)
    if im.format == "JPEG":
        im.draft("RGB", (600, 600))
    return im


def fiche(p, base):
    try:
        im = Image.open(p)
        w, h = im.size
        d = date_exif(im)
        m = modele(im)
        im2 = ouvrir_petit(p)
        im2.load()
        from PIL import ImageOps
        try:
            im2 = ImageOps.exif_transpose(im2)
        except Exception:
            pass
        W, H = im2.size
        return {"chemin": str(p), "rel": str(p.relative_to(base)), "octets": p.stat().st_size,
                "w": w, "h": h, "w_aff": W, "h_aff": H, "exif_date": d, "appareil": m, "dhash": dhash(im2)}
    except Exception as e:
        return {"chemin": str(p), "rel": str(p.relative_to(base)), "erreur": repr(e)}


def main():
    photos = []
    for p in sorted(RACINE.rglob("*")):
        if not p.is_file() or p.suffix.lower() not in EXT:
            continue
        rel = p.relative_to(RACINE)
        if rel.parts[0] in IGNORE:
            continue
        photos.append(fiche(p, RACINE))
    site = [fiche(p, SITE_IMG) for p in sorted(SITE_IMG.glob("*.webp"))]
    SORTIE.write_text(json.dumps({"photos": photos, "site": site}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(len(photos), "photos,", len(site), "images du site")


if __name__ == "__main__":
    main()
