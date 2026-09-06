<?php
if ($_SERVER["REQUEST_METHOD"] == "POST" && empty($_POST['website'])) {

    $to = "contact.hourdis@gmail.com";
    $from = "hourdismg@hourdismg.artimmomada.com"; // adresse de ton domaine
    $subject = isset($_POST['subject']) ? $_POST['subject'] : "Demande de devis";

    $name = strip_tags($_POST['name']);
    $phone = strip_tags($_POST['phone']);
    $email = filter_var($_POST['email'], FILTER_SANITIZE_EMAIL);
    $location = strip_tags($_POST['location']);
    $surface = strip_tags($_POST['surface']);
    $message = strip_tags($_POST['message']);

    $body = "
        Nouvelle demande de devis depuis le site HOURDIS MG :\n\n
        Nom : $name\n
        Téléphone : $phone\n
        Email : $email\n
        Localisation : $location\n
        Surface : $surface m²\n
        Message : $message\n
    ";

    $headers = "From: $from\r\n";
    if (!empty($email)) {
        $headers .= "Reply-To: $email\r\n";
    }

    // Utilisation de -f pour définir l'envelope sender (obligatoire sur o2switch)
    if (mail($to, $subject, $body, $headers, "-f$from")) {
        echo "Message envoyé avec succès.";
    } else {
        echo "Erreur lors de l'envoi du message.";
    }

} else {
    echo "Formulaire invalide.";
}
?>
