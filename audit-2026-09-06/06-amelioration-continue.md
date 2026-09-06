# 06 — Amélioration continue

Objectif : que le site dise lui-même quand il casse, ce qu'il rapporte, et quoi améliorer, sans
qu'Andry ait à l'ouvrir. Ce qui est **livré** est dans le dépôt ; ce qui est **à installer** tient
en une commande ou un clic ; ce qui est **proposé** a son coût.

## 1. Observabilité

| Besoin | État | Comment |
|---|---|---|
| Disponibilité, chaque minute, alerte téléphone | **à installer** (5 min) | UptimeRobot gratuit : moniteur HTTP(s) sur `https://hourdis.fonenako.mg/` avec mot-clé `Hourdis Madagascar`, intervalle 5 min (1 min en payant), alerte e-mail + webhook Telegram (`https://api.telegram.org/bot<jeton>/sendMessage?chat_id=<id>&text=Hourdis%20DOWN`) |
| Contrôle profond quotidien (bundle servi, MIME, formulaire vivant, en-têtes, certificat, TTFB) | **livré** : `outils/verifier_en_ligne.py` + `verifier_en_ligne.cmd` | Planificateur de tâches Windows, 07:30, ou GitHub Actions nocturne (déjà dans `qualite.yml`) ; alerte Telegram sur défaut seulement |
| Erreurs front | sans objet (4 Ko de JS, 0 dépendance) ; `devis_erreur` est compté dans `stat.php` avec le code HTTP | rapport hebdo |
| Erreurs back | `hourdis-data/contact.log` (mail ok/KO, telegram ok/KO, robots, limites) | lu par `rapport_hebdo.php` ; à surveiller : une suite de « mail KO » = boîte cPanel supprimée ou quota |
| RUM des Core Web Vitals réels | **proposé** (1 h) | 25 lignes dans `main.js` : `PerformanceObserver` LCP/CLS/INP → `stat.envoyer('vitals', {x: 'lcp=1440;cls=0;inp=120'})` sur `visibilitychange` ; `rapport_hebdo.php` calcule le 75e percentile |

## 2. Analytics respectueux et exploitables

**Livré** : `stat.php` + `main.js` enregistrent, sans cookie ni IP, les événements `page`,
`clic_tel`, `clic_whatsapp`, `clic_messenger`, `clic_email`, `calc_ouvert` (produit), `calc_vers_devis`,
`devis_envoye`, `devis_erreur`, avec page, domaine d'origine, largeur d'écran, langue, famille
d'appareil. `rapport_hebdo.php` (cron cPanel samedi 07:00) envoie sur Telegram : pages vues et
variation, appareils, origines, prises de contact et **taux de conversion**, entonnoir calculateur →
devis, demandes reçues avec l'état des deux canaux. Chaque chiffre est recalculé depuis
`stats.sqlite` et `leads.jsonl`, jamais repris d'un rapport précédent.

Installation (cPanel → Tâches cron) :

```
0 7 * * 6  /usr/local/bin/php /home/<compte>/hourdis-outils/rapport_hebdo.php
```

## 3. Qualité en continu

**Livré** dans `.github/workflows/qualite.yml` :

- à chaque poussée : `build.py` (9 garde-fous) puis `tests/smoke_test.py` sur le build (26
  contrôles : pages, console, mobile, menu, calculateur, visionneuse, formulaire, 8 largeurs,
  axe-core) ; captures en artefact 14 jours ;
- chaque nuit 04:17 : le même banc **contre la production** (formulaire intercepté), `verifier_en_ligne.py`,
  liens cassés (lychee) et **Lighthouse CI avec budgets bloquants** (`lighthouserc.json` :
  performance ≥ 0,90, accessibilité ≥ 0,95, LCP ≤ 2,5 s, CLS ≤ 0,1, TBT ≤ 200 ms).

Dépendances : le site n'en a plus ; pour les actions GitHub, ajouter `.github/dependabot.yml` :

```yaml
version: 2
updates:
  - package-ecosystem: github-actions
    directory: /
    schedule: { interval: monthly }
```

## 4. Retour utilisateur

**Proposé** (1 h) : sous chaque réponse de la FAQ, « Cette réponse vous a aidé ? Oui / Non », qui
envoie `stat.envoyer('faq_utile', {x: id + ':' + oui|non})` ; le rapport hebdo liste les questions
les moins utiles. Après un devis, sur `/merci` : « Qu'est-ce qui vous a décidé ? » (3 cases :
prix, livraison, conseil). Pas d'enregistrement de session : inutile sur une page, et coûteux en
données pour le visiteur.

## 5. Expérimentation

Pas d'infrastructure A/B : à moins de 1 000 visites par semaine, aucun test ne serait
significatif. Les variantes se décident sur le rapport hebdo (par exemple, si `clic_whatsapp` >
`clic_tel`, remonter WhatsApp en premier) et se déploient en 5 minutes.

## 6. Agent d'amélioration hebdomadaire (proposé, 4 h)

Le dimanche, un cron du pont Claude Code (ou une routine `schedule`) lit : le rapport Telegram de
la veille, `leads.jsonl` (motifs de demande), l'export Search Console (requêtes, positions), les
échecs du banc nocturne. Il produit **3 actions priorisées** avec le fichier à modifier, et pour les
plus simples (texte de FAQ, alt, description, ajout d'une question posée trois fois par des clients)
une **branche `amelioration/<date>`** avec la modification, le build et le banc passés ; Andry
fusionne ou refuse en un message. Jamais de déploiement sans son accord.

## 7. SEO et GEO en continu

- Search Console : export hebdo CSV des requêtes et positions dans `hourdis-data/` (à la main
  le premier mois, puis API) ; alerte si une page perd > 30 % d'impressions sur 4 semaines.
- Citations IA : une fois par mois, poser 5 questions à ChatGPT, Gemini et Perplexity (« combien de
  hourdis par m² à Madagascar », « prix hourdis Antananarivo ») et noter si le site est cité ;
  ajuster `llms.txt` et la FAQ.
- Sitemap : régénéré à chaque build (`lastmod` = date du build).

## 8. Sauvegardes et restauration

| Quoi | Où | Test |
|---|---|---|
| Code et contenu | GitHub `parpaing25/HourdisMG` (branche + `main` après fusion) | `git clone` + `python build.py` = site complet en 2 min |
| Originaux photo | `sources-photos/` (PC) + serveur `/image/*.jpg` jusqu'au nettoyage + téléphone d'Andry | copier aussi sur `G:\Mon Drive` une fois |
| Demandes de devis et statistiques (`hourdis-data/`) | serveur o2switch, hors racine web | **cron cPanel mensuel** : `0 3 1 * * tar czf /home/<compte>/sauvegardes/hourdis-data-$(date +\%Y\%m).tgz /home/<compte>/hourdis-data` puis téléchargement via le Gestionnaire de fichiers ; **restauration testée** : extraire dans un dossier temporaire et lancer `php rapport_hebdo.php` dessus |
| Sauvegarde hébergeur | JetBackup o2switch (quotidienne, 14 jours) | **NON VÉRIFIÉ** : ouvrir cPanel → JetBackup, restaurer un fichier test, noter la date dans la checklist |
