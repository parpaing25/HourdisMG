from bot import redaction

TEXTE = """Bienvenue sur notre blog. Cliquez ici pour vous abonner à la newsletter.
Avant de couler la dalle de compression, vérifiez l'étaiement des poutrelles tous les 1,50 m : c'est l'erreur la plus fréquente.
Les hourdis en terre cuite se posent à sec entre les poutrelles, sans mortier, en commençant par la rive.
Il faisait beau ce jour-là et l'équipe était de bonne humeur.
Comptez 9 hourdis par m² pour un entraxe de 60 cm et prévoyez 3 % de casse.
Copyright 2024 tous droits réservés."""


def test_phrases_cles_prennent_le_metier_pas_le_bruit():
    phrases = redaction.phrases_cles(TEXTE, 3)
    assert len(phrases) == 3
    assert all("newsletter" not in p and "Copyright" not in p and "beau" not in p for p in phrases)
    assert any("étaiement" in p for p in phrases) and any("9 hourdis" in p for p in phrases)


TRANSCRIPTION = ("bonjour aujourd'hui on pose les hourdis en terre cuite entre les poutrelles il faut d'abord vérifier "
                 "l'étaiement tous les 1,50 m sinon le plancher fléchit ensuite on place le treillis soudé et le chaînage "
                 "puis on coule la dalle de compression de 5 cm attention à ne jamais marcher sur les hourdis sans planche "
                 "de répartition c'est l'erreur classique on compte neuf hourdis par mètre carré pour un entraxe de 60 "
                 "et n'oubliez pas de vous abonner à la chaîne merci ") * 2


def test_phrases_cles_sur_une_transcription_sans_ponctuation():
    phrases = redaction.phrases_cles(TRANSCRIPTION, 3)
    assert len(phrases) == 3
    assert all(len(p) <= 262 and p.endswith(("…", ".")) for p in phrases)
    assert any("hourdis" in p for p in phrases)
    assert all("abonner" not in p for p in phrases)


def test_phrases_cles_ecarte_le_bourrage_de_mots_cles():
    bourrage = ("Dans ce tutoriel nous allons découvrir comment monter une cloison en brique creuse avec soin. "
                "Nous traiterons également des sujets similaires tels que monter cloison brique, monter cloison "
                "brique creuse, monter cloison brique de verre, monter une cloison en brique creuse, monter une "
                "cloison en brique de verre, cloison brique, brique cloison, brique de cloison, brique pour cloison.")
    phrases = redaction.phrases_cles(bourrage, 3)
    assert phrases and all("tels que" not in p and p.count(",") < 4 for p in phrases)


def test_resume_propre_sans_liens():
    description = ("Bonjour, je vous montre comment maçonner un mur en briques creuses.\n"
                   "⚡ Les liens ci dessous sont affiliés, une commission m'est reversée.\n"
                   "-Truelle ronde 20 cm : https://amzn.to/3naI9Z4\n🧱 MACONNERIE 🧱\n"
                   "Ce sont des briques de 15 cm posées au mortier de chaux.")
    r = redaction.resume_propre(description)
    assert r == ("Bonjour, je vous montre comment maçonner un mur en briques creuses. "
                 "Ce sont des briques de 15 cm posées au mortier de chaux.")
    assert redaction.resume_propre("x" * 1000, 100).endswith("…")


def test_rediger_mix_contient_source_contact_hashtags(cfg):
    t = {"id": "a1", "url": "https://exemple.fr/pose", "titre": "Pose hourdis", "texte": TEXTE, "genre": "article",
         "auteur": "Rector", "themes": ["pose", "erreurs"], "conseils": []}
    post = redaction.rediger(t, cfg, "mix")
    assert "https://exemple.fr/pose" in post and "Rector" in post
    assert cfg["contact_ligne"] in post and cfg["hashtags"] in post
    assert "✅" in post
    assert len(post) <= 1900
    # Deux accroches (MG puis FR) et deux appels à l'action.
    assert "👉" in post and post.count("👉") == 2


def test_rediger_video_et_langue_unique(cfg):
    t = {"id": "b2", "url": "https://youtube.com/watch?v=x", "titre": "Plancher hourdis", "texte": "", "resume": "Les étapes.",
         "genre": "video", "auteur": "POINT.P", "themes": ["pose"], "conseils": ["Étayer avant de couler."], "duree_s": 148}
    post = redaction.rediger(t, cfg, "fr")
    assert "🎥 Vidéo : Plancher hourdis (2 min 28)" in post
    assert "✅ Étayer avant de couler." in post
    assert post.count("👉") == 1 and "Source" in post


def test_assembler_depuis_ia_ajoute_ce_qui_manque(cfg):
    t = {"url": "https://x.fr/a", "auteur": "X"}
    post = redaction.assembler_depuis_ia("Accroche IA\n\nCorps.", t, cfg, "fr")
    assert post.startswith("Accroche IA") and "https://x.fr/a" in post and cfg["hashtags"] in post
