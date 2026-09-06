<?php
/**
 * Formulaire de devis HOURDIS MADAGASCAR — réception, validation, envoi.
 *
 * Ce que ce script garantit (audit du 06/09/2026, corrigé après la revue adversariale du même jour) :
 *  - il RÉPOND VRAIMENT : e-mail via mail() avec un expéditeur du domaine (SPF + DKIM passent),
 *    et notification Telegram instantanée à Andry si le jeton est configuré. Il suffit qu'UN
 *    des deux canaux passe pour dire « ok » au client ; l'échec de l'autre est journalisé AVEC
 *    la réponse du serveur, sinon la panne reste invisible.
 *  - AUCUNE DEMANDE NE SE PERD EN SILENCE : même une demande écartée comme robot est écrite dans
 *    refuses.jsonl, pour qu'un vrai client mal jugé puisse être rappelé et que le rapport le voie.
 *  - il valide côté serveur (le JavaScript n'est qu'un confort) : nom, téléphone malgache,
 *    e-mail facultatif, lieu, surface bornée, message tronqué, caractères de contrôle retirés
 *    — retours chariot compris, pour qu'aucun champ ne puisse jamais porter d'en-tête.
 *  - il résiste aux robots : pot de miel `website`, délai minimal depuis l'affichage (champ `t`),
 *    et 5 envois par heure et par adresse, comptés dans une vraie section critique (flock) et
 *    seulement sur les demandes VALIDES — un numéro mal tapé ne consomme pas le quota d'un client.
 *  - il ne fait jamais fuir un détail interne : réponses génériques, affichage d'erreurs coupé,
 *    journal hors racine web, adresse réseau tronquée (IPv4 comme IPv6).
 *  - horodatage en UTC dans les journaux (comme stat.php, pour que les rapports comparent la même
 *    échelle) et heure de Tana dans ce qu'un humain lit.
 *  - il sert le formulaire AVEC et SANS JavaScript : JSON si `Accept: application/json`,
 *    sinon redirection 303 vers /merci ou /#contact.
 *
 * Configuration : ../hourdis-config.php (HORS racine web, jamais dans git). Modèle fourni dans
 * le dépôt : outils-serveur/hourdis-config.exemple.php.
 */
declare(strict_types=1);

@ini_set('display_errors', '0');   // rien ne doit jamais précéder le JSON dans le corps de la réponse
header('X-Content-Type-Options: nosniff');
header('Cache-Control: no-store');

