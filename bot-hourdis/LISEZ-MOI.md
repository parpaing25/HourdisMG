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

### Audit du 06/09/2026 — ce qui a changé, et pourquoi

La première tournée complète (131 pages examinées) et les 13 premières trouvailles ont servi
de banc. Sept défauts mesurés, tous corrigés et tenus par des tests :

| Ce qui n'allait pas | Ce qui a été fait |
|---|---|
| **Le BTP générique passait.** « Comment maintenir une pression d'eau régulière ? » (37/100) et « décryptage des normes pour vos gants » (51/100) sont entrés sans jamais nommer un hourdis, une brique, une tuile ou la terre cuite : 12 points de métier et 30 de bonus. | Le **produit doit être nommé** (`lexique.ESSENTIELS`) : dans le titre, ou trois fois dans le texte. Et les **bonus sont plafonnés par le cœur** — un article ne peut plus doubler sa note parce qu'il est long et pédagogique. |
| **Les titres étaient abîmés.** Batirama sert dans sa propre balise `<title>` « Ddécryptage des normes pourvos gants » alors que son `<h1>` est intact. | Le `<h1>` de l'article passe **avant** la balise `<title>` (`toile.titre_de_page`), et la queue « … \| Nom du site » est retirée. |
| **Un mur anti-robot devenait une fiche.** Une page de blocage de 529 caractères (« anubis n'a pas réussi à charger son code javascript ») a été rangée comme un article. | `toile.est_sans_contenu()` refuse les murs, les paywalls et les pages presque vides, **sur le chemin unique**, avant toute écriture. |
| **« javascript » rejetait de bons articles.** Un article universitaire sur les tuiles médiévales était classé « informatique » à cause du bandeau de sa page. | Les mots d'ossature de page (`javascript`, `plugin`, `wordpress theme`) sortent des repoussoirs. |
| **L'âge jetait l'intemporel.** « La liste des DTU à jour » (88/100) et « Les nouvelles tuiles à emboîtement » (92/100) étaient écartées pour être nées avant 2012 — un seuil hérité d'AKORA, où il protégeait des prix. | Le couperet d'âge ne s'applique **qu'aux actualités**. Une technique ne se périme pas. Et le **canal de découverte ne décide plus du genre** : une adresse en `/edito/` ou `/article/` reste un article même trouvée par Google Actualités. |
| **Les condensés entraient.** « La sélection quotidienne de l'actu du BTP » (82 092 caractères, vingt articles) était gardée à 80/100. | La taille se juge **avant** le nombre de liens, et `/emailing`, `newsletter`, `/archives/` sont exclus. |
| **Les titres de PDF étaient des libellés de bouton.** Quatre fiches « Télécharger la fiche », deux « Afficher le document ». | Le document s'annonce lui-même (`toile.titre_du_pdf`), et `lexique.TITRE_DE_SERVICE` refuse les libellés d'interface. |

Trois ajouts qui en découlent :

- **« Renoter la pile »** (onglet Trouvailles) applique les règles d'aujourd'hui aux trouvailles
  déjà collectées — une correction du tri doit nettoyer le stock, pas seulement le flux. Ce
  qu'Andry a gardé, programmé ou publié n'est **jamais** dégardé ; seule sa note est rafraîchie.
- **« Ajouter les sources conseillées manquantes »** (onglet Sources) : les 17 sources d'origine
  étaient toutes françaises. Cinq recherches tournées vers Madagascar et l'Afrique s'y ajoutent,
  sans jamais faire revenir une source qu'Andry a supprimée.
- **Une recherche YouTube qui dépasse son délai garde ses résultats partiels** au lieu de rendre
  la source morte, et le délai passe de 120 à 240 s (les requêtes en malgache sont les plus lentes).

### Le score (0-100), et pourquoi il s'explique

`score.py` est déterministe. Il additionne les mots du métier (`lexique.py` : « hourdis »
pèse 10, « béton » 3, « biriky » 7, « beam and block » 10…), le signal « ça enseigne »
(comment, étapes, erreurs, ahoana, torohevitra…), les thèmes reconnus, le genre (une
vidéo de pose vaut plus qu'un communiqué), la longueur, la langue. Il **écarte d'office**
un texte sans aucun mot du métier, un repoussoir non contredit (annonce immobilière,
brique de lait, Lego…), et — depuis l'audit — **un texte qui ne nomme jamais le produit**.

Trois portes, dans cet ordre : les **repoussoirs** (le motif le plus précis gagne : « annonce
immobilière » se lit mieux dans le journal que « produit jamais nommé »), puis le **produit
nommé**, puis le **barème**, dont les bonus ne peuvent pas dépasser le cœur. Mesuré sur les
13 premières trouvailles : deux verdicts changent, les deux dans le bon sens, et le bon tuto
« Comment monter une cloison en brique » — qui n'a que le mot « brique » — reste.

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

### 🚀 Publier en un clic

Le bouton « 🚀 Publier » (sur chaque carte, et en tête du panneau de détail) fait tout :

1. **refait le texte** — le modèle réécrit s'il est allumé (résumé, conseils, FR + MG),
   sinon le gabarit refait le brouillon depuis le texte ; décochez « refaire le texte »
   pour imposer celui du panneau ;
2. **importe les médias** — les images de l'article (jusqu'à `un_clic_photos_max`), la
   vignette YouTube, et **la vidéo elle-même** (MP4, 720p max, `video_taille_max_mo`,
   `video_duree_max_s`) dans `media/` du dossier de la fiche ;
3. **publie avec le contenu attaché** — vidéo native (`graph-video`), sinon album de
   photos + texte + lien, sinon texte + lien. Une vidéo refusée par Facebook (droits,
   poids, jeton sans `publish_video`) retombe sur l'album, la publication n'est pas perdue.

L'avancement s'affiche dans le panneau (« Téléchargement de la vidéo… », « Envoi… »)
et dans le journal. « Essai à blanc » fait tout sauf envoyer. Si la publication est
éteinte, le bouton propose de l'allumer et recommence.

⚠ Une vidéo republiée reste celle de son auteur : la source est toujours citée dans la
description, et c'est vous qui décidez, vidéo par vidéo. Pour partager sans republier,
décochez « importer la vidéo » : la vignette et le lien partent à la place.

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
python -m pytest tests -q        (81 tests, dossier de données jetable)
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
tests/                 81 tests
data/                  base, config, session Facebook, collecte — HORS dépôt
```
