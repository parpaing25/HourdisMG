"""Relecture par un modèle — FACULTATIVE. Résumé, conseils, brouillon FR + MG.

Le tri et le rangement ne dépendent jamais du modèle : `score.py` note, le bot
range. Le modèle arrive APRÈS, sur les meilleures trouvailles, pour ce qui
demande du jugement : tirer trois conseils d'une transcription de vingt
minutes, dire si un article dit quelque chose de faux, écrire un malgache
correct.

Trois transports, réglés dans l'onglet Réglages :

  - `compatible` : n'importe quel fournisseur à l'API OpenAI (Groq par défaut,
    clé dans ~/.hourdis-secrets/llm_key.txt ou GROQ_API_KEY du profil Hermes).
    ⚠ Le quota Groq est PAR ORGANISATION : la clé du profil hourdis partage
    peut-être ses 200 000 jetons/jour avec le bot Messenger de Fonenako
    (incident du 03-04/09/2026, 1 076 réponses 429). D'où les plafonds
    `llm_relire_max` et `llm_score_min_pour_relire`.
  - `anthropic` : l'API Claude officielle (clé dans ~/.hourdis-secrets/).
  - `passerelle` : le LiteLLM d'Hermes — qui ne répond plus en local depuis
    le retour des bots sur le VPS (04/09/2026). Gardé pour le jour où il revient.
"""
from __future__ import annotations

import json

import requests

from . import base, config, redaction

SYSTEME = """Tu es l'assistant éditorial de la page Facebook « Hourdis Madagascar », qui vend des hourdis, briques creuses, briquettes, plaquettes et tuiles en terre cuite fabriqués près d'Antananarivo. On te donne un contenu trouvé sur le web (article, transcription de vidéo, guide, publication). Tu réponds UNIQUEMENT par un objet JSON, sans texte autour, avec ces clés :

{
  "pertinent": true/false — utile à quelqu'un qui construit ou pose des planchers hourdis, murs en brique, toitures en tuile à Madagascar,
  "score": 0-100 — intérêt pour la page (100 = conseil de pose concret, illustré, fiable),
  "resume_fr": "2 à 3 phrases en français, factuelles",
  "conseils": ["3 à 5 conseils CONCRETS tirés du contenu, en français, une phrase chacun, sans prix"],
  "themes": ["parmi : pose, calcul, erreurs, comparatif, isolation, toiture, murs, plancher, etaiement, securite, fabrication, entretien, madagascar"],
  "langue": "fr" | "mg" | "en" — langue du contenu,
  "post_fr": "publication Facebook prête : accroche d'une ligne avec un emoji, puis 4 à 7 lignes courtes et aérées, SANS prix, SANS numéro de téléphone, SANS hashtags, SANS lien (ils sont ajoutés ensuite)",
  "post_mg": "la même publication en malgache correct — alphabet malgache seulement (pas de c, u, q, w, x, ç), particule VE pour une question fermée, ton chaleureux et vouvoiement (ianao / tompoko)",
  "avertissements": ["ce que le contenu affirme de faux, de dangereux ou d'inapplicable à Madagascar ; ou vide"]
}

Règles absolues : n'invente aucun chiffre qui n'est pas dans le contenu ; ne cite aucun prix ; ne recopie pas le texte, reformule ; un contenu sur les hourdis en polystyrène ou en bois reste pertinent comme comparatif ; si le contenu est hors sujet, pertinent=false et les posts sont des chaînes vides."""

TAILLE_MAX = 22_000


class LLMIndisponible(Exception):
    """Le modèle n'a pas répondu. Jamais fatal."""


def _extraire_json(contenu: str) -> dict:
    debut, fin = contenu.find("{"), contenu.rfind("}")
    if debut < 0 or fin < debut:
        raise LLMIndisponible("réponse sans JSON")
    try:
        return json.loads(contenu[debut:fin + 1])
    except json.JSONDecodeError as e:
        raise LLMIndisponible(f"JSON illisible : {str(e)[:80]}") from e


def _contenu(t: dict) -> str:
    entete = (f"Titre : {t.get('titre', '')}\nGenre : {t.get('genre', '')}\n"
              f"Auteur : {t.get('auteur', '')}\nAdresse : {t.get('url', '')}\n"
              f"Date : {t.get('publie_le') or 'inconnue'}\n\n")
    texte = (t.get("texte") or t.get("resume") or "").strip()
    return entete + texte[:TAILLE_MAX]


