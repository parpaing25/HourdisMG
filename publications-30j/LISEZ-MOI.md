# Série de 30 publications — page Facebook Hourdis Madagascar

Du **samedi 19/09 au dimanche 18/10/2026**, une publication par jour à **18:00** (heure de Tana),
sur la page Hourdis Madagascar (id 470850726774233). Préparée le 18/09/2026 à la demande d'Andry :
« programme pour les 30 jours, des hourdis dans nos dossiers, divers publications, et mentionne le
site web ».

## La chaîne

| Étape | Fichier | Ce qu'il fait |
|---|---|---|
| Textes | `serie.py` | les 30 publications : texte, gabarit d'affiche, cible sur le site |
| Photos | `catalogue.py`, `planches.py` → `photos.json` | tri des photos d'atelier (`ASA\SERA ORDI KELY\sera\hourdis`), 38 retenues, `photos-rejetees.json` dit pourquoi les autres ne servent pas |
| Attribution | `affectation.json` | une photo par publication, jamais deux fois |
| Fabrication | `fabriquer.py tout` | `sortie/<date>-<slug>/` : `brouillon.txt` (texte exact), `affiche-fil.png` 1080×1350, `fiche.json` |
| Captures | `fabriquer.py captures` | calculatrice et formulaire de devis, sur le site **local** (`python build.py --servir`) : une capture en ligne écrirait de fausses visites dans `stat.php` |
| Contrôle | `verifier.py` | prix = `site/data/produits.json`, calculs m² → pièces justes, aucun « stock »/« disponible », lien `utm_content=jNN`, 5 hashtags, débuts tous différents, photos uniques. Sans `VERDICT ok`, rien ne part |
| Relecture | `fabriquer.py planche`, `fabriquer.py cahier` | planches des 30 affiches ; `cahier.html` = affiche + texte exact, jour par jour |

Refaire après toute modification de `serie.py` : `python publications-30j/fabriquer.py tout`,
puis `verifier.py`, puis regarder `planche-1.jpg` et `planche-2.jpg`.

## Ce qu'il faut savoir

- **Sources des faits** : les prix et les quantités par m² viennent de `site/data/produits.json`, les conseils
  techniques de `site/faq.html`. La page et le site disent la même chose.
- **Les hourdis sont sur commande** (≈ 30 jours de production + 3 à 7 jours de livraison). Aucune publication
  ne dit « en stock » : les anciennes publications de la page le disaient, contre la règle d'Andry du 06/09/2026.
- **Hauteur 12/15/20 illisible sur les photos**, et les noms de fichiers contredisent l'étiquetage du site
  (le fichier « Hourdis 15 » est affiché comme hourdis 12 sur le site, une copie nommée « Hourdis 20 » comme
  hourdis 15). Les publications « hourdis 20/15 » et « brique creuse 20/15/10 » sont donc des cartes texte avec
  une bande photo de production, sans gros plan qui prétendrait montrer la hauteur. **À trancher par Andry**,
  pour le site aussi.
- **Numéros** : seuls les numéros d'appel figurent (032 47 041 43, 033 71 063 34). Le numéro WhatsApp est en
  doute (le site dit 032 47 041 43, une note du 06/09 dit 032 72 09 033).
- **Lien** : `utm_content=j01…j30` ne se lit pas dans `stat.php` (il ne garde que le chemin) mais dans les
  journaux d'accès Apache d'o2switch, qui gardent l'adresse complète.

## Reels — ce qui part vraiment à 18:00 (ordre d'Andry du 18/09/2026)

« Crée des reels à publier à chaque 18 h et programme la publication » : la série part en
**reels** (1080×1920, ~12,5 s), un par jour à 18:00, avec le texte de `brouillon.txt` en légende.
Les affiches 1080×1350 restent en réserve ; elles ne sont PAS programmées (sinon deux
publications par jour).

| Étape | Fichier |
|---|---|
| Scènes (3 par reel, écrites à la main, contrôlées par `verifier.py`) | `reels_scenes.py` |
| Rendu : scènes PNG + montage `marketing/atelier/clip.py` de Fonenako (importé, pas copié) | `reels.py tout` → `sortie/<post>/reel.mp4` |
| Programmation par l'API Reels (start → envoi → finish `SCHEDULED`) | `programmer_reels.py` (à blanc par défaut, `--envoyer`, `--relire`) |
| Trace des reels acceptés (identifiants vidéo) | `programmation-reels.json` |

- **Son** : musique Mixkit de la bibliothèque de l'atelier (sans attribution), catégories annonce
  et confiance, jamais deux jours de suite la même. Sans voix, `clip.py` laissait la musique à 0.22
  (−27,5 LUFS, inaudible) : `reels.py` ramène chaque reel vers −14 LUFS (mesuré −15,9 sur le premier).
  **Niveau choisi par la norme, pas encore à l'oreille d'Andry.**
- Essai du 18/09 : reel du 19/09 accepté (`published: false`, `publish_status: scheduled`,
  15:00 UTC = 18:00 Tana), contrôle de droits d'auteur de Facebook passé sans correspondance.

## Série de 14:00 — publications photo (demande d'Andry du 18/09/2026)

« Fais des publications encore pour 30 jours, à chaque 14 h, regarde les publications
nécessaires et attirantes » : `serie14.py`, 30 publications photo du 19/09 au 18/10 à 14:00,
en plus des reels de 18:00, sans doubler le sujet du reel du même jour.

