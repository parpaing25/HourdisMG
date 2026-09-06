# 07 — Checklist de lancement (J-7 → J+30)

Cocher dans l'ordre. Les commandes sont pour **Windows PowerShell 5.1** (une commande par ligne,
jamais `&&`) ou pour Git Bash quand c'est indiqué. Responsable : Andry, sauf mention.

## J-7 — Décisions et comptes

- [ ] **Q1** Trancher les prix Hourdis 15 et 12 → éditer `site/data/produits.json` (champ `prix`).
- [ ] **Q2** Remplir les 7 cases « À COMPLÉTER » de `site/mentions-legales.html` et l'acompte dans `site/faq.html` (#paiement).
- [ ] **Q3** Confirmer que le 032 47 041 43 est sur WhatsApp (sinon dire lequel, ou retirer).
- [ ] **Q4** cPanel → Comptes de messagerie → créer `hourdis@fonenako.mg` (mot de passe dans le trousseau).
- [ ] **Q5** Photographier le hourdis 12, le hourdis 15 sans filigrane, la brique creuse 10 finie → `sources-photos/`, adapter `outils/preparer_images.py`, relancer `python outils\preparer_images.py sources-photos`.
- [ ] F-30 Vérifier qui répond aux messages privés de la page Facebook (un seul automate).
- [ ] Créer le compte Google Search Console pour `hourdis.fonenako.mg` (vérification par balise HTML : l'ajouter dans `site/_partials/header.html` est inutile, la mettre dans le `<head>` de `site/index.html`) et Bing Webmaster (import depuis Search Console).

## J-3 — Serveur

- [ ] cPanel → Gestionnaire de fichiers → créer `/home/<compte>/hourdis-outils/` et y déposer `outils-serveur/rapport_hebdo.php`.
- [ ] Copier `outils-serveur/hourdis-config.exemple.php` en `/home/<compte>/hourdis-config.php` (hors racine web) ; renseigner `from_email`, `telegram_token` (celui de @Hourdis_bot), `telegram_chat` (identifiant Telegram d'Andry).
- [ ] cPanel → Tâches cron → `0 7 * * 6 /usr/local/bin/php /home/<compte>/hourdis-outils/rapport_hebdo.php`.
- [ ] cPanel → JetBackup → restaurer un fichier test → noter la date ici : ______.
- [ ] cPanel → Sélecteur PHP → vérifier PHP ≥ 8.1 (le `contact.php` utilise `str_contains`, `never`).

## J-1 — Répétition générale en local (Claude ou Andry)

```powershell
cd "C:\Users\ANDRIANIRINA\Desktop\Site Hourdis"
python build.py
python tests\smoke_test.py http://127.0.0.1:8765
```

(le banc a besoin du serveur : dans une seconde fenêtre `python build.py --servir`).

- [ ] `BUILD OK` et `OK : 0 contrôle(s) en échec`.
- [ ] Regarder `tests\captures\mobile-accueil.jpg` et `bureau-1366.jpg`.
- [ ] `git status` propre, branche poussée.

## Jour J — Mise en ligne (Claude, sur ordre d'Andry)

Git Bash :

```bash
bash ~/.deploy-sites/redeploy.sh hourdis
```

- [ ] Sortie `DEPLOIEMENT VERIFIE` (bundle en ligne = bundle local, servi en JavaScript).
- [ ] `python outils/verifier_en_ligne.py --toujours` → `OK : 0 point(s) en défaut`, message Telegram reçu.
- [ ] **Test réel du formulaire** depuis un téléphone : envoyer une demande « TEST LANCEMENT » ; vérifier (a) la page `/merci`, (b) l'e-mail dans Gmail **hors indésirables**, (c) la notification Telegram, (d) la ligne dans `/home/<compte>/hourdis-data/leads.jsonl`.
- [ ] Sans JavaScript (Chrome → paramètres du site → JavaScript bloqué) : le formulaire envoie et redirige vers `/merci`.
- [ ] `python tests/smoke_test.py https://hourdis.fonenako.mg` → 0 échec.
- [ ] Facebook Sharing Debugger sur `https://hourdis.fonenako.mg/` → « Récupérer à nouveau », image 1200 × 630 visible.
- [ ] Test des résultats enrichis Google (search.google.com/test/rich-results) sur `/` et `/faq` : LocalBusiness et FAQPage sans erreur.
- [ ] Search Console → Sitemaps → soumettre `https://hourdis.fonenako.mg/sitemap.xml` ; Inspection d'URL → demander l'indexation de `/` et `/faq`.
- [ ] **Nettoyage du serveur** (après tous les points ci-dessus) :

```powershell
python outils\nettoyage_serveur.py
python outils\nettoyage_serveur.py --executer
python outils\verifier_en_ligne.py
```

- [ ] Fusionner la branche `audit/pre-lancement-2026-09` dans `main` (`git checkout main ; git merge --ff-only audit/pre-lancement-2026-09 ; git push`).
- [ ] Publier sur la page Facebook le lien du site (le bot marketing peut rédiger le post ; recompter les chiffres avant).

## Retour arrière (< 15 min)

L'ancienne version en ligne (qui n'était pas dans git : dépôt ≠ production avant l'audit) est
archivée dans `audit-2026-09-06/ancienne-version/` (`index.html`, `src/`, `contact.php`,
`send_mail.php`, `.htaccess`). Ses images restent sur le serveur jusqu'au nettoyage.

- **Avant le nettoyage** : téléverser par FTP les fichiers de `ancienne-version/` à la racine du
  site, `index.html` en dernier ; les anciennes images sont encore en place.
- **Après le nettoyage** : `git revert` du commit de fusion, puis `bash ~/.deploy-sites/redeploy.sh hourdis`.

Ce retour n'a d'intérêt qu'en cas de page blanche, ce que le déploiement atomique et
`verifier_en_ligne.py` excluent : l'ancien formulaire, lui, n'envoyait rien.

## J+1

- [ ] Telegram : aucune alerte de `verifier_en_ligne`.
- [ ] `hourdis-data/contact.log` : pas de « mail KO » en série.
- [ ] Search Console : page `/` explorée.
- [ ] Un vrai client a-t-il écrit ? Le rappeler dans l'heure et noter le délai.

## J+7

- [ ] Premier rapport hebdo Telegram (samedi 07:00) reçu et lisible ; sinon `php rapport_hebdo.php` à la main.
- [ ] Lire `origines` : si Facebook < 50 %, le post de lancement n'a pas circulé.
- [ ] Lire `devis_erreur` : > 0 → ouvrir `contact.log`.
- [ ] Banc nocturne GitHub vert 7 fois.
- [ ] Installer UptimeRobot (06 §1).

## J+30

- [ ] Rapport : taux de conversion (contacts / pages vues) et top produit du calculateur → décider l'ordre des cartes.
- [ ] Collecter 3 photos de planchers livrés + 2 phrases de clients → section « Ils nous ont fait confiance » (F-26).
- [ ] Search Console : requêtes où le site apparaît sans clic → titres à ajuster ; positions de « hourdis prix », « hourdis madagascar », « brique creuse tana ».
- [ ] Décider l'intégration IA n° 1 (qualification des demandes, 05) et la version malgache.
- [ ] DMARC `fonenako.mg` : lire les rapports, passer à `p=quarantine` si rien de légitime n'échoue (avec l'app Fonenako).
- [ ] Renouvellement du certificat (échéance 15/10/2026) : `verifier_en_ligne.py` alertera sous 14 jours ; confirmer qu'o2switch l'a renouvelé.
