<?php

// Assurez-vous que les paramètres 'user' et 'mandat' sont présents
if (isset($_GET['user']) && isset($_GET['mandat'])) {
    // Nettoyage des paramètres pour éviter les injections de chemin de fichier
    $user = basename($_GET['user']);
    $mandat = basename($_GET['mandat']);

    // Construire le chemin vers le fichier transactions.txt
    $cheminFichier = "./$user/$mandat/transactions.txt";

    // Vérifier si le fichier existe avant de tenter de l'effacer
    if (file_exists($cheminFichier)) {
        // Tenter d'effacer le fichier
        if (unlink($cheminFichier)) {
            echo "Le fichier des transactions a été effacé avec succès.";
        } else {
            echo "Erreur: Impossible d'effacer le fichier transactions.txt.";
        }
    } else {
        echo "Erreur: Le fichier transactions.txt n'existe pas.";
    }
} else {
    echo "Erreur: Les paramètres 'user' et 'mandat' sont requis.";
}
