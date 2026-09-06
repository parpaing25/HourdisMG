"""Prépare toutes les images du site depuis les originaux (photos d'Andry).

    python outils/preparer_images.py <dossier_originaux>

Le dossier des originaux contient les JPEG/PNG bruts (8000×6000 pour la plupart) : ils
NE SONT PAS dans git (30 Mo), ils restent sur le serveur (/image/*.jpg) et sur le téléphone
d'Andry. Le script écrit dans site/image/ des WebP légers aux noms sans espace ni accent,
et dans site/ les icônes (favicon, apple-touch, manifest) et l'image de partage 1200×630.

Règles : une photo produit = 720×540 (cartes 368 px, écrans ×2), une photo de galerie =
800×600, le bandeau en 3 largeurs (640 / 960 / 1920). Qualité WebP 78 : au-delà le poids
grimpe sans gain visible sur un téléphone.
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageOps

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RACINE = Path(__file__).resolve().parent.parent
SITE = RACINE / "site"
IMG = SITE / "image"
IMG.mkdir(parents=True, exist_ok=True)
Q = 78


def ouvrir(p: Path) -> Image.Image:
    im = Image.open(p)
    im = ImageOps.exif_transpose(im)  # photos de téléphone : orientation dans l'EXIF
    return im.convert("RGB")


def couvrir(im: Image.Image, w: int, h: int) -> Image.Image:
    """Recadre au centre pour remplir exactement w×h (comme object-fit: cover)."""
    return ImageOps.fit(im, (w, h), Image.LANCZOS, centering=(0.5, 0.5))


def webp(src: Path, dest: str, w: int, h: int, q: int = Q, boite: tuple[float, float, float, float] | None = None) -> None:
    """boite = (x0, y0, x1, y1) en fractions : zone gardée AVANT le recadrage ; sert à retirer le
    filigrane du téléphone (« REDMI K20 PRO », coin inférieur gauche des photos de la page Facebook)."""
    im = ouvrir(src)
    if boite:
        W, H = im.size
        im = im.crop((int(boite[0] * W), int(boite[1] * H), int(boite[2] * W), int(boite[3] * H)))
    im = couvrir(im, w, h)
    out = IMG / dest
    im.save(out, "WEBP", quality=q, method=6)
    print(f"  {dest:<34} {w}x{h}  {out.stat().st_size // 1024:>4} Ko  ← {src.name}")


def main(orig: Path) -> None:
    def o(nom: str) -> Path:
        p = orig / nom
        if not p.exists():
            sys.exit(f"original introuvable : {p}")
        return p

    print("— Bandeau (3 largeurs) —")
    hero = o("Hourdis_maina_betsaka_1920x1080.jpg")
    # le bandeau est couvert d'un dégradé à 70-80 % d'opacité : la qualité 66 suffit, et il pèse deux fois moins
    webp(hero, "hero-1920.webp", 1920, 1080, q=66)
    webp(hero, "hero-960.webp", 960, 540, q=66)
    webp(hero, "hero-640.webp", 640, 360, q=66)

    print("— Produits (720×540) —")
    # Photos reprises de la page Facebook HourdisMG (06/09/2026, décision d'Andry : « refais les photos »),
    # filigrane du téléphone retiré par la boîte de recadrage. Le même hourdis sert d'illustration aux
    # trois épaisseurs : les alt le disent, personne ne peut lire 12, 15 ou 20 cm sur une photo.
    SANS_FILIGRANE = (0.06, 0.02, 0.98, 0.85)
    webp(o("fb-hourdis-20.jpg"), "hourdis-20.webp", 720, 540, boite=SANS_FILIGRANE)
    webp(o("fb-hourdis-15.jpg"), "hourdis-15.webp", 720, 540, boite=SANS_FILIGRANE)
    webp(o("fb-hourdis-12.jpg"), "hourdis-12.webp", 720, 540, boite=SANS_FILIGRANE)
    # ces deux originaux portent aussi le filigrane « REDMI K20 PRO » en bas à gauche : même recadrage
    webp(o("272687838_316063163787066_1797550773836676255_n.jpg"), "brique-creuse-20.webp", 720, 540, boite=SANS_FILIGRANE)
    webp(o("BC 15.png"), "brique-creuse-15.webp", 720, 540, boite=SANS_FILIGRANE)
    webp(o("fb-briques-creuses-pile.jpg"), "brique-creuse-10.webp", 720, 540)
    webp(o("IMG_20230807_125850.jpg"), "tuile-mecanique.webp", 720, 540)
    webp(o("Tuile exaille .jpg"), "tuile-ecaille.webp", 720, 540)

    print("— Galerie « notre production » (800×600) —")
    webp(o("464868525_861513232633185_9206288329122918718_n.jpg"), "galerie-sechage-hourdis.webp", 800, 600)
    webp(o("Hourdis maina betsaka 2.jpg"), "galerie-stock-hourdis.webp", 800, 600)
    webp(o("Hourdis mando sur etalage.jpg"), "galerie-hourdis-etalage.webp", 800, 600)
    webp(o("Brique creuse mando sur etalage.jpg"), "galerie-briques-etalage.webp", 800, 600)
    webp(o("Brique creuse maina Betsaka profil.jpg"), "galerie-briques-seches.webp", 800, 600)
    webp(o("Fandorana brique creuse.jpg"), "galerie-fandorana-briques.webp", 800, 600)
    webp(o("Tuile.jpg"), "galerie-tuiles.webp", 800, 600)

    # ⚠ PAS de section « chantiers » : les photos de chantier des publications Facebook (murs vus d'avion,
    # maison à garage sectionnel, plancher vu de dessous) sont des images d'illustration EUROPÉENNES, pas des
    # chantiers du client. Les légender « nos réalisations » répéterait exactement la faute que l'audit a
    # relevée sur l'ancien site (photo Pexels titrée « Équipe HOURDIS MADAGASCAR »). Elles ne reviendront que
    # le jour où Andry fournira des photos de planchers qu'il a réellement livrés.

    print("— À propos (800×600) —")
    webp(o("Brique_creuse_hero_1920x1080.jpg"), "apropos-atelier.webp", 800, 600)

    print("— Logo, icônes, image de partage —")
    logo = ouvrir(o("logo.jpg"))
    logo.resize((160, 160), Image.LANCZOS).save(IMG / "logo.webp", "WEBP", quality=90, method=6)
    for taille in (32, 180, 192, 512):
        logo.resize((taille, taille), Image.LANCZOS).save(SITE / f"icon-{taille}.png", "PNG", optimize=True)
    logo.resize((48, 48), Image.LANCZOS).save(SITE / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
    og = couvrir(ouvrir(hero), 1200, 630)
    og.save(IMG / "og-1200x630.jpg", "JPEG", quality=82, optimize=True, progressive=True)
    print("  og-1200x630.jpg", (IMG / "og-1200x630.jpg").stat().st_size // 1024, "Ko ;",
          "icônes 32/180/192/512 + favicon.ico écrits dans site/")

    total = sum(p.stat().st_size for p in IMG.iterdir())
    print(f"\nsite/image : {len(list(IMG.iterdir()))} fichiers, {total // 1024} Ko au total")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(Path(sys.argv[1]))
