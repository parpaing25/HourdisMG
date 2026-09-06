"""Rapport hebdomadaire du site Hourdis, calculé DEPUIS LE PC : même contenu que
outils-serveur/rapport_hebdo.php, pour le cas où le cron cPanel n'est pas posé.

    python outils/rapport_hebdo_local.py            # calcule et envoie sur Telegram
    python outils/rapport_hebdo_local.py --sans-telegram

Télécharge par FTP (lecture seule) /hourdis-data/stats.sqlite (ou stats.jsonl) et leads.jsonl,
compte les 7 derniers jours contre les 7 précédents, envoie le texte sur Telegram avec le jeton
de @Hourdis_bot (~/.hermes/profiles/hourdis/.env). Chaque chiffre vient des deux fichiers.
Planifier : Planificateur de tâches → samedi 07:00 → outils/rapport_hebdo_local.cmd
"""
from __future__ import annotations

import ftplib
import json
import re
import sqlite3
import sys
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
# 🔴 JAMAIS dans dist/ : ce dossier part en entier à la racine web au déploiement suivant, et
# leads.jsonl contient les noms, téléphones et messages des clients. (Revue du 06/09/2026.)
TMP = Path.home() / ".hourdis-rapport"
TMP.mkdir(parents=True, exist_ok=True)
ENV = Path.home() / ".hermes" / "profiles" / "hourdis" / ".env"
CREDS = open(r"C:\Users\ANDRIANIRINA\.deploy-sites\ftp_deploy.py", encoding="utf-8").read()
cred = lambda k: re.search(k + r'\s*=\s*"([^"]+)"', CREDS).group(1)

ftp = ftplib.FTP(cred("HOST"), timeout=120)
ftp.login(cred("USER"), cred("PASS"))
ftp.set_pasv(True)
for nom in ("stats.sqlite", "stats.jsonl", "leads.jsonl", "refuses.jsonl"):
    try:
        with open(TMP / nom, "wb") as fh:
            ftp.retrbinary(f"RETR /hourdis-data/{nom}", fh.write)
    except Exception:
        (TMP / nom).unlink(missing_ok=True)
ftp.quit()

now = datetime.now(timezone.utc)
depuis, avant = now - timedelta(days=7), now - timedelta(days=14)
# Tout est horodaté en UTC au format court « ...Z », par stat.php comme par contact.php : les
# comparaisons de chaînes ci-dessous n'ont de sens que si les deux côtés ont exactement ce format.
FMT = "%Y-%m-%dT%H:%M:%SZ"
evts: list[dict] = []
if (TMP / "stats.sqlite").exists():
    con = sqlite3.connect(TMP / "stats.sqlite")
    for ts, e, page, ref, famille, extra in con.execute("SELECT ts, e, page, ref, famille, extra FROM evenements WHERE ts >= ?", (avant.strftime(FMT),)):
        evts.append({"ts": ts, "e": e, "page": page, "ref": ref, "famille": famille, "extra": extra})
    con.close()
if (TMP / "stats.jsonl").exists():
    for l in (TMP / "stats.jsonl").read_text(encoding="utf-8").splitlines():
        try:
            d = json.loads(l)
            if d.get("ts", "") >= avant.strftime(FMT):
                evts.append(d)
        except Exception:
            pass


def compter(de: datetime, a: datetime) -> dict:
    c = Counter(); familles, refs, produits = Counter(), Counter(), Counter()
    for ev in evts:
        ts = ev.get("ts", "")
        if not (de.strftime("%Y-%m-%dT%H:%M:%S") <= ts < a.strftime("%Y-%m-%dT%H:%M:%S")):
            continue
        if ev.get("famille") == "robot":
            c["robots"] += 1; continue
        e = ev.get("e")
        if e == "page":
            c["pages"] += 1; familles[ev.get("famille") or "?"] += 1; refs[ev.get("ref") or "direct"] += 1
        elif e == "calc_ouvert":
            c["calc"] += 1; produits[ev.get("extra") or "?"] += 1
        else:
            c[e] += 1
    return {"c": c, "familles": familles, "refs": refs, "produits": produits}


