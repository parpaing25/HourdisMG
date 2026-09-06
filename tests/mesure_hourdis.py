"""Mesure réelle du site hourdis.fonenako.mg : vitals, réseau, a11y (axe), parcours, débordements.
Sortie : audit/resultats.json + captures JPEG (<= 1400 px, <= 300 Ko) dans audit/captures/.
"""
import sys, json, time, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "https://hourdis.fonenako.mg/"
OUT = Path(__file__).parent / "audit"
CAP = OUT / "captures"
CAP.mkdir(parents=True, exist_ok=True)
UA_MOBILE = ("Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 "
             "(KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36")
UA_DESKTOP = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36")
AXE = "https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.10.2/axe.min.js"

VITALS_INIT = r"""
window.__v = {lcp: 0, cls: 0, shifts: [], inp: null, longtasks: 0};
try {
  new PerformanceObserver(l => { for (const e of l.getEntries()) { window.__v.lcp = e.startTime; window.__v.lcpEl = (e.element && (e.element.tagName + (e.element.className ? '.' + e.element.className : ''))) || ''; window.__v.lcpUrl = e.url || ''; } })
    .observe({type: 'largest-contentful-paint', buffered: true});
  new PerformanceObserver(l => { for (const e of l.getEntries()) { if (!e.hadRecentInput) { window.__v.cls += e.value; window.__v.shifts.push({t: Math.round(e.startTime), v: +e.value.toFixed(4), src: (e.sources||[]).map(s => s.node && (s.node.tagName + (s.node.className ? '.' + s.node.className : ''))).slice(0,3)}); } } })
    .observe({type: 'layout-shift', buffered: true});
  new PerformanceObserver(l => { window.__v.longtasks += l.getEntries().length; })
    .observe({type: 'longtask', buffered: true});
} catch (e) { window.__v.err = String(e); }
"""

def vitals(page):
    return page.evaluate(r"""() => {
      const nav = performance.getEntriesByType('navigation')[0] || {};
      const paint = Object.fromEntries(performance.getEntriesByType('paint').map(p => [p.name, Math.round(p.startTime)]));
      const res = performance.getEntriesByType('resource').map(r => ({
        url: r.name, type: r.initiatorType, bytes: r.transferSize, dur: Math.round(r.duration), proto: r.nextHopProtocol, renderBlocking: r.renderBlockingStatus }));
      return {
        ttfb: Math.round(nav.responseStart || 0), domContentLoaded: Math.round(nav.domContentLoadedEventEnd || 0),
        load: Math.round(nav.loadEventEnd || 0), proto: nav.nextHopProtocol, transfer: nav.transferSize,
        fcp: paint['first-contentful-paint'], lcp: Math.round(window.__v.lcp), lcpEl: window.__v.lcpEl, lcpUrl: window.__v.lcpUrl,
        cls: +window.__v.cls.toFixed(4), shifts: window.__v.shifts, longtasks: window.__v.longtasks,
        resources: res, nResources: res.length, totalBytes: res.reduce((a, r) => a + (r.transferSize || r.bytes || 0), 0) + (nav.transferSize || 0),
        thirdParty: [...new Set(res.map(r => new URL(r.url).host).filter(h => h !== location.host))],
      };
    }""")

