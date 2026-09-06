"""Chaque banc tourne dans un dossier de données JETABLE.

🔴 Sans HOURDIS_BOT_DATA, `bot.base` s'initialise sur la VRAIE base au premier
import : c'est ainsi que les 32 sources d'Andry ont été effacées chez AKORA le
23/08/2026. La variable est posée AVANT tout import du paquet.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

_DOSSIER = tempfile.mkdtemp(prefix="hourdis-tests-")
os.environ["HOURDIS_BOT_DATA"] = _DOSSIER
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest  # noqa: E402

from bot import base, config  # noqa: E402


@pytest.fixture(autouse=True)
def _base_propre():
    """Une base vide à chaque test, dans le dossier jetable."""
    assert str(config.DOSSIER_DONNEES).startswith(_DOSSIER), "les tests ne touchent pas la vraie base"
    with base._verrou, base.connexion() as cx:
        for table in ("trouvailles", "sources", "candidats", "publications", "journal", "etat"):
            cx.execute(f"DELETE FROM {table}")
    import shutil
    shutil.rmtree(config.DOSSIER_DONNEES / "collecte", ignore_errors=True)
    yield


@pytest.fixture
def cfg():
    c = config.charger()
    c.update({"telecharger_images": False, "garder_les_ecartees": True, "score_min": 35,
              "llm_actif": False, "publication_active": False})
    return c
