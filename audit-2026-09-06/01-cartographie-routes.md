# 01 — Cartographie et vérification des chemins

Méthode : `curl` avec un agent utilisateur Android réaliste (o2switch sert une page de blocage 429
au Chromium headless nu), listing FTP du doc root en lecture seule, Playwright sur mobile et bureau.
Mesures du 06/09/2026 entre 05:13 et 05:20 UTC.

## 1. Routes constatées en ligne (avant correction)

| Route | Type | Statut | Temps 1er octet | Problème | Action |
|---|---|---|---|---|---|
| `https://hourdis.fonenako.mg/` | page | 200, `text/html`, 44 Ko (13,6 Ko compressé) | 0,86 s | seule page du site ; titre 51 c., description 121 c., canonical, OG, JSON-LD LocalBusiness présents | conservée, reconstruite (voir 03) |
| `http://hourdis.fonenako.mg/` | redirection | 301 → https | 0,37 s | correct | — |
| `https://www.hourdis.fonenako.mg/` | doublon | **200** (même page, pas de redirection) | 0,83 s | contenu dupliqué ; le certificat couvre bien `www` | 301 vers l'hôte nu (`.htaccess`) |
| `/index.html` | doublon | 200 | — | doublon de `/`, atténué par le canonical | 301 vers `/` (règle générale `*.html` → URL propre) |
| `/robots.txt` | fichier | 200, 73 o | 0,57 s | `Allow: /` + sitemap ; rien sur les robots IA ; `contact.php` ouvert à l'indexation | réécrit |
| `/sitemap.xml` | fichier | 200, 237 o | 0,57 s | 1 URL, pas de `lastmod` | généré par le build : 4 URL + `lastmod` |
| `/contact.php` | script | **200 « Formulaire invalide. »** en GET | 0,60 s | existe mais **jamais appelé** par le JavaScript ; expéditeur `@hourdismg.artimmomada.com` (domaine mort) | remplacé : POST seul, JSON, Telegram, journal |
| `/send_mail.php` | script | (vu par FTP, 2,5 Ko) | — | second script d'envoi, orphelin, même expéditeur mort | refusé par `.htaccess`, à effacer (nettoyage) |
| `/src/` `/src/js/` `/src/styles/` | dossiers | **200, listing Apache** | 0,6 s | `Options +Indexes` par défaut : arborescence visible | `Options -Indexes` + 404 sur `/src/` hors css/js |
| `/image/` | dossier | **200, listing** de 43 fichiers | — | expose 6 originaux JPEG de 8000 × 6000 (30 Mo) et des doublons | listing coupé ; nettoyage des orphelins |
| `/src/App.tsx` `/src/main.tsx` `/package.json` `/package-lock.json` `/tsconfig*.json` `/vite.config.ts` | sources | **200** | — | sources et versions de dépendances publiques (reconnaissance facilitée) | refusés par `.htaccess`, puis effacés |
| `/.bolt/` `/.env` `/.git/` `/.htaccess` | sensibles | 403 | — | protégés par o2switch (aucun `.git` ni `.env` présent, vérifié par FTP) | — |
| `/favicon.ico` | icône | **404** | — | onglet sans icône ; `<link rel=icon>` pointe sur un WebP de 120 px | `favicon.ico` + PNG 32/180/192/512 + manifest |
| `/manifest.json` `/llms.txt` | fichiers | 404 | — | absents | ajoutés (`manifest.webmanifest`, `llms.txt`) |
| `/page-inexistante` | 404 | **404 Apache brut** (355 o, sans style ni lien) | 0,62 s | cul-de-sac | `404.html` designée + `ErrorDocument` |
| `/wp-login.php` | sonde | 503 | — | pare-feu o2switch | — |
| `/cgi-bin/` | dossier | 403 | — | vide (FTP) | protégé, conservé |
| `/project/` | dossier | (vide, FTP) | — | reste d'un ancien import | effacé au nettoyage |
| `/.well-known/acme-challenge/` | Let's Encrypt | — | — | nécessaire au renouvellement | jamais touché |

## 2. Liens sortants et ressources

