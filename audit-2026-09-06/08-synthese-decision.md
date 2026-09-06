# 08 — Synthèse et décision

**Site** : hourdis.fonenako.mg — vitrine du fabricant de hourdis, briques et tuiles (Ambohimanga Rova).
**Audit** : 06/09/2026, site en ligne, serveur, dépôt, bible business. **Décision : NO-GO sur la
version en ligne ; GO CONDITIONNEL sur la version corrigée**, dès que quatre actions d'Andry sont faites.

## Ce qu'il faut savoir en trente secondes

1. **Le formulaire de devis n'a jamais envoyé une seule demande** depuis la mise en ligne
   (17/07/2026). Il affiche « envoyée avec succès » sans rien envoyer. Personne ne pouvait le voir :
   aucun journal, aucune mesure. C'est corrigé, et chaque demande arrivera désormais par e-mail
   **et** par Telegram sur le téléphone.
2. **Le site n'existait nulle part ailleurs que sur le serveur**, et la commande de déploiement
   l'aurait remplacé par une page vide. Il est maintenant dans le dépôt, reconstruit par un script
   qui refuse un site cassé, déployé sans coupure.
3. **Deux prix différaient** entre le site et la page Facebook (hourdis 15 et 12). Tranché : la page
   Facebook fait référence, le site est aligné.
4. Le site promettait la livraison « dans tout Madagascar » et montrait une photo d'équipe achetée
   sur une banque d'images. Les textes disent maintenant ce que la bible business dit.
5. **Le formulaire corrigé a été exercé sur le vrai serveur**, dans un vrai navigateur : e-mail reçu,
   notification Telegram reçue, demande journalisée, 24 contrôles au vert. Une revue adversariale a
   ensuite trouvé douze défauts de plus, dont un qui aurait avalé en silence la demande de tout
   client dont le téléphone avance. Tous corrigés et retestés.

## Tableau de bord

| Domaine | Poids | Avant | Après | P0 avant | Verdict après |
|---|---|---|---|---|---|
| Performance | 12 | 88 | 95 | — | ✓ |
| Sécurité | 15 | 48 | 94 | HSTS absent | ✓ (délivrabilité à tester en ligne) |
| Design, UX | 10 | 67 | 92 | — | ✓ |
| Mobile | 12 | 70 | 93 | — | ✓ (appareil réel à tester) |
| Accessibilité | 8 | 69 | 92 | — | ✓ (lecteur d'écran à tester) |
| SEO, GEO | 8 | 66 | 90 | — | ✓ (Search Console à créer) |
| Pages, contenu | 8 | 32 | 88 | — | ✓ (mentions légales à compléter) |
| Fonctionnel | 12 | 80 | 97 | **formulaire mort** | ✓ **testé pour de vrai sur le serveur** |
| Code, qualité | 7 | 44 | 90 | — | ✓ |
| IA | 5 | 25 | 40 | — | plan livré |
| Amélioration continue | 6 | 0 | 47 | — | socle livré, à compléter |
| Ops, lancement | 5 | 40 | 85 | déploiement destructeur | ✓ |
| **Note pondérée /100** | 108 | **57,5** | **87,3** | 4 P0 | |

Règle : GO = note ≥ 85, zéro P0, tous les domaines ≥ 70. Après correction, deux domaines restent
sous 70 (IA, amélioration continue) : **GO CONDITIONNEL**, avec plan sous 30 jours (07).

## Conditions du GO — état au 06/09/2026 après les réponses d'Andry

| # | Action | État |
|---|---|---|
| 1 | **Q1** prix hourdis 15 et 12 | **fait** : référence = page Facebook, site aligné (3 000 / 2 800 Ar) |
| 2 | **Q4** expéditeur des devis et configuration serveur | **fait** : e-mail testé depuis le serveur (arrive en boîte de réception sans boîte cPanel), Telegram testé, config posée hors racine web |
| 3 | **Q3** WhatsApp, **Q5** photos | **fait** : confirmé ; photos reprises de la page Facebook |
| 4 | **Q2** identité légale | **partiel** : NIF et STAT reportés (décision d'Andry) ; dénomination, forme, adresse et responsable restent à donner (4 cases surlignées sur la page) |
| 5 | Dire « déploie » ; puis envoyer une demande test depuis son téléphone et confirmer qu'elle arrive (Gmail + Telegram) | **à faire** |

Puis, sans bloquer : nettoyage du serveur, cron du rapport hebdo (ou tâche locale), Search Console.

## Top 10 des actions (impact / effort)

| # | Action | Impact | Effort | État |
|---|---|---|---|---|
| 1 | Formulaire réel + Telegram + journal | chaque lead compte | 3 h | **fait** |
| 2 | Source unique du site + build + déploiement sûr | plus de risque de page vide | 4 h | **fait** |
| 3 | Expéditeur sur un domaine vivant | e-mails délivrés | 15 min | **Andry** |
| 4 | Prix uniques site/bot | confiance client | 2 min | **Andry** |
| 5 | En-têtes de sécurité, listing coupé, sources retirées | surface d'attaque | 1 h | **fait** |
| 6 | Livraison, délais, catalogue complet, FAQ | moins d'appels perdus, GEO | 6 h | **fait** |
| 7 | En-tête compact, menu 44 px, dialogues natifs | usage mobile | 3 h | **fait** |
| 8 | Mesure + rapport hebdo + contrôle quotidien | on saura | 4 h | **fait**, cron à poser |
| 9 | Mentions légales et confidentialité | conformité | 5 h | **fait**, 7 cases à remplir |
| 10 | Qualification IA des demandes sur Telegram | Andry rappelle les bons clients d'abord | 3 h | proposé (05) |

## Cinq propositions pour un site « 2026 »

1. **« Envoyez votre plan, on calcule »** : photo du plan de plancher → nombre de hourdis, poutrelles,
   budget, validé par un ingénieur avant envoi. Aucun concurrent local ne le fait. 12 h, ≈ 1 €/mois.
2. **Assistant devis FR/MG sur le site**, borné au catalogue, transfert WhatsApp en un clic. 8 h, ≈ 2 €/mois.
3. **Version malgache** relue par Andry, avec `hreflang` : la moitié des clients écrivent en malgache. 6 h.
4. **Suivi de commande par WhatsApp** : après validation, un message automatique à J-1 de la
   livraison avec l'heure et le camion (Twilio/WhatsApp Business API ou, gratuit, un rappel Telegram
   à Andry qui envoie lui-même). 4 h.
5. **Page « Chantiers livrés »** alimentée depuis la page Facebook (photos et posts avec accord des
   clients), la preuve sociale qui manque aujourd'hui. 3 h + collecte.

## Ce qui n'a pas pu être vérifié

Appareil réel Android/iPhone, lecteur d'écran, délivrabilité e-mail (boîte à créer), Search
Console, sauvegarde JetBackup, page Facebook et répondeur automatique (Facebook refuse les
requêtes automatiques). Chacun a sa procédure dans 02 et 07.
