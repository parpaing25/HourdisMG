<?php
/**
 * Formulaire de devis HOURDIS MADAGASCAR — réception, validation, envoi.
 *
 * Ce que ce script garantit (audit pré-lancement du 06/09/2026) :
 *  - il RÉPOND VRAIMENT : e-mail via mail() avec un expéditeur du domaine (SPF + DKIM passent),
 *    et notification Telegram instantanée à Andry si le jeton est configuré. Il suffit qu'UN
 *    des deux canaux passe pour dire « ok » au client ; l'échec de l'autre est journalisé.
 *  - il valide côté serveur (le JavaScript n'est qu'un confort) : nom, téléphone malgache,
 *    e-mail facultatif, lieu, surface bornée, message tronqué, caractères de contrôle retirés.
 *  - il résiste aux robots : pot de miel `website`, délai minimal depuis l'affichage (champ `t`),
 *    limite de 5 envois par heure et par adresse IP.
 *  - il ne fait jamais fuir un détail interne : réponses génériques, journal hors racine web.
 *  - il sert le formulaire AVEC et SANS JavaScript : JSON si `Accept: application/json`,
 *    sinon redirection 303 vers /merci ou /#contact.
 *
 * Configuration : ../hourdis-config.php (HORS racine web, jamais dans git). Modèle fourni dans
 * le dépôt : outils-serveur/hourdis-config.exemple.php.
 */
declare(strict_types=1);

header('X-Content-Type-Options: nosniff');
header('Cache-Control: no-store');

$CONFIG = [
    'to_email'       => 'contact.hourdis@gmail.com',
    'from_email'     => 'hourdis@fonenako.mg',   // boîte à créer dans cPanel (domaine avec SPF + DKIM)
    'from_name'      => 'HOURDIS MADAGASCAR — site',
    'telegram_token' => '',
    'telegram_chat'  => '',
    'dossier_donnees'=> dirname(__DIR__) . '/hourdis-data',
    'max_par_heure'  => 5,
    'delai_min_ms'   => 3000,
];
$fichierConfig = dirname(__DIR__) . '/hourdis-config.php';
if (is_readable($fichierConfig)) {
    $perso = include $fichierConfig;
    if (is_array($perso)) { $CONFIG = array_merge($CONFIG, $perso); }
}

$veutJson = str_contains($_SERVER['HTTP_ACCEPT'] ?? '', 'application/json')
    || ($_SERVER['HTTP_X_REQUESTED_WITH'] ?? '') === 'fetch';

function repondre(bool $ok, string $message, int $code = 200): never {
    global $veutJson;
    http_response_code($code);
    if ($veutJson) {
        header('Content-Type: application/json; charset=utf-8');
        echo json_encode($ok ? ['ok' => true] : ['ok' => false, 'error' => $message], JSON_UNESCAPED_UNICODE);
    } else {
        header('Location: ' . ($ok ? '/merci' : '/#contact'), true, 303);
    }
    exit;
}

function journal(string $ligne): void {
    global $CONFIG;
    $d = $CONFIG['dossier_donnees'];
    if (!is_dir($d) && !@mkdir($d, 0700, true)) { return; }
    @file_put_contents($d . '/contact.log', date('c') . ' ' . $ligne . "\n", FILE_APPEND | LOCK_EX);
}

if (($_SERVER['REQUEST_METHOD'] ?? 'GET') !== 'POST') {
    if ($veutJson) { repondre(false, 'Méthode non autorisée.', 405); }
    header('Location: /#contact', true, 303);
    exit;
}

// ── Robots : pot de miel et délai minimal. On répond « ok » pour ne rien leur apprendre. ──
if (trim((string)($_POST['website'] ?? '')) !== '') { journal('robot pot-de-miel'); repondre(true, ''); }
$t = (int)($_POST['t'] ?? 0);
if ($t > 0 && (int)(microtime(true) * 1000) - $t < $CONFIG['delai_min_ms']) { journal('robot trop rapide'); repondre(true, ''); }

// ── Limite par adresse : 5 envois par heure ──
$ip = $_SERVER['REMOTE_ADDR'] ?? '0.0.0.0';
$dossierLimite = $CONFIG['dossier_donnees'] . '/limite';
if (is_dir($dossierLimite) || @mkdir($dossierLimite, 0700, true)) {
    $f = $dossierLimite . '/' . hash('sha256', $ip . date('YmdH')) . '.n';
    $n = is_file($f) ? (int)file_get_contents($f) : 0;
    if ($n >= (int)$CONFIG['max_par_heure']) {
        journal('limite atteinte');
        repondre(false, 'Trop de demandes depuis votre connexion. Appelez-nous au 032 47 041 43.', 429);
    }
    @file_put_contents($f, (string)($n + 1), LOCK_EX);
    // ménage : fichiers de plus de 2 h
    foreach ((array)glob($dossierLimite . '/*.n') as $vieux) { if (filemtime($vieux) < time() - 7200) { @unlink($vieux); } }
}

// ── Validation ──
function champ(string $k, int $max): string {
    $v = (string)($_POST[$k] ?? '');
    $v = preg_replace('/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/u', '', $v) ?? '';
    $v = trim($v);
    return mb_substr($v, 0, $max);
}
$nom      = champ('name', 80);
$tel      = champ('phone', 20);
$email    = champ('email', 120);
$lieu     = champ('location', 120);
$surface  = champ('surface', 12);
$message  = champ('message', 2000);

