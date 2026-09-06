# 00 — Fiche d'identité du site hourdis.fonenako.mg

*Audit pré-lancement du 06/09/2026. Tout ce qui suit a été lu sur le site en ligne, sur le serveur
(FTP en lecture seule), dans le dépôt `parpaing25/HourdisMG` et dans la bible business du bot
Hourdis (`~/.hermes/profiles/hourdis/bible-business.md`, fournie par Andry le 16/07/2026).*

## But et conversion

- **But principal** : vendre des hourdis, briques creuses et tuiles en terre cuite fabriqués à
  Ambohimanga Rova à des chantiers d'Antananarivo et de sa périphérie.
- **Action de conversion n° 1** : la **demande de devis**, par téléphone, WhatsApp, Messenger ou
  formulaire. Il n'y a ni vente en ligne, ni paiement, ni compte client : le site doit produire un
  rappel téléphonique avec un prix, une quantité et une date de livraison.
- **Conversion n° 2** : le calculateur de quantités (surface → pièces → budget), qui prépare le devis.

## Type

Vitrine commerciale locale, **une page** en ligne au moment de l'audit (plus `robots.txt`,
`sitemap.xml`, deux scripts PHP jamais appelés). Pas d'espace connecté, pas d'API.

## Audiences

| Segment | Ce qu'il cherche | Appareil et contexte |
|---|---|---|
| Particulier qui construit sa maison | un prix clair, « combien de pièces pour X m² », la livraison | Android d'entrée ou de milieu de gamme, 3G/4G irrégulière, données payées au Mo |
| Maçon, chef de chantier | disponibilité, délai, prix par pièce, remise volume | téléphone, souvent depuis un groupe Facebook construction |
| Petite entreprise BTP | catalogue complet, devis écrit | téléphone et ordinateur |

Langues : le site est en français ; les échanges (page Facebook, Messenger) se font en français
et en malgache. Paiement : espèces et mobile money, hors ligne. **Hypothèse** : plus des trois
quarts des visites viendront de Facebook sur mobile (c'est le canal d'acquisition de la page
`HourdisMG`, qui publie deux fois par jour) ; le site n'a aucune mesure d'audience pour le confirmer.

## Parcours critiques (testés en phase 2)

1. **Facebook → accueil → prix → appel ou WhatsApp** (mobile, 3G) : le plus fréquent.
2. **Accueil → calculateur → « demander un devis » → formulaire → confirmation → rappel** : le
   parcours à valeur ; **cassé au moment de l'audit** (le formulaire n'envoie rien, voir 02 · F-01).
3. **Google « hourdis prix Madagascar » → produits ou FAQ → contact** : acquisition hors Facebook.
4. **Lien partagé sur Messenger ou dans un groupe → aperçu (Open Graph) → page** : le partage est
   le bouche-à-oreille du marché.
5. **Client rappelé → section livraison et délais → confirmation de commande** : fixer les
   attentes (30 jours de production, 1 500 Ar/km) avant qu'elles ne déçoivent.

## Modèle économique et ce qui coûte de l'argent si ça casse

Vente de matériaux à la pièce. Ordre de grandeur d'une commande : un plancher de 50 m² en hourdis
15 = 450 pièces × 2 800 Ar = **1 260 000 Ar** hors livraison (calcul depuis les prix affichés). Ce
qui coûte :

- **Un formulaire qui ne part pas** = 100 % des demandes du formulaire perdues, sans que personne
  ne le sache (aucun journal). C'est l'état constaté depuis la mise en ligne du 17/07/2026.
- **Un prix faux affiché** = une négociation qui commence mal, ou une vente à perte.
- **Une promesse fausse** (« livraison dans tout Madagascar », « stock disponible ») = déception,
  avis négatif, temps perdu au téléphone.
- **Un site lent sur 3G** = le visiteur Facebook repart avant le prix.

## Stack détectée et maturité

| Couche | Constat | Preuve |
|---|---|---|
| Front | HTML statique + `src/styles/main.css` + `src/js/main.js` **servis bruts**, sans build ; le dépôt est un gabarit Vite + React (Bolt) dont `App.tsx` contient encore « Start prompting… » | `/src/App.tsx` répond 200 en ligne ; `git log` : 3 commits, dernier « Added Fandorana brique creuse.jpg » |
| Serveur | Apache o2switch (`Server: o2switch-PowerBoost-v3`), HTTP/2, Brotli, TLS 1.2/1.3, Let's Encrypt jusqu'au 15/10/2026 | en-têtes HTTP, `openssl s_client` |
| Back | `contact.php` (mail() depuis `hourdismg@hourdismg.artimmomada.com`, domaine qui **ne résout plus**) et `send_mail.php`, jamais appelés par le JavaScript | FTP, `main.js` ligne `simulateSubmission` |
| Base de données, auth, paiement | aucun | — |
| Analytics, monitoring, CI, tests | **aucun** | dépôt et serveur |
| Déploiement | `redeploy.sh hourdis` lançait `npm run build` sur le gabarit Bolt : **aurait mis en ligne une page vide** | `~/.deploy-sites/redeploy.sh` avant correction |
| Dépôt ≠ production | le serveur porte des fichiers absents du dépôt (`contact.php`, `send_mail.php`, `.htaccess`, `image/*.webp`, balises OG, JSON-LD) ; le dépôt porte des images Pexels que le site n'utilise plus | `diff` index.html en ligne / dépôt : 67 lignes CSS, 39 lignes JS, en-tête HTML entier |

