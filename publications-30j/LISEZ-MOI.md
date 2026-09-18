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

## Programmation — en attente

La programmation par l'API Graph (jeton de page du profil Hermes `hourdis`, `pages_manage_posts`) a été
**refusée par le classificateur de la session** le 18/09/2026 : elle attend l'ordre explicite d'Andry.
Méthode prévue : `POST /{page}/photos` avec l'affiche, la légende, `published=false` et
`scheduled_publish_time` (18:00 Tana), une par une, en s'arrêtant au premier refus ; puis relecture de
`GET /{page}/scheduled_posts` (texte identique, image présente, bonne heure).

⚠ **Une seule voie doit publier** : sur le VPS, les crons Hermes `hourdis` `calendrier-hebdo`
(5b0556cf3133) et `publier-du-jour` (d2824e3427fc) sont actifs. Ils ne publient qu'après un « OK » d'Andry
à la proposition du lundi, et n'ont jamais rien publié (`published.log` vide). Pendant la série, les mettre
en pause : `docker exec -u hermes hermes hermes --profile hourdis cron pause <id>`.
