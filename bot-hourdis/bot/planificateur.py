"""Tournées et publications aux heures dites — un seul fil, discret.

Repris du planificateur d'AKORA, qui a appris deux choses en production :

  - un créneau reste DÛ jusqu'à l'arrivée du suivant : un bot qui revient
    après une panne rattrape la tournée manquée, jamais deux d'un coup ;
  - les tâches du jour tournent APRÈS la collecte, dans le même fil — pas
    pendant, sur les données de la veille.

Et la règle du 03/09/2026 : pas de Chromium automatique pendant une session
Claude. Ici la tournée part quand même pour sa partie WEB (elle ne pèse rien),
et c'est le collecteur qui suspend la partie Facebook — sauf si
`web_pendant_session_claude` est faux, où tout attend comme chez les frères.
"""
from __future__ import annotations

import threading
from datetime import date, datetime

from . import base, publication, session_claude, sources_decouverte
from .config import charger

CLE_DERNIER = "planificateur_dernier_creneau"
CLE_TACHES = "planificateur_dernieres_taches"
CLE_DECOUVERTE = "derniere_decouverte"
CLE_PUBLICATION = "planificateur_derniere_publication"
VERIFICATION = 30


def _heures(config: dict, cle: str = "heures_collecte") -> list[str]:
    valides = []
    for brut in config.get(cle) or []:
        try:
            datetime.strptime(str(brut).strip(), "%H:%M")
            valides.append(str(brut).strip())
        except ValueError:
            base.logguer(f"Heure illisible dans {cle}, ignorée : {brut!r}", "avert")
    return sorted(valides)


def creneau_du(heures: list[str], maintenant: datetime) -> str:
    """Le créneau DÛ à cet instant : le dernier dont l'heure est passée aujourd'hui."""
    du = ""
    for heure in heures:
        moment = datetime.combine(maintenant.date(), datetime.strptime(heure, "%H:%M").time())
        if moment <= maintenant:
            du = heure
    return du


def prochain_passage(heures: list[str], actif: bool) -> str:
    if not heures or not actif:
        return ""
    maintenant = datetime.now()
    for heure in heures:
        if datetime.combine(maintenant.date(), datetime.strptime(heure, "%H:%M").time()) > maintenant:
            return f"aujourd'hui {heure}"
    return f"demain {heures[0]}"


class Planificateur:
    def __init__(self, lancer_collecte, est_occupe) -> None:
        self.lancer_collecte = lancer_collecte
        self.est_occupe = est_occupe
        self.arret = threading.Event()
        self._suspendu_pour = None
        self.fil = threading.Thread(target=self._boucle, daemon=True)
        self.fil.start()

    def _boucle(self) -> None:
        while not self.arret.wait(VERIFICATION):
            try:
                self._verifier()
            except Exception as e:                            # noqa: BLE001
                base.logguer(f"Planificateur : {e}", "erreur")
            try:
                self._verifier_publication()
            except Exception as e:                            # noqa: BLE001
                base.logguer(f"Planificateur (publication) : {e}", "erreur")

    def _verifier(self, maintenant: datetime | None = None) -> None:
        config = charger()
        if not config.get("collecte_auto"):
            return
        heures = _heures(config)
        if not heures:
            return
        maintenant = maintenant or datetime.now()
        heure = creneau_du(heures, maintenant)
        if not heure:
            return
        marque = f"{maintenant.date().isoformat()} {heure}"
        if base.lire_etat(CLE_DERNIER) == marque or self.est_occupe():
            return
        if not config.get("web_pendant_session_claude", True):
            session = session_claude.active()
            if session:
                if self._suspendu_pour != marque:
                    self._suspendu_pour = marque
                    base.logguer(f"Tournée de {heure} suspendue — {session}. Elle partira "
                                 "d'elle-même quand la session s'éteindra.", "info")
                return
        base.ecrire_etat(CLE_DERNIER, marque)
        base.logguer(f"Tournée automatique de {heure}.", "info")
        lancee = self.lancer_collecte(apres=lambda: self._taches_du_jour(config))
        if lancee is False:
            self._taches_du_jour(config)

    def _taches_du_jour(self, config: dict) -> None:
        aujourdhui = date.today().isoformat()
        if base.lire_etat(CLE_TACHES) == aujourdhui:
            return
        base.ecrire_etat(CLE_TACHES, aujourdhui)
        if config.get("decouverte_auto"):
            derniere = base.lire_etat(CLE_DECOUVERTE)
            jours = int(config.get("decouverte_jours", 7))
            due = not derniere or (date.today() - date.fromisoformat(derniere[:10])).days >= jours
            if due:
                resultat = sources_decouverte.decouvrir(config)
                base.ecrire_etat(CLE_DECOUVERTE, aujourdhui)
                base.logguer(f"Découverte de sources : {resultat['nouveaux']} candidat(s) nouveau(x) "
                             f"sur {resultat['examines']} trouvailles.", "info")

    def _verifier_publication(self, maintenant: datetime | None = None) -> None:
        config = charger()
        if not (config.get("publication_active") and config.get("publication_auto_programmee")):
            return
        heures = _heures(config, "heures_publication")
        if not heures:
            return
        maintenant = maintenant or datetime.now()
        heure = creneau_du(heures, maintenant)
        if not heure:
            return
        marque = f"{maintenant.date().isoformat()} {heure}"
        if base.lire_etat(CLE_PUBLICATION) == marque:
            return
        base.ecrire_etat(CLE_PUBLICATION, marque)
        prochaine = publication.prochaine_a_publier()
        if not prochaine:
            base.logguer(f"Créneau de publication {heure} : rien de programmé.", "info")
            return
        resultat = publication.publier(prochaine["id"], config)
        if not resultat.get("ok"):
            base.logguer(f"Publication programmée refusée : {resultat.get('erreur')}", "erreur")

    def fermer(self) -> None:
        self.arret.set()


def bilan_du_jour(config: dict) -> dict:
    fait = base.gardables_aujourdhui()
    objectif = int(config.get("objectif_par_jour") or 0)
    heures = _heures(config)
    heures_pub = _heures(config, "heures_publication")
    return {
        "actif": bool(config.get("collecte_auto")),
        "heures": heures,
        "prochain": prochain_passage(heures, bool(config.get("collecte_auto"))),
        "trouves": fait,
        "objectif": objectif,
        "atteint": bool(objectif and fait >= objectif),
        "publication_auto": bool(config.get("publication_active") and config.get("publication_auto_programmee")),
        "heures_publication": heures_pub,
        "prochaine_publication": prochain_passage(
            heures_pub, bool(config.get("publication_active") and config.get("publication_auto_programmee"))),
        "session_claude": session_claude.active() or "",
    }