def _via_compatible(systeme: str, contenu: str, cfg: dict) -> dict:
    cle = config.cle_llm_compatible()
    if not cle:
        raise LLMIndisponible("aucune clé : ~/.hourdis-secrets/llm_key.txt ou GROQ_API_KEY du profil Hermes")
    adresse = (cfg.get("llm_url") or "https://api.groq.com/openai/v1").rstrip("/")
    corps = {
        "model": cfg.get("llm_modele") or "llama-3.3-70b-versatile",
        "messages": [{"role": "system", "content": systeme},
                     {"role": "user", "content": contenu}],
        "temperature": 0.3,
        "max_tokens": 2200,
        "response_format": {"type": "json_object"},
    }
    try:
        r = requests.post(f"{adresse}/chat/completions", json=corps,
                          headers={"Authorization": f"Bearer {cle}"},
                          timeout=int(cfg.get("llm_delai", 90)))
    except requests.RequestException as e:
        raise LLMIndisponible(str(e)[:160]) from e
    if not r.ok:
        # Le CORPS de l'erreur, pas le seul statut : « 400 json_validate_failed »
        # et « 429 quota » se soignent différemment (leçon du 03/09/2026).
        raise LLMIndisponible(f"HTTP {r.status_code} — {r.text[:200]}")
    try:
        texte = r.json()["choices"][0]["message"]["content"]
    except (KeyError, IndexError, ValueError) as e:
        raise LLMIndisponible(f"réponse inattendue : {r.text[:120]}") from e
    if not texte:
        raise LLMIndisponible("réponse vide (content null)")
    return _extraire_json(texte)


def _via_passerelle(systeme: str, contenu: str, cfg: dict) -> dict:
    adresse = (cfg.get("llm_passerelle") or "http://127.0.0.1:4000").rstrip("/")
    try:
        r = requests.post(f"{adresse}/v1/chat/completions", json={
            "model": cfg.get("llm_modele_passerelle") or "claude-abo",
            "max_tokens": 3000,
            "messages": [{"role": "system", "content": systeme},
                         {"role": "user", "content": contenu}],
        }, timeout=int(cfg.get("llm_delai", 90)))
    except requests.RequestException as e:
        raise LLMIndisponible(f"passerelle injoignable : {str(e)[:120]}") from e
    if not r.ok:
        raise LLMIndisponible(f"HTTP {r.status_code} — {r.text[:160]}")
    texte = r.json()["choices"][0]["message"]["content"]
    if not texte:
        raise LLMIndisponible("réponse vide")
    return _extraire_json(texte)


