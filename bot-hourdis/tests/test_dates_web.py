from datetime import date

from bot import dates_web

AUJOURDHUI = date(2026, 9, 6)


def test_jsonld_prioritaire():
    code = ('<html><head><script type="application/ld+json">{"@type":"Article",'
            '"datePublished":"2024-03-12T10:00:00+01:00"}</script>'
            '<meta property="article:published_time" content="2023-01-01"></head></html>')
    assert dates_web.date_de_page(code, "https://x.fr/a", aujourdhui=AUJOURDHUI) == (date(2024, 3, 12), "jsonld")


def test_meta_puis_time_puis_url():
    assert dates_web.date_de_page('<meta name="pubdate" content="2025-07-01">', "", aujourdhui=AUJOURDHUI) == (date(2025, 7, 1), "meta")
    assert dates_web.date_de_page('<time class="entry-date" datetime="2022-11-30T08:00:00Z">30 nov</time>', "",
                                  aujourdhui=AUJOURDHUI) == (date(2022, 11, 30), "time")
    assert dates_web.date_de_page("<p>rien</p>", "https://blog.fr/2021/05/17/pose-hourdis", aujourdhui=AUJOURDHUI) == (date(2021, 5, 17), "url")


def test_texte_avec_annee_seulement():
    texte = "Publié le 12 mars 2024 par la rédaction. La pose des hourdis…"
    assert dates_web.date_de_page("<p>x</p>", "https://x.fr/a", texte, AUJOURDHUI) == (date(2024, 3, 12), "texte")
    # Sans année, on ne devine pas : « 12 mars » peut être un événement à venir.
    assert dates_web.date_de_page("<p>x</p>", "https://x.fr/a", "Rendez-vous le 12 mars au salon", AUJOURDHUI) == (None, "")


def test_futur_et_prehistoire_refuses():
    assert dates_web.date_de_page('<meta name="date" content="2031-01-01">', "", aujourdhui=AUJOURDHUI) == (None, "")
    assert dates_web.date_de_page('<meta name="date" content="1998-01-01">', "", aujourdhui=AUJOURDHUI) == (None, "")


def test_mois_dans_url_est_approximatif():
    assert dates_web.date_de_page("", "https://x.fr/2020/06/dossier", aujourdhui=AUJOURDHUI) == (date(2020, 6, 1), "url_mois")


def test_lire_iso_formes():
    assert dates_web.lire_iso("Tue, 12 Mar 2024 07:00:00 GMT", AUJOURDHUI) == date(2024, 3, 12)
    assert dates_web.lire_iso("20240312", AUJOURDHUI) == date(2024, 3, 12)
    assert dates_web.lire_iso("1710230400", AUJOURDHUI) == date(2024, 3, 12)
    assert dates_web.lire_iso("n'importe quoi", AUJOURDHUI) is None


def test_jsonld_casse_rattrape():
    code = '<script type="application/ld+json">{"@type":"VideoObject","uploadDate":"2024-02-02",}</script>'
    assert dates_web.date_de_page(code, "", aujourdhui=AUJOURDHUI) == (date(2024, 2, 2), "jsonld")