def structure(page):
    return page.evaluate(r"""() => {
      const vw = window.innerWidth;
      const vis = el => { const r = el.getBoundingClientRect(); const s = getComputedStyle(el); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none'; };
      const wide = [...document.querySelectorAll('body *')].filter(el => { const r = el.getBoundingClientRect(); return vis(el) && (r.right > vw + 1 || r.left < -1); }).slice(0, 15).map(el => el.tagName + (el.id ? '#' + el.id : '') + (el.className && typeof el.className === 'string' ? '.' + el.className.split(' ')[0] : '') + ' right=' + Math.round(el.getBoundingClientRect().right));
      const targets = [...document.querySelectorAll('a, button, input, textarea, select, [role=button]')].filter(vis).map(el => { const r = el.getBoundingClientRect(); return {t: el.tagName, txt: (el.getAttribute('aria-label') || el.textContent || el.name || '').trim().slice(0, 30), w: Math.round(r.width), h: Math.round(r.height)}; });
      const small44 = targets.filter(t => t.w < 44 || t.h < 44);
      const small24 = targets.filter(t => t.w < 24 || t.h < 24);
      const heads = [...document.querySelectorAll('h1,h2,h3,h4,h5,h6')].map(h => h.tagName + ': ' + h.textContent.trim().slice(0, 50));
      const imgs = [...document.images].map(i => ({src: i.currentSrc.split('/').pop().slice(0, 50), alt: i.alt, w: i.naturalWidth, h: i.naturalHeight, dw: Math.round(i.getBoundingClientRect().width), dh: Math.round(i.getBoundingClientRect().height), lazy: i.loading, srcset: !!i.srcset}));
      const inputsNoLabel = [...document.querySelectorAll('input:not([type=hidden]), textarea, select')].filter(i => !i.labels || i.labels.length === 0).filter(i => !i.getAttribute('aria-label') && !i.getAttribute('aria-hidden')).map(i => i.id || i.name);
      const inputs = [...document.querySelectorAll('form input:not([type=hidden]), form textarea')].map(i => ({id: i.id, type: i.type, inputmode: i.getAttribute('inputmode'), autocomplete: i.getAttribute('autocomplete'), required: i.required}));
      const landmarks = ['header','nav','main','footer','[role=banner]','[role=main]','[role=contentinfo]'].map(s => s + '=' + document.querySelectorAll(s).length);
      const header = document.querySelector('.header'); const hh = header ? header.getBoundingClientRect().height : 0;
      const fixed = [...document.querySelectorAll('body *')].filter(el => ['fixed','sticky'].includes(getComputedStyle(el).position) && vis(el)).map(el => el.className + ' h=' + Math.round(el.getBoundingClientRect().height));
      const text = document.body.innerText; const words = text.split(/\s+/).filter(Boolean).length;
      const lorem = /lorem ipsum/i.test(text);
      return {scrollWidth: document.documentElement.scrollWidth, innerWidth: vw, overflowX: document.documentElement.scrollWidth > vw, wide, nTargets: targets.length, small44, small24, heads, imgs, inputsNoLabel, inputs, landmarks, headerHeight: hh, fixed, words, lorem, lang: document.documentElement.lang, title: document.title, docHeight: document.documentElement.scrollHeight};
    }""")

def shot(page, name, full=False, quality=60):
    p = CAP / f"{name}.jpg"
    page.screenshot(path=str(p), type="jpeg", quality=quality, full_page=full)
    return p.name

def run_axe(page):
    try:
        page.add_script_tag(url=AXE)
        page.wait_for_function("typeof axe !== 'undefined'", timeout=15000)
        r = page.evaluate("async () => { const r = await axe.run(document, {runOnly: {type: 'tag', values: ['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22aa','best-practice']}}); return {violations: r.violations.map(v => ({id: v.id, impact: v.impact, help: v.help, n: v.nodes.length, tags: v.tags.filter(t => t.startsWith('wcag')), sample: v.nodes.slice(0,3).map(n => ({target: n.target.join(' '), msg: (n.failureSummary||'').slice(0,220)}))})), passes: r.passes.length, incomplete: r.incomplete.map(i => ({id: i.id, n: i.nodes.length}))}; }")
        return r
    except Exception as e:
        return {"error": str(e)}

def focus_walk(page, n=20):
    out = []
    for _ in range(n):
        page.keyboard.press("Tab")
        info = page.evaluate("""() => { const el = document.activeElement; if (!el || el === document.body) return {tag: 'BODY'}; const s = getComputedStyle(el); const r = el.getBoundingClientRect(); return {tag: el.tagName, txt: (el.getAttribute('aria-label') || el.textContent || '').trim().slice(0, 25), outline: s.outlineStyle + ' ' + s.outlineWidth, boxShadow: s.boxShadow !== 'none', visible: r.width > 0 && r.top >= 0 && r.top < window.innerHeight}; }""")
        out.append(info)
    return out

