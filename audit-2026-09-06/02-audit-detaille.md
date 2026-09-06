# 02 — Audit détaillé par domaine

Chaque constat porte : **ID · criticité** (P0 bloquant, P1 majeur, P2 mineur, P3 amélioration) ·
localisation · preuve · action · correctif · effort (H). Deux notes par domaine : **avant** (le site
en ligne le 06/09/2026) et **après** (le build `dist/` de ce dépôt, mesuré en local par
`tests/smoke_test.py` ; ce qui reste à faire par Andry est marqué). Les preuves numériques viennent
de `tests/mesure_hourdis.py` (Playwright, Pixel 7 émulé et bureau 1366, 3G lent 400 kbit/s + CPU ×4),
de `curl`, d'`openssl` et du listing FTP.

## Tableau des constats (toutes criticités)

| ID | Crit. | Constat | Où | Correctif | H |
|---|---|---|---|---|---|
| F-01 | **P0** | Le formulaire de devis **n'envoie rien** : `handleSubmit` appelle `simulateSubmission` (2 s d'attente) puis affiche « envoyée avec succès ». 0 requête réseau après clic (Playwright). Toutes les demandes depuis le 17/07/2026 sont perdues. | `src/js/main.js` en ligne, classe `ContactForm` | `site/src/js/main.js` : `fetch('/contact.php')`, validation, redirection `/merci`, repli WhatsApp ; `site/contact.php` réécrit | 3 |
| F-02 | **P0** | Les deux scripts d'envoi expédient depuis `hourdismg@hourdismg.artimmomada.com` : **le domaine ne résout plus** (`curl: Could not resolve host`). Même appelés, les e-mails partiraient d'un domaine mort : indésirables ou rejet. | `contact.php`, `send_mail.php` (serveur) | expéditeur `hourdis@fonenako.mg` (SPF + DKIM existants), copie **Telegram** ; boîte à créer dans cPanel (**Q4**) | 1 + Andry |
| F-03 | **P0** | **Le déploiement documenté détruit la production** : `redeploy.sh hourdis` lançait `npm run build` sur le gabarit Bolt (`App.tsx` = « Start prompting… ») ; le dépôt ne contient ni `contact.php`, ni `.htaccess`, ni les WebP, ni les balises OG en ligne. Aucune sauvegarde du site réel hors serveur. | `~/.deploy-sites/redeploy.sh`, dépôt HourdisMG (3 commits) | `site/` = source de vérité, `build.py`, `redeploy.sh` corrigé, gabarit Vite retiré | 4 |
| F-04 | **P0** | **Aucun en-tête de sécurité** : pas de HSTS, pas de CSP, pas de `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`. | en-têtes HTTP de `/` | `site/.htaccess` §5 : HSTS 1 an, CSP stricte sans `unsafe-inline` (le site n'a plus aucun style ni script en ligne, vérifié par le build), nosniff, DENY, referrer, permissions | 1 |
| F-05 | P1 | `Cache-Control: public, max-age=31536000, immutable` sur `src/js/main.js` et `src/styles/main.css` **dont les noms ne changent jamais** : toute correction resterait invisible un an aux visiteurs revenus. | `.htaccess` serveur, en-têtes mesurés | ressources hachées `assets/index-<hash>.css/.js` (build), immutable seulement sur elles | (F-03) |
| F-06 | P1 | Listing Apache sur `/src/`, `/src/js/`, `/src/styles/`, `/image/` ; `/src/App.tsx`, `/package.json`, `/package-lock.json`, `tsconfig*` servis ; 6 originaux JPEG 8000 × 6000 (30 Mo) publics. | listing FTP, `curl` | `Options -Indexes`, `RedirectMatch 404`, `FilesMatch` refusés ; `outils/nettoyage_serveur.py` | 1 |
| F-07 | P1 | **Prix contradictoires** : Hourdis 15 = 3 000 Ar (bible) / 2 800 Ar (site) ; Hourdis 12 = 2 800 / 2 500. Le bot Facebook et le site annoncent des prix différents. | `bible-business.md` ligne « Hourdis 15x33x33 », `index.html` cartes | `site/data/produits.json` = source unique (cartes, tableau, JSON-LD, FAQ) ; valeur à trancher (**Q1**) | 0,5 + Andry |
| F-08 | P1 | Promesses et contenus faux : « Livraison dans tout Madagascar » (bible : Tana et périphérie, 1 500 Ar/km) ; « Mises en œuvre – nos réalisations sur différents chantiers » illustrées par des piles de stock ; photo **Pexels** légendée « Équipe HOURDIS MADAGASCAR sur un chantier » ; « © 2025 ». | `index.html` en ligne, sections À propos, Galerie, Footer | textes réécrits depuis la bible ; section « Livraison et délais » ; galerie « Notre production » ; photo d'atelier ; année automatique | 2 |
| F-09 | P1 | **Catalogue incomplet** : 6 produits affichés sur 13 (tuiles mécanique et écaille, brique repressée, briquette, plaquette, plaquette chinois, tonette absents). | bible vs `index.html` | 8 cartes avec photo + tableau de 5 produits, tous avec calculateur | 1 |
| F-10 | P1 | **Pages manquantes** : mentions légales, politique de confidentialité, FAQ, 404 designée, page de confirmation. | `sitemap.xml` : 1 URL | 5 pages construites (voir 04) | 5 |
| F-11 | P1 | **Aucune mesure, aucune alerte, aucun journal** : pas d'analytics, pas de suivi de disponibilité, pas de trace des demandes. Impossible de savoir si le site sert. | dépôt, serveur | `stat.php` (sans cookie), `leads.jsonl`, `rapport_hebdo.php` (cron cPanel → Telegram), `verifier_en_ligne.py` (quotidien), CI nocturne | 4 |
| F-12 | P1 | Mise en page : de 769 à 1119 px les liens du menu passent sur **2 à 3 lignes** (en-tête 134 px) ; à 1366 px « Contact » touche le bord (conteneur sans marge) ; sur mobile l'en-tête fixe fait **129 px = 15 % de l'écran**. | mesures Playwright 769/820/900/1024/1366, capture mobile | en-tête 64 px mobile / 80 px bureau, burger sous 1120 px, `nav-container` à marges, liens `nowrap` | 2 |
| F-13 | P1 | Dialogues non conformes : **Échap ne ferme pas** le calculateur ; le focus **sort** de la modale au Tab ; la visionneuse ne reçoit pas le focus ; le menu mobile ignore Échap ; le fond reste défilable. | `main.js` classes `Calculator`, `Lightbox`, `Navigation` | élément `<dialog>` natif (`showModal` : piège du focus, Échap, `::backdrop`), retour du focus, Échap sur le menu | 1,5 |
| F-14 | P2 | Cibles tactiles sous 44 px : liens du menu mobile 26 px, contact rapide 35 px, boutons réseaux 40 px, liens de navigation 26 px. | `struct.small44` (6 sur mobile, 12 sur bureau) | `--tap: 44px` sur tous les liens et boutons, menu avec `min-height` | (F-12) |
| F-15 | P2 | Hiérarchie de titres : h1 → h3 (axe `heading-order`, 2 nœuds). | sections Atouts et À propos | h2 visibles ajoutés, h4 → h3 | 0,2 |
| F-16 | P2 | `prefers-reduced-motion` ignoré (animations 0,3 s partout) ; `viewport-fit=cover` absent. | `main.css` | media query qui neutralise transitions et animations ; `viewport-fit=cover` | 0,2 |
| F-17 | P2 | Formulaire : validation `required` seule, aucun message en ligne, pas d'`autocomplete`, pas d'`inputmode`, erreurs non annoncées. | `index.html` formulaire | règles par champ, `aria-invalid`, `aria-describedby`, `autocomplete`, `inputmode`, `role=alert` | (F-01) |
| F-18 | P2 | Calculateur : accepte 1 000 000 000 m² → « 25 200 000 000 000 Ar » ; aucune passerelle vers le devis. | `Calculator.calculate` | plafond 10 000 m², note casse 3-5 %, bouton « Demander un devis pour cette quantité » qui pré-remplit le formulaire | 0,5 |
| F-19 | P2 | `www.` sert la page sans redirection ; sitemap sans `lastmod` ; `favicon.ico` 404 ; image OG 1920 × 1080 en JPEG de 642 Ko. | `curl`, `sitemap.xml` | 301 www → nu ; sitemap généré ; favicon.ico + PNG 32/180/192/512 ; `og-1200x630.jpg` 212 Ko | 0,5 |
| F-20 | P2 | Bandeau 1920 px (306 Ko) servi à tous les téléphones, sans `srcset`. | `hero-image` | `hero-640/960/1920.webp` + `srcset` + `imagesrcset` sur le preload (100 Ko sur mobile) | 0,3 |
| F-21 | P2 | JSON-LD minimal : aucune offre, pas de FAQ, adresse « Antananarivo ». | `<script type=ld+json>` | `hasOfferCatalog` (13 offres, prix MGA), `areaServed`, `priceRange`, `WebSite`, `FAQPage` généré depuis la page FAQ | 0,5 |
| F-22 | P2 | Photos : filigrane « REDMI K20 PRO 48MP » sur le hourdis 15 ; hourdis 12 sans photo propre ; brique creuse 10 illustrée par des briques crues grises. | cartes produits | à refaire par Andry (**Q5**) ; `preparer_images.py` prêt à les intégrer | Andry |
| F-23 | P2 | `npm audit` : 20 vulnérabilités dont 12 hautes (rollup, postcss…) dans des dépendances **jamais livrées**, mais présentes dans le dépôt et dans `redeploy.sh`. | `package-lock.json` | dépendances et gabarit retirés : le site n'a plus aucune dépendance | (F-03) |
| F-24 | P3 | Site en français seulement pour une clientèle qui écrit en malgache sur la page. | — | version MG proposée (05, plan IA) après relecture d'Andry | 6 |
| F-25 | P3 | DMARC `p=none` sur `fonenako.mg` (partagé avec l'application Fonenako). | DNS | passer à `p=quarantine` après 2 semaines de rapports `rua` ; à décider pour les deux sites | 0,5 |
| F-26 | P3 | Aucune preuve sociale : pas de témoignage, pas de photo de chantier livré. | — | demander 3 photos de planchers posés + 2 phrases de clients (checklist J+30) | Andry |
| F-27 | P3 | L'ancienne adresse `hourdismg.artimmomada.com` (domaine perdu) est encore le premier résultat Google. | recherche « hourdis Madagascar » | rien à rediriger ; soumettre `hourdis.fonenako.mg` dans Search Console | 0,3 |
| F-28 | P3 | `contact.php` prenait le sujet depuis `$_POST['subject']` (injection d'en-tête possible en appel direct) ; `send_mail.php` affiche l'adresse expéditeur dans son message d'erreur. | scripts serveur | sujet fixé côté serveur, messages génériques, `send_mail.php` refusé puis effacé | (F-01) |
| F-29 | P2 | À 768 px en émulation mobile, largeur de mise en page 813 px (débordement de 45 px). Élément non isolé avant correction. | `breakpoints[768].scrollWidth` | après correction : 0 débordement de 360 à 1536 px (banc) | (F-12) |
| F-30 | P2 | **NON VÉRIFIÉ** : le bot Hermes `hourdis` (profil marketing, `engagement.py`) répond-il aux messages privés de la page ? Le site envoie vers `m.me/HourdisMG`. Règle du répondeur unique (incident Fonenako du 04/09). | `~/.hermes/profiles/hourdis/cron/jobs.json` | vérifier à la main dans la boîte de la page qui répond ; un seul automate | 0,5 |

---

## 2.1 Performance et Core Web Vitals — poids 12 — **avant 88 · après 95**

| Contrôle | Mesure (mobile, Pixel 7 émulé) | Verdict |
|---|---|---|
| LCP < 2,5 s | **1,44 s** (élément : `p.hero-subtitle`) ; 3G lent : 1,68 s | ✓ |
| INP < 200 ms | non mesurable en laboratoire ; 0 tâche longue, JS 4,7 Ko | ✓ probable, **à confirmer avec le RUM (06)** |
| CLS < 0,1 | **0** (0 décalage, même après défilement complet) | ✓ |
| TTFB < 800 ms | **597 ms** (Tana → serveur Clermont-Ferrand : incompressible en dessous de ~450 ms) | ✓ |
| FCP < 1,8 s | 1,44 s | ✓ |
| Poids première vue < 1,5 Mo, JS < 300 Ko | 430 Ko (8 requêtes), JS 4,7 Ko ; page complète 939 Ko (16 requêtes) | ✓ |
| Images | WebP, dimensions déclarées, lazy hors écran, `fetchpriority=high` sur le bandeau ✓ ; **pas de `srcset`**, bandeau 1920 px de 306 Ko sur mobile (F-20) | −5 |
| Polices | 0 police chargée (pile système) | ✓ |
| Cache, compression, protocole | Brotli, HTTP/2, TLS 1.3 ✓ ; **immutable sur des fichiers non hachés** (F-05) | −7 |
| Code splitting, tiers | sans objet (4,7 Ko) ; 1 domaine tiers (Pexels) | ✓ |
| 3G lent + CPU ×4 | chargement complet 9,7 s, mais contenu visible à 1,7 s : utilisable | ✓ |

Après : bandeau en 3 tailles (100 Ko sur mobile), ressources hachées, 0 domaine tiers, première vue
≈ 207 Ko (build). Reste : `index.html` pèse 61 Ko brut (icônes SVG répétées en ligne ; 13 Ko en
Brotli) — un sprite SVG le ramènerait sous 40 Ko (P3, 1 h).

## 2.2 Sécurité — poids 15 — **avant 48 (P0 ouvert) · après 94**

| Contrôle | Avant | Après |
|---|---|---|
| **[P0]** HTTPS, HSTS, contenu mixte | HTTPS ✓, redirection 301 ✓, **HSTS absent** (F-04), 0 contenu mixte | HSTS `max-age=31536000`. Pas de `preload` : il engagerait `fonenako.mg` et tous ses sous-domaines, décision à prendre avec l'application Fonenako |
| **[P0]** Secrets côté client / dépôt | aucun secret ; mais sources et versions publiques (F-06) | sources retirées, `hourdis-config.php` hors racine web et hors git |
| **[P0]** Authentification, autorisation, IDOR | sans objet (aucun compte) | — |
| **[P0]** Injection | XSS : aucune entrée utilisateur rendue en HTML (calculateur et visionneuse lisent le DOM du site) ✓ ; `contact.php` : `strip_tags` seul, sujet injectable (F-28) | validation stricte, caractères de contrôle retirés, sujet fixé, en-têtes construits côté serveur, `Reply-To` seulement si e-mail valide |
| En-têtes | aucun (F-04) | CSP `default-src 'self'` sans `unsafe-inline` (le build refuse tout `style=`), nosniff, DENY, referrer, permissions, COOP |
| CSRF | formulaire anonyme, sans session : risque nul ; pot de miel présent mais inutile (F-01) | pot de miel + délai minimal 3 s + limite 5/h/IP |
| Upload | sans objet | — |
| Limitation de débit | aucune | 5 envois/heure/IP (`contact.php`), 60/min sur `stat.php` implicite (204 rapide) ; pare-feu o2switch en amont |
| Dépendances | 12 vulnérabilités hautes (F-23), non livrées | 0 dépendance |
| Clés Supabase/Firebase | sans objet | — |
| Bots / spam | honeypot HTML jamais exploité | pot de miel + délai + limite ; pas de CAPTCHA (rien qui bloque un maçon sur 3G) |
| Journaux, erreurs | `send_mail.php` révèle l'expéditeur (F-28) | messages génériques, journal hors racine, IP tronquée |
| Sauvegardes, retour arrière | **aucune copie du site réel** hors serveur (F-03) | git = code ; originaux photo dans `sources-photos/` ; retour arrière = `git checkout` + `redeploy.sh` (< 5 min) ; sauvegarde JetBackup o2switch **NON VÉRIFIÉ — ouvrir cPanel → JetBackup et lancer une restauration de test d'un fichier** |
| E-mails SPF/DKIM/DMARC | `fonenako.mg` : SPF ✓ (`ip4:109.234.166.169`), DKIM `default` ✓, DMARC `p=none` ; **expéditeur sur un domaine mort** (F-02) | expéditeur `hourdis@fonenako.mg` ; DMARC à durcir (F-25) ; **délivrabilité NON VÉRIFIÉE tant que la boîte n'existe pas — test : envoyer un devis, vérifier l'arrivée dans Gmail hors indésirables** |
| Consentement, confidentialité, effacement | pas de cookie (rien à consentir) ✓ ; aucune politique, aucune mention (F-10) | politique de confidentialité, mentions légales, droit d'effacement par e-mail/WhatsApp, mesure sans identifiant, respect de Global Privacy Control |

## 2.3 Design et UX — poids 10 — **avant 67 · après 92**

- Système : jetons couleur/typo/espacement présents (`:root`) mais espacements hors grille et deux
  gris concurrents ; après : palette 1 primaire + 1 accent + neutres, échelle 14/16/18/20/24/32/40,
  grille 4/8, rayons et ombres en jetons (`main.css` en-tête).
- Hiérarchie : un CTA primaire par écran ✓ ; ligne de texte du sous-titre 34ch, paragraphes ≤ 70ch.
- États : chargement ✓ ; **succès fictif, erreur jamais atteinte** (F-01) ; après : succès = page
  merci, erreur = message + 3 boutons de repli, champ invalide = bordure + message + focus.
- Micro-interactions : 180 ms, `reduced-motion` respecté (F-16).
- Mode sombre : fond blanc explicite, non cassé ✓ ; `color-scheme: light` déclaré.
- Formulaires (F-17) corrigés.
- Copywriting (F-08) : contradictions retirées, ton unique (vouvoiement, phrases courtes, chiffres
  sourcés) ; l'orthographe a été relue ; aucun lorem ipsum.
- Comparé à Rector / KP1 / Beton Ouest : le site en ligne « fait 2018 » par l'en-tête massif, la
  navigation qui déborde, les icônes dans des ronds pleins et la galerie sans légende. Le site
  reconstruit tient la comparaison sur mobile (capture `tests/captures/mobile-accueil.jpg`) ; il
  reste en dessous sur la preuve sociale (F-26) et la photo (F-22).
- Identité : favicon, icônes 180/192/512, image de partage 1200 × 630, manifest.

## 2.4 Mobile et responsive — poids 12 — **avant 70 · après 93**

| Contrôle | Avant | Après (banc) |
|---|---|---|
| 360 / 390 / 414 / 768 / 1024 / 1280 / 1536 + paysage 844 × 390 | 0 débordement sauf 768 (F-29) ; navigation 769-1119 sur 2-3 lignes (F-12) | 0 débordement sur les 8 largeurs, en-tête 64/80 px |
| **[P0]** débordement, éléments coupés, superpositions | « Contact » au bord à 1366 ; menu 3 lignes | ✓ |
| Cibles ≥ 44 × 44, espacement 8 px | 6 cibles < 44 sur mobile (F-14) | liens du menu 54 px, contact rapide 44 px, boutons 44 px |
| Navigation mobile | fermeture au tap extérieur ✓, pas d'Échap, bouton menu qui disparaît au défilement | Échap, `aria-expanded`, `aria-controls`, en-tête qui revient dès qu'on remonte, jamais caché menu ouvert |
| Zones sûres | `viewport-fit` absent | `viewport-fit=cover` |
| Zoom | autorisé ✓ | ✓ |
| Tableaux larges | aucun | tableau des 5 produits dans un conteneur à défilement horizontal |
| Fixes/sticky | en-tête 129 px = 15 % | 64 px = 7,6 % |
| Réseau faible | utilisable ✓ | ✓, 207 Ko |
| PWA | rien | manifest + icônes (installable), pas de mode hors ligne (site vitrine : inutile) |
| Appareil réel | **NON VÉRIFIÉ — à tester manuellement : ouvrir le site sur un Android d'entrée de gamme (Chrome) et un iPhone (Safari) ; contrôler le menu, le calculateur, l'envoi du formulaire, la visionneuse** | idem |

## 2.5 Accessibilité WCAG 2.2 AA — poids 8 — **avant 69 · après 92**

- Contraste : tous les textes ≥ 4,5:1 (calculé : `#7A7A7A` 4,29:1 n'est utilisé qu'en grand texte
  ≥ 20 px gras, où 3:1 suffit ; `#B85C38` sur blanc 4,54:1) ; texte blanc sur le bandeau ≈ 4,5:1
  selon la photo (ombre portée ajoutée). Après : axe 0 violation sur `/` et `/faq` (deux contrastes
  corrigés en cours de banc : `.cta-band p` 3,9 → 4,6 ; fil d'Ariane 4,1 → 7,1).
- Clavier : focus visible ✓ ; modales non conformes (F-13) → `<dialog>` natif.
- Sémantique : un h1 ✓, ordre corrigé (F-15), landmarks header/nav/main/footer ✓, listes réelles.
- Alternatives : `alt` présents mais pauvres (« Tuile ») ; Pexels trompeur ; après : alt descriptifs,
  photos décoratives (`alt=""`) sur le bandeau, légendes de galerie.
- Formulaires : labels ✓ ; erreurs annoncées (`role=alert`, `aria-describedby`) après.
- ARIA : `role=dialog aria-modal` sans piège de focus (trompeur) → natif ; `aria-current` sur la
  section visible ; `aria-live` sur le résultat du calcul.
- Langue : `lang="fr"` ✓ ; les mots malgaches des légendes (« maina », « mando ») sont retirés du
  texte visible ou traduits.
- Cibles ≥ 24 px ✓ (WCAG 2.5.8), et ≥ 44 après.
- **Lecteur d'écran : NON VÉRIFIÉ — à tester manuellement avec TalkBack (Android) sur le parcours
  calculateur → devis, et NVDA sur bureau.**
- Déclaration d'accessibilité : pas d'obligation à Madagascar ; non publiée.

## 2.6 SEO, GEO et découvrabilité — poids 8 — **avant 66 · après 90**

- Title 51 c. ✓, description 121 c. (courte) ; après : 61 c. et 158 c., uniques sur 4 pages.
- Canonical ✓, robots ✓, sitemap 1 URL sans `lastmod` (F-19) ; `www` en doublon ; après :
  sitemap 4 URL générées, `noindex` sur merci et 404, 301 www.
- URL propres : `/faq`, `/mentions-legales`, `/confidentialite` (réécriture Apache).
- Données structurées : LocalBusiness minimal → `LocalBusiness` + `HomeAndConstructionBusiness`
  avec `hasOfferCatalog` (13 produits, prix MGA), `areaServed`, `WebSite`, et `FAQPage` (13 Q/R)
  **à valider dans le test des résultats enrichis de Google après mise en ligne** (checklist).
- Open Graph ✓ ; image 1200 × 630 ✓ après ; `og:locale fr_MG`.
- Rendu : HTML statique complet ✓ (0 dépendance au JS pour le contenu et les prix).
- Multilingue : FR seul (F-24) ; pas de redirection par IP ✓.
- GEO : FAQ de 13 questions à réponse directe, `llms.txt`, robots IA autorisés explicitement,
  faits chiffrés (pièces/m², tarif au km, délais) répétés dans FAQ + JSON-LD + llms.txt.
- Search Console / Bing : **NON VÉRIFIÉ — vérifier la propriété (balise HTML ou DNS sur
  fonenako.mg), soumettre le sitemap** (checklist J-1).
- Contenu : 433 mots en ligne → ≈ 1 900 mots sur 4 pages indexables, sans doublon.

## 2.7 Pages nécessaires et contenu — poids 8 — **avant 32 · après 88**

| Page | Avant | Après |
|---|---|---|
| Accueil : proposition de valeur < 5 s, preuve, CTA | valeur ✓, **preuve sociale ✗**, CTA ✓ | 3 engagements chiffrés, galerie de production, CTA + 4 contacts rapides ; témoignages toujours absents (F-26) |
| À propos / confiance | photo Pexels, texte générique | atelier réel, fabrication, clients, ingénieur BTP |
| Contact | formulaire mort, 4 moyens | 5 moyens + formulaire réel + horaires |
| Mentions légales · Confidentialité · Cookies · CGU/CGV | **absentes** | mentions et confidentialité construites (04) ; cookies : sans objet (aucun cookie) ; CGV : sans objet (pas de vente en ligne), prix qualifiés d'indicatifs |
| FAQ | absente | 13 questions (quantités, épaisseur, matériaux, prix, livraison, délais, paiement, devis, remise, pose, erreurs, réseaux) |
| 404 / 500 / maintenance | Apache brut | 404 designée ; 500 sans objet (statique) |
| Confirmation | message fictif | `/merci` : 3 étapes, WhatsApp, retour |
| Statut / incident | sans objet pour une vitrine | `verifier_en_ligne.py` alerte Telegram |
| **Métier** : catalogue, fiche, devis, livraison, réalisations, avis | 6/13 produits, devis mort, livraison fausse, réalisations = stock, 0 avis | 13 produits avec calculateur, devis réel, livraison et délais de la bible, « notre production », avis à collecter |

## 2.8 Fonctionnel et parcours critiques — poids 12 — **avant 80 mais P0 ouvert → BLOQUANT · après 95**

| Parcours | Avant | Après (banc local, `contact.php` simulé) |
|---|---|---|
| 1. Facebook → accueil → appel | ✓ (liens `tel:` corrects) | ✓ + clics mesurés |
| 2. calculateur → devis → confirmation → rappel | **cassé** : F-01, F-02, F-18 | ✓ : calcul 50 m² → 450 pcs, pré-remplissage, POST `/contact.php`, page merci ; **e-mail et Telegram réels NON VÉRIFIÉS jusqu'à la mise en ligne (Q4)** |
| 3. Google → FAQ → contact | pas de FAQ | ✓ |
| 4. partage → aperçu OG | image 1920 × 1080 lourde | image 1200 × 630, à revalider dans le Sharing Debugger Facebook |
| 5. livraison et délais | contradictoire | section dédiée + FAQ |
| Cas limites | 1e9 m² accepté ; double clic non protégé ; caractères spéciaux OK ; réseau coupé → « succès » | plafond, verrou anti-double envoi, délai 15 s, repli WhatsApp avec le texte de la demande |
| E-mails transactionnels | jamais envoyés | 1 e-mail texte UTF-8 + 1 message Telegram ; gabarit dans `contact.php` |
| Console | 0 erreur ✓ | 0 erreur, 0 avertissement (banc) |
| Données de test | aucune | aucune (le banc n'écrit rien en production) |

## 2.9 Qualité technique et code — poids 7 — **avant 44 · après 90**

Avant : gabarit mort, deux scripts d'envoi concurrents, dépôt désynchronisé, README d'un mot, 0
test, 0 CI, dette non listée. Après : `site/` source unique, `build.py` avec 9 garde-fous, banc
Playwright de 26 contrôles, CI GitHub (build + banc à chaque poussée, banc + liens + Lighthouse
chaque nuit), README opérationnel, dette listée ici (F-22, F-24, F-25, F-26, sprite SVG). Reste :
pas de test unitaire sur `build.py` (−5), pas d'environnement de préproduction (le build local +
`--servir` en tient lieu).

## 2.10 Intégrations IA — poids 5 — **avant 25 · après 40 (plan livré, non déployé)**

Rien sur le site. Hors site, le profil Hermes `hourdis` (@Hourdis_bot) rédige les publications
Facebook et répond aux commentaires ; sa bible business est la source des prix. Le plan (05)
propose quatre intégrations classées par valeur ; la première (assistant devis sur le site, borné
au catalogue) porterait le domaine à ≈ 80.

## 2.11 Amélioration continue — poids 6 — **avant 0 · après 47**

Livré : contrôle quotidien avec alerte, mesure sans cookie, rapport hebdomadaire Telegram, CI
nocturne (banc, liens, Lighthouse avec budgets). Manquent encore (06) : RUM des vitals réels,
disponibilité toutes les minutes (UptimeRobot), retour utilisateur, agent d'amélioration hebdo,
suivi Search Console, sauvegarde mensuelle testée des demandes.

## 2.12 Ops, lancement, résilience — poids 5 — **avant 40 · après 85**

DNS propre (A 109.234.166.169, TTL 86 400 ; abaisser à 3 600 n'est utile qu'avant un changement
d'hébergeur). Certificat Let's Encrypt renouvelé par o2switch (échéance 15/10/2026, surveillée par
`verifier_en_ligne.py`). Pas de préproduction ni de test de charge : site statique sur mutualisé,
un pic Facebook de 500 visites/h reste négligeable ; `contact.php` est limité par IP. Plan de
bascule, incident et J+1/J+7/J+30 : 07. Coûts : hébergement o2switch mutualisé partagé avec
Fonenako (déjà payé), domaine `fonenako.mg` (déjà payé), Telegram 0, GitHub Actions 0 (dépôt public
ou quota gratuit) → **0 Ar de coût additionnel**. Propriété : tout (hébergeur, DNS, dépôt, page
Facebook, bot) est rattaché à Andry seul (−5) ; documenter les accès dans un coffre partagé.
