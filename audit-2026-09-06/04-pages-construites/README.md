# 04 — Pages construites

Toutes vivent dans `site/`, partagent l'en-tête et le pied de page (`site/_partials/`), la feuille
de style et le script uniques, et passent le build et le banc. Les URL sont propres (`/faq`) grâce
au `.htaccess` ; le serveur local de `build.py --servir` imite la règle.

| Page | URL | Rôle | SEO | Contenu à compléter |
|---|---|---|---|---|
| `faq.html` | `/faq` | 13 questions en 3 groupes (quantités et choix ; commande, livraison, paiement ; pose et technique). Tableau de prix injecté depuis `produits.json`. JSON-LD **FAQPage** généré par le build depuis les `<details>`. Bandeau d'appel au devis. | title 59 c., description 158 c., canonical, OG | modes de paiement et acompte (#paiement, case visible) |
| `mentions-legales.html` | `/mentions-legales` | éditeur, hébergeur (o2switch), propriété intellectuelle, prix indicatifs, responsabilité, données, droit applicable (lois 2014-024 et 2014-038), date de mise à jour automatique | `noarchive` | dénomination, forme, NIF, STAT, RCS, adresse, responsable de publication (7 cases « À COMPLÉTER » surlignées jaune : elles se voient, on ne peut pas les oublier) |
| `confidentialite.html` | `/confidentialite` | résumé « en une minute », formulaire (données, finalité, destinataires, durée 24 mois, sécurité), mesure d'audience sans cookie, liens Meta, droits (accès, rectification, effacement, CMIL), hébergement, mise à jour | `noarchive` | aucun |
| `merci.html` | `/merci` | confirmation réelle : 3 étapes (rappel, devis, validation), WhatsApp pré-rempli, appel, retour. Cible de l'événement `devis_envoye`. | `noindex` | aucun |
| `404.html` | ErrorDocument 404 et 403 | code, titre, 3 boutons (prix, FAQ, devis), téléphone | `noindex` | aucun |
| **Accueil reconstruit** `index.html` | `/` | bandeau + preuves ; contact rapide ×4 ; 3 engagements ; **13 produits** (8 cartes + tableau) avec calculateur ; « Notre production » (6 photos réelles légendées) ; **Livraison et délais** (nouvelle section) ; Comment choisir + 3 familles ; Pourquoi l'hourdis ; À propos (photo d'atelier) ; aperçu FAQ ; contact (5 moyens) + formulaire réel | title 61 c., description 158 c., JSON-LD LocalBusiness + 13 offres + WebSite, OG 1200 × 630 | Q1, Q3, Q5 |

Fichiers annexes construits : `robots.txt` (robots IA autorisés, scripts exclus), `llms.txt`,
`manifest.webmanifest`, `favicon.ico`, `icon-32/180/192/512.png`, `image/og-1200x630.jpg`,
`sitemap.xml` (généré, 4 URL avec `lastmod`).

## Ce qui n'a pas été construit, et pourquoi

- **Version malgache** : la règle du dépôt Fonenako impose la relecture d'Andry sur tout texte
  malgache avant rendu ; un gabarit `index.mg.html` serait un faux livrable. Plan et coût dans 05.
- **Témoignages / réalisations** : pas de matière vérifiable (aucune photo de chantier livré,
  aucun avis client sourcé). Inventer une preuve sociale serait pire que son absence (F-26).
- **CGV, page cookies** : sans objet (pas de vente en ligne, pas de cookie).