$CONFIG = [
    'to_email'       => 'contact.hourdis@gmail.com',
    'from_email'     => 'hourdis@fonenako.mg',   // adresse du domaine : SPF + DKIM la couvrent, aucune boîte n'est nécessaire
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

function dossier(): string {
    global $CONFIG;
    $d = $CONFIG['dossier_donnees'];
    if (!is_dir($d)) { @mkdir($d, 0700, true); }
    return $d;
}

function journal(string $ligne): void {
    $d = dossier();
    if (!is_dir($d)) { return; }
    @file_put_contents($d . '/contact.log', gmdate('Y-m-d\TH:i:s\Z') . ' ' . $ligne . "\n", FILE_APPEND | LOCK_EX);
}

/** Écrit une ligne dans un des deux journaux de demandes (leads.jsonl ou refuses.jsonl). */
function noter(string $fichier, array $ligne): void {
    $d = dossier();
    if (!is_dir($d)) { return; }
    @file_put_contents($d . '/' . $fichier, json_encode($ligne, JSON_UNESCAPED_UNICODE) . "\n", FILE_APPEND | LOCK_EX);
}

if (($_SERVER['REQUEST_METHOD'] ?? 'GET') !== 'POST') {
    if ($veutJson) { repondre(false, 'Méthode non autorisée.', 405); }
    header('Location: /#contact', true, 303);
    exit;
}

// ── Lecture et nettoyage des champs ──────────────────────────────────────────
/**
 * Par défaut TOUT caractère de contrôle saute, retours chariot compris : un "\r\n" dans un champ
 * qui finirait un jour dans un en-tête d'e-mail, c'est une injection d'en-tête. Le sujet est encodé
 * en base64 et le nom ne va aujourd'hui que dans le corps, donc rien n'est exploitable — mais la
 * ligne de défense se pose ici, pas dans la confiance qu'on fait au reste du fichier.
 * Un champ multiligne garde ses sauts de ligne, normalisés en "\n", et rien d'autre.
 * Constaté le 06/09/2026 par le test de bout en bout : la classe précédente sautait \x0A et \x0D.
 */
function champ(string $k, int $max, bool $multiligne = false): string {
    $v = (string)($_POST[$k] ?? '');
    if ($multiligne) {
        $v = str_replace(["\r\n", "\r"], "\n", $v);
        $v = preg_replace('/[^\P{C}\n]/u', '', $v) ?? '';
    } else {
        $v = preg_replace('/\p{C}/u', '', $v) ?? '';
    }
    return mb_substr(trim($v), 0, $max);
}
$nom      = champ('name', 80);
$tel      = champ('phone', 20);
$email    = champ('email', 120);
$lieu     = champ('location', 120);
$surface  = champ('surface', 12);
$message  = champ('message', 2000, true);
$telNu    = preg_replace('/[\s.\-()]/', '', $tel) ?? '';

$ip = $_SERVER['REMOTE_ADDR'] ?? '0.0.0.0';
// assez pour repérer un abus répété, pas assez pour identifier un abonné — IPv6 comprise
$reseau = str_contains($ip, ':')
    ? implode(':', array_slice(explode(':', $ip), 0, 3)) . '::x'
    : (preg_replace('/\.\d+$/', '.x', $ip) ?? '0.0.0.x');

/** La trace commune aux deux journaux : ce qu'il faut pour rappeler quelqu'un. */
function trace(array $extra = []): array {
    global $nom, $telNu, $email, $lieu, $surface, $message;
    return array_merge([
        'ts' => gmdate('Y-m-d\TH:i:s\Z'),   // UTC, comme stat.php : les rapports comparent la même échelle
        'nom' => $nom, 'tel' => $telNu, 'email' => $email, 'lieu' => $lieu,
        'surface' => $surface, 'message' => $message,
    ], $extra);
}

// ── Robots : pot de miel et délai minimal ────────────────────────────────────
// On répond « ok » pour ne rien leur apprendre, MAIS on garde la demande dans refuses.jsonl :
// si c'était un vrai client, il doit pouvoir être rappelé, et le rapport doit le voir.
if (trim((string)($_POST['website'] ?? '')) !== '') {
    journal('robot pot-de-miel');
    noter('refuses.jsonl', trace(['refuse' => 'pot de miel']));
    repondre(true, '');
}
$t = (int)($_POST['t'] ?? 0);
if ($t > 0) {
    // $t vient de l'horloge du NAVIGATEUR. Un téléphone qui avance donne un écart NÉGATIF : sans le
    // test de signe, ce client honnête était traité comme un robot et sa demande disparaissait.
    // (Constaté le 06/09/2026 en revue ; les horloges décalées sont courantes sur les téléphones.)
    $ecart = (int)(microtime(true) * 1000) - $t;
    if ($ecart >= 0 && $ecart < (int)$CONFIG['delai_min_ms']) {
        journal('robot trop rapide (' . $ecart . ' ms)');
        noter('refuses.jsonl', trace(['refuse' => 'trop rapide']));
        repondre(true, '');
    }
}

// ── Validation ───────────────────────────────────────────────────────────────
$erreurs = [];
if (mb_strlen($nom) < 2) { $erreurs[] = 'nom'; }
if (!preg_match('/^(?:\+?261|0)3[2-9]\d{7}$/', $telNu)) { $erreurs[] = 'téléphone'; }
if ($email !== '' && !filter_var($email, FILTER_VALIDATE_EMAIL)) { $erreurs[] = 'e-mail'; }
if (mb_strlen($lieu) < 2) { $erreurs[] = 'lieu'; }
$surfaceNum = (float)str_replace(',', '.', $surface);
if ($surface !== '' && (!is_numeric(str_replace(',', '.', $surface)) || $surfaceNum <= 0 || $surfaceNum > 100000)) { $erreurs[] = 'surface'; }
if ($erreurs) {
    journal('refus validation : ' . implode(',', $erreurs));
    repondre(false, 'Vérifiez : ' . implode(', ', $erreurs) . '.', 422);
}

// ── Limite : 5 envois valides par heure et par adresse ───────────────────────
// APRÈS la validation (un numéro mal tapé ne consomme pas le quota) et dans une VRAIE section
// critique : lire, décider et écrire sous le même verrou, sinon deux requêtes simultanées lisent
// la même valeur et passent toutes les deux.
$dossierLimite = dossier() . '/limite';
if (is_dir($dossierLimite) || @mkdir($dossierLimite, 0700, true)) {
    $f = $dossierLimite . '/' . hash('sha256', $ip . gmdate('YmdH')) . '.n';
    $h = @fopen($f, 'c+');
    if ($h) {
        @flock($h, LOCK_EX);
        $n = (int)stream_get_contents($h);
        if ($n >= (int)$CONFIG['max_par_heure']) {
            @flock($h, LOCK_UN); @fclose($h);
            journal('limite atteinte');
            noter('refuses.jsonl', trace(['refuse' => 'limite horaire']));
            repondre(false, 'Trop de demandes depuis votre connexion. Appelez-nous au 032 47 041 43.', 429);
        }
        rewind($h); ftruncate($h, 0); fwrite($h, (string)($n + 1)); fflush($h);
        @flock($h, LOCK_UN); @fclose($h);
    }
    // ménage : compteurs de plus de 2 h. Une requête concurrente peut les effacer en même temps.
    foreach ((array)glob($dossierLimite . '/*.n') as $vieux) {
        if ((int)@filemtime($vieux) < time() - 7200) { @unlink($vieux); }
    }
}

// ── Contenu ──────────────────────────────────────────────────────────────────
$telAffiche = preg_match('/^0(\d{2})(\d{2})(\d{3})(\d{2})$/', $telNu, $m) ? "0$m[1] $m[2] $m[3] $m[4]" : $telNu;
$heureTana = (new DateTimeImmutable('now', new DateTimeZone('Indian/Antananarivo')))->format('d/m/Y à H:i');
$corps = implode("\n", [
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
    "Reçu le $heureTana (heure de Tana)",
    "Réseau : $reseau",
]);

// ── Canal 1 : e-mail (expéditeur du domaine, enveloppe -f, sujet encodé : aucune injection possible) ──
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
// TEXTE BRUT, sans parse_mode : avec Markdown, une adresse e-mail contenant un souligné ou un
// message contenant une étoile seule fait répondre 400 « Can't parse entities » à l'API, et la
// notification disparaissait sans laisser de trace lisible. (Revue du 06/09/2026.)
$okTelegram = false;
$erreurTelegram = '';
if ($CONFIG['telegram_token'] !== '' && $CONFIG['telegram_chat'] !== '' && function_exists('curl_init')) {
    $texte = "🧱 DEVIS HOURDIS\n"
        . "$nom — $telAffiche" . ($email !== '' ? " — $email" : '') . "\n"
        . "📍 $lieu" . ($surface !== '' ? " · $surface m²" : '') . "\n"
        . ($message !== '' ? '💬 ' . mb_substr($message, 0, 600) . "\n" : '')
        . "\n📞 tel:+" . preg_replace('/^0/', '261', $telNu);
    $ch = curl_init('https://api.telegram.org/bot' . $CONFIG['telegram_token'] . '/sendMessage');
    curl_setopt_array($ch, [
        CURLOPT_POST => true, CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 8,
        CURLOPT_POSTFIELDS => ['chat_id' => $CONFIG['telegram_chat'], 'text' => $texte],
    ]);
    $rep = curl_exec($ch);
    if ($rep === false) {
        $erreurTelegram = 'curl: ' . curl_error($ch);
    } else {
        $j = json_decode((string)$rep, true);
        $okTelegram = ($j['ok'] ?? false) === true;
        if (!$okTelegram) { $erreurTelegram = mb_substr((string)($j['description'] ?? $rep), 0, 200); }
    }
    curl_close($ch);
} else {
    $erreurTelegram = 'non configuré';
}

// ── Journal des demandes (hors racine web) : le rapport hebdo le lit, et rien ne se perd ──
noter('leads.jsonl', trace(['mail' => $okMail, 'telegram' => $okTelegram]));
journal(($okMail ? 'mail ok' : 'mail KO') . ' / ' . ($okTelegram ? 'telegram ok' : 'telegram KO : ' . $erreurTelegram));

if ($okMail || $okTelegram) { repondre(true, ''); }
repondre(false, 'Nous n’avons pas pu enregistrer votre demande. Appelez-nous au 032 47 041 43.', 500);