| Cible | Constat | Action |
|---|---|---|
| `https://www.facebook.com/HourdisMG/` (×2), `https://m.me/HourdisMG` (×2) | la page existe (résultat de recherche « Hourdis Madagascar \| Antananarivo \| Facebook ») ; Facebook refuse les requêtes automatiques (400), donc **NON VÉRIFIÉ automatiquement — à ouvrir à la main** | conservés, `rel="noopener noreferrer"` déjà présent |
| `tel:+261324704143`, `tel:+261337106334`, `mailto:contact.hourdis@gmail.com` | corrects | conservés |
| `https://images.pexels.com/photos/1216589/...` | **photo de banque d'images** présentée comme « Équipe HOURDIS MADAGASCAR sur un chantier », 1 seule ressource tierce (AVIF, 38 Ko) | remplacée par une photo de l'atelier ; le build refuse toute image Pexels/Unsplash |
| Ancres `#accueil #produits #mises-en-oeuvre #comment-choisir #pourquoi-choisir #a-propos #contact` | toutes existent | renommées (`#production`, `#livraison`, `#a-propos`…) ; le build vérifie chaque ancre |
| Polices, scripts tiers | **aucun** (les icônes sont des SVG en ligne) : 0 domaine tiers, bien | conservé |

Total en ligne avant correction : **0 lien interne cassé**, 1 ressource tierce, 1 image trompeuse.

## 3. Redirections

| Test | Résultat |
|---|---|
| http → https | 301 direct, 1 saut |
| www → nu | **absent** (corrigé) |
| barre finale, majuscules | site mono-page : sans objet ; après correction, `/faq/` → `faq.html` (règle `^([a-z0-9-]+)/?$`) |
| ancienne adresse `hourdismg.artimmomada.com` | **le domaine ne résout plus** ; Google l'affiche encore en premier résultat pour « hourdis Madagascar » avec le même titre. Impossible de rediriger (domaine perdu) : Google le retirera de lui-même ; demander l'indexation de `hourdis.fonenako.mg` dans Search Console (07-checklist) |

## 4. Pages orphelines et culs-de-sac

- Orphelins servis mais non liés : `send_mail.php`, le fichier `images` (copie du logo sans extension),
  les originaux JPEG/PNG d'`/image/`, tout `/src/` sauf css et js, les configs Vite.
- Cul-de-sac fonctionnel : le message « Votre demande a été envoyée avec succès ! » après un envoi
  **qui n'a pas eu lieu** (aucune requête réseau, mesuré par Playwright : `form_requests_after_submit = []`).
  Le visiteur n'a ni page de confirmation, ni suite, ni repli.

## 5. Profondeur

Toutes les sections sont à 1 clic (ancres). Après correction : FAQ, mentions légales,
confidentialité à 1 clic depuis l'en-tête ou le pied de page ; « merci » à 1 clic après envoi.

## 6. Routes protégées

Aucune (pas d'authentification). Les deux scripts PHP sont les seules routes à traitement :
`contact.php` et `stat.php` refusent GET (303 / 405), limitent par adresse, ne renvoient jamais de
détail interne.

## 7. Pages système

| Page | Avant | Après |
|---|---|---|
| 404 | Apache brut | `404.html` : titre, trois boutons, numéro de téléphone, `noindex` |
| 403 | page o2switch générique (5,9 Ko) | `ErrorDocument 403 /404.html` |
| 500 | page o2switch (non provoquée) | inchangée ; `contact.php` capte ses propres erreurs et répond un message humain |
| maintenance | aucune | site statique : un déploiement atomique n'a pas de fenêtre d'indisponibilité |
| confirmation | aucune | `merci.html` (étapes suivantes, WhatsApp, retour) |

## 8. Routes après correction (build `dist/`)

| Route | Rôle | Indexable |
|---|---|---|
| `/` | accueil, produits, production, livraison, FAQ (aperçu), contact | oui |
| `/faq` | 13 questions, JSON-LD FAQPage | oui |
| `/mentions-legales`, `/confidentialite` | pages légales | oui (`noarchive`) |
| `/merci` | confirmation après devis | non (`noindex`) |
| `/404.html` | page d'erreur | non |
| `/contact.php` (POST), `/stat.php` (POST) | traitement | non (`robots.txt`) |
| `/assets/index-<hash>.css`, `/assets/index-<hash>.js` | ressources immuables (cache 1 an) | — |
| `/image/*.webp`, `/image/og-1200x630.jpg`, `/icon-*.png`, `/favicon.ico`, `/manifest.webmanifest` | médias | — |
| `/robots.txt`, `/sitemap.xml`, `/llms.txt` | découvrabilité | — |
| `www.` → 301, `*.html` → 301 URL propre, `/src/*`, `/package.json`, `/.bolt/*`, `/project/*` → 404 / refusé | hygiène | — |

Vérifié localement par `tests/smoke_test.py` (0 échec) et `build.py` (0 lien interne cassé,
0 ancre manquante).
