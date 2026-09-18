# -*- coding: utf-8 -*-
"""programmer_photos.py — programme les publications PHOTO d'une série sur la page Hourdis.

Demande d'Andry du 18/09/2026 : « fais des publications encore pour 30 jours, à chaque 14 h ».
La série de 14:00 est serie14.py ; les reels de 18:00 ont leur propre outil
(programmer_reels.py).

    set HOURDIS_SERIE=serie14
    python publications-30j/programmer_photos.py              # à blanc : ce qui partirait
    python publications-30j/programmer_photos.py --envoyer 1  # la première seulement (essai)
    python publications-30j/programmer_photos.py --envoyer    # toutes celles qui ne le sont pas encore
    python publications-30j/programmer_photos.py --relire     # compare la file de Facebook à la série

Chaque publication = l'affiche (affiche-fil.png) avec sa légende (brouillon.txt), en
published=false + scheduled_publish_time à l'heure de la série (heure de Tana). Rien n'est
public avant l'heure ; Andry peut la modifier ou la supprimer dans Business Suite.

Idempotent : programmation-photos<NOM>.json garde l'identifiant de chaque envoi réussi, et la
file de Facebook est relue avant tout envoi (même début de texte = déjà programmée). Arrêt au
premier refus. Le jeton (profil Hermes hourdis) n'est jamais affiché ni écrit ailleurs.
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
from fabriquer import SERIE, HEURE, NOM, dossier  # noqa: E402  (série choisie par HOURDIS_SERIE)

API = "https://graph.facebook.com/v21.0"
TANA = ZoneInfo("Indian/Antananarivo")
JOURNAL = ICI / f"programmation-photos{NOM}.json"


def jeton() -> tuple[str, str]:
    env = {}
    for l in (Path.home() / ".hermes/profiles/hourdis/.env").read_text(encoding="utf-8").splitlines():
        if "=" in l and not l.lstrip().startswith("#"):
            k, v = l.split("=", 1)
            env[k.strip()] = v.strip().strip("'\"")
    return env["FB_PAGE_ID"], env["FB_PAGE_TOKEN"]


def quand(p: dict) -> datetime:
    h, m = map(int, HEURE.split(":"))
    return datetime.fromisoformat(p["date"]).replace(hour=h, minute=m, tzinfo=TANA)


def file_facebook(pid: str, tok: str) -> list[dict]:
    res, url, params = [], f"{API}/{pid}/scheduled_posts", {
        "access_token": tok, "limit": 100, "fields": "id,message,scheduled_publish_time,full_picture"}
    for _ in range(5):
        r = requests.get(url, params=params, timeout=60).json()
        if "error" in r:
            raise SystemExit(f"lecture de la file refusée : {r['error'].get('message', '')[:200]}")
        res += r.get("data", [])
        url, params = r.get("paging", {}).get("next"), {}
        if not url:
            break
    return res


def lire_journal() -> dict:
    return json.loads(JOURNAL.read_text(encoding="utf-8")) if JOURNAL.exists() else {}


def main(argv: list[str]) -> int:
    pid, tok = jeton()
    file = file_facebook(pid, tok)
    if "--relire" in argv:
        return relire(file)
    deja = {(x.get("message") or "")[:80]: x for x in file}
    j = lire_journal()
    envoyer = "--envoyer" in argv
    limite = None
    if envoyer:
        i = argv.index("--envoyer")
        if i + 1 < len(argv) and argv[i + 1].isdigit():
            limite = int(argv[i + 1])
    maintenant = datetime.now(TANA)
    faits = 0
    for p in SERIE:
        d = dossier(p)
        texte = (d / "brouillon.txt").read_text(encoding="utf-8")
        t = quand(p)
        cle = f"{p['date']}-{p['slug']}"
        if cle in j or texte[:80] in deja:
            print(f"· {cle} déjà programmée")
            continue
        if (t - maintenant).total_seconds() < 20 * 60:
            print(f"⚠ {cle} : {t:%d/%m %H:%M} est trop proche ou passé, non programmée")
            continue
        if not envoyer:
            print(f"(à blanc) {cle} → {t:%a %d/%m/%Y %H:%M} Tana · {len(texte)} car. · "
                  f"affiche {(d / 'affiche-fil.png').stat().st_size // 1024} Ko")
            continue
        if limite is not None and faits >= limite:
            break
        with open(d / "affiche-fil.png", "rb") as f:
            r = requests.post(f"{API}/{pid}/photos", timeout=180,
                              data={"access_token": tok, "caption": texte, "published": "false",
                                    "scheduled_publish_time": str(int(t.timestamp()))},
                              files={"source": ("affiche.png", f, "image/png")})
        try:
            corps = r.json()
        except ValueError:
            corps = {"brut": r.text[:300]}
        if r.status_code != 200 or "id" not in corps:
            print(f"❌ {cle} : HTTP {r.status_code} {json.dumps(corps, ensure_ascii=False)[:400]}")
            return 2
        j[cle] = {"photo_id": corps.get("id"), "post_id": corps.get("post_id"), "quand": t.isoformat(),
                  "envoye_le": datetime.now(TANA).isoformat(timespec="seconds")}
        JOURNAL.write_text(json.dumps(j, ensure_ascii=False, indent=2), encoding="utf-8")
        faits += 1
        print(f"✅ {cle} programmée pour {t:%a %d/%m %H:%M} Tana · {corps.get('post_id') or corps.get('id')}", flush=True)
        time.sleep(2)
    if envoyer and faits:
        time.sleep(4)
        return relire(file_facebook(pid, tok))
    return 0


def relire(file: list[dict]) -> int:
    """La file de Facebook fait foi : texte EXACT, image présente, bonne heure."""
    par_debut = {(x.get("message") or "")[:80]: x for x in file}
    bons, vus = 0, 0
    for p in SERIE:
        texte = (dossier(p) / "brouillon.txt").read_text(encoding="utf-8")
        x = par_debut.get(texte[:80])
        if not x:
            continue
        vus += 1
        heure = x.get("scheduled_publish_time")
        vue = (datetime.fromtimestamp(int(heure), TANA) if str(heure).isdigit()
               else datetime.strptime(str(heure), "%Y-%m-%dT%H:%M:%S%z").astimezone(TANA))
        ok = vue == quand(p) and (x.get("message") or "").strip() == texte.strip() and bool(x.get("full_picture"))
        bons += ok
        print(f"   {'✅' if ok else '⚠️'} {p['date']} {p['slug']} → {vue:%d/%m %H:%M} Tana"
              f"{'' if (x.get('message') or '').strip() == texte.strip() else ' · TEXTE DIFFÉRENT'}"
              f"{'' if x.get('full_picture') else ' · SANS IMAGE'}")
    print(f"\n{bons}/{vus} publications de la série conformes dans la file de Facebook "
          f"({len(file)} éléments programmés au total sur la page).")
    return 0 if bons == vus else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
