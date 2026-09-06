<?php
/**
 * Envoi du formulaire HOURDIS MG (o2switch)
 * Expéditeur technique (From/Return-Path) = boîte du domaine
 * Destinataire = Gmail de réception
 */

$TO_EMAIL   = 'contact.hourdis@gmail.com';                 // ← où tu veux recevoir
$FROM_EMAIL = 'hourdismg@hourdismg.artimmomada.com';      // ← ta boîte du domaine (existe dans cPanel)
$FROM_NAME  = 'HOURDIS MADAGASCAR';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
  http_response_code(405);
  exit('Méthode non autorisée');
}

// honeypot anti-spam (si tu ajoutes <input name="website" style="display:none"> dans le form)
if (!empty($_POST['website'] ?? '')) {
  http_response_code(200);
  exit('OK');
}

// Récupération des champs EXACTS de ton HTML
function g($k){ return isset($_POST[$k]) ? trim((string)$_POST[$k]) : ''; }
function clean($s){ return strip_tags($s); }

$name     = clean(g('name'));
$phone    = clean(g('phone'));
$emailRaw = g('email');
$email    = filter_var($emailRaw, FILTER_VALIDATE_EMAIL) ? $emailRaw : '';
$location = clean(g('location'));
$surface  = clean(g('surface'));
$message  = trim(g('message'));

if ($name === '' || $phone === '' || $location === '') {
  http_response_code(422);
  exit("Merci de renseigner au minimum Nom, Téléphone et Localisation.");
}

$subject = 'Demande de devis - HOURDIS MG';

$body = implode("\n", [
  "Nouvelle demande de devis",
  "==========================",
  "",
  "Nom complet : $name",
  "Téléphone   : $phone",
  "Email       : " . ($email ?: '—'),
  "Localisation: $location",
  "Surface (m²): " . ($surface !== '' ? $surface : '—'),
  "",
  "Message :",
  $message !== '' ? $message : '—',
  "",
  '---',
  "Date  : " . date('Y-m-d H:i:s'),
  "IP    : " . ($_SERVER['REMOTE_ADDR'] ?? 'n/a'),
  "Page  : " . ($_SERVER['HTTP_REFERER'] ?? ('https://' . $_SERVER['HTTP_HOST'])),
]);

$headers   = [];
$headers[] = "From: $FROM_NAME <$FROM_EMAIL>";
$headers[] = "Reply-To: " . ($email ?: $FROM_EMAIL);
$headers[] = "MIME-Version: 1.0";
$headers[] = "Content-Type: text/plain; charset=UTF-8";

$subjectEnc = '=?UTF-8?B?'.base64_encode($subject).'?=';

// IMPORTANT sur o2switch : envelope sender = -f adresse de ton domaine
$ok = @mail($TO_EMAIL, $subjectEnc, $body, implode("\r\n", $headers), "-f$FROM_EMAIL");

if ($ok) {
  // Soumission classique (non-AJAX) : petit message simple
  echo "✅ Merci, votre demande a été envoyée. Nous vous répondrons rapidement.";
  exit;
}

http_response_code(500);
echo "❌ Erreur d'envoi. Vérifiez que l'adresse expéditeur ($FROM_EMAIL) existe bien dans cPanel.";