$telNu = preg_replace('/[\s.\-()]/', '', $tel) ?? '';
$erreurs = [];
if (mb_strlen($nom) < 2) { $erreurs[] = 'nom'; }
if (!preg_match('/^(?:\+?261|0)3[2-9]\d{7}$/', $telNu)) { $erreurs[] = 'téléphone'; }
if ($email !== '' && !filter_var($email, FILTER_VALIDATE_EMAIL)) { $erreurs[] = 'e-mail'; }
if (mb_strlen($lieu) < 2) { $erreurs[] = 'lieu'; }
if ($surface !== '' && (!is_numeric(str_replace(',', '.', $surface)) || (float)str_replace(',', '.', $surface) <= 0 || (float)str_replace(',', '.', $surface) > 100000)) { $erreurs[] = 'surface'; }
if ($erreurs) {
    repondre(false, 'Vérifiez : ' . implode(', ', $erreurs) . '.', 422);
}

// ── Contenu ──
$telAffiche = preg_match('/^0(\d{2})(\d{2})(\d{3})(\d{2})$/', $telNu, $m) ? "0$m[1] $m[2] $m[3] $m[4]" : $telNu;
$lignes = [
    'Nouvelle demande de devis — site hourdis.fonenako.mg',
    '======================================================',
    '',
    "Nom       : $nom",
    "Téléphone : $telAffiche",
    'E-mail    : ' . ($email !== '' ? $email : '—'),
    "Lieu      : $lieu",
    'Surface   : ' . ($surface !== '' ? $surface . ' m²' : '—'),
    '',
    'Projet :',
    $message !== '' ? $message : '—',
    '',
    '---',
    'Reçu le ' . date('d/m/Y à H:i') . ' (heure serveur)',
    'Réseau : ' . preg_replace('/\.\d+$/', '.x', $ip),   // adresse tronquée : assez pour repérer un abus, pas plus
];
$corps = implode("\n", $lignes);

// ── Canal 1 : e-mail (expéditeur du domaine, enveloppe -f, sujet fixe : aucune injection possible) ──
$okMail = false;
$sujet = '=?UTF-8?B?' . base64_encode("Devis hourdis — $nom, $lieu") . '?=';
$entetes = [
    'From: =?UTF-8?B?' . base64_encode($CONFIG['from_name']) . '?= <' . $CONFIG['from_email'] . '>',
    'Reply-To: ' . ($email !== '' ? $email : $CONFIG['to_email']),
    'MIME-Version: 1.0',
    'Content-Type: text/plain; charset=UTF-8',
    'Content-Transfer-Encoding: 8bit',
    'X-Mailer: hourdis-site',
];
try {
    $okMail = @mail($CONFIG['to_email'], $sujet, $corps, implode("\r\n", $entetes), '-f' . $CONFIG['from_email']);
} catch (Throwable $e) { $okMail = false; }

// ── Canal 2 : Telegram (le plus fiable pour un rappel dans l'heure) ──
$okTelegram = false;
if ($CONFIG['telegram_token'] !== '' && $CONFIG['telegram_chat'] !== '' && function_exists('curl_init')) {
    $texte = "🧱 *Devis hourdis*\n" .
        "*$nom* — $telAffiche" . ($email !== '' ? " — $email" : '') . "\n" .
        "📍 $lieu" . ($surface !== '' ? " · $surface m²" : '') . "\n" .
        ($message !== '' ? "💬 " . mb_substr($message, 0, 600) . "\n" : '') .
        "\n📞 tel:+" . preg_replace('/^0/', '261', $telNu);
    $ch = curl_init('https://api.telegram.org/bot' . $CONFIG['telegram_token'] . '/sendMessage');
    curl_setopt_array($ch, [
        CURLOPT_POST => true, CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 6,
        CURLOPT_POSTFIELDS => ['chat_id' => $CONFIG['telegram_chat'], 'text' => $texte, 'parse_mode' => 'Markdown'],
    ]);
    $rep = curl_exec($ch);
    $okTelegram = $rep !== false && (json_decode((string)$rep, true)['ok'] ?? false) === true;
    curl_close($ch);
}

// ── Journal des demandes (hors racine web) : pour le rapport hebdo et pour ne jamais perdre un lead ──
$d = $CONFIG['dossier_donnees'];
if (is_dir($d) || @mkdir($d, 0700, true)) {
    @file_put_contents($d . '/leads.jsonl', json_encode([
        'ts' => date('c'), 'nom' => $nom, 'tel' => $telNu, 'email' => $email, 'lieu' => $lieu,
        'surface' => $surface, 'message' => $message, 'mail' => $okMail, 'telegram' => $okTelegram,
    ], JSON_UNESCAPED_UNICODE) . "\n", FILE_APPEND | LOCK_EX);
}
journal(($okMail ? 'mail ok' : 'mail KO') . ' / ' . ($okTelegram ? 'telegram ok' : 'telegram KO ou non configuré'));

if ($okMail || $okTelegram) { repondre(true, ''); }
repondre(false, 'Nous n’avons pas pu enregistrer votre demande.', 500);
