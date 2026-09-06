# HOURDIS MADAGASCAR — hourdis.fonenako.mg

Site vitrine du fabricant de hourdis, briques creuses et tuiles en terre cuite (Ambohimanga Rova,
Antananarivo). **Site statique** : HTML, CSS, JavaScript sans dépendance, deux scripts PHP
(formulaire de devis, mesure d'audience). Hébergé chez o2switch, déployé par FTP atomique.

Audit pré-lancement du 06/09/2026 : `audit-2026-09-06/` (fiche d'identité, cartographie, audit
détaillé, corrections, plan IA, amélioration continue, checklist de lancement, synthèse).

## Où est quoi

| Dossier / fichier | Rôle |
|---|---|
| `site/` | **La source du site.** `index.html`, pages (`faq`, `mentions-legales`, `confidentialite`, `merci`, `404`), `_partials/` (en-tête, pied de page), `src/styles/main.css`, `src/js/main.js`, `image/`, `contact.php`, `stat.php`, `.htaccess`, `robots.txt`, `llms.txt`, `manifest.webmanifest`, icônes |
| `site/data/produits.json` | **La seule source des prix et du catalogue.** Le build l'injecte dans les cartes, le tableau, le JSON-LD et la FAQ |
| `build.py` | `site/` → `dist/` : partiels, produits, hash des ressources (`assets/index-<hash>.css/.js`), sitemap, puis **garde-fous** (style en ligne, liens cassés, h1, alt, titres, budget de poids). `--servir` pour regarder en local |
| `tests/smoke_test.py` | Banc Playwright : pages, console, mobile 390, menu, calculateur, visionneuse, formulaire, 7 points de rupture, axe-core |
| `outils/preparer_images.py` | Originaux → WebP légers, icônes, image de partage |
| `outils/verifier_en_ligne.py` | Contrôle quotidien de la production, alerte Telegram |
| `outils/nettoyage_serveur.py` | Retire du serveur ce que le build ne contient pas (à blanc par défaut) |
| `outils-serveur/` | À copier **hors racine web** sur o2switch : `hourdis-config.exemple.php`, `rapport_hebdo.php` |
| `.github/workflows/qualite.yml` | CI : build + banc à chaque poussée ; chaque nuit banc + liens + Lighthouse contre la prod |
| `bot-hourdis/` | Bot de veille web (port 8761), indépendant du site |

## Travailler

```powershell
python build.py --servir          # construit et sert http://127.0.0.1:8765
python tests/smoke_test.py        # banc contre le serveur local
python tests/smoke_test.py https://hourdis.fonenako.mg   # banc contre la prod (rien n'est envoyé)
```

Changer un prix : `site/data/produits.json`, puis `python build.py`. Changer un texte : la page
dans `site/`. Ajouter une photo : l'original dans `sources-photos/` (hors git), une ligne dans
`outils/preparer_images.py`, puis `python outils/preparer_images.py sources-photos`.

## Déployer

```bash
bash ~/.deploy-sites/redeploy.sh hourdis
```

`redeploy.sh` appelle `python build.py` (jamais npm pour ce site), puis `ftp_deploy_atomique.py` :
envoi de tout, bascule d'`index.html` en dernier, nettoyage des orphelins d'`assets/`, vérification
en ligne du bundle et de son type MIME. **Un déploiement n'est fini que vérifié** : le script sort en
code 3 sur un écart. Puis `python outils/verifier_en_ligne.py`.

Première mise en ligne de cette version : suivre `audit-2026-09-06/07-checklist-lancement.md`
(boîte `hourdis@fonenako.mg` à créer dans cPanel, `hourdis-config.php` à poser hors racine web,
nettoyage du serveur après vérification).

## Ce qui n'est plus là

Le dépôt a démarré comme un gabarit Vite + React (Bolt) jamais utilisé : la page servie en
production a toujours été `index.html` + `src/styles/main.css` + `src/js/main.js`, bruts. Le gabarit
(`App.tsx`, `main.tsx`, Tailwind, tsconfig, `package.json`) a été retiré le 06/09/2026 : il
n'entrait pas dans le site et un `npm run build` l'aurait remplacé par une page vide.
