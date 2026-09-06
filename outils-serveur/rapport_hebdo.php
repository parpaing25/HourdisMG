<?php
/**
 * Rapport hebdomadaire du site Hourdis — à lancer par le cron cPanel, le samedi à 07:00 :
 *
 *     0 7 * * 6  /usr/local/bin/php /home/<compte>/hourdis-outils/rapport_hebdo.php
 *
 * Copier ce fichier HORS racine web (/home/<compte>/hourdis-outils/). Il lit :
 *   - /home/<compte>/hourdis-data/stats.sqlite  (ou stats.jsonl)  — événements anonymes de stat.php
 *   - /home/<compte>/hourdis-data/leads.jsonl                      — demandes de devis de contact.php
 * et envoie le résumé sur Telegram (jeton et destinataire de /home/<compte>/hourdis-config.php),
 * en comparant à la semaine précédente. Chaque chiffre vient de ces deux fichiers, rien d'autre.
 */
declare(strict_types=1);

$base = dirname(__DIR__);
$config = is_readable("$base/hourdis-config.php") ? include "$base/hourdis-config.php" : [];
$donnees = $config['dossier_donnees'] ?? "$base/hourdis-data";
$depuis = new DateTimeImmutable('-7 days', new DateTimeZone('UTC'));
$avant  = new DateTimeImmutable('-14 days', new DateTimeZone('UTC'));

/** @return array<int, array{ts:string,e:string,page:string,ref:string,famille:string,extra:string}> */
function evenements(string $dossier, DateTimeImmutable $depuis): array {
    $out = [];
    if (is_file("$dossier/stats.sqlite")) {
        $pdo = new PDO('sqlite:' . "$dossier/stats.sqlite");
        $st = $pdo->prepare('SELECT ts, e, page, ref, famille, extra FROM evenements WHERE ts >= ? ORDER BY ts');
        $st->execute([$depuis->format('Y-m-d\TH:i:s\Z')]);
        $out = $st->fetchAll(PDO::FETCH_ASSOC);
    }
    if (is_file("$dossier/stats.jsonl")) {
        foreach (file("$dossier/stats.jsonl", FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) as $l) {
            $d = json_decode($l, true);
            if (is_array($d) && ($d['ts'] ?? '') >= $depuis->format('c')) { $out[] = $d; }
        }
    }
    return $out;
}

function compter(array $evts, DateTimeImmutable $de, DateTimeImmutable $a): array {
    $c = ['pages' => 0, 'tel' => 0, 'whatsapp' => 0, 'messenger' => 0, 'email' => 0, 'calc' => 0, 'calc_devis' => 0, 'devis' => 0, 'devis_erreur' => 0, 'robots' => 0, 'familles' => [], 'refs' => [], 'produits' => []];
    foreach ($evts as $ev) {
        $ts = $ev['ts'] ?? '';
        if ($ts < $de->format('Y-m-d\TH:i:s') || $ts >= $a->format('Y-m-d\TH:i:s')) { continue; }
        if (($ev['famille'] ?? '') === 'robot') { $c['robots']++; continue; }
        switch ($ev['e'] ?? '') {
            case 'page': $c['pages']++; $c['familles'][$ev['famille'] ?? '?'] = ($c['familles'][$ev['famille'] ?? '?'] ?? 0) + 1;
                $r = $ev['ref'] ?: 'direct'; $c['refs'][$r] = ($c['refs'][$r] ?? 0) + 1; break;
            case 'clic_tel': $c['tel']++; break;
            case 'clic_whatsapp': $c['whatsapp']++; break;
            case 'clic_messenger': $c['messenger']++; break;
            case 'clic_email': $c['email']++; break;
            case 'calc_ouvert': $c['calc']++; $p = $ev['extra'] ?: '?'; $c['produits'][$p] = ($c['produits'][$p] ?? 0) + 1; break;
            case 'calc_vers_devis': $c['calc_devis']++; break;
            case 'devis_envoye': $c['devis']++; break;
            case 'devis_erreur': $c['devis_erreur']++; break;
        }
    }
    arsort($c['refs']); arsort($c['produits']); arsort($c['familles']);
    return $c;
}

