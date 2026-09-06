#!/usr/bin/env python
"""Lance le bot de veille Hourdis et ouvre son interface.

    python demarrer.py
    python demarrer.py --port 8761 --sans-navigateur
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

# Console Windows en cp1252 : un emoji dans un print tuerait le bot (règle du 04/09/2026).
for flux in (sys.stdout, sys.stderr):
    try:
        flux.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

from bot.config import PORT                       # noqa: E402
from bot.serveur import demarrer                  # noqa: E402

TAILLE_MAX_JOURNAL = 2 * 1024 * 1024


def journaliser_les_plantages() -> Path:
    """Sans fenêtre (gardien, tâche planifiée), stderr part dans data/bot-erreurs.log."""
    from bot.config import DOSSIER_DONNEES
    DOSSIER_DONNEES.mkdir(parents=True, exist_ok=True)
    chemin = DOSSIER_DONNEES / "bot-erreurs.log"
    try:
        if chemin.exists() and chemin.stat().st_size > TAILLE_MAX_JOURNAL:
            chemin.replace(chemin.with_suffix(".log.1"))
    except OSError:
        pass
    fichier = open(chemin, "a", encoding="utf-8", buffering=1)      # noqa: SIM115
    fichier.write(f"\n=== démarrage {datetime.now():%Y-%m-%d %H:%M:%S} (pid {os.getpid()}) ===\n")
    sys.stderr = fichier
    import faulthandler
    faulthandler.enable(file=fichier, all_threads=True)
    return chemin


def main() -> None:
    analyseur = argparse.ArgumentParser(description="Bot de veille Hourdis")
    analyseur.add_argument("--port", type=int, default=PORT)
    analyseur.add_argument("--sans-navigateur", action="store_true")
    options = analyseur.parse_args()
    print(f"\n  Bot de veille Hourdis — http://127.0.0.1:{options.port}")
    print("  Laissez cette fenetre ouverte tant que vous travaillez.\n")
    if options.sans_navigateur:
        journaliser_les_plantages()
    demarrer(port=options.port, ouvrir=not options.sans_navigateur)


if __name__ == "__main__":
    main()
