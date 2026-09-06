# 03 — Corrections : où est chaque correctif

Les correctifs sont **appliqués** dans `site/` (source), pas livrés en patchs à côté : le build et le
banc les vérifient. Ce dossier dit, constat par constat (P0 et P1), quel fichier porte la
correction et l'extrait qui compte. Le diff complet : `git diff 5d749d5..HEAD` sur la branche
`audit/pre-lancement-2026-09`.

| ID | Fichier(s) | Ce qui a changé |
|---|---|---|
| F-01 formulaire simulé | `site/src/js/main.js` § *Formulaire de devis* ; `site/contact.php` ; `site/merci.html` | `fetch(form.action, {method:'POST', body: FormData, headers:{Accept:'application/json'}})` ; 200 + `{ok:true}` → `/merci` ; sinon message + repli WhatsApp/appel/Messenger avec le texte de la demande ; sans JavaScript le formulaire poste normalement et `contact.php` redirige en 303 |
| F-02 expéditeur mort | `site/contact.php` (`from_email`), `outils-serveur/hourdis-config.exemple.php` | `hourdis@fonenako.mg` par défaut, surchargeable hors racine web ; enveloppe `-f` ; notification Telegram ; journal `leads.jsonl` : **aucune demande ne se perd même si l'e-mail échoue** |
| F-03 déploiement destructeur | `build.py`, `site/`, `~/.deploy-sites/redeploy.sh` (cas `hourdis`), `.gitignore`, `README.md` | `site/` → `dist/` sans npm ; gabarit Vite retiré du dépôt ; le script de déploiement appelle `python build.py` et refuse un build en échec |
| F-04 en-têtes de sécurité | `site/.htaccess` §5 | HSTS, CSP stricte, nosniff, X-Frame-Options, Referrer-Policy, Permissions-Policy, COOP ; `build.py` refuse tout `style=` en ligne pour que la CSP tienne |
| F-05 cache immutable sur fichiers fixes | `build.py` (`hacher`), `site/.htaccess` §5 | `assets/index-<sha256:8>.css/.js` ; `immutable` limité à `.css/.js` (tous hachés), images 30 jours, HTML/PHP `no-cache` |
| F-06 listing et sources exposées | `site/.htaccess` §3, `outils/nettoyage_serveur.py` | `Options -Indexes`, `RedirectMatch 404` sur `.git .bolt node_modules project cgi-bin src/*` hors css/js, `FilesMatch` refusé sur configs/sources/journaux ; nettoyage à blanc puis `--executer` |
| F-07 prix contradictoires | `site/data/produits.json`, `build.py` (`rendre_produits`) | une seule source injectée dans les cartes, le tableau, le JSON-LD et la FAQ ; l'alerte Q1 est écrite dans le fichier lui-même |
| F-08 promesses fausses | `site/index.html` (sections `#livraison`, `#production`, `#a-propos`, pied de page), `site/_partials/footer.html` | zones, tarif au km, délais de la bible ; « Notre production » ; photo d'atelier `apropos-atelier.webp` ; année calculée |
| F-09 catalogue incomplet | `site/data/produits.json`, `build.py` | 4 catégories, 13 produits, calculateur sur chacun (`pcs_m2` par produit ou hérité) |
| F-10 pages manquantes | `site/faq.html`, `mentions-legales.html`, `confidentialite.html`, `merci.html`, `404.html`, `_partials/` | voir 04 |
| F-11 aucune mesure | `site/stat.php`, `site/src/js/main.js` § *Mesure*, `outils-serveur/rapport_hebdo.php`, `outils/verifier_en_ligne.py`, `.github/workflows/qualite.yml` | événements anonymes → SQLite hors racine ; rapport samedi 07:00 Telegram ; contrôle quotidien ; CI nocturne |
| F-12 mise en page en-tête | `site/src/styles/main.css` § *En-tête*, `site/_partials/header.html` | `--header-h` 64/80 px, burger sous 1120 px, liens `nowrap`, conteneur 1200 px à marges, libellés courts |
| F-13 dialogues | `site/index.html` (`<dialog id="calculatorModal">`, `<dialog id="lightbox">`), `main.js` § *Dialogues* | `showModal()` : focus piégé, Échap, fond inerte ; retour du focus ; Échap sur le menu |

Extraits essentiels :

```php
// site/contact.php — ce qui garantit qu'une demande n'est jamais perdue
$okMail     = @mail($CONFIG['to_email'], $sujet, $corps, implode("\r\n", $entetes), '-f' . $CONFIG['from_email']);
$okTelegram = /* sendMessage via l'API Bot, 6 s de délai */;
@file_put_contents($d . '/leads.jsonl', json_encode([...]) . "\n", FILE_APPEND | LOCK_EX);
if ($okMail || $okTelegram) { repondre(true, ''); }
```

```apache
# site/.htaccess — la CSP tient parce que le site n'a plus aucun style ni script en ligne
Header always set Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; form-action 'self'; frame-ancestors 'none'; base-uri 'self'; object-src 'none'; upgrade-insecure-requests"
```

```python
# build.py — les garde-fous qui refusent le build
"style=" en ligne · lien interne cassé · ancre absente · ≠ 1 h1 · img sans alt · title hors 20-65 · description hors 100-165 · marqueur oublié · photo de banque d'images · première vue > 500 Ko
```

## Ce qui n'est PAS corrigé par le code (décision ou action d'Andry)

- **Q1** prix Hourdis 15 / 12 → `site/data/produits.json`, champ `prix`.
- **Q2** identité légale → `site/mentions-legales.html`, cases « À COMPLÉTER » ; acompte → `site/faq.html` (#paiement).
- **Q3** WhatsApp sur le 032 → sinon retirer `.is-whatsapp` et le repli WhatsApp dans `main.js`.
- **Q4** boîte `hourdis@fonenako.mg` + `hourdis-config.php` sur le serveur.
- **Q5** trois photos → `sources-photos/`, `outils/preparer_images.py`.
- F-25 DMARC, F-26 témoignages, F-30 répondeur unique de la page Facebook.