Maturité : **prototype mis en ligne**. Zéro test, zéro CI, zéro sauvegarde vérifiée du code réel.

## Contexte réglementaire

- **Madagascar** : loi n° 2014-038 sur la protection des données à caractère personnel (CMIL) ;
  loi n° 2014-024 sur les transactions électroniques (identification du professionnel : nom,
  adresse, NIF/STAT, moyens de contact). Le site n'avait ni mentions légales ni politique de
  confidentialité.
- **RGPD** : non applicable en pratique (clients malgaches), mais suivi comme bonne pratique : pas
  de cookie, pas de traceur, donc **pas de bandeau à afficher** ; droits d'accès et d'effacement
  décrits.
- **TVA, CGV** : pas de vente en ligne, donc pas de CGV obligatoires ; en revanche les prix affichés
  doivent être qualifiés d'indicatifs et le devis écrit désigné comme seul engagement.

## Références du secteur (pour calibrer « 2026 »)

| Référence | Ce qu'elle fait mieux | Ce qu'on lui prend |
|---|---|---|
| **Beton Ouest** (betonouest.mg, Odoo) — concurrent direct, hourdis 12/16/20 × 20 × 50 à 4 100 – 4 800 Ar | catalogue produit par produit avec panier | des fiches produit avec dimensions, prix, pièces par m² ; leur certificat TLS est expiré, leur site est inaccessible aux navigateurs stricts : une faiblesse à ne pas reproduire |
| **Rector** (rector.fr) — leader français du plancher poutrelles-hourdis | documentation technique, calculateurs, guides de pose | le calculateur lié au devis, la FAQ technique (entraxe, portée, étaiement) |
| **KP1** (kp1.fr) | configurateur de plancher, contenu pédagogique | la structure « choisir selon charge / portée / isolation / budget », le contenu GEO |
| Local, SEO : gcm.mg (guide construction), polytech.mg (article « dimensions hourdis ») | ils occupent les requêtes informationnelles | la FAQ doit répondre mieux qu'eux à « combien de hourdis par m² » |

## Hypothèses retenues

1. Le catalogue et les prix de la bible business (16/07/2026) sont la vérité commerciale, sauf
   pour les deux prix où le site publié diffère (voir Q1) : le site corrigé garde les prix
   **publiés** en attendant l'arbitrage.
2. Les zones, tarifs et délais de livraison de la bible (confirmés le 12/08/2026) remplacent le
   « livraison dans tout Madagascar » du site.
3. Le numéro 032 47 041 43 a WhatsApp (Q3) ; sinon le bouton est retiré en une ligne.
4. Une boîte `hourdis@fonenako.mg` peut être créée dans cPanel (le domaine a SPF et DKIM) : c'est
   l'expéditeur des e-mails de devis.
5. Le site reste en français ; une version malgache est proposée en amélioration (plan IA), à
   faire relire par Andry avant mise en ligne.

## Questions bloquantes (5)

| # | Question | Pourquoi elle bloque |
|---|---|---|
| **Q1** | **Prix du Hourdis 15 et du Hourdis 12** : bible 3 000 / 2 800 Ar, site 2 800 / 2 500 Ar. Lequel est vrai ? | Un des deux canaux publics ment aux clients depuis juillet. Un seul champ à changer dans `site/data/produits.json`. |
| **Q2** | **Identité légale** : dénomination, forme juridique, NIF, STAT, RCS, adresse ; modes de paiement et acompte (FAQ). | Les mentions légales et la FAQ portent des cases « À COMPLÉTER » visibles tant qu'elles ne sont pas remplies. |
| **Q3** | Le **032 47 041 43 est-il sur WhatsApp** ? | Trois boutons WhatsApp pointent dessus, dont le repli du formulaire quand le réseau tombe. |
| **Q4** | Accord pour **créer `hourdis@fonenako.mg`** dans cPanel et pour recevoir les devis **sur Telegram** (@Hourdis_bot) en plus de Gmail ? | Sans cela, les e-mails partent d'un domaine mort et finissent en indésirables ; Telegram est le canal qui réveille le téléphone. |
| **Q5** | **Trois photos à refaire** : le hourdis 12 n'a pas de photo (celle du 15 est réutilisée), la photo du hourdis 15 porte le filigrane « REDMI K20 PRO », la photo de la brique creuse 10 montre des briques crues (grises) et non le produit fini. | Ce sont les trois cartes que le client regarde avant d'appeler. |
