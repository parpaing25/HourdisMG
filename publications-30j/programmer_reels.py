# -*- coding: utf-8 -*-
"""programmer_reels.py — programme les reels de la série sur la page Hourdis Madagascar.

Ordre d'Andry du 18/09/2026 : « crée des reels à publier à chaque 18 h et programme la
publication ».

    python publications-30j/programmer_reels.py              # à blanc : ce qui partirait
    python publications-30j/programmer_reels.py --envoyer 1  # le premier reel seulement (essai)
    python publications-30j/programmer_reels.py --envoyer    # tous ceux qui ne le sont pas encore
    python publications-30j/programmer_reels.py --relire     # état de chaque reel chez Facebook

API Reels de la page, en trois temps : upload_phase=start → envoi du fichier sur
rupload.facebook.com → upload_phase=finish avec video_state=SCHEDULED et
scheduled_publish_time (18:00 heure de Tana). La légende est brouillon.txt, le texte exact
de la publication. Rien n'est public avant l'heure : le reel attend dans les contenus
programmés de Business Suite, où Andry peut le modifier ou le supprimer.

Idempotent : programmation-reels.json garde l'identifiant de chaque reel accepté ; un reel
déjà présent n'est jamais renvoyé. Arrêt au premier refus : on ne martèle pas l'API.
Le jeton (profil Hermes hourdis) n'est jamais affiché ni écrit ailleurs.
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
# Série choisie par HOURDIS_SERIE : « serie » (reels muets de 18:00, défaut) ou
# « serie_voix » (reels expliqués de 10:00). Chacune a son propre journal.
from fabriquer import SERIE, HEURE, NOM, dossier  # noqa: E402

API = "https://graph.facebook.com/v21.0"
TANA = ZoneInfo("Indian/Antananarivo")
JOURNAL = ICI / f"programmation-reels{NOM}.json"


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


def lire_journal() -> dict:
    return json.loads(JOURNAL.read_text(encoding="utf-8")) if JOURNAL.exists() else {}


def corps(r: requests.Response) -> dict:
    try:
        return r.json()
    except ValueError:
        return {"brut": r.text[:300]}


def programmer(pid: str, tok: str, p: dict) -> dict:
    d = dossier(p)
    video = d / "reel.mp4"
    texte = (d / "brouillon.txt").read_text(encoding="utf-8")
    t = quand(p)
    r = requests.post(f"{API}/{pid}/video_reels", timeout=60,
                      data={"upload_phase": "start", "access_token": tok})
    j = corps(r)
    if r.status_code != 200 or "video_id" not in j:
        return {"ok": False, "etape": "start", "http": r.status_code, "reponse": j}
    vid = j["video_id"]
    taille = video.stat().st_size
    with open(video, "rb") as f:
        r = requests.post(j.get("upload_url") or f"https://rupload.facebook.com/video-upload/v21.0/{vid}",
                          timeout=600, data=f,
                          headers={"Authorization": f"OAuth {tok}", "offset": "0", "file_size": str(taille)})
    if r.status_code != 200 or not corps(r).get("success"):
        return {"ok": False, "etape": "envoi", "video_id": vid, "http": r.status_code, "reponse": corps(r)}
    r = requests.post(f"{API}/{pid}/video_reels", timeout=120,
                      data={"access_token": tok, "video_id": vid, "upload_phase": "finish",
                            "video_state": "SCHEDULED", "scheduled_publish_time": str(int(t.timestamp())),
                            "description": texte})
    j = corps(r)
    if r.status_code != 200 or not j.get("success"):
        return {"ok": False, "etape": "finish", "video_id": vid, "http": r.status_code, "reponse": j}
    return {"ok": True, "video_id": vid, "quand": t.isoformat(), "octets": taille}


def etat(tok: str, vid: str) -> dict:
    r = requests.get(f"{API}/{vid}", timeout=60,
                     params={"access_token": tok, "fields": "status,description,scheduled_publish_time,length"})
    return corps(r)


def main(argv: list[str]) -> int:
    pid, tok = jeton()
    j = lire_journal()
    if "--relire" in argv:
        return relire(tok, j)
    envoyer = "--envoyer" in argv
    limite = None
    if envoyer:
        i = argv.index("--envoyer")
        if i + 1 < len(argv) and argv[i + 1].isdigit():
            limite = int(argv[i + 1])
    maintenant = datetime.now(TANA)
    faits = 0
    for p in SERIE:
        cle = f"{p['date']}-{p['slug']}"
        video = dossier(p) / "reel.mp4"
        t = quand(p)
        if cle in j:
            print(f"· {cle} déjà programmé ({j[cle]['video_id']})")
            continue
        if not video.exists():
            print(f"⚠ {cle} : reel.mp4 absent, non programmé")
            continue
        if (t - maintenant).total_seconds() < 20 * 60:
            print(f"⚠ {cle} : {t:%d/%m %H:%M} est trop proche ou passé, non programmé")
            continue
        if not envoyer:
            print(f"(à blanc) {cle} → {t:%a %d/%m/%Y %H:%M} Tana · {video.stat().st_size // 1024} Ko")
            continue
        if limite is not None and faits >= limite:
            break
        r = programmer(pid, tok, p)
        if not r["ok"]:
            print(f"❌ {cle} : refus à l'étape {r['etape']} — HTTP {r.get('http')} "
                  f"{json.dumps(r.get('reponse'), ensure_ascii=False)[:500]}")
            if r.get("video_id"):
                print(f"   vidéo {r['video_id']} créée mais non programmée : à vérifier dans Business Suite")
            return 2
        j[cle] = {"video_id": r["video_id"], "quand": r["quand"],
                  "envoye_le": datetime.now(TANA).isoformat(timespec="seconds")}
        JOURNAL.write_text(json.dumps(j, ensure_ascii=False, indent=2), encoding="utf-8")
        faits += 1
        print(f"✅ {cle} programmé pour {t:%a %d/%m %H:%M} Tana · vidéo {r['video_id']}", flush=True)
        time.sleep(3)
    if envoyer and faits:
        time.sleep(5)
        return relire(tok, lire_journal())
    return 0


def relire(tok: str, j: dict) -> int:
    """Facebook fait foi : chaque reel du journal existe-t-il, avec le bon texte, à la bonne
    heure, et dans quel état de traitement ?"""
    bons = 0
    for p in SERIE:
        cle = f"{p['date']}-{p['slug']}"
        if cle not in j:
            continue
        e = etat(tok, j[cle]["video_id"])
        if "error" in e:
            print(f"   ❌ {cle} : {e['error'].get('message', '')[:160]}")
            continue
        texte = (dossier(p) / "brouillon.txt").read_text(encoding="utf-8")
        st = e.get("status") or {}
        # Facebook rend l'heure en texte ISO (« 2026-09-19T15:00:00+0000 »), parfois en nombre
        heure = e.get("scheduled_publish_time")
        try:
            vue = (datetime.fromtimestamp(int(heure), TANA) if str(heure).isdigit()
                   else datetime.strptime(str(heure), "%Y-%m-%dT%H:%M:%S%z").astimezone(TANA))
        except ValueError:
            vue = None
        heure_txt = vue.strftime("%d/%m %H:%M Tana") if vue else str(heure)
        ok_t = vue == quand(p)
        ok_m = (e.get("description") or "").strip() == texte.strip()
        pub = (st.get("publishing_phase") or {}).get("status")
        bons += ok_t and ok_m
        print(f"   {'✅' if ok_t and ok_m else '⚠️'} {cle} → {heure_txt} · vidéo {st.get('video_status')} · "
              f"traitement {(st.get('processing_phase') or {}).get('status')} · publication {pub}"
              f"{'' if ok_m else ' · TEXTE DIFFÉRENT'}{'' if ok_t else ' · HEURE À VÉRIFIER'}")
    print(f"\n{bons}/{len(j)} reels programmés conformes (texte exact, 18:00 Tana).")
    return 0 if bons == len(j) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
