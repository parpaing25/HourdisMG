"""Vérification quotidienne de hourdis.fonenako.mg — dit si le site est VRAIMENT en état.

    python outils/verifier_en_ligne.py                 # contrôle + alerte Telegram si un point tombe
    python outils/verifier_en_ligne.py --toujours      # envoie aussi le compte rendu quand tout va bien
    python outils/verifier_en_ligne.py --sans-telegram # CI : sortie console et code de retour seulement

Points contrôlés (chacun a déjà été vu cassé sur un site d'Andry) :
  - la page d'accueil répond 200, en HTML, avec le titre attendu et un bundle haché assets/index-*.js ;
  - ce bundle et la feuille de style sont servis avec le bon type MIME (o2switch rend 200 text/html
    pour un fichier ABSENT : le code HTTP seul ne prouve rien) ;
  - /faq, /robots.txt, /sitemap.xml, /llms.txt répondent 200 ; une page inconnue rend 404 ;
  - contact.php refuse le GET (303/405) au lieu de répondre « Formulaire invalide » en 200 ;
  - /image/ et /src/ ne listent plus le contenu du serveur ;
  - en-têtes de sécurité présents (HSTS, CSP, nosniff) ;
  - certificat TLS valide encore 14 jours ;
  - temps jusqu'au premier octet < 1,5 s (moyenne de 3 mesures).
Alerte : Telegram via @Hourdis_bot (jeton et destinataire lus dans ~/.hermes/profiles/hourdis/.env).
Planifier sur le PC : Planificateur de tâches → tous les jours 07:30 → outils/verifier_en_ligne.cmd
"""
from __future__ import annotations

import json
import os
import re
import socket
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HOTE = "hourdis.fonenako.mg"
BASE = f"https://{HOTE}"
UA = "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36"
ENV_HERMES = Path.home() / ".hermes" / "profiles" / "hourdis" / ".env"
problemes: list[str] = []
constats: list[str] = []


def ok(msg: str) -> None:
    constats.append("✓ " + msg)


def ko(msg: str) -> None:
    problemes.append(msg)
    constats.append("✗ " + msg)


def lire(url: str, methode: str = "GET") -> tuple[int, dict, bytes, float]:
    """Rend le code 0 quand le site est INJOIGNABLE (DNS, connexion refusée, TLS, délai dépassé).
    Sans ce filet, l'exception traversait le script et le chien de garde mourait sans envoyer
    d'alerte, exactement dans le seul cas pour lequel il existe. (Revue du 06/09/2026.)"""
    req = urllib.request.Request(url, method=methode, headers={"User-Agent": UA, "Cache-Control": "no-cache"})
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            corps = r.read()
            return r.status, dict(r.headers), corps, time.perf_counter() - t0
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read(), time.perf_counter() - t0
    except Exception as e:
        return 0, {}, f"{type(e).__name__}: {e}".encode(), time.perf_counter() - t0


