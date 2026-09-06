# Bot de veille Hourdis

Il cherche sur le web — et un peu sur Facebook — des **conseils, tutos et techniques**
sur les hourdis, la terre cuite (briques, tuiles), la pose de planchers et la
construction ; il **note** chaque trouvaille, la **range dans un dossier daté** avec
son texte en `.txt`, et **prépare une publication** pour la page Facebook
« Hourdis Madagascar ». Vous relisez, vous publiez.

C'est le quatrième bot de collecte de la machine, sur le port **8761**. Il reprend ce
que les trois autres ont appris : la lecture du web ouvert de Diako, la fraîcheur et le
planificateur d'AKORA, le verrou navigateur et la règle « pas de Chromium pendant une
session Claude » des trois. Il en diffère sur l'essentiel : **le web d'abord**, Facebook
très peu.

## Démarrer

```
DEMARRER.bat            (ou : python demarrer.py)
```

L'interface s'ouvre sur http://127.0.0.1:8761. Première installation :

```
pip install -r requirements.txt
python -m playwright install chromium     (seulement pour la partie Facebook)
```

Le gardien des bots (`~/bots-hub/redemarrer-les-bots.ps1`) et le poste de pilotage
(8760) connaissent ce bot : il est relevé et surveillé comme les autres.

## Ce que fait une tournée

1. **Les recherches web** — chaque requête interroge Google Actualités et Bing (leurs
   flux RSS, sans clé). Les liens Google sont résolus vers l'article réel
   (`batchexecute`), la page est lue, datée, notée.
2. **YouTube** — recherches et chaînes suivies, via `yt-dlp` : titre, chaîne, durée, vues,
   date de mise en ligne, description, et **les sous-titres** — c'est le texte du tuto,
   rangé dans `texte.txt`. La vidéo elle-même n'est jamais téléchargée.
3. **Les sites** (fabricants, presse) — l'accueil et deux ou trois rubriques (conseils,
   blog, guides) ouvrent les articles ; les **PDF** de pose ou de prescription sont lus
   (`pypdf`).
4. **Les flux RSS** déclarés tels quels.
5. **Facebook**, en dernier et petit : les pages et groupes déclarés, six défilements
   chacun — derrière trois garde-fous (mémoire, verrou navigateur partagé, session Claude).
6. **La relecture par un modèle**, si elle est allumée : résumé, 3 à 5 conseils, brouillon
   FR + MG, avertissements.

Tout passe par le même chemin : adresse canonique (sans `utm_`, `fbclid`…), empreinte
du texte (le même tuto repris par trois sites n'entre qu'une fois), **score**, date,
dossier. Ce qui est écarté est **compté et dit** dans le journal.

### Le score (0-100), et pourquoi il s'explique

`score.py` est déterministe. Il additionne les mots du métier (`lexique.py` : « hourdis »
pèse 10, « béton » 3, « biriky » 7, « beam and block » 10…), le signal « ça enseigne »
(comment, étapes, erreurs, ahoana, torohevitra…), les thèmes reconnus, le genre (une
vidéo de pose vaut plus qu'un communiqué), la longueur, la langue. Il **écarte d'office**
un texte sans aucun mot du métier, ou un repoussoir non contredit (annonce immobilière,
brique de lait, Lego…).

Chaque fiche garde ses **motifs** (« hourdis ×4 », « tutoriel », « anglais ») : un
score qu'on comprend se règle. Les écartées restent visibles (filtre « Écartées ») pour
ça, et le seuil `score_min` se change dans Réglages.

### La date de publication — jamais inventée

`dates_web.py` cherche la date dans la page (JSON-LD, balises meta, `<time>`, l'adresse,
le texte), le flux, YouTube ou Facebook. **Quand elle est introuvable, la fiche va dans
`date-inconnue/`** — pas dans le dossier du jour. Une date estampillée « aujourd'hui »
sur un article de 2019 serait un mensonge rangé (règle héritée de `fraicheur.py`,
AKORA, 24/08/2026). Dans le panneau de détail, vous corrigez la date : la fiche déménage.

## Les dossiers

```
data/collecte/
  2026-09-04/
    INDEX.txt                                   score | genre | titre | adresse
    pose-plancher-hourdis-poutrelles--a1b2c3/
      texte.txt          en-tête (titre, adresse, auteur, date et d'où elle vient,
                         score, thèmes, motifs) puis texte intégral ou transcription
      fiche.json         tout ce qu'on sait, pour les machines
      post-facebook.txt  brouillon de publication prêt à coller
      images/            vignette, photos utiles (jusqu'à 4, ≥ 400 px)
  date-inconnue/
```

Le dossier racine se déplace dans Réglages (`dossier_collecte`) — sur `C:`, jamais sur
`G:` pendant une synchronisation Drive.

## Publier sur la page

Le bot **prépare**, l'humain **appuie**. `post-facebook.txt` suit la bible business de la
page : accroche (MG et/ou FR selon le réglage), 3 conseils tirés du texte, source citée,
appel à l'action, contact, hashtags — **jamais de prix**.

- Publication **éteinte** (défaut) : copiez le texte depuis le panneau ou le dossier.
- Publication **active** (Réglages) : le bouton « Publier maintenant » envoie sur la page
  par l'API Graph (jeton de page du profil Hermes hourdis, ou
  `~/.hourdis-secrets/facebook.txt`), « Programmer » utilise la programmation de Facebook
  (10 min à 30 jours), « À blanc » montre ce qui partirait.
