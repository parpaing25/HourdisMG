"""Nettoie le doc root hourdis.fonenako.mg de tout ce que le build ne contient pas.

    python outils/nettoyage_serveur.py             # LISTE seulement (à blanc), ne touche à rien
    python outils/nettoyage_serveur.py --executer  # efface, après un déploiement VÉRIFIÉ

Pourquoi : le serveur porte encore les sources Vite/React (src/App.tsx, package.json, tsconfig…),
les originaux photo (8000×6000, 30 Mo) et l'ancien send_mail.php, tous listés publiquement par
Apache jusqu'au nouveau .htaccess. Le déploiement atomique n'efface que dans assets/ : ce script
fait le reste, une fois, et seulement sur ordre.

Jamais effacé : .well-known/ (renouvellement Let's Encrypt), cgi-bin/, .htaccess.
Les originaux photo sont d'abord TÉLÉCHARGÉS dans sources-photos/ (ignoré par git) : rien ne se perd.
"""
from __future__ import annotations

import ftplib
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RACINE = Path(__file__).resolve().parent.parent
DIST = RACINE / "dist"
SOURCES = RACINE / "sources-photos"
ROOT = "hourdis.fonenako.mg"
PROTEGES = {".well-known", "cgi-bin"}

CREDS = open(r"C:\Users\ANDRIANIRINA\.deploy-sites\ftp_deploy.py", encoding="utf-8").read()
cred = lambda k: re.search(k + r'\s*=\s*"([^"]+)"', CREDS).group(1)

if not DIST.exists():
    sys.exit("dist/ absent : lancer python build.py d'abord (le nettoyage se calcule par rapport au build).")
attendus = {p.relative_to(DIST).as_posix() for p in DIST.rglob("*") if p.is_file()}

ftp = ftplib.FTP(cred("HOST"), timeout=120)
ftp.login(cred("USER"), cred("PASS"))
ftp.set_pasv(True)

fichiers: list[tuple[str, int]] = []
dossiers: list[str] = []


def parcourir(path: str) -> None:
    for name, f in ftp.mlsd(path):
        if name in (".", ".."):
            continue
        rel = (path[len(ROOT) + 1:] + "/" + name).lstrip("/")
        if rel.split("/")[0] in PROTEGES:
            continue
        if f.get("type") == "dir":
            dossiers.append(rel)
            parcourir(path + "/" + name)
        elif f.get("type") == "file":
            fichiers.append((rel, int(f.get("size", 0))))


parcourir(ROOT)
orphelins = [(r, s) for r, s in fichiers if r not in attendus and r != ".htaccess"]
total = sum(s for _r, s in orphelins)
print(f"en ligne : {len(fichiers)} fichiers ; dans le build : {len(attendus)} ; à effacer : {len(orphelins)} ({total / 1048576:.1f} Mo)")
for r, s in sorted(orphelins):
    print(f"  {s:>9}  {r}")

if "--executer" not in sys.argv:
    print("\nÀ blanc : rien n'a été touché. Relancer avec --executer après un déploiement vérifié.")
    ftp.quit()
    sys.exit(0)

SOURCES.mkdir(exist_ok=True)
sauves = 0
for r, s in orphelins:
    if r.startswith("image/") and r.lower().endswith((".jpg", ".jpeg", ".png")):
        cible = SOURCES / Path(r).name
        if not cible.exists():
            with open(cible, "wb") as fh:
                ftp.retrbinary(f"RETR {ROOT}/{r}", fh.write)
            sauves += 1
print(f"{sauves} original(aux) photo sauvegardé(s) dans {SOURCES}")

effaces = 0
for r, _s in orphelins:
    try:
        ftp.delete(f"{ROOT}/{r}")
        effaces += 1
    except Exception as e:
        print(f"  non effacé [{type(e).__name__}] {r}")
for d in sorted(dossiers, key=len, reverse=True):
    try:
        ftp.rmd(f"{ROOT}/{d}")
        print(f"  dossier vide retiré : {d}/")
    except Exception:
        pass  # non vide : on le garde
ftp.quit()
print(f"{effaces} fichier(s) effacé(s). Relancer outils/verifier_en_ligne.py pour confirmer que le site répond.")