class SansRedirection(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def statut_sans_suivre(url: str) -> int:
    op = urllib.request.build_opener(SansRedirection)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        return op.open(req, timeout=30).status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return 0


def controler() -> None:
    # 1. accueil
    code, ent, corps, dt = lire(BASE + "/?v=" + str(int(time.time())))
    page = corps.decode("utf-8", "replace")
    if code == 200 and "text/html" in ent.get("Content-Type", "") and "Hourdis Madagascar" in page:
        ok(f"accueil 200 HTML en {dt:.2f} s")
    else:
        ko(f"accueil : code {code}, type {ent.get('Content-Type')}, titre {'présent' if 'Hourdis Madagascar' in page else 'ABSENT'}")
        return
    if "tiger" in page and "429" in page:
        ko("o2switch sert sa page de blocage (tigre) : l'agent utilisateur est jugé robot")
    # 2. bundle + css : présents, servis avec le bon type, ET identiques au build local
    m_js = re.search(r'src="(/assets/index-[A-Za-z0-9_-]+\.js)"', page)
    m_css = re.search(r'href="(/assets/index-[A-Za-z0-9_-]+\.css)"', page)
    for m, attendu in ((m_js, "javascript"), (m_css, "text/css")):
        if not m:
            ko(f"la page ne référence aucun {attendu} haché dans assets/ (ancienne version en ligne ?)")
            continue
        c, e, _b, _t = lire(BASE + m.group(1))
        if c == 200 and attendu in e.get("Content-Type", ""):
            ok(f"{m.group(1)} servi en {e.get('Content-Type')}")
        else:
            ko(f"{m.group(1)} : code {c}, type {e.get('Content-Type')} (fichier absent ?)")
    # Un bundle haché servi correctement ne prouve PAS que c'est le BON : sans cette comparaison,
    # une version d'il y a six mois passait le contrôle au vert. (Revue du 06/09/2026.)
    local = Path(__file__).resolve().parent.parent / "dist" / "index.html"
    if local.exists():
        attendu_js = re.search(r"/assets/index-[A-Za-z0-9_-]+\.js", local.read_text(encoding="utf-8", errors="replace"))
        en_ligne = m_js.group(1) if m_js else None
        if attendu_js and en_ligne == attendu_js.group(0):
            ok(f"le bundle en ligne est celui du build local ({en_ligne})")
        elif attendu_js:
            ko(f"bundle en ligne {en_ligne} ≠ build local {attendu_js.group(0)} (déploiement non fait ou build local plus récent)")
    else:
        constats.append("· build local absent : impossible de comparer le bundle (lancer python build.py)")
    # 3. pages et fichiers
    for chemin, attendu in (("/faq", 200), ("/mentions-legales", 200), ("/confidentialite", 200), ("/robots.txt", 200), ("/sitemap.xml", 200), ("/llms.txt", 200), ("/page-inexistante-" + str(int(time.time())), 404)):
        c, _e, _b, _t = lire(BASE + chemin)
        (ok if c == attendu else ko)(f"{chemin} → {c}" + ("" if c == attendu else f" (attendu {attendu})"))
    # 4. formulaire vivant, pas de listing, pas de sources
    c = statut_sans_suivre(BASE + "/contact.php")
    (ok if c in (303, 405) else ko)(f"contact.php en GET → {c}" + ("" if c in (303, 405) else " (attendu 303 ou 405 : le script a-t-il été remplacé ?)"))
    for chemin in ("/image/", "/src/", "/package.json", "/src/App.tsx", "/.bolt/prompt"):
        c, _e, b, _t = lire(BASE + chemin)
        listing = b"Index of" in b
        (ko if (listing or c == 200) else ok)(f"{chemin} → {c}{' LISTING' if listing else ''}")
    # 5. en-têtes
    for nom in ("Strict-Transport-Security", "Content-Security-Policy", "X-Content-Type-Options"):
        (ok if nom in ent else ko)(f"en-tête {nom} {'présent' if nom in ent else 'ABSENT'}")
    # 6. certificat
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((HOTE, 443), timeout=15) as s, ctx.wrap_socket(s, server_hostname=HOTE) as ss:
            cert = ss.getpeercert()
        fin = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
        jours = (fin - datetime.now(timezone.utc)).days
        (ok if jours >= 14 else ko)(f"certificat valide encore {jours} jours")
    except Exception as e:
        ko(f"certificat : {type(e).__name__} {e}")
    # 7. TTFB
    mesures = []
    for _ in range(3):
        req = urllib.request.Request(BASE + "/?t=" + str(time.time()), headers={"User-Agent": UA})
        t0 = time.perf_counter()
        with urllib.request.urlopen(req, timeout=30) as r:
            r.read(1)
        mesures.append(time.perf_counter() - t0)
    ttfb = sum(mesures) / len(mesures)
    (ok if ttfb < 1.5 else ko)(f"premier octet {ttfb * 1000:.0f} ms (moyenne de 3)")


def telegram(texte: str) -> None:
    if not ENV_HERMES.exists():
        print("(pas de .env Hermes hourdis : alerte Telegram impossible)")
        return
    env = dict(re.findall(r"^([A-Z_]+)=(.*)$", ENV_HERMES.read_text(encoding="utf-8"), re.M))
    jeton = env.get("TELEGRAM_BOT_TOKEN", "").strip()
    dest = env.get("TELEGRAM_ALLOWED_USERS", "").split(",")[0].strip()
    if not jeton or not dest:
        print("(jeton ou destinataire Telegram vide)")
        return
    data = urllib.parse.urlencode({"chat_id": dest, "text": texte}).encode()
    try:
        urllib.request.urlopen(f"https://api.telegram.org/bot{jeton}/sendMessage", data, timeout=15).read()
        print("alerte Telegram envoyée")
    except Exception as e:
        print("Telegram KO :", e)


def main() -> None:
    try:
        controler()
    except Exception as e:   # une panne du contrôle ne doit jamais remplacer l'alerte par une trace
        ko(f"contrôle interrompu : {type(e).__name__} {e}")
    print("\n".join(constats))
    etat = "PROBLÈME" if problemes else "OK"
    print(f"\n{etat} : {len(problemes)} point(s) en défaut sur {len(constats)}")
    if "--sans-telegram" not in sys.argv and (problemes or "--toujours" in sys.argv):
        titre = f"{'🔴' if problemes else '🟢'} hourdis.fonenako.mg — {etat}\n"
        telegram(titre + "\n".join(("✗ " + p) for p in problemes) if problemes else titre + "\n".join(constats[:12]))
    sys.exit(1 if problemes else 0)


if __name__ == "__main__":
    main()
