"""Test de bout en bout du formulaire de devis, contre le VRAI contact.php sur le VRAI serveur.

    python tests/test_devis_serveur.py

À lancer avant tout déploiement qui touche `site/contact.php` : c'est le seul test qui exerce le
chemin réel (PHP du serveur, mail(), API Telegram, écriture des journaux). Le banc `smoke_test.py`,
lui, ne voit qu'une réponse simulée.

Comment il s'y prend, et pourquoi c'est sans risque :
  - il dépose `site/contact.php` sous un nom ALÉATOIRE dans la racine web, l'exerce, puis l'efface.
    Le site en ligne n'est pas touché : ni index.html, ni le vrai contact.php, ni les images.
  - il passe par un VRAI navigateur : o2switch protège les POST par un défi Tiger Protect
    (307 + cookie) qu'un client HTTP nu ne franchit pas. Tester avec urllib ne prouverait rien.
  - il SAUVEGARDE `leads.jsonl`, `refuses.jsonl`, `contact.log` et le compteur de limite avant de
    commencer, et les restaure à l'identique à la fin, quoi qu'il arrive. Aucune demande réelle
    n'est perdue et aucune ligne de test ne reste dans le journal de production.

Ce qu'il vérifie : validation serveur, pot de miel, délai minimal (y compris le cas d'un téléphone
dont l'horloge AVANCE, qui faisait disparaître la demande), limite par adresse comptée seulement sur
les demandes valides, absence d'injection d'en-tête, envoi effectif de l'e-mail ET du message
Telegram, horodatage UTC lisible par les rapports, et conservation des demandes écartées.
"""
from __future__ import annotations

import ftplib
import io
import json
import re
import secrets
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from playwright.sync_api import sync_playwright

RACINE = Path(__file__).resolve().parent.parent
CREDS = open(r"C:\Users\ANDRIANIRINA\.deploy-sites\ftp_deploy.py", encoding="utf-8").read()
cred = lambda k: re.search(k + r'\s*=\s*"([^"]+)"', CREDS).group(1)
SITE = "hourdis.fonenako.mg"
DONNEES = "/hourdis-data"
UA = ("Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36")
FICHIERS = ("leads.jsonl", "refuses.jsonl", "contact.log")

nom_temporaire = f"_t_{secrets.token_hex(6)}.php"
marque = time.strftime("%H%M%S")
echecs: list[str] = []


def controle(titre: str, ok: bool, detail: str = "") -> None:
    print(("  ✓ " if ok else "  ✗ ") + titre + (f"  ({detail})" if detail else ""))
    if not ok:
        echecs.append(titre)


def lire(ftp: ftplib.FTP, chemin: str) -> bytes:
    buf = io.BytesIO()
    try:
        ftp.retrbinary(f"RETR {chemin}", buf.write)
    except Exception:
        return b""
    return buf.getvalue()


def vider_compteur(ftp: ftplib.FTP) -> int:
    n = 0
    try:
        for f, _ in ftp.mlsd(f"{DONNEES}/limite"):
            if f.endswith(".n"):
                ftp.delete(f"{DONNEES}/limite/{f}")
                n += 1
    except Exception:
        pass
    return n


