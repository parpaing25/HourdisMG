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
PRIX = {pr["prix"] for c in PRODUITS["categories"] for pr in c["produits"]} | {1500}
RATIOS = {9, 12, 15, 75}
INTERROGATIFS = r"\b(firy|inona|ahoana|aiza|iza|rahoviana|nahoana|ohatrinona|sa|ve)\b|\?\s*$"


def main() -> int:
    erreurs, avis = [], []
    compte = {"montants": 0, "exemples": 0, "questions": 0, "calculs": 0}
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
    for a in avis:
        print("⚠", a)
    for e in erreurs:
        print("❌", e)
    print(f"\ncontrôlés : {compte['montants']} montants en Ar, {compte['exemples']} exemples m² → pièces, "
          f"{compte['calculs']} calculs refaits, {compte['questions']} questions")
    print(f"{'VERDICT ok' if not erreurs else 'VERDICT REFUSÉ'} — {len(erreurs)} erreur(s), {len(avis)} avertissement(s)")
    return 0 if not erreurs else 1


if __name__ == "__main__":
    sys.exit(main())
