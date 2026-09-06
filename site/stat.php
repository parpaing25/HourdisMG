<?php
/**
 * Mesure d'audience première partie, sans cookie ni identifiant : un événement = une ligne.
 * Reçoit le JSON envoyé par main.js (sendBeacon) et l'ajoute dans ../hourdis-data/stats.sqlite
 * (hors racine web). Aucune donnée personnelle : pas d'adresse IP conservée, pas d'agent complet,
 * seulement le type d'événement, la page, le domaine d'origine, la largeur d'écran et la langue.
 * Le rapport hebdomadaire (outils-serveur/rapport_hebdo.php) lit cette base.
 */
declare(strict_types=1);

header('Cache-Control: no-store');
if (($_SERVER['REQUEST_METHOD'] ?? 'GET') !== 'POST') { http_response_code(405); exit; }

$brut = file_get_contents('php://input', false, null, 0, 2048);
$d = json_decode((string)$brut, true);
if (!is_array($d)) { http_response_code(204); exit; }

$autorises = ['page', 'clic_tel', 'clic_whatsapp', 'clic_messenger', 'clic_email', 'calc_ouvert', 'calc_vers_devis', 'devis_envoye', 'devis_erreur'];
$e = (string)($d['e'] ?? '');
if (!in_array($e, $autorises, true)) { http_response_code(204); exit; }

$page   = mb_substr(preg_replace('/[^a-zA-Z0-9\/\-_.#]/', '', (string)($d['p'] ?? '')) ?? '', 0, 80);
$ref    = mb_substr(preg_replace('/[^a-zA-Z0-9\-.]/', '', strtolower((string)($d['r'] ?? ''))) ?? '', 0, 80);
$larg   = max(0, min(5000, (int)($d['w'] ?? 0)));
$langue = mb_substr(preg_replace('/[^a-zA-Z\-]/', '', (string)($d['l'] ?? '')) ?? '', 0, 12);
$extra  = mb_substr(preg_replace('/[^\p{L}\p{N} ×,.\-]/u', '', (string)($d['x'] ?? '')) ?? '', 0, 80);
$famille = 'autre';
$ua = strtolower($_SERVER['HTTP_USER_AGENT'] ?? '');
if (str_contains($ua, 'bot') || str_contains($ua, 'spider') || str_contains($ua, 'crawl')) { $famille = 'robot'; }
elseif (str_contains($ua, 'android')) { $famille = 'android'; }
elseif (str_contains($ua, 'iphone') || str_contains($ua, 'ipad')) { $famille = 'ios'; }
elseif (str_contains($ua, 'windows') || str_contains($ua, 'macintosh') || str_contains($ua, 'linux')) { $famille = 'ordinateur'; }

$dossier = dirname(__DIR__) . '/hourdis-data';
if (!is_dir($dossier) && !@mkdir($dossier, 0700, true)) { http_response_code(204); exit; }

try {
    $pdo = new PDO('sqlite:' . $dossier . '/stats.sqlite', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_TIMEOUT => 3]);
    $pdo->exec('PRAGMA journal_mode=WAL');
    $pdo->exec('CREATE TABLE IF NOT EXISTS evenements (id INTEGER PRIMARY KEY, ts TEXT NOT NULL, e TEXT NOT NULL, page TEXT, ref TEXT, largeur INTEGER, langue TEXT, famille TEXT, extra TEXT)');
    $pdo->exec('CREATE INDEX IF NOT EXISTS idx_ts ON evenements (ts)');
    $st = $pdo->prepare('INSERT INTO evenements (ts, e, page, ref, largeur, langue, famille, extra) VALUES (?,?,?,?,?,?,?,?)');
    $st->execute([gmdate('Y-m-d\TH:i:s\Z'), $e, $page, $ref, $larg, $langue, $famille, $extra]);
} catch (Throwable $err) {
    // repli : une ligne JSON par événement, le rapport sait lire les deux
    @file_put_contents($dossier . '/stats.jsonl', json_encode(['ts' => gmdate('c'), 'e' => $e, 'page' => $page, 'ref' => $ref, 'largeur' => $larg, 'langue' => $langue, 'famille' => $famille, 'extra' => $extra]) . "\n", FILE_APPEND | LOCK_EX);
}
http_response_code(204);
