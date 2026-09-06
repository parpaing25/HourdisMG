from bot import toile

PAGE = """<html><head><title>Poser un plancher hourdis | Rector</title>
<meta property="og:image" content="/img/couverture.jpg"><meta name="description" content="Le guide de pose.">
<script>var x = 1;</script><style>.a{}</style></head>
<body><nav><a href="/produits">Produits</a><a href="/conseils/">Conseils</a><a href="/conseils/etaiement">Étaiement</a></nav>
<article><h1>Poser un plancher hourdis</h1><p>Première étape : l'étaiement des poutrelles.</p>
<p>%s</p><img data-src="/img/photo1.jpg" src="pixel.gif"><a href="/docs/guide-de-pose.pdf">Guide de pose (PDF)</a>
<a href="https://www.youtube.com/watch?v=x">Vidéo</a><a href="/conseils/etaiement-ita.htm">Italiano</a></article>
<footer><p>Mentions légales</p><a href="/mentions-legales">ML</a></footer></body></html>""" % ("Texte long. " * 60)


def test_mettre_a_plat_et_contenu_principal():
    plat = toile.mettre_a_plat(PAGE)
    assert plat["titre"] == "Poser un plancher hourdis | Rector"
    assert plat["description"] == "Le guide de pose."
    assert "var x" not in plat["texte"] and "Première étape" in plat["texte"]
    assert plat["images"][0] == "/img/couverture.jpg" and "/img/photo1.jpg" in plat["images"]
    corps = toile.mettre_a_plat(toile.contenu_principal(PAGE))["texte"]
    assert "Mentions légales" not in corps and "Première étape" in corps


def test_pages_a_visiter_et_pdf():
    plat = toile.mettre_a_plat(PAGE)
    base_url = "https://www.rector.fr/conseils/poser"
    pages = toile.pages_a_visiter(plat["liens"], base_url, set())
    urls = [u for _, u in pages]
    assert "https://www.rector.fr/conseils/etaiement" in urls
    assert all("mentions-legales" not in u and "-ita.htm" not in u and "youtube" not in u for u in urls)
    assert urls[0] == "https://www.rector.fr/conseils/etaiement"      # le plus prometteur d'abord
    pdf = toile.pdf_trouves(plat["liens"], base_url)
    assert pdf == [("https://www.rector.fr/docs/guide-de-pose.pdf", "Guide de pose (PDF)")]


def test_ressemble_a_une_liste():
    # Une rubrique : 40 titres, 40 accroches moyennes, aucun paragraphe long.
    rubrique_html = "".join(f"<h3><a href='/article/{i}-pose-hourdis'>Titre {i}</a></h3>" for i in range(40))
    rubrique_texte = "\n".join(f"Titre {i}\n" + "Accroche de l'article sur la pose des hourdis, " * 4 for i in range(40))
    assert toile.ressemble_a_une_liste({"html": rubrique_html, "texte": rubrique_texte}, 40)
    # Un long guide : 12 titres mais 18 paragraphes longs — c'est un article.
    guide_html = "".join(f"<h2>Étape {i}</h2>" for i in range(12))
    guide_texte = "\n".join(f"Étape {i}\n" + "Paragraphe détaillé sur la pose du plancher hourdis. " * 8 for i in range(18))
    assert not toile.ressemble_a_une_liste({"html": guide_html, "texte": guide_texte}, 30)
    # Peu de liens d'articles : jamais une liste, quel que soit le reste.
    assert not toile.ressemble_a_une_liste({"html": rubrique_html, "texte": rubrique_texte}, 5)


def test_trier_pour_suivre_articles_d_abord_listes_jamais():
    liens = [(30, "https://b.com/rubrique-article/l-info/4-technique-page-2.html"),
             (25, "https://b.com/article/229-les-nouvelles-tuiles-a-emboitement.html"),
             (20, "https://b.com/conseils/"),
             (18, "https://b.com/conseils/poser-un-plancher-hourdis-en-cinq-etapes"),
             (12, "https://b.com/produits")]
    assert toile.trier_pour_suivre(liens) == [
        "https://b.com/article/229-les-nouvelles-tuiles-a-emboitement.html",
        "https://b.com/conseils/poser-un-plancher-hourdis-en-cinq-etapes",
        "https://b.com/produits"]
    # La pagination n'est plus une page à visiter.
    pages = toile.pages_a_visiter([("/rubrique-article/l-info/4-technique-page-2.html", "Technique"),
                                   ("/article/1-pose-hourdis.html", "Pose hourdis")], "https://b.com/", set())
    assert [u for _, u in pages] == ["https://b.com/article/1-pose-hourdis.html"]


def test_images_utiles_filtre_les_logos():
    images = toile.images_utiles(["/logo.png", "/img/a.jpg", "data:image/png;base64,x", "/img/a.jpg", "/x.svg"],
                                 "https://a.fr/p")
    assert images == ["https://a.fr/img/a.jpg"]
