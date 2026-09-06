"""« Publier en un clic » : texte refait, médias importés, envoi — sans réseau."""
from pathlib import Path

from bot import base, publication, rangement, youtube


def _video(tid_url="https://youtube.com/watch?v=abc123", statut="gardee"):
    return base.ajouter_trouvaille({
        "url": tid_url, "titre": "Comment poser un plancher hourdis", "genre": "video",
        "texte": "on pose les hourdis entre les poutrelles puis on vérifie l'étaiement avant de couler "
                 "la dalle de compression " * 4,
        "auteur": "POINT.P", "score": 80, "statut": statut, "themes": ["pose"], "duree_s": 148,
    })


def test_video_id_de():
    assert youtube.video_id_de("https://youtube.com/watch?v=abc123") == "abc123"
    assert youtube.video_id_de("https://youtu.be/xyz789?t=1") == "xyz789"
    assert youtube.video_id_de("https://www.youtube.com/shorts/sh0rt_id") == "sh0rt_id"
    assert youtube.video_id_de("https://www.rector.fr/") == ""


def test_un_clic_a_blanc_video(cfg, monkeypatch):
    tid = _video()
    dossier = rangement.racine(cfg) / rangement.chemin_de(base.trouvaille(tid), cfg).relative_to(rangement.racine(cfg))

    def faux_telechargement(video_id, dossier_media, hauteur_max, taille_max_mo):
        assert video_id == "abc123" and hauteur_max == 720
        Path(dossier_media).mkdir(parents=True, exist_ok=True)
        chemin = Path(dossier_media) / "video.mp4"
        chemin.write_bytes(b"\x00" * 1024)
        return chemin, ""

    monkeypatch.setattr(youtube, "telecharger_video", faux_telechargement)
    monkeypatch.setattr(rangement, "telecharger_images", lambda urls, d, c, deja=0: [])
    etapes = []
    r = publication.publier_en_un_clic(tid, cfg, progression=etapes.append, a_blanc=True)
    assert r["ok"] and r["a_blanc"] and r["mode"] == "video"
    assert Path(r["video"]).is_file() and Path(r["video"]).parent == dossier / "media"
    assert "https://youtube.com/watch?v=abc123" in r["message"]     # la source est citée
    assert any("gabarit" in e for e in etapes) and any("Vidéo prête" in e for e in etapes)
    t = base.trouvaille(tid)
    assert t["post"] == r["message"] and t["statut"] == "gardee"     # à blanc : rien ne change
    assert base.publications()[0]["a_blanc"] == 1


def test_un_clic_refuse_si_eteinte_ou_deja_publiee(cfg):
    tid = _video("https://youtube.com/watch?v=def456")
    assert "éteinte" in publication.publier_en_un_clic(tid, cfg)["erreur"]
    base.modifier_trouvaille(tid, {"statut": "publiee"})
    cfg["publication_active"] = True
    assert "déjà" in publication.publier_en_un_clic(tid, cfg)["erreur"]


def test_un_clic_envoi_video_puis_repli_photos(cfg, monkeypatch):
    """Facebook refuse la vidéo → l'album de photos part quand même."""
    tid = _video("https://youtube.com/watch?v=ghi789")
    cfg["publication_active"] = True
    monkeypatch.setattr(publication, "jeton", lambda: ("PAGE", "TOKEN"))

    def faux_telechargement(video_id, dossier_media, hauteur_max, taille_max_mo):
        Path(dossier_media).mkdir(parents=True, exist_ok=True)
        chemin = Path(dossier_media) / "video.mp4"
        chemin.write_bytes(b"\x00" * 10)
        return chemin, ""

    def fausses_images(urls, dossier, c, deja=0):
        Path(dossier).mkdir(parents=True, exist_ok=True)
        (Path(dossier) / "image-1.jpg").write_bytes(b"\xff\xd8")
        return ["images/image-1.jpg"]

    envois = []
    monkeypatch.setattr(youtube, "telecharger_video", faux_telechargement)
    monkeypatch.setattr(rangement, "telecharger_images", fausses_images)
    monkeypatch.setattr(publication, "_envoyer_video",
                        lambda page, tok, video, texte, titre: envois.append("video") or ("", "Permissions error (code 200)"))
    monkeypatch.setattr(publication, "_envoyer_photos",
                        lambda page, tok, photos, texte, lien: envois.append(("photos", len(photos))) or ("123_456", ""))
    r = publication.publier_en_un_clic(tid, cfg, progression=lambda m: None, message="Texte imposé par Andry")
    assert r["ok"] and r["fb_id"] == "123_456" and r["mode"] == "photos"
    assert envois == ["video", ("photos", 1)]
    assert "vidéo refusée" in r["detail"]
    t = base.trouvaille(tid)
    assert t["statut"] == "publiee" and t["publie_fb_id"] == "123_456" and t["post"] == "Texte imposé par Andry"
    assert base.publications()[0]["resultat"] == "ok (photos)"


def test_un_clic_article_sans_image_part_en_lien(cfg, monkeypatch):
    tid = base.ajouter_trouvaille({"url": "https://www.rector.fr/conseils/pose", "titre": "Pose hourdis", "genre": "article",
                                   "texte": "Les hourdis se posent entre les poutrelles. " * 20, "score": 70, "statut": "gardee"})
    cfg["publication_active"] = True
    monkeypatch.setattr(publication, "jeton", lambda: ("PAGE", "TOKEN"))
    monkeypatch.setattr(publication.toile, "lire_page", lambda url, session=None: {"images": []})
    monkeypatch.setattr(rangement, "telecharger_images", lambda urls, d, c, deja=0: [])
    monkeypatch.setattr(publication, "_envoyer_texte", lambda page, tok, texte, lien: ("789", "") if lien else ("", "pas de lien"))
    r = publication.publier_en_un_clic(tid, cfg, progression=lambda m: None)
    assert r["ok"] and r["mode"] == "lien" and r["fb_id"] == "789"