- Automatisation « Publier les programmées aux heures dites » : le planificateur publie
  la prochaine trouvaille **que vous avez passée en « programmée »** — jamais une que
  vous n'avez pas relue.

⚠ **Un seul répondeur par page** : ce bot publie, il ne répond à aucun message ni
commentaire (rôle du profil Hermes hourdis).

## L'interface

| Onglet | Ce qu'on y fait |
|---|---|
| Tableau de bord | lancer/arrêter la tournée, importer une adresse, voir l'avancement, les dernières gardées, le journal |
| Trouvailles | filtrer (statut, genre, thème, source, mot, tri), garder / écarter / programmer, en lot ; « Détail / post » ouvre le panneau |
| Publication | état du jeton de page, file d'attente, historique |
| Dossiers | l'arborescence par date, ouverture dans l'Explorateur |
| Sources | ajouter (une adresse **ou des mots**), activer/mettre en pause, rendement (examinées, gardées, échecs), collecter une source seule |
| Nouvelles sources | les chaînes et sites que le bot propose de suivre, à adopter ou écarter |
| Automatisation | heures de tournée, objectif du jour, relecture IA, découverte, publication programmée |
| Réglages | tri, budget, rangement, Facebook (lecture), publication, modèle |
| Journal | tout, filtrable par niveau |

## Réglages qui comptent

- `score_min` (35) — sous ce score, écartée.
- `jours_max` (0 = illimité) pour les tutos, `jours_max_actualites` (540) pour les actualités.
- `videos_par_recherche`, `videos_details_max`, `transcriptions_max`, `pages_par_site`,
  `resultats_par_recherche_web` — le budget d'une tournée. Une tournée doit rester une
  lecture, pas un aspirateur.
- `web_pendant_session_claude` (vrai) — la partie web (~100 Mo) tourne même quand une
  session Claude est ouverte ; seule la partie Chromium attend. À faux, tout attend.
- `llm_actif` (faux) — transports `compatible` (Groq par défaut, clé du profil Hermes
  hourdis ou `~/.hourdis-secrets/llm_key.txt`), `anthropic`, `passerelle`. ⚠ Le quota Groq
  est par organisation et peut être partagé avec le bot Messenger de Fonenako
  (200 000 jetons/jour) : plafonds bas.

## Secrets

Rien dans le dépôt. Le bot lit, dans l'ordre :

- `~/.hourdis-secrets/facebook.txt` (`FB_PAGE_ID=…`, `FB_PAGE_TOKEN=…`), sinon
  `~/.hermes/profiles/hourdis/.env` — le jeton de page posé le 16/07/2026 ;
- `~/.hourdis-secrets/llm_key.txt`, sinon `GROQ_API_KEY` du même `.env` ;
- `~/.hourdis-secrets/anthropic_key.txt`, sinon `~/.fonenako-secrets/anthropic_key.txt`.

La session Facebook de **lecture** (Playwright) vit dans `data/profil-fb/` : utilisez un
compte dédié à la veille.

## Ce qui casse un jour ou l'autre

- **Le DOM de Facebook** : `facebook.py` porte le script d'extraction du bot Diako
  (dernier passage réel le 02/09/2026). Si la partie Facebook rend « 0 publication » alors
  que la session est connectée, c'est là.
- **Google Actualités** change ses liens : `flux.resoudre_lien_google` essaie la
  redirection, le base64 (2023) puis `batchexecute` (2024+). En échec, la trouvaille
  garde le lien Google, son titre et son éditeur, sans texte.
- **yt-dlp** vieillit vite : `pip install -U yt-dlp` quand la recherche YouTube rend vide.
- **Le jeton de page** expire ou est révoqué : Publication → « Vérifier le jeton ».

## Tests

```
python -m pytest tests -q        (57 tests, dossier de données jetable)
```

Les tests posent `HOURDIS_BOT_DATA` sur un dossier temporaire avant tout import : ils
ne touchent jamais `data/`.

## Organisation des fichiers

```
bot/
  config.py            réglages (data/config.json) et emplacement des secrets
  base.py              SQLite : sources, trouvailles, candidats, publications, journal
  lexique.py           mots du métier FR/MG/EN, thèmes, repoussoirs
  score.py             la note et ses motifs
  dates_web.py         date de publication d'une page web
  fraicheur.py         dates relatives/absolues (copie d'AKORA)
  toile.py             lire une page, un site, un PDF — poliment
  flux.py              RSS/Atom, Google Actualités, Bing, chaînes YouTube
  youtube.py           yt-dlp : recherche, fiches, sous-titres
  facebook.py          la petite partie Facebook (Playwright)
  collecteur.py        la tournée, et le chemin unique de traitement
  rangement.py         dossiers par date, texte.txt, INDEX.txt, images
  redaction.py         brouillon de publication sans modèle
  analyse_llm.py       relecture par un modèle (facultative)
  publication.py       API Graph : publier, programmer, à blanc
  sources_decouverte.py  nouvelles sources depuis ce qu'on a gardé
  planificateur.py     tournées et publications aux heures dites
  serveur.py           API + interface (FastAPI)
  verrou_navigateur.py, session_claude.py   copies à l'identique des trois bots frères
web/                   index.html, app.js, style.css
tests/                 57 tests
data/                  base, config, session Facebook, collecte — HORS dépôt
```