$maintenant = new DateTimeImmutable('now', new DateTimeZone('UTC'));
$evts = evenements($donnees, $avant);
$sem = compter($evts, $depuis, $maintenant);
$prec = compter($evts, $avant, $depuis);

$leads = [];
if (is_file("$donnees/leads.jsonl")) {
    foreach (file("$donnees/leads.jsonl", FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) as $l) {
        $d = json_decode($l, true);
        if (is_array($d) && ($d['ts'] ?? '') >= $depuis->format('c')) { $leads[] = $d; }
    }
}

$delta = fn(int $a, int $b): string => $b === 0 ? ($a > 0 ? ' (nouveau)' : '') : sprintf(' (%+d %%)', (int)round(($a - $b) * 100 / $b));
$contacts = $sem['tel'] + $sem['whatsapp'] + $sem['messenger'] + $sem['email'] + $sem['devis'];
$taux = $sem['pages'] > 0 ? round($contacts * 100 / $sem['pages'], 1) : 0;

$lignes = [
    "📊 Hourdis — semaine du " . $depuis->setTimezone(new DateTimeZone('Indian/Antananarivo'))->format('d/m') . " au " . $maintenant->setTimezone(new DateTimeZone('Indian/Antananarivo'))->format('d/m/Y'),
    "",
    "Pages vues : {$sem['pages']}" . $delta($sem['pages'], $prec['pages']) . ($sem['robots'] ? " · robots exclus : {$sem['robots']}" : ''),
    "Appareils : " . (implode(', ', array_map(fn($k, $v) => "$k $v", array_keys($sem['familles']), $sem['familles'])) ?: '—'),
    "Origines : " . (implode(', ', array_slice(array_map(fn($k, $v) => "$k $v", array_keys($sem['refs']), $sem['refs']), 0, 5)) ?: '—'),
    "",
    "Prises de contact : $contacts (taux $taux %)",
    "  📞 appels {$sem['tel']} · 💬 WhatsApp {$sem['whatsapp']} · Messenger {$sem['messenger']} · e-mail {$sem['email']}",
    "  🧾 devis envoyés {$sem['devis']}" . $delta($sem['devis'], $prec['devis']) . ($sem['devis_erreur'] ? " · ⚠ erreurs d'envoi {$sem['devis_erreur']}" : ''),
    "Calculateur : ouvert {$sem['calc']} fois, {$sem['calc_devis']} ont poursuivi vers le devis",
    "  produits calculés : " . (implode(', ', array_slice(array_map(fn($k, $v) => "$k ($v)", array_keys($sem['produits']), $sem['produits']), 0, 4)) ?: '—'),
];
if ($leads) {
    $lignes[] = "";
    $lignes[] = "Demandes reçues (" . count($leads) . ") :";
    foreach (array_slice($leads, -8) as $l) {
        $lignes[] = "  • " . substr($l['ts'], 5, 5) . " {$l['nom']} — {$l['lieu']}" . ($l['surface'] !== '' ? " · {$l['surface']} m²" : '') . (($l['mail'] ?? true) ? '' : ' · mail KO') . (($l['telegram'] ?? true) ? '' : ' · TG KO');
    }
}
if ($sem['pages'] === 0) {
    $lignes[] = "";
    $lignes[] = "⚠ Aucune page vue enregistrée : stat.php est-il joignable ? (POST /stat.php → 204)";
}
$texte = implode("\n", $lignes);
echo $texte, "\n";

$jeton = $config['telegram_token'] ?? '';
$chat = $config['telegram_chat'] ?? '';
if ($jeton !== '' && $chat !== '' && function_exists('curl_init')) {
    $ch = curl_init("https://api.telegram.org/bot$jeton/sendMessage");
    curl_setopt_array($ch, [CURLOPT_POST => true, CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 10, CURLOPT_POSTFIELDS => ['chat_id' => $chat, 'text' => $texte]]);
    $rep = curl_exec($ch);
    echo (($rep !== false && (json_decode((string)$rep, true)['ok'] ?? false)) ? "envoyé sur Telegram\n" : "Telegram KO : $rep\n");
}