def _via_anthropic(systeme: str, contenu: str, cfg: dict) -> dict:
    try:
        import anthropic
    except ImportError as e:
        raise LLMIndisponible("paquet `anthropic` absent (pip install anthropic)") from e
    cle = config.cle_anthropic()
    if not cle:
        raise LLMIndisponible("aucune clé Anthropic dans ~/.hourdis-secrets/anthropic_key.txt")
    client = anthropic.Anthropic(api_key=cle)
    try:
        reponse = client.messages.create(
            model=cfg.get("llm_modele_anthropic") or "claude-sonnet-5",
            max_tokens=3000,
            system=[{"type": "text", "text": systeme, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": contenu}],
        )
    except Exception as e:
        raise LLMIndisponible(str(e)[:200]) from e
    return _extraire_json("".join(b.text for b in reponse.content
                                  if getattr(b, "type", "") == "text"))


def _appeler(contenu: str, cfg: dict) -> dict:
    transport = cfg.get("llm_transport", "compatible")
    if transport == "anthropic":
        return _via_anthropic(SYSTEME, contenu, cfg)
    if transport == "passerelle":
        return _via_passerelle(SYSTEME, contenu, cfg)
    return _via_compatible(SYSTEME, contenu, cfg)


def _liste(valeur) -> list[str]:
    if isinstance(valeur, list):
        return [str(v).strip() for v in valeur if str(v).strip()][:6]
    if isinstance(valeur, str) and valeur.strip():
        return [valeur.strip()]
    return []


def relire(t: dict, cfg: dict) -> dict:
    """Fait relire une trouvaille. Rend la réponse normalisée ; lève LLMIndisponible."""
    if not (t.get("texte") or t.get("resume")):
        raise LLMIndisponible("rien à lire")
    brut = _appeler(_contenu(t), cfg)
    try:
        score_ia = max(0, min(100, int(brut.get("score") or 0)))
    except (TypeError, ValueError):
        score_ia = 0
    return {
        "pertinent": bool(brut.get("pertinent", score_ia >= 40)),
        "score_ia": score_ia,
        "resume": str(brut.get("resume_fr") or "").strip()[:1200],
        "conseils": _liste(brut.get("conseils")),
        "themes": [th for th in _liste(brut.get("themes")) if th in
                   ("pose", "calcul", "erreurs", "comparatif", "isolation", "toiture", "murs",
                    "plancher", "etaiement", "securite", "fabrication", "entretien", "prix",
                    "madagascar")],
        "langue": str(brut.get("langue") or "")[:2],
        "post_fr": str(brut.get("post_fr") or "").strip()[:1500],
        "post_mg": str(brut.get("post_mg") or "").strip()[:1500],
        "avertissements": _liste(brut.get("avertissements")),
    }


def appliquer(tid: str, lecture: dict, cfg: dict) -> dict:
    """Écrit la relecture dans la trouvaille (et réécrit son dossier). Rend la fiche."""
    from . import rangement
    t = base.trouvaille(tid)
    if not t:
        return {}
    champs = {
        "score_ia": lecture["score_ia"],
        "relu_le": base.maintenant(),
        "avertissements": lecture["avertissements"],
    }
    if lecture["resume"]:
        champs["resume"] = lecture["resume"]
    if lecture["conseils"]:
        champs["conseils"] = lecture["conseils"]
    if lecture["themes"]:
        champs["themes"] = sorted(set(t.get("themes") or []) | set(lecture["themes"]))
    if lecture["langue"] and not t.get("langue"):
        champs["langue"] = lecture["langue"]
    langue = (cfg.get("langue_post") or "mix").lower()
    if lecture["post_fr"] or lecture["post_mg"]:
        if langue == "mg" and lecture["post_mg"]:
            champs["post"] = redaction.assembler_depuis_ia(lecture["post_mg"], t, cfg, "mg")
        elif langue == "fr" and lecture["post_fr"]:
            champs["post"] = redaction.assembler_depuis_ia(lecture["post_fr"], t, cfg, "fr")
        elif lecture["post_mg"] and lecture["post_fr"]:
            champs["post"] = redaction.assembler_depuis_ia(
                lecture["post_mg"] + "\n\n— — —\n\n" + lecture["post_fr"], t, cfg, "mg")
        elif lecture["post_fr"]:
            champs["post"] = redaction.assembler_depuis_ia(lecture["post_fr"], t, cfg, "fr")
        if lecture["post_mg"]:
            champs["post_mg"] = lecture["post_mg"]
    if not lecture["pertinent"] and lecture["score_ia"] < 25 and t.get("statut") == "nouvelle":
        champs["statut"] = "ecartee"
        champs["motif_ecart"] = "jugée hors sujet par le modèle"
    base.modifier_trouvaille(tid, champs)
    t = base.trouvaille(tid) or t
    if t.get("dossier") or t.get("statut") != "ecartee":
        try:
            t["dossier"] = rangement.ranger(t, cfg)
            base.modifier_trouvaille(tid, {"dossier": t["dossier"]})
        except OSError as e:
            base.logguer(f"Dossier non réécrit après relecture : {e}", "avert")
    return t


def tester(cfg: dict) -> dict:
    """Un appel minuscule pour vérifier clé, adresse et modèle."""
    essai = {"titre": "Test", "genre": "article", "url": "https://exemple.test",
             "texte": "Pose de hourdis en terre cuite sur poutrelles précontraintes : "
                      "vérifier l'étaiement avant de couler la dalle de compression."}
    try:
        lecture = relire(essai, cfg)
    except LLMIndisponible as e:
        return {"ok": False, "erreur": str(e)}
    return {"ok": True, "score_ia": lecture["score_ia"], "resume": lecture["resume"][:200],
            "transport": cfg.get("llm_transport"), "modele": cfg.get("llm_modele")}