sem, prec = compter(depuis, now), compter(avant, depuis)


def demandes(fichier: str) -> list[dict]:
    out = []
    if (TMP / fichier).exists():
        for l in (TMP / fichier).read_text(encoding="utf-8").splitlines():
            try:
                d = json.loads(l)
                if d.get("ts", "") >= depuis.strftime(FMT):
                    out.append(d)
            except Exception:
                pass
    return out


leads = demandes("leads.jsonl")
refuses = demandes("refuses.jsonl")


def delta(a: int, b: int) -> str:
    return (" (nouveau)" if a else "") if b == 0 else f" ({(a - b) * 100 // b:+d} %)"


c, p = sem["c"], prec["c"]
contacts = c["clic_tel"] + c["clic_whatsapp"] + c["clic_messenger"] + c["clic_email"] + c["devis_envoye"]
taux = round(contacts * 100 / c["pages"], 1) if c["pages"] else 0
tana = timezone(timedelta(hours=3))
lignes = [
    f"📊 Hourdis — semaine du {depuis.astimezone(tana):%d/%m} au {now.astimezone(tana):%d/%m/%Y}",
    "",
    f"Pages vues : {c['pages']}{delta(c['pages'], p['pages'])}" + (f" · robots exclus : {c['robots']}" if c["robots"] else ""),
    "Appareils : " + (", ".join(f"{k} {v}" for k, v in sem["familles"].most_common()) or "—"),
    "Origines : " + (", ".join(f"{k} {v}" for k, v in sem["refs"].most_common(5)) or "—"),
    "",
    f"Prises de contact : {contacts} (taux {taux} %)",
    f"  📞 appels {c['clic_tel']} · 💬 WhatsApp {c['clic_whatsapp']} · Messenger {c['clic_messenger']} · e-mail {c['clic_email']}",
    f"  🧾 devis envoyés {c['devis_envoye']}{delta(c['devis_envoye'], p['devis_envoye'])}" + (f" · ⚠ erreurs d'envoi {c['devis_erreur']}" if c["devis_erreur"] else ""),
    f"Calculateur : ouvert {c['calc']} fois, {c['calc_vers_devis']} ont poursuivi vers le devis",
    "  produits calculés : " + (", ".join(f"{k} ({v})" for k, v in sem["produits"].most_common(4)) or "—"),
]
if leads:
    lignes += ["", f"Demandes reçues ({len(leads)}) :"] + [
        f"  • {l['ts'][5:10]} {l['nom']} — {l['lieu']}" + (f" · {l['surface']} m²" if l.get("surface") else "") + ("" if l.get("mail", True) else " · mail KO") + ("" if l.get("telegram", True) else " · TG KO")
        for l in leads[-8:]]
if refuses:
    # une demande écartée comme robot ou par la limite peut être un vrai client : on la montre
    lignes += ["", f"⚠ Demandes ÉCARTÉES ({len(refuses)}) — vérifier qu'aucun vrai client n'est dedans :"] + [
        f"  • {l['ts'][5:10]} {l.get('nom') or '(sans nom)'} {l.get('tel') or ''} — {l.get('refuse')}"
        for l in refuses[-6:]]
if c["pages"] == 0:
    lignes += ["", "⚠ Aucune page vue enregistrée : stat.php est-il joignable ? (POST /stat.php → 204)"]
texte = "\n".join(lignes)
print(texte)

if "--sans-telegram" not in sys.argv and ENV.exists():
    env = dict(re.findall(r"^([A-Z_]+)=(.*)$", ENV.read_text(encoding="utf-8"), re.M))
    jeton, dest = env.get("TELEGRAM_BOT_TOKEN", "").strip(), env.get("TELEGRAM_ALLOWED_USERS", "").split(",")[0].strip()
    if jeton and dest:
        urllib.request.urlopen(f"https://api.telegram.org/bot{jeton}/sendMessage", urllib.parse.urlencode({"chat_id": dest, "text": texte}).encode(), timeout=20).read()
        print("\nenvoyé sur Telegram")
