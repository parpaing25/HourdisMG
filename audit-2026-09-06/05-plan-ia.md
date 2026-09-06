# 05 — Plan d'intégrations IA

Contexte : ce site vend un produit simple (13 références, prix publics) à une clientèle qui
préfère parler, en français ou en malgache, et qui paie ses données mobiles. L'IA utile ici n'est
pas un chatbot de plus : c'est ce qui **fait gagner un appel**, **évite un prix inventé** et
**enlève du travail à Andry**. Le socle existe déjà hors site : le profil Hermes `hourdis`
(@Hourdis_bot, bible business, connecteur Facebook) et le pont Claude Code du PC.

Règles non négociables pour tout ce qui suit : prix et délais lus **uniquement** dans
`site/data/produits.json` (jamais générés) ; mention « assistant automatique » ; aucune donnée
personnelle envoyée au modèle sans nécessité (le nom et le téléphone restent dans `contact.php`) ;
repli WhatsApp si l'API tombe ; plafond de dépense mensuel ; journal des conversations hors
racine web ; jeu de 30 questions de test rejoué avant chaque changement ; bouton « signaler ».

## Classement par valeur

| # | Intégration | Gain attendu | Coût mensuel | Effort | Risque | Décision |
|---|---|---|---|---|---|---|
| 1 | **Qualification des demandes** : chaque devis reçu est classé (chantier réel / curieux / spam), résumé en une ligne et enrichi (surface → pièces → budget) dans la notification Telegram | Andry rappelle d'abord les vrais chantiers ; 0 devis oublié | ≈ 0,3 € (Claude Haiku 4.5, 200 demandes) | 3 h | faible : le classement n'efface rien, il ordonne | **faire en premier** |
| 2 | **Assistant devis sur le site** (« Posez votre question »), réponses depuis FAQ + catalogue, en FR et MG, transfert WhatsApp en un clic, transcript envoyé à Andry si le visiteur laisse son numéro | capte les visiteurs de nuit et ceux qui n'appellent pas ; alimente la FAQ avec les vraies questions | ≈ 2 € (Haiku 4.5, 500 conversations de 6 tours) ; 0 € avec Gemini Flash gratuit en secours | 8 h | moyen : un prix halluciné. Parade : le modèle ne cite que des chiffres présents dans le contexte, vérifiés par regex avant envoi ; sinon « je vous mets en relation » | faire après le lancement, une fois 2 semaines de mesure lues |
| 3 | **« Envoyez votre plan »** : photo ou PDF du plan de plancher → surface par pièce → nombre de hourdis, poutrelles à prévoir, budget, validé par Andry (ingénieur) avant envoi au client | différenciant : aucun concurrent local ne le fait ; transforme un plan en devis en 10 min | ≈ 1 € (vision Claude, 50 plans) | 12 h | élevé si non relu : un plancher sous-dimensionné. Parade : sortie = brouillon pour Andry, jamais envoyée directement | prototype à 3 mois |
| 4 | **Version malgache assistée** : traduction de la page et de la FAQ par Claude, **relue et corrigée par Andry** (règle : aucun texte MG sans relecture), puis `hreflang` | audience bilingue ; requêtes MG sur Google et Facebook | 0 € (une fois) | 6 h + relecture | faible | à planifier |
| 5 | **Agent d'amélioration hebdomadaire** (voir 06) : lit le rapport, les demandes, Search Console, propose 3 actions | itération sans réunion | ≈ 0,5 € | 4 h | faible | avec 06 |
| — | Recherche sémantique, recommandations, personnalisation | 13 produits, une page : sans valeur | — | — | — | ne pas faire |

## Architecture commune

```
navigateur ──POST──▶ /contact.php (o2switch) ──▶ e-mail + Telegram + leads.jsonl
                                           └──▶ (1) qualification : cron cPanel toutes les 10 min
                                                    lit leads.jsonl → API Claude → Telegram enrichi

navigateur ──POST──▶ Edge Function Supabase `assistant-hourdis` (projet Fonenako existant, région ap-southeast-1)
                     contexte = faq.html + produits.json (mis en cache 1 h) → Claude Haiku 4.5
                     ↳ garde-fous : chiffres ∈ produits.json, sujet ∈ {hourdis, briques, tuiles, livraison, devis}
                     ↳ journal Supabase `assistant_conversations` (sans téléphone), plafond 5 000 tours/mois
```

Pourquoi une Edge Function plutôt que PHP : la clé d'API reste hors du serveur mutualisé, le
plafond et le journal existent déjà dans le projet Fonenako, et le pattern est éprouvé
(`agent-fonenako`). La CSP du site ajoutera `connect-src https://<projet>.supabase.co`.

## Code de démarrage — (1) qualification des demandes

`outils-serveur/qualifier_demandes.py` (cron cPanel `*/10 * * * *`, Python 3 disponible chez
o2switch ; clé dans `hourdis-config.php`) :

```python
import json, os, time, urllib.request
from pathlib import Path
D = Path.home() / "hourdis-data"; CONF = json.loads(Path.home().joinpath("hourdis-config.json").read_text())
vu = set((D / "qualifies.txt").read_text().split()) if (D / "qualifies.txt").exists() else set()
for ligne in (D / "leads.jsonl").read_text(encoding="utf-8").splitlines():
    lead = json.loads(ligne)
    if lead["ts"] in vu: continue
    prompt = ("Tu classes une demande de devis de matériaux (hourdis, briques, tuiles) à Antananarivo. "
              "Réponds en JSON {classe: 'chantier'|'curieux'|'spam', resume: '<1 ligne>', urgence: 1-3}. "
              f"Demande : lieu={lead['lieu']} surface={lead['surface']} message={lead['message'][:500]}")
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", method="POST",
        headers={"x-api-key": CONF["anthropic_key"], "anthropic-version": "2023-06-01", "content-type": "application/json"},
        data=json.dumps({"model": "claude-haiku-4-5-20251001", "max_tokens": 200, "messages": [{"role": "user", "content": prompt}]}).encode())
    rep = json.loads(urllib.request.urlopen(req, timeout=20).read())["content"][0]["text"]
    verdict = json.loads(rep[rep.find("{"):rep.rfind("}") + 1])
    texte = f"{'🔥' if verdict['urgence'] == 3 else '🧱'} {verdict['classe'].upper()} — {verdict['resume']}\n{lead['nom']} {lead['tel']} · {lead['lieu']}"
    urllib.request.urlopen(f"https://api.telegram.org/bot{CONF['telegram_token']}/sendMessage",
        data=json.dumps({"chat_id": CONF["telegram_chat"], "text": texte}).encode(), timeout=15)
    (D / "qualifies.txt").open("a").write(lead["ts"] + "\n")
```

Le nom et le téléphone ne partent **pas** au modèle (seuls lieu, surface, message). Coût : ~300
jetons par demande.

## Jeu d'évaluation (à tenir dans `tests/assistant-questions.json` quand l'assistant existe)

30 questions réelles tirées des messages de la page (à extraire via bot-page), avec la réponse
attendue et les chiffres qui doivent y figurer ; 10 questions hors sujet (politique, médical,
concurrents) où la seule réponse acceptée est un renvoi vers l'humain ; 5 pièges de prix (« c'est
bien 2 000 Ar le hourdis 20 ? ») où le modèle doit corriger avec la valeur du catalogue.