def main():
    R = {"url": URL, "date": time.strftime("%Y-%m-%d %H:%M"), "views": {}}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        # ── 1. Mobile 390 (Pixel 7 class) ────────────────────────────────
        for label, vp, ua, mobile, scale in [
            ("mobile390", {"width": 390, "height": 844}, UA_MOBILE, True, 3),
            ("desktop1366", {"width": 1366, "height": 768}, UA_DESKTOP, False, 1),
        ]:
            ctx = browser.new_context(viewport=vp, user_agent=ua, is_mobile=mobile, has_touch=mobile, device_scale_factor=scale, locale="fr-FR")
            page = ctx.new_page()
            page.add_init_script(VITALS_INIT)
            console, errors, responses = [], [], []
            page.on("console", lambda m: console.append({"type": m.type, "text": m.text[:200]}))
            page.on("pageerror", lambda e: errors.append(str(e)[:300]))
            page.on("response", lambda r: responses.append({"url": r.url[:120], "status": r.status, "ct": r.headers.get("content-type", "")[:40], "cache": r.headers.get("cache-control", ""), "enc": r.headers.get("content-encoding", "")}))
            t0 = time.time()
            page.goto(URL, wait_until="load", timeout=60000)
            page.wait_for_load_state("networkidle", timeout=30000)
            page.wait_for_timeout(2500)
            V = {"wall_load_s": round(time.time() - t0, 2)}
            V["vitals"] = vitals(page)
            V["struct"] = structure(page)
            V["console"] = console
            V["pageerrors"] = errors
            V["responses"] = responses
            V["bad_responses"] = [r for r in responses if r["status"] >= 400]
            V["shots"] = [shot(page, f"{label}-01-hero")]
            # scroll through page to trigger lazy images + observe CLS after scroll
            for y in range(0, V["struct"]["docHeight"], vp["height"] // 2):
                page.evaluate(f"window.scrollTo(0, {y})"); page.wait_for_timeout(150)
            page.wait_for_timeout(1000)
            V["vitals_after_scroll"] = {k: vitals(page)[k] for k in ("cls", "shifts", "nResources", "totalBytes")}
            V["struct_after_scroll"] = {k: structure(page)[k] for k in ("imgs", "overflowX", "scrollWidth", "wide")}
            # header behaviour after scrolling down
            V["header_after_scroll_down"] = page.evaluate("() => { const h = document.querySelector('.header'); return {transform: h.style.transform, top: h.getBoundingClientRect().top}; }")
            page.evaluate("document.querySelector('#produits').scrollIntoView()"); page.wait_for_timeout(600)
            V["shots"].append(shot(page, f"{label}-02-produits"))
            page.evaluate("document.querySelector('#contact').scrollIntoView()"); page.wait_for_timeout(600)
            V["shots"].append(shot(page, f"{label}-03-contact"))
            # axe
            page.evaluate("window.scrollTo(0,0)"); page.wait_for_timeout(300)
            V["axe"] = run_axe(page)
            # keyboard focus walk
            page.evaluate("window.scrollTo(0,0)")
            V["focus_walk"] = focus_walk(page, 14)
            # ── mobile menu ──
            if mobile:
                page.click("#navToggle"); page.wait_for_timeout(500)
                V["menu_open"] = page.evaluate("() => { const m = document.querySelector('#navMenu'); const r = m.getBoundingClientRect(); const links = [...m.querySelectorAll('a')].map(a => { const b = a.getBoundingClientRect(); return {t: a.textContent.trim(), h: Math.round(b.height), visible: b.height > 0 && b.top < window.innerHeight}; }); return {expanded: document.querySelector('#navToggle').getAttribute('aria-expanded'), h: Math.round(r.height), links, coversScreen: r.height / window.innerHeight}; }")
                V["shots"].append(shot(page, f"{label}-04-menu"))
                page.keyboard.press("Escape"); page.wait_for_timeout(300)
                V["menu_closes_on_escape"] = page.evaluate("!document.querySelector('#navMenu').classList.contains('active')")
                # le header se cache au défilement vers le bas : remonter d'abord, sinon le bouton est hors écran
                page.evaluate("window.scrollTo(0,0)"); page.wait_for_timeout(700)
                V["toggle_visible_after_scroll_down_then_up"] = page.evaluate("() => { const r = document.querySelector('#navToggle').getBoundingClientRect(); return r.top >= 0 && r.bottom <= window.innerHeight; }")
                page.evaluate("document.querySelector('#navToggle').click()"); page.wait_for_timeout(300)
                page.evaluate("document.querySelector(\"#navMenu a[href='#produits']\").click()"); page.wait_for_timeout(1200)
                V["menu_link_navigates"] = page.evaluate("() => ({closed: !document.querySelector('#navMenu').classList.contains('active'), scrollY: Math.round(window.scrollY), produitsTop: Math.round(document.querySelector('#produits').getBoundingClientRect().top), headerTransform: document.querySelector('.header').style.transform})")
            # ── calculator modal ──
            page.evaluate("document.querySelector('#produits').scrollIntoView()"); page.wait_for_timeout(300)
            page.click(".calculator-btn >> nth=1"); page.wait_for_timeout(400)
            page.fill("#calcSurface", "50"); page.wait_for_timeout(300)
            V["calculator"] = page.evaluate("() => ({title: document.querySelector('#calculatorTitle').textContent, result: document.querySelector('#calculatorResult').innerText.replace(/\\s+/g,' ').slice(0,300), focusInModal: !!document.activeElement.closest('#calculatorModal'), bodyScrollLocked: getComputedStyle(document.body).overflow})")
            V["shots"].append(shot(page, f"{label}-05-calculateur"))
            page.fill("#calcSurface", "-5"); page.wait_for_timeout(200)
            V["calculator_negative"] = page.evaluate("document.querySelector('#calculatorResult').className")
            page.fill("#calcSurface", "1e9"); page.wait_for_timeout(200)
            V["calculator_huge"] = page.evaluate("document.querySelector('#calculatorResult').innerText.replace(/\\s+/g,' ').slice(0,200)")
            page.keyboard.press("Escape"); page.wait_for_timeout(300)
            V["calculator_closes_on_escape"] = page.evaluate("!document.querySelector('#calculatorModal').classList.contains('active')")
            # tab out of modal?
            if not V["calculator_closes_on_escape"]:
                for _ in range(4): page.keyboard.press("Tab")
                V["calculator_focus_escapes_modal"] = page.evaluate("!document.activeElement.closest('#calculatorModal')")
                page.click("#closeCalculator"); page.wait_for_timeout(200)
            # ── lightbox ──
            page.evaluate("document.querySelector('#mises-en-oeuvre').scrollIntoView()"); page.wait_for_timeout(300)
            page.click(".gallery-item >> nth=0"); page.wait_for_timeout(800)
            V["lightbox"] = page.evaluate("() => { const i = document.querySelector('#lightboxImage'); return {src: i.src.split('/').pop(), natural: i.naturalWidth + 'x' + i.naturalHeight, displayed: Math.round(i.getBoundingClientRect().width) + 'x' + Math.round(i.getBoundingClientRect().height), focusInside: !!document.activeElement.closest('#lightbox')}; }")
            V["shots"].append(shot(page, f"{label}-06-lightbox"))
            page.keyboard.press("Escape"); page.wait_for_timeout(300)
            # ── contact form : does anything leave the browser ? ──
            sent = []
            page.on("request", lambda rq: sent.append({"url": rq.url[:150], "method": rq.method, "post": (rq.post_data or "")[:100]}))
            page.evaluate("document.querySelector('#contact').scrollIntoView()"); page.wait_for_timeout(300)
            page.fill("#name", "Test Audit"); page.fill("#phone", "0340000000"); page.fill("#location", "Ambohimanga <script>x</script> 🧱")
            page.fill("#surface", "50"); page.fill("#message", "Test audit, ne pas traiter")
            n_before = len(sent)
            page.click("#contactForm button[type=submit]"); page.wait_for_timeout(400)
            V["form_loading_state"] = page.evaluate("document.querySelector('#contactForm button[type=submit]').innerText")
            page.wait_for_timeout(3000)
            V["form_requests_after_submit"] = sent[n_before:]
            V["form_message"] = page.evaluate("() => { const m = document.querySelector('.form-message'); return m ? m.textContent : null; }")
            V["shots"].append(shot(page, f"{label}-07-form-envoye"))
            # ── dark mode ──
            page.emulate_media(color_scheme="dark"); page.evaluate("window.scrollTo(0,0)"); page.wait_for_timeout(400)
            V["dark_bg"] = page.evaluate("getComputedStyle(document.body).backgroundColor + ' / ' + getComputedStyle(document.body).color")
            page.emulate_media(color_scheme="light")
            # ── reduced motion honoured ? ──
            page.emulate_media(reduced_motion="reduce")
            V["reduced_motion_transition"] = page.evaluate("getComputedStyle(document.querySelector('.product-card')).transitionDuration + ' | anim=' + getComputedStyle(document.querySelector('.hero-content')).animationName")
            ctx.close()
            R["views"][label] = V
            print(f"[{label}] ok — LCP {V['vitals']['lcp']} ms, CLS {V['vitals']['cls']}, {V['vitals']['nResources']} req, {V['vitals']['totalBytes']//1024} Ko, overflowX={V['struct']['overflowX']}, axe viol={len(V['axe'].get('violations', []))}")

        # ── 2. Breakpoint sweep for horizontal overflow ─────────────────
        R["breakpoints"] = {}
        ctx = browser.new_context(user_agent=UA_MOBILE, is_mobile=True, has_touch=True)
        page = ctx.new_page()
        for w in (360, 390, 414, 768, 1024, 1280, 1536):
            page.set_viewport_size({"width": w, "height": 800})
            if w == 360: page.goto(URL, wait_until="networkidle", timeout=60000)
            page.wait_for_timeout(500)
            s = structure(page)
            R["breakpoints"][w] = {"overflowX": s["overflowX"], "scrollWidth": s["scrollWidth"], "wide": s["wide"][:5], "small44": len(s["small44"]), "headerHeight": s["headerHeight"]}
            print(f"[bp {w}] overflow={s['overflowX']} scrollWidth={s['scrollWidth']} small44={len(s['small44'])}")
        # landscape 844x390
        page.set_viewport_size({"width": 844, "height": 390}); page.wait_for_timeout(500)
        s = structure(page); R["breakpoints"]["844x390-paysage"] = {"overflowX": s["overflowX"], "headerHeight": s["headerHeight"], "fixed": s["fixed"]}
        shot(page, "paysage-844x390")
        ctx.close()

        # ── 3. Slow 3G + CPU 4x ──────────────────────────────────────────
        ctx = browser.new_context(viewport={"width": 390, "height": 844}, user_agent=UA_MOBILE, is_mobile=True, has_touch=True, device_scale_factor=3)
        page = ctx.new_page(); page.add_init_script(VITALS_INIT)
        cdp = ctx.new_cdp_session(page)
        cdp.send("Network.enable")
        cdp.send("Network.emulateNetworkConditions", {"offline": False, "latency": 400, "downloadThroughput": 400 * 1024 / 8, "uploadThroughput": 400 * 1024 / 8})
        cdp.send("Emulation.setCPUThrottlingRate", {"rate": 4})
        t0 = time.time()
        page.goto(URL, wait_until="load", timeout=120000)
        R["slow3g"] = {"wall_load_s": round(time.time() - t0, 2)}
        page.wait_for_timeout(3000)
        R["slow3g"].update({k: vitals(page)[k] for k in ("ttfb", "fcp", "lcp", "cls", "load", "domContentLoaded", "totalBytes")})
        R["slow3g"]["shot"] = shot(page, "slow3g-apres-load")
        print("[slow3g]", R["slow3g"])
        ctx.close()
        browser.close()
    (OUT / "resultats.json").write_text(json.dumps(R, ensure_ascii=False, indent=1), encoding="utf-8")
    print("écrit", OUT / "resultats.json")

if __name__ == "__main__":
    main()