- **Nécessaires** : bâties sur ce que les clients demandent vraiment. Relevé du 18/09 sur 948
  messages privés et 21 commentaires (thèmes comptés par script, aucun nom retenu) :
  disponible/stock 186 · prix 110 · adresse 108 · plancher/dalle 79 · quantités 76 ·
  hauteur 12/15/20 64 · livraison 41 · photos réelles 26 · pose. Les questions sont reformulées.
- **Attirantes** : budgets chiffrés sur des cas réels (10 m × 8 m, mur 40 m × 2,5 m, tafo
  100 m², étage 60 m²), vraies photos de l'atelier en collage, pose en 3 épisodes, quiz,
  vocabulaire du chantier, schéma à l'échelle des hourdis 12/15/20.
- Gabarits ajoutés à `fabriquer.py` : `question`, `collage`, `hauteurs`, `note` sous les cartes.
- `verifier.py` refait chaque calcul « A × B = C » (21 dans cette série) ; un total n'est admis
  que s'il sort d'un calcul juste. Une photo ne sert qu'une fois dans la série.
- Commandes : `set HOURDIS_SERIE=serie14` puis `fabriquer.py tout`, `verifier.py`,
  `fabriquer.py planche`, `fabriquer.py cahier` (→ `cahier-14h.html`), `programmer_photos.py`.

## Série de 10:00 — reels EXPLIQUÉS par la voix Abidi (demande d'Andry du 18/09/2026, 22 h 50)

« Crée des reels, et travaille avec les voix malgaches comme Abidi, pour explication » puis
« fais pour 30 j, regarde les bonnes heures pour les publications » : `serie_voix.py`, 30 reels
de 20 à 30 s, du 20/09 au 19/10 à **10:00**.

- **L'heure est mesurée** : 797 messages clients depuis 2025, pics à 10 h, 13 h, 15 h et 18 h,
  2 à 3 fois plus en semaine que le week-end ; les publications de 10 h ont eu 0,96 réaction en
  moyenne (170 publications) contre 0,81 à 18 h et 0,5 à 7 h. 14:00 et 18:00 étaient déjà sur
  des pics.
- **La voix est la chaîne validée à l'oreille**, importée telle quelle : `voix.narration()`
  (N3 du 04/09/2026) et `marketing/atelier/film.py` (musique « tuto » 0.22 en side-chain,
  −14 LUFS). `voix_reels.py` n'ajoute que le lexique de « hourdis » et des sous-titres terre cuite.
- **« hourdis » porte un u** (hors alphabet malgache) : `voix_reels.py essai` le fait dire de
  quatre façons (`essai-prononciation/ESSAI-hourdis-1-2-3-4.mp3`). Le choix d'Andry s'écrit dans
  `prononciation.json` ({"hourdis": "ordy"} par exemple), puis `voix_reels.py tout` refait les
  voix. Sans ce fichier, « ordy » par défaut, NON validé. Mesure du 18/09 : « hourdis » brut
  dure 10,4 s contre ~6 s pour les trois autres — Abidi bute dessus.
- **Nombres** : `{n:3400}` dans le texte ; la voix dit « telo arivo sy efajato », les
  sous-titres et la légende écrivent « 3 400 » (section `## MG` de post.md). Même forme que la
  narration Fonenako validée (« iray hetsy sy roa alina »).
- `voix_reels.py verifier` : alphabet malgache, particule « ve », prix et calculs des écrans,
  voix et sous-titres coupés pareil, photos uniques. Calibré le 18/09 sur 4 fautes glissées
  exprès (c/q/u, question sans ve, calcul faux, prix hors catalogue) : 4 sur 4 attrapées.
- Programmation : `set HOURDIS_SERIE=serie_voix` puis `programmer_reels.py` (journal
  `programmation-reels-voix.json`).
- **19/09 — tranché sur délégation d'Andry (« essaye de trancher les meilleurs »)** :
  « hourdis » se dit **hordy** (`prononciation.json`, raisons écrites dedans) ; 19 reels le
  disent, les 11 autres ne prononcent pas le mot. On **garde trois publications par jour**
  (10 h reel expliqué, 14 h photo, 18 h reel musique) : trois pics mesurés, trois formats,
  et supprimer des reels programmés serait destructif — à revoir après une semaine de mesures.
  L'oreille automatique (whisper-base) ne sait pas lire le malgache (étalonnée sur une
  narration validée : charabia) : elle a écarté des variantes, elle n'a pas choisi seule.
- Fin de série : le 18/10 (trois séries) et le 19/10 (10:00) dépassaient la fenêtre de
  ~29 jours : `programmer-18-octobre.cmd`, à lancer le dimanche 20/09 après 10:00.

## Publications photo de la série de 18:00 — non programmées

La programmation par l'API Graph (jeton de page du profil Hermes `hourdis`, `pages_manage_posts`) a été
**refusée par le classificateur de la session** le 18/09/2026 : elle attend l'ordre explicite d'Andry.
Méthode prévue : `POST /{page}/photos` avec l'affiche, la légende, `published=false` et
`scheduled_publish_time` (18:00 Tana), une par une, en s'arrêtant au premier refus ; puis relecture de
`GET /{page}/scheduled_posts` (texte identique, image présente, bonne heure).

⚠ **Une seule voie doit publier** : sur le VPS, les crons Hermes `hourdis` `calendrier-hebdo`
(5b0556cf3133) et `publier-du-jour` (d2824e3427fc) sont actifs. Ils ne publient qu'après un « OK » d'Andry
à la proposition du lundi, et n'ont jamais rien publié (`published.log` vide). Pendant la série, les mettre
en pause : `docker exec -u hermes hermes hermes --profile hourdis cron pause <id>`.