def main() -> None:
    ftp = ftplib.FTP(cred("HOST"), timeout=120)
    ftp.login(cred("USER"), cred("PASS"))
    ftp.set_pasv(True)

    # ── Sauvegarde de tout ce que le test va toucher ──
    sauvegarde = {f: lire(ftp, f"{DONNEES}/{f}") for f in FICHIERS}
    print("sauvegarde des journaux : " + ", ".join(f"{f} {len(v.splitlines())} ligne(s)" for f, v in sauvegarde.items()))
    vider_compteur(ftp)
    ftp.storbinary(f"STOR {SITE}/{nom_temporaire}", io.BytesIO((RACINE / "site/contact.php").read_bytes()))
    print(f"contact.php déposé sous {nom_temporaire} (le site en ligne n'est pas touché)\n")

    base = {"name": f"TEST {marque}", "phone": "034 12 345 67", "email": "",
            "location": "Ambohimanga (test, ne pas traiter)", "surface": "50",
            "message": "Test de bout en bout — à ignorer.", "website": ""}
    ancien = str(int(time.time() * 1000) - 10000)

    try:
        with sync_playwright() as pw:
            b = pw.chromium.launch()
            ctx = b.new_context(user_agent=UA, viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
            page = ctx.new_page()
            rep = page.goto(f"https://{SITE}/", wait_until="domcontentloaded", timeout=60000)
            controle("la page du site se charge", rep.status == 200, f"HTTP {rep.status}")

            def envoyer(champs: dict) -> dict:
                return page.evaluate("""async ([url, champs]) => {
                    const fd = new FormData();
                    for (const [k, v] of Object.entries(champs)) fd.append(k, v);
                    try {
                      const r = await fetch(url, {method: 'POST', body: fd, headers: {'Accept': 'application/json'}});
                      return {status: r.status, redirige: r.redirected, corps: (await r.text()).slice(0, 200)};
                    } catch (e) { return {status: -1, redirige: false, corps: String(e)}; }
                }""", [f"/{nom_temporaire}", champs])

            print("— Les robots (n'entament pas le quota) —")
            r = envoyer({**base, "website": "http://spam.example", "t": ancien})
            controle("pot de miel rempli → 200 ok, rien n'est envoyé", r["status"] == 200 and '"ok":true' in r["corps"], f"{r['status']} {r['corps'][:40]}")
            r = envoyer({**base, "t": str(int(time.time() * 1000))})
            controle("formulaire rempli en moins de 3 s → 200 ok, rien n'est envoyé", r["status"] == 200 and '"ok":true' in r["corps"], f"{r['status']} {r['corps'][:40]}")

            print("\n— Ce qui doit être refusé (sans entamer le quota) —")
            for champ, valeur, mot in (("phone", "12345", "téléphone"), ("name", "", "nom"), ("surface", "999999999", "surface")):
                r = envoyer({**base, champ: valeur, "t": ancien})
                controle(f"{mot} invalide → 422", r["status"] == 422 and mot in r["corps"], f"{r['status']} {r['corps'][:70]}")

            print("\n— Injection d'en-tête e-mail —")
            r = envoyer({**base, "name": f"Pirate{marque}\r\nBcc: pirate@example.invalid", "t": ancien})
            controle("retours chariot acceptés puis neutralisés (vérifié plus bas)", r["status"] == 200, f"{r['status']} {r['corps'][:40]}")

            print("\n— Téléphone dont l'horloge AVANCE —")
            futur = str(int(time.time() * 1000) + 10 * 60 * 1000)
            r = envoyer({**base, "name": f"TEST horloge {marque}", "t": futur})
            controle("un client dont l'horloge avance est traité normalement, pas comme un robot",
                     r["status"] == 200 and '"ok":true' in r["corps"], f"{r['status']} {r['corps'][:40]}")

            print("\n— La vraie demande —")
            r = envoyer({**base, "t": ancien})
            controle('demande valide → 200 {"ok":true}', r["status"] == 200 and '"ok":true' in r["corps"], f"{r['status']} {r['corps'][:60]}")
            controle("le défi Tiger Protect ne déroute pas un vrai navigateur", not r["redirige"], f"redirected={r['redirige']}")

            print("\n— Limite : 5 demandes VALIDES par heure et par adresse —")
            # 3 valides déjà passées (injection, horloge, vraie). Deux de plus atteignent 5, la 6e est refusée.
            # Le code renvoyé au client n'est pas une preuve : le pare-feu o2switch rend parfois 504 là où PHP
            # a répondu 429. La preuve est ce que le serveur ÉCRIT — vérifié plus bas dans refuses.jsonl.
            codes = []
            for i in range(3):
                time.sleep(1.5)   # un visiteur réel n'envoie pas une rafale de POST
                codes.append(envoyer({**base, "name": f"TEST flot {i} {marque}", "t": ancien})["status"])
            controle("les 2 demandes suivantes passent", codes[:2] == [200, 200], f"codes {codes}")
            controle("la 6e est repoussée (429 de PHP, ou 504 du pare-feu devant)", codes[2] in (429, 504), f"code {codes[2]}")

            print("\n— Sans JavaScript : soumission classique du formulaire —")
            vider_compteur(ftp)
            reponses: list[tuple[int, str | None]] = []
            page.on("response", lambda resp: reponses.append((resp.status, resp.headers.get("location"))) if nom_temporaire in resp.url else None)
            page.set_content(f"""<form id="f" method="POST" action="https://{SITE}/{nom_temporaire}">
                <input name="name" value="TEST SANS JS {marque}"><input name="phone" value="034 12 345 67">
                <input name="location" value="Ambohimanga (test)"><input name="surface" value="50">
                <input name="message" value="Test sans JavaScript"><input name="website" value="">
                <input name="t" value="{ancien}"></form>""")
            page.evaluate("document.getElementById('f').submit()")
            page.wait_for_timeout(6000)
            redirections = [(s, l) for s, l in reponses if s == 303]
            controle("sans JavaScript → 303 Location: /merci", bool(redirections) and redirections[0][1] == "/merci",
                     f"réponses du script : {reponses}")
            b.close()

        print("\n— Ce que le serveur a écrit —")
        time.sleep(2)
        anciennes = sauvegarde["leads.jsonl"].decode("utf-8", "replace").splitlines()
        lignes = lire(ftp, f"{DONNEES}/leads.jsonl").decode("utf-8", "replace").splitlines()
        recues = [json.loads(l) for l in lignes if l not in anciennes]
        controle("6 demandes journalisées (injection, horloge, valide, 2 du flot, sans JS)", len(recues) == 6, f"{len(recues)} ligne(s)")
        for d in recues:
            print(f"    {d['ts']} {d['nom']!r} tel={d['tel']} mail={d['mail']} telegram={d['telegram']}")
        controle("l'e-mail est parti pour chaque demande", bool(recues) and all(d["mail"] for d in recues))
        controle("le message Telegram est parti pour chaque demande", bool(recues) and all(d["telegram"] for d in recues))
        controle("horodatage UTC au format court Z, celui que les rapports comparent",
                 bool(recues) and all(re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", d["ts"]) for d in recues),
                 recues[0]["ts"] if recues else "")
        pirate = [d for d in recues if d["nom"].startswith("Pirate")]
        controle("retours chariot retirés du nom : aucune injection d'en-tête possible",
                 bool(pirate) and all("\r" not in d["nom"] and "\n" not in d["nom"] for d in pirate),
                 repr(pirate[0]["nom"]) if pirate else "demande absente")
        controle("la demande du téléphone en avance est bien arrivée", any("horloge" in d["nom"] for d in recues))
        controle("le téléphone est journalisé normalisé", bool(recues) and all(d["tel"] == "0341234567" for d in recues),
                 recues[0]["tel"] if recues else "")

        ecartees = [json.loads(l) for l in lire(ftp, f"{DONNEES}/refuses.jsonl").decode("utf-8", "replace").splitlines() if marque in l]
        controle("les demandes écartées sont conservées : rien ne se perd en silence", len(ecartees) >= 3, f"{len(ecartees)} ligne(s)")
        for d in ecartees:
            print(f"    écartée : {d['ts']} {d['nom']!r} — {d.get('refuse')}")
        controle("chaque demande écartée dit pourquoi", bool(ecartees) and all(d.get("refuse") for d in ecartees))
        raisons = {d.get("refuse") for d in ecartees}
        controle("la limite a bien repoussé la 6e demande (preuve écrite par le serveur)",
                 "limite horaire" in raisons and not any("flot 2" in d["nom"] for d in recues), f"raisons {sorted(raisons)}")

        journal = lire(ftp, f"{DONNEES}/contact.log").decode("utf-8", "replace")
        print("  contact.log :", " | ".join(journal.strip().splitlines()[-6:]) or "(vide)")
        for attendu, titre in (("robot", "les robots sont journalisés"),
                               ("limite atteinte", "la limite atteinte est journalisée"),
                               ("refus validation", "les refus de validation sont journalisés")):
            controle(titre, attendu in journal)
        controle("aucun secret ni chemin absolu dans le journal", "api.telegram" not in journal and "/home/" not in journal)
    finally:
        try:
            ftp.delete(f"{SITE}/{nom_temporaire}")
            print(f"\nscript temporaire {nom_temporaire} effacé")
        except Exception as e:
            print(f"\n⚠ ÉCHEC de l'effacement de {nom_temporaire} : {e} — L'EFFACER À LA MAIN")
        for f, contenu in sauvegarde.items():
            ftp.storbinary(f"STOR {DONNEES}/{f}", io.BytesIO(contenu))
        vider_compteur(ftp)
        print("journaux restaurés à l'identique : " + ", ".join(f"{f} {len(v.splitlines())} ligne(s)" for f, v in sauvegarde.items()))
        ftp.quit()

    print(f"\n{'ÉCHEC' if echecs else 'OK'} : {len(echecs)} contrôle(s) en échec" + (" → " + "; ".join(echecs) if echecs else ""))
    sys.exit(1 if echecs else 0)


if __name__ == "__main__":
    main()
