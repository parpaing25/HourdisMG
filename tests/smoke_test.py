"""Banc de fumée du site Hourdis : parcours critiques, mobile, accessibilité.

    python tests/smoke_test.py                        # contre http://127.0.0.1:8765 (python build.py --servir)
    python tests/smoke_test.py https://hourdis.fonenako.mg   # contre la production (lecture seule : le
                                                       # formulaire est intercepté, rien n'est envoyé)

Sortie : une ligne par contrôle, code 1 si un contrôle tombe. Captures dans tests/captures/.
Passe un agent utilisateur réaliste : o2switch sert une page de blocage 429 au Chromium headless nu.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8765").rstrip("/")
CAP = Path(__file__).parent / "captures"
CAP.mkdir(exist_ok=True)
UA_MOBILE = "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36"
UA_DESKTOP = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
AXE = "https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.10.2/axe.min.js"
echecs: list[str] = []


def controle(nom: str, ok: bool, detail: str = "") -> None:
    print(("  ✓ " if ok else "  ✗ ") + nom + (f"  ({detail})" if detail else ""))
    if not ok:
        echecs.append(nom)


def structure(page):
    return page.evaluate("""() => { const d = document.documentElement; const h = document.querySelector('.header');
      return {overflow: d.scrollWidth > d.clientWidth, clientWidth: d.clientWidth, scrollWidth: d.scrollWidth,
              headerH: h ? h.getBoundingClientRect().height : 0, h1: document.querySelectorAll('h1').length,
              toggleVisible: (() => { const t = document.getElementById('navToggle'); return !!t && getComputedStyle(t).display !== 'none'; })()}; }""")


def main() -> None:
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True)

        # ── Pages, statuts, console ──
        ctx = b.new_context(viewport={"width": 1366, "height": 768}, user_agent=UA_DESKTOP)
        page = ctx.new_page()
        console = []
        page.on("console", lambda m: console.append(m.text) if m.type in ("error", "warning") else None)
        page.on("pageerror", lambda e: console.append("pageerror " + str(e)))
        print("— Pages —")
        for chemin in ("/", "/faq", "/mentions-legales", "/confidentialite", "/merci"):
            r = page.goto(BASE + chemin, wait_until="networkidle", timeout=60000)
            s = structure(page)
            controle(f"{chemin} répond 200 et a une seule h1", r is not None and r.status == 200 and s["h1"] == 1, f"{r.status if r else None}, h1={s['h1']}")
            for bloc in page.evaluate("[...document.querySelectorAll('script[type=\"application/ld+json\"]')].map(s => s.textContent)"):
                try:
                    json.loads(bloc)
                except Exception as e:
                    controle(f"{chemin} JSON-LD valide", False, str(e)[:80])
        controle("console sans erreur ni avertissement sur les 5 pages", not console, "; ".join(console)[:200])
        r = page.goto(BASE + "/page-qui-n-existe-pas", wait_until="networkidle")  # cette navigation produit légitimement un 404 en console
        controle("page absente → 404 designée", r is not None and r.status == 404 and page.locator("h1").inner_text().startswith("Cette page"), str(r.status if r else None))
        ctx.close()

        # ── Mobile 390 : en-tête, menu, débordements, calculateur, visionneuse, formulaire ──
        print("— Mobile 390 —")
        ctx = b.new_context(viewport={"width": 390, "height": 844}, user_agent=UA_MOBILE, is_mobile=True, has_touch=True, device_scale_factor=2)
        page = ctx.new_page()
        envois = []
        page.on("request", lambda rq: envois.append(rq) if rq.method == "POST" else None)
        if not BASE.startswith("http://127."):
            page.route("**/contact.php", lambda route: route.fulfill(status=200, content_type="application/json", body='{"ok":true}'))
        page.goto(BASE + "/", wait_until="networkidle", timeout=60000)
        s = structure(page)
        controle("en-tête ≤ 72 px (≤ 9 % de l'écran)", s["headerH"] <= 72, f"{s['headerH']:.0f} px")
        controle("aucun débordement horizontal à 390", not s["overflow"], f"{s['scrollWidth']}/{s['clientWidth']}")
        page.screenshot(path=str(CAP / "mobile-accueil.jpg"), type="jpeg", quality=60)

        page.click("#navToggle")
        page.wait_for_timeout(300)
        hauteurs = page.evaluate("[...document.querySelectorAll('#navMenu a')].map(a => a.getBoundingClientRect().height)")
        controle("menu ouvert, liens ≥ 44 px", page.get_attribute("#navToggle", "aria-expanded") == "true" and min(hauteurs) >= 44, f"min {min(hauteurs):.0f} px")
        page.keyboard.press("Escape")
        page.wait_for_timeout(200)

        # Toute la page, pas seulement le menu : compacter une carte ne doit jamais rétrécir sa cible.
        # (Le 06/09/2026, la refonte mobile a ramené les 8 boutons « Calculer » à 39 px sans que rien ne le dise.)
        petites = page.evaluate("""() => [...document.querySelectorAll('a, button, input:not([type=hidden]), textarea, select')]
            .filter(el => { const r = el.getBoundingClientRect();
              return r.width > 0 && (r.width < 44 || r.height < 44) && !el.closest('.hp') && el.parentElement.tagName !== 'P'; })
            .map(el => ((el.textContent || el.getAttribute('aria-label') || el.name || '?').trim().slice(0, 24)) + ' ' + Math.round(el.getBoundingClientRect().height) + 'px')""")
        controle("toutes les cibles tactiles de la page font 44 px", not petites, "; ".join(petites[:5]))
        page.screenshot(path=str(CAP / "mobile-menu.jpg"), type="jpeg", quality=60)
        page.keyboard.press("Escape")
        page.wait_for_timeout(200)
        controle("Échap ferme le menu et rend le focus au bouton", page.get_attribute("#navToggle", "aria-expanded") == "false" and page.evaluate("document.activeElement.id") == "navToggle")

        premier = page.locator(".calculator-btn").first
        premier.scroll_into_view_if_needed()
        premier.click()
        page.wait_for_timeout(300)
        controle("calculateur : dialogue ouvert, focus dans le champ", page.evaluate("document.getElementById('calculatorModal').open && document.activeElement.id === 'calcSurface'"))
        page.fill("#calcSurface", "50")
        page.wait_for_timeout(150)
        resultat = page.inner_text("#calculatorResult")
        controle("calculateur : 50 m² → 450 pièces", "450" in resultat, resultat.replace("\n", " ")[:80])
        page.screenshot(path=str(CAP / "mobile-calculateur.jpg"), type="jpeg", quality=60)
        page.fill("#calcSurface", "999999")
        page.wait_for_timeout(150)
        texte = page.inner_text("#calculatorResult").replace(" ", " ").replace(" ", " ")  # fr-FR sépare les milliers par une espace fine
        controle("calculateur : surface plafonnée à 10 000 m²", "10 000 m²" in texte and "90 000 pcs" in texte, texte.replace("\n", " ")[:90])
        page.click("#calcToQuote")
        page.wait_for_timeout(700)
        controle("« demander un devis » pré-remplit le formulaire", page.input_value("#surface") != "" and "Demande de devis" in page.input_value("#message"))

        page.locator(".gallery-item").first.scroll_into_view_if_needed()
        page.locator(".gallery-item").first.click()
        page.wait_for_timeout(300)
        controle("visionneuse ouverte avec légende", page.evaluate("document.getElementById('lightbox').open && document.getElementById('lightboxCaption').textContent.length > 3"))
        page.keyboard.press("Escape")
        page.wait_for_timeout(200)
        controle("Échap ferme la visionneuse", page.evaluate("!document.getElementById('lightbox').open"))

        page.locator("#contact").scroll_into_view_if_needed()
        page.fill("#name", "Test banc")
        page.fill("#phone", "12345")
        page.fill("#location", "Ambohimanga")
        n0 = len(envois)
        page.click("#contactForm button[type=submit]")
        page.wait_for_timeout(300)
        controle("téléphone invalide : erreur en ligne, aucun envoi", page.locator("#phoneError").is_visible() and len(envois) == n0 and page.evaluate("document.activeElement.id") == "phone")
        page.fill("#phone", "034 12 345 67")
        page.evaluate("document.getElementById('formStartedAt').value = String(Date.now() - 5000)")
        page.click("#contactForm button[type=submit]")
        page.wait_for_url("**/merci*", timeout=15000)
        posts = [rq.url for rq in envois if "contact.php" in rq.url]
        controle("formulaire valide : POST /contact.php puis page merci", len(posts) == 1 and "/merci" in page.url, f"{len(posts)} POST, url {page.url[-30:]}")
        page.screenshot(path=str(CAP / "mobile-merci.jpg"), type="jpeg", quality=60)
        ctx.close()

        # ── Points de rupture ──
        print("— Points de rupture —")
        ctx = b.new_context(user_agent=UA_DESKTOP)
        page = ctx.new_page()
        page.goto(BASE + "/", wait_until="networkidle", timeout=60000)
        for w in (360, 414, 768, 820, 1024, 1120, 1280, 1536):
            page.set_viewport_size({"width": w, "height": 800})
            page.wait_for_timeout(250)
            s = structure(page)
            attendu_burger = w < 1120  # en dessous, la marque et les six liens ne tiennent pas sur une rangée
            controle(f"{w} px : pas de débordement, en-tête {s['headerH']:.0f} px, burger={'oui' if s['toggleVisible'] else 'non'}", not s["overflow"] and s["headerH"] <= 84 and s["toggleVisible"] == attendu_burger)
        page.set_viewport_size({"width": 820, "height": 600})
        page.screenshot(path=str(CAP / "tablette-820.jpg"), type="jpeg", quality=60)
        page.set_viewport_size({"width": 1366, "height": 768})
        page.wait_for_timeout(250)
        page.screenshot(path=str(CAP / "bureau-1366.jpg"), type="jpeg", quality=60)

        # ── Accessibilité (axe-core) ──
        print("— Accessibilité —")
        try:
            page.add_script_tag(url=AXE)
            page.wait_for_function("typeof axe !== 'undefined'", timeout=15000)
            for chemin in ("/", "/faq"):
                page.goto(BASE + chemin, wait_until="networkidle")
                page.add_script_tag(url=AXE)
                page.wait_for_function("typeof axe !== 'undefined'", timeout=15000)
                res = page.evaluate("async () => { const r = await axe.run(document, {runOnly: {type: 'tag', values: ['wcag2a','wcag2aa','wcag21aa','wcag22aa','best-practice']}}); return r.violations.map(v => v.id + ' (' + v.impact + ', ' + v.nodes.length + ')'); }")
                controle(f"axe-core {chemin} : 0 violation", not res, "; ".join(res)[:200])
        except Exception as e:
            controle("axe-core chargé", False, str(e)[:80])
        ctx.close()
        b.close()

    print(f"\n{'ÉCHEC' if echecs else 'OK'} : {len(echecs)} contrôle(s) en échec" + (" → " + ", ".join(echecs) if echecs else ""))
    sys.exit(1 if echecs else 0)


if __name__ == "__main__":
    main()
