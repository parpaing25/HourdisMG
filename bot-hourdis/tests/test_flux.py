from datetime import date

from bot import flux

RSS = """<?xml version="1.0"?><rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/">
<channel><title>"hourdis" - Google Actualités</title>
<item><title>RE2020 et planchers poutrelles, quelle solution ? - Batiweb</title>
<link>https://news.google.com/rss/articles/CBMiXYZ?oc=5</link>
<pubDate>Tue, 30 Jan 2024 08:00:00 GMT</pubDate>
<description>&lt;a href="x"&gt;RE2020 et planchers&lt;/a&gt;&amp;nbsp;&lt;font&gt;Batiweb&lt;/font&gt;</description>
<source url="https://www.batiweb.com">Batiweb</source></item>
<item><title>Sans lien</title></item>
<item><title>Avec guid</title><guid isPermaLink="true">https://exemple.fr/a?utm_source=rss</guid>
<media:content url="https://exemple.fr/img.jpg"/></item>
</channel></rss>"""

ATOM = """<?xml version="1.0"?><feed xmlns:yt="http://www.youtube.com/xml/schemas/2015"
 xmlns:media="http://search.yahoo.com/mrss/" xmlns="http://www.w3.org/2005/Atom">
<entry><id>yt:video:abc123</id><yt:videoId>abc123</yt:videoId><yt:channelId>UC1</yt:channelId>
<title>Comment réaliser un plancher hourdis ?</title>
<link rel="alternate" href="https://www.youtube.com/watch?v=abc123"/>
<author><name>POINT.P</name><uri>https://www.youtube.com/channel/UC1</uri></author>
<published>2023-05-04T09:00:00+00:00</published>
<media:group><media:description>Les étapes de pose.</media:description>
<media:thumbnail url="https://i.ytimg.com/vi/abc123/hqdefault.jpg"/>
<media:community><media:statistics views="324808"/></media:community></media:group></entry></feed>"""


def test_rss_google_actualites(monkeypatch):
    entrees = flux._lire_rss(__import__("xml.etree.ElementTree", fromlist=["x"]).fromstring(RSS))
    assert len(entrees) == 2
    e = entrees[0]
    assert e["titre"] == "RE2020 et planchers poutrelles, quelle solution ?"
    assert e["source"] == "Batiweb"
    assert e["publie_le"] == date(2024, 1, 30)
    assert "RE2020 et planchers" in e["resume"] and "<" not in e["resume"]
    assert entrees[1]["url"] == "https://exemple.fr/a?utm_source=rss"
    assert entrees[1]["image"] == "https://exemple.fr/img.jpg"


def test_atom_youtube():
    entrees = flux._lire_atom(__import__("xml.etree.ElementTree", fromlist=["x"]).fromstring(ATOM))
    assert len(entrees) == 1
    e = entrees[0]
    assert e["video_id"] == "abc123" and e["chaine_id"] == "UC1"
    assert e["auteur"] == "POINT.P" and e["vues"] == 324808
    assert e["publie_le"] == date(2023, 5, 4)
    assert e["image"].endswith("hqdefault.jpg")


def test_adresses_de_recherche():
    assert "news.google.com/rss/search?q=pose+hourdis" in flux.flux_google_actualites("pose hourdis")
    assert flux.flux_bing("a b") == "https://www.bing.com/search?format=rss&q=a+b"
    assert flux.flux_chaine_youtube("UC1").endswith("channel_id=UC1")


def test_resoudre_lien_google_laisse_les_autres():
    assert flux.resoudre_lien_google("https://www.batirama.com/x") == "https://www.batirama.com/x"


def test_resoudre_lien_google_format_2023(monkeypatch):
    import base64

    class Reponse:
        url = "https://news.google.com/rss/articles/X"
        text = ""

    class Session:
        def get(self, *a, **k):
            return Reponse()

    brut = b"\x08\x13\x22\x2ahttps://www.exemple.fr/article-hourdis\xd2\x01\x00"
    ident = base64.urlsafe_b64encode(brut).decode().rstrip("=")
    url = f"https://news.google.com/rss/articles/{ident}?oc=5"
    assert flux.resoudre_lien_google(url, Session()) == "https://www.exemple.fr/article-hourdis"
