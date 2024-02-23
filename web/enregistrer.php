<?php
// enregistrer.php
$data = json_decode(file_get_contents('php://input'), true);

// Construire le chemin du fichier transaction.txt
$user = $data['user'];
$mandat = $data['mandat'];
$cheminFichier = "./$user/$mandat/transactions.txt";

// Préparer la ligne à enregistrer
$line = $data['date'] . '::' . $data['debit'] . '::' . $data['credit'] . '::' . $data['commentaire'] . '::' . $data['montant'] . "\n";

// Enregistrer dans le fichier
file_put_contents($cheminFichier, $line, FILE_APPEND);

$urlRedirection = "etape1.html?user=" . urlencode($user) . "&mandat=" . urlencode($mandat) . "&record=ok";
header("Location: $urlRedirection");
exit;
?>
