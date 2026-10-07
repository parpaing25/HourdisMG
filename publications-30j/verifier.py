# -*- coding: utf-8 -*-
"""verifier.py — refuse une série qui ment, se répète ou contredit le site.

    python publications-30j/verifier.py

Contrôles, tous bloquants sauf mention :
  - 30 publications, une par jour, du 19/09 au 18/10, dossiers et affiches présents ;
  - chaque montant « N Ar » est un prix de produits.json ou le tarif de livraison ;
  - chaque exemple « X m² → Y pièces » respecte un des ratios du catalogue (9, 12, 15, 75) ;
  - aucun mot interdit : les hourdis sont SUR COMMANDE (règle d'Andry du 06/09/2026) ;
  - le lien du site porte utm_content=jNN, le bon numéro ; 5 hashtags exactement ;
  - deux publications ne commencent jamais pareil (leçon du 18/09 : un outil a visé
    le mauvais onglet à cause de deux débuts identiques) ;
  - une photo ne sert qu'une fois ;
  - avertissement : question fermée en malgache sans la particule « ve ».
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
from fabriquer import (PRODUITS, SERIE, PREFIXE, _MODULE, dossier, texte_complet,  # noqa: E402
                       affectation)

DEBUT = getattr(_MODULE, "DEBUT", "2026-09-19")
NB = r"\d{1,3}(?:[  ]\d{3})*(?:,\d+)?"
CALCUL = re.compile(rf"({NB})\s*(?:m²|m|Ar)?\s*×\s*({NB})\s*(?:m²|m|Ar)?\s*=\s*({NB})")


def nombre(s: str) -> float:
    return float(re.sub(r"[  ]", "", s).replace(",", "."))

INTERDITS = [r"\bstock disponible\b", r"\bmisy hatrany\b", r"\ben stock\b", r"\bdispo\b",
             r"\bdisponible\b", r"whatsapp", r"@gmail", r"\bpromo\b", r"\bgaranti"]
# une série peut DURCIR la liste (jamais l'alléger) : INTERDITS_EN_PLUS dans son module
INTERDITS += list(getattr(_MODULE, "INTERDITS_EN_PLUS", []))
TELEPHONES = {"032 47 041 43", "033 71 063 34"}
TEL = re.compile(r"\b0\d{2}[  ]?\d{2}[  ]?\d{3}[  ]?\d{2}\b")
# le délai du catalogue, en jours : ≈ 30 de production + 3 à 7 de livraison (produits.json)
DELAI = (33, 37)
PRIX = {pr["prix"] for c in PRODUITS["categories"] for pr in c["produits"]} | {1500}
RATIOS = {9, 12, 15, 75}
INTERROGATIFS = r"\b(firy|inona|ahoana|aiza|iza|rahoviana|nahoana|ohatrinona|sa|ve)\b|\?\s*$"


def main() -> int:
    erreurs, avis = [], []
    compte = {"montants": 0, "exemples": 0, "questions": 0, "calculs": 0, "dates": 0}
    if len(SERIE) != 30:
        erreurs.append(f"{len(SERIE)} publications au lieu de 30")
    debut = date.fromisoformat(DEBUT)
    for i, p in enumerate(SERIE):
        if p["date"] != (debut + timedelta(days=i)).isoformat():
            erreurs.append(f"{p['slug']} : date {p['date']} hors de la suite quotidienne")
    debuts = {}
    for i, p in enumerate(SERIE, 1):
        t = texte_complet(p)
        nom = f"{i:02d} {p['slug']}"
        d = dossier(p)
        for f in ("brouillon.txt", "affiche-fil.png", "fiche.json"):
            if not (d / f).exists():
                erreurs.append(f"{nom} : {f} absent")
        if (d / "brouillon.txt").exists() and (d / "brouillon.txt").read_text(encoding="utf-8") != t:
            erreurs.append(f"{nom} : brouillon.txt différent du texte de serie.py (refabriquer)")
        # chaque calcul « A × B = C » (m, m², Ar) est refait ; un total juste devient un montant
        # admis pour CETTE publication (un budget n'est pas un prix du catalogue)
        admis = set(PRIX)
        for m in CALCUL.finditer(t):
            compte["calculs"] += 1
            a_, b_, c_ = (nombre(m.group(k)) for k in (1, 2, 3))
            if abs(a_ * b_ - c_) > 0.51:
                erreurs.append(f"{nom} : calcul faux {m.group(0)!r} (= {a_ * b_:g})")
            elif c_ == int(c_):
                admis.add(int(c_))
        for m in re.finditer(r"(\d{1,3}(?:[  ]\d{3})*)\s*Ar\b", t):
            v = int(re.sub(r"\D", "", m.group(1)))
            compte["montants"] += 1
            if v not in admis:
                erreurs.append(f"{nom} : montant {m.group(0)!r} absent du catalogue")
        for m in re.finditer(r"(\d+(?:,\d+)?)\s*m²\s*(?:→|:)\s*(\d[\d  ]*)\s*(?:pièces|hourdis|briques|tuiles)", t):
            s = float(m.group(1).replace(",", ".")); n = int(re.sub(r"\D", "", m.group(2)))
            compte["exemples"] += 1
            if not any(abs(n - s * r) < 1 for r in RATIOS):
                erreurs.append(f"{nom} : exemple faux {m.group(0)!r}")
        # les montants écrits SUR l'affiche (prix, lignes) passent le même contrôle
        a = p["affiche"]
        sur_affiche = " ".join([a.get(k) or "" for k in ("prix", "titre", "sous_titre", "question", "note")]
                               + a.get("lignes", []))
        for m in re.finditer(r"(\d{1,3}(?:[  ]\d{3})*)\s*Ar\b", sur_affiche):
            compte["montants"] += 1
            if int(re.sub(r"\D", "", m.group(1))) not in admis:
                erreurs.append(f"{nom} : montant de l'affiche {m.group(0)!r} absent du catalogue")
        for m in re.finditer(r"(\d+(?:,\d+)?)\s*m²\s*→\s*(\d[\d  ]*)\s*pièces", sur_affiche):
            compte["exemples"] += 1
            if not any(abs(int(re.sub(r"\D", "", m.group(2))) - float(m.group(1).replace(",", ".")) * r) < 1 for r in RATIOS):
                erreurs.append(f"{nom} : exemple faux sur l'affiche {m.group(0)!r}")
        # les scènes des reels passent le même contrôle que les textes et les affiches
        from reels_scenes import SCENES
        a_des_reels = _MODULE.__name__ == "serie"      # seule la série de 18:00 part en reels
        sc = SCENES.get(p["slug"], {}) if a_des_reels else {}
        en_reel = " ".join(str(x) for s_ in sc.values() for v_ in s_.values() for x in (v_ if isinstance(v_, list) else [v_]))
        for m in re.finditer(r"(\d{1,3}(?:[  ]\d{3})*)\s*Ar\b", en_reel):
            compte["montants"] += 1
            if int(re.sub(r"\D", "", m.group(1))) not in admis:
                erreurs.append(f"{nom} : montant du reel {m.group(0)!r} absent du catalogue")
        for m in re.finditer(r"(\d+(?:,\d+)?)\s*m²\s*→\s*(\d[\d  ]*)\s*(?:pièces|tuiles|hourdis|briques)", en_reel):
            compte["exemples"] += 1
            if not any(abs(int(re.sub(r"\D", "", m.group(2))) - float(m.group(1).replace(",", ".")) * r) < 1 for r in RATIOS):
                erreurs.append(f"{nom} : exemple faux dans le reel {m.group(0)!r}")
        for motif in INTERDITS:
            if re.search(motif, en_reel, re.I):
                erreurs.append(f"{nom} : mot interdit dans le reel /{motif}/")
        if a_des_reels and p["affiche"]["gabarit"] != "tarifs" and not sc:
            erreurs.append(f"{nom} : aucune scène de reel écrite")
        for motif in INTERDITS:
            if re.search(motif, t, re.I):
                erreurs.append(f"{nom} : mot interdit /{motif}/")
        # seuls les deux numéros d'appel de la page peuvent figurer dans un texte
        for m in TEL.finditer(t):
            if re.sub(r"[  ]", " ", m.group(0)) not in TELEPHONES:
                erreurs.append(f"{nom} : numéro inconnu {m.group(0)!r}")
        # le calendrier annoncé est REFAIT : commande + 33 à + 37 jours (≈ 30 de production
        # + 3 à 7 de livraison), et les deux dates doivent être écrites dans le texte
        cal = p.get("calendrier")
        if cal:
            compte["dates"] += 1
            c0 = date.fromisoformat(cal["commande"])
            attendu = [c0 + timedelta(days=DELAI[0]), c0 + timedelta(days=DELAI[1])]
            dits = [date.fromisoformat(x) for x in cal["chantier"]]
            if dits != attendu:
                erreurs.append(f"{nom} : calendrier faux, {cal['commande']} + {DELAI[0]}–{DELAI[1]} j "
                               f"donne {attendu[0]}…{attendu[1]}, pas {dits[0]}…{dits[1]}")
            for d_ in [c0] + dits:
                if f"{d_:%d/%m}" not in t:
                    erreurs.append(f"{nom} : la date {d_:%d/%m} du calendrier n'est pas écrite dans le texte")
        if f"utm_content={PREFIXE}{i:02d}" not in t:
            erreurs.append(f"{nom} : lien sans utm_content={PREFIXE}{i:02d}")
        if len(re.findall(r"(?<!\w)#\w+", t.split("\n")[-1])) != 5:
            erreurs.append(f"{nom} : il faut 5 hashtags sur la dernière ligne")
        if len(t) > 2000:
            erreurs.append(f"{nom} : {len(t)} caractères, trop long")
        cle = t[:60]
        if cle in debuts:
            erreurs.append(f"{nom} : même début que {debuts[cle]}")
        debuts[cle] = nom
        for ligne in t.split("\n"):
            compte["questions"] += "?" in ligne and "http" not in ligne
            if "?" in ligne and "http" not in ligne and not re.search(INTERROGATIFS.replace(r"|\?\s*$", ""), ligne, re.I):
                avis.append(f"{nom} : question sans interrogatif ni « ve » : {ligne.strip()[:70]}")
    # une photo ne sert qu'une fois DANS une série (bandes, photos pleines et cases de collage)
    emplois = list(affectation().items()) + [(p["slug"], c) for p in SERIE for c in p["affiche"].get("photos", [])]
    vues = {}
    for slug, pid in emplois:
        if pid in vues:
            erreurs.append(f"photo {pid} employée deux fois : {vues[pid]} et {slug}")
        vues[pid] = slug
    # au moins trois mises en page différentes dans une série
    gabarits = {p["affiche"]["gabarit"] for p in SERIE}
    if len(gabarits) < 3:
        erreurs.append(f"une seule famille d'affiche : {sorted(gabarits)} (il en faut au moins 3)")
    # photos employées : connues du catalogue, assez larges, sans filigrane (sur demande du module)
    if getattr(_MODULE, "PHOTOS_EXIGEANTES", False):
        cat = {x["id"]: x for x in json.loads((ICI / "photos.json").read_text(encoding="utf-8"))}
        for pid in {x[1] for x in emplois}:
            info = cat.get(pid)
            if not info:
                erreurs.append(f"photo {pid} absente de photos.json (photo de provenance inconnue ?)")
                continue
            if int(info["dimensions"].split("x")[0]) < 1080:
                erreurs.append(f"photo {pid} : {info['dimensions']}, trop petite pour une affiche 1080")
            if any("filigrane" in d.lower() for d in info["defauts"]):
                erreurs.append(f"photo {pid} : filigrane ({info['defauts']})")
    # la série est-elle répartie comme la mesure ? (plus fort reste, refait ici)
    mesure = getattr(_MODULE, "MESURE", None)
    if mesure:
        total = sum(mesure.values())
        brut = {k: v * len(SERIE) / total for k, v in mesure.items()}
        attendu = {k: int(v) for k, v in brut.items()}
        reste = sorted(mesure, key=lambda k: (-(brut[k] - attendu[k]), -mesure[k]))
        for k in reste[:len(SERIE) - sum(attendu.values())]:
            attendu[k] += 1
        obtenu = {k: 0 for k in mesure}
        for p in SERIE:
            th = p.get("theme")
            if th not in obtenu:
                erreurs.append(f"{p['slug']} : thème {th!r} hors de la mesure")
            else:
                obtenu[th] += 1
        if obtenu != attendu:
            erreurs.append(f"répartition {obtenu} ≠ mesure au prorata {attendu}")
        else:
            print("répartition au prorata de la mesure :",
                  " · ".join(f"{k} {mesure[k]}→{attendu[k]}" for k in mesure))
    for a in avis:
        print("⚠", a)
    for e in erreurs:
        print("❌", e)
    print(f"\ncontrôlés : {compte['montants']} montants en Ar, {compte['exemples']} exemples m² → pièces, "
          f"{compte['calculs']} calculs refaits, {compte['dates']} calendriers refaits, "
          f"{compte['questions']} questions, {len(gabarits)} mises en page")
    print(f"{'VERDICT ok' if not erreurs else 'VERDICT REFUSÉ'} — {len(erreurs)} erreur(s), {len(avis)} avertissement(s)")
    return 0 if not erreurs else 1


if __name__ == "__main__":
    sys.exit(main())
