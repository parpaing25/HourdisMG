from datetime import date

from bot import youtube

VTT = """WEBVTT
Kind: captions
Language: fr

00:00:00.000 --> 00:00:02.500 align:start position:0%
on pose les <c>hourdis</c> entre les

00:00:02.500 --> 00:00:04.000 align:start position:0%
on pose les hourdis entre les
poutrelles

00:00:04.000 --> 00:00:06.000
poutrelles
puis on coule la dalle
"""


def test_vtt_en_texte_sans_repetitions():
    texte = youtube.vtt_en_texte(VTT)
    assert texte == "on pose les hourdis entre les poutrelles puis on coule la dalle"


def test_depuis_json_flat_et_complet():
    plat = {"id": "SKQw0yhaKP4", "title": "Comment réaliser un plancher hourdis ?", "duration": 148, "view_count": 324808,
            "channel": "POINT.P", "channel_id": "UC1", "channel_url": "https://www.youtube.com/channel/UC1",
            "description": "Les étapes", "thumbnails": [{"url": "a.jpg", "width": 120}, {"url": "b.jpg", "width": 480}],
            "live_status": "not_live"}
    f = youtube._depuis_json(plat)
    assert f["url"] == "https://www.youtube.com/watch?v=SKQw0yhaKP4" and f["image"] == "b.jpg"
    assert f["publie_le"] is None and f["duree_s"] == 148 and f["auteur"] == "POINT.P"
    complet = dict(plat, upload_date="20230504", webpage_url="https://www.youtube.com/watch?v=SKQw0yhaKP4",
                   chapters=[{"title": "Étaiement"}, {"title": "Coulage"}])
    f2 = youtube._depuis_json(complet)
    assert f2["publie_le"] == date(2023, 5, 4) and f2["chapitres"] == ["Étaiement", "Coulage"]


def test_duree_lisible():
    assert youtube.duree_lisible(148) == "2 min 28"
    assert youtube.duree_lisible(3720) == "1 h 02 min"
    assert youtube.duree_lisible(None) == ""
