<?php
/**
 * Configuration du formulaire de devis — à copier HORS de la racine web :
 *
 *     /home/<compte>/hourdis-config.php        (la racine web est /home/<compte>/hourdis.fonenako.mg/)
 *
 * Jamais dans git, jamais dans la racine web. contact.php la lit avec dirname(__DIR__).
 *
 * 1. Créer la boîte hourdis@fonenako.mg dans cPanel (Comptes de messagerie). Le domaine fonenako.mg
 *    a déjà un SPF qui inclut le serveur (ip4:109.234.166.169) et une clé DKIM (default._domainkey) :
 *    les e-mails partis de cette boîte arrivent chez Gmail sans passer par les indésirables.
 *    L'ancien expéditeur hourdismg@hourdismg.artimmomada.com pointe sur un domaine qui n'existe plus.
 * 2. Jeton Telegram : celui de @Hourdis_bot (profil Hermes hourdis, variable TELEGRAM_BOT_TOKEN),
 *    chat = l'identifiant Telegram d'Andry (TELEGRAM_ALLOWED_USERS). Le bot doit avoir reçu au moins
 *    un message d'Andry pour pouvoir lui écrire.
 */
return [
    'to_email'       => 'contact.hourdis@gmail.com',
    'from_email'     => 'hourdis@fonenako.mg',
    'from_name'      => 'HOURDIS MADAGASCAR — site',
    'telegram_token' => '',          // 123456789:AA…  (laisser vide pour désactiver)
    'telegram_chat'  => '',          // identifiant numérique du destinataire
    'max_par_heure'  => 5,
    'delai_min_ms'   => 3000,
];
