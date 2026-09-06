"""La partie Facebook — volontairement PETITE : deux ou trois pages de métier.

Le web est la source principale de ce bot. Facebook ne sert qu'à suivre les
pages et groupes où des maçons et des fabricants malgaches montrent leurs
chantiers : peu de défilements (6 par source), pauses humaines, session
enregistrée une fois dans un profil Chromium dédié.

Tout ce qui touche au navigateur reprend ce que les trois bots frères ont appris
en production (sélecteurs, dépliage « Voir plus », lecture de la date hors du
corps du message, garde-fou mémoire) — le script d'extraction est celui du bot
Diako, tel quel, parce que c'est le plus récent à avoir tourné contre le vrai
DOM (02/09/2026).

Les trois garde-fous qui l'entourent sont dans le collecteur : mémoire
disponible, verrou navigateur partagé (~/bots-hub), et session Claude active
(règle du 03/09/2026 pour les tournées automatiques).
"""
from __future__ import annotations

import contextlib
import random
import shutil
import sqlite3
import tempfile
import time
from pathlib import Path
from urllib.parse import urlsplit

from . import base, fraicheur
from .config import PROFIL_NAVIGATEUR

CLE_SESSION = "session_facebook"

JS_EXTRAIRE_FIL = r"""
(largeurMin) => {
  const estRacine = (el, sel) => !el.parentElement?.closest(sel);
  let blocs = [...document.querySelectorAll('div[aria-posinset]')]
    .filter(el => estRacine(el, 'div[aria-posinset]'));
  if (!blocs.length) blocs = [...document.querySelectorAll('div[role="feed"] > div')];
  if (!blocs.length) {
    blocs = [...document.querySelectorAll('div[role="article"]')]
      .filter(el => estRacine(el, 'div[role="article"]'));
  }
  const BRUIT = /^(facebook|j'aime|jaime|commenter|partager|répondre|repondre|voir plus|… en voir plus|en voir plus|tout voir|auteur|top fan|membre|admin|modérateur|moderateur|suivre|rejoindre|voir la traduction|traduction)$/i;
  const nettoyer = (t) => (t || '').split('\n').map(l => l.trim()).filter(l => l && !BRUIT.test(l)).join('\n');
  return blocs.map(el => {
    const liens = [...el.querySelectorAll('a[href]')].map(a => a.href);
    const EST_PERMALIEN = /facebook\.com\/(?!search\/)[^?#]*\/(posts|permalink|videos|reel)\/[^/?#]+/;
    const permalien = liens.find(h => EST_PERMALIEN.test(h) || /[?&](story_fbid|multi_permalinks)=\d/.test(h)) || '';
    const images = [...el.querySelectorAll('img')]
      .map(i => ({url: i.currentSrc || i.src, largeur: i.naturalWidth || i.width || 0}))
      .filter(o => o.url && o.url.includes('scontent') && o.largeur >= largeurMin)
      .map(o => o.url);
    const message = el.querySelector('[data-ad-preview="message"], [data-ad-comet-preview="message"]');
    const texte = nettoyer(message ? message.innerText : el.innerText);
    const heure = (() => {
      const MOIS = '(?:jan|f[ée]v|mar|avr|apr|mai|may|juin|jun|juil|jul|ao[uû]|aug|sep|oct|nov|d[ée]c)\\p{L}*';
      const SUR = new RegExp('^\\s*(?:il y a\\s+|about\\s+)?(?:\\d{1,3}\\s*(?:min|mn|h|hr|j|d|sem|w|mo|an|y)\\b|hier|yesterday|aujourd|just now|maintenant|\\d{4}-\\d{2}-\\d{2}|\\d{1,2}[\\/.-]\\d{1,2}[\\/.-]\\d{2,4}|\\d{1,2}(?:er)?\\s+' + MOIS + '|' + MOIS + '\\.?\\s+\\d{1,2})', 'iu');
      const PROBABLE = /(\d{1,3}\s*(?:min|mn|h|j|d|sem|w|mois|an|y)\b|hier|yesterday|\d{1,2}[\/.-]\d{1,2}[\/.-]\d{2,4}|\d{4}-\d{2}-\d{2}|\d{1,2}\s+\p{L}{3,}\s+\d{4}|\p{L}{3,}\s+\d{1,2},?\s+\d{4})/iu;
      const dansLeMessage = (n) => !!n.closest('[data-ad-preview="message"], [data-ad-comet-preview="message"]');
      const vus = [];
      const pousser = (v) => { const t = (v || '').replace(/\s+/g, ' ').trim(); if (t && t.length <= 60) vus.push(t); };
      try {
        for (const ab of el.querySelectorAll('abbr[data-utime]')) {
          const s = Number(ab.getAttribute('data-utime'));
          if (s > 0) pousser(new Date(s * 1000).toISOString().slice(0, 10));
        }
        const liens2 = el.querySelectorAll('a[href*="/posts/"], a[href*="permalink"], a[href*="story_fbid"], a[href*="/videos/"], a[href*="/photos/"], a[href*="/reel/"]');
        for (const a of liens2) {
          if (dansLeMessage(a)) continue;
          pousser(a.getAttribute('aria-label')); pousser(a.getAttribute('title'));
          pousser(a.getAttribute('data-tooltip-content')); pousser(a.innerText);
          for (const sp of a.querySelectorAll('span')) pousser(sp.innerText);
        }
        for (const n of el.querySelectorAll('[data-tooltip-content], abbr[title], abbr, [aria-label]')) {
          if (dansLeMessage(n)) continue;
          pousser(n.getAttribute('data-tooltip-content')); pousser(n.getAttribute('title'));
          pousser(n.getAttribute('aria-label'));
          if (n.tagName === 'ABBR') pousser(n.innerText);
        }
      } catch (e) {}
      return vus.find(t => SUR.test(t)) || vus.find(t => PROBABLE.test(t)) || '';
    })();
    let auteurDuGroupe = '';
    for (const a of el.querySelectorAll('a[href]')) {
      const href = a.getAttribute('href') || '';
      const nom = (a.innerText || '').trim().split('\n')[0];
      if (nom && nom.length >= 3 && /^\/groups\/[0-9A-Za-z._-]+\/user\/\d+\/?/.test(href)) { auteurDuGroupe = nom; break; }
    }
    const enTete = el.querySelector('h2 a, h3 a, h4 a, strong a, h2 span, h3 span');
    const auteur = auteurDuGroupe || (enTete?.innerText || '').split('\n')[0].trim();
    const sites = [...new Set([...el.querySelectorAll('a[href]')]
      .map(a => a.getAttribute('href') || '')
      .map(h => { const m = h.match(/^https?:\/\/([^/?#]+)/); return m ? m[1] : ''; })
      .filter(d => d && !/facebook\.com|fbcdn|fb\.me|messenger\.com|instagram\.com|l\.php/.test(d))
      .map(d => d.replace(/^www\./, '').toLowerCase()))].slice(0, 4);
    const permalienPropre = (() => {
      if (!permalien) return '';
      try {
        const u = new URL(permalien); const garde = new URLSearchParams();
        for (const k of ['story_fbid', 'id', 'multi_permalinks']) { if (u.searchParams.has(k)) garde.set(k, u.searchParams.get(k)); }
        u.search = garde.toString() ? '?' + garde.toString() : ''; u.hash = '';
        return u.toString();
      } catch (e) { return permalien.split('?')[0]; }
    })();
    return {texte, permalien: permalienPropre, images, heure, auteur, sites};
  }).filter(p => p.texte.length > 10 || p.images.length > 0);
}
"""

JS_DEPLIER = """
() => {
  const libelles = ['Voir plus', 'See more', 'En voir plus', 'Afficher plus', 'Hijery bebe kokoa'];
  const boutons = [...document.querySelectorAll('div[role="button"], span[role="button"]')]
    .filter(b => libelles.some(l => (b.innerText || '').trim() === l));
  boutons.forEach(b => { try { b.click(); } catch (e) {} });
  return boutons.length;
}
"""


def memoire_libre_mo() -> int | None:
    """Mémoire ENGAGEABLE disponible (Mo) — c'est elle qui plafonne, pas la RAM."""
    try:
        import ctypes

        class _Etat(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]
        etat = _Etat()
        etat.dwLength = ctypes.sizeof(_Etat)
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(etat)):
            return None
        return int(min(etat.ullAvailPageFile, etat.ullAvailPhys) // (1024 * 1024))
    except Exception:
        return None


def session_enregistree() -> bool:
    """Le cookie `c_user` existe-t-il dans le profil Chromium ? Lu sur une COPIE."""
    fichier = PROFIL_NAVIGATEUR / "Default" / "Network" / "Cookies"
    if not fichier.exists():
        return False
    with tempfile.TemporaryDirectory() as dossier:
        copie = Path(dossier) / "cookies.db"
        try:
            shutil.copy2(fichier, copie)
            cx = sqlite3.connect(copie, timeout=2)
            try:
                nombre = cx.execute(
                    "SELECT COUNT(*) FROM cookies WHERE host_key LIKE '%facebook.com' "
                    "AND name = 'c_user'").fetchone()[0]
            finally:
                cx.close()
            base.ecrire_etat(CLE_SESSION, "1" if nombre else "0")
            return nombre > 0
        except (OSError, sqlite3.Error):
            return base.lire_etat(CLE_SESSION) == "1"


def oublier_session() -> None:
    if PROFIL_NAVIGATEUR.exists():
        shutil.rmtree(PROFIL_NAVIGATEUR, ignore_errors=True)
    base.ecrire_etat(CLE_SESSION, "0")
    base.logguer("Session Facebook effacée.", "avert")


def adresse_de_visite(source: dict) -> str:
    url = (source.get("url") or "").rstrip("/")
    if source.get("genre") == "groupe_fb" and not url.endswith("?sorting_setting=CHRONOLOGICAL"):
        return url + "?sorting_setting=CHRONOLOGICAL"
    return url


def _contexte(pw, visible: bool):
    PROFIL_NAVIGATEUR.mkdir(parents=True, exist_ok=True)
    return pw.chromium.launch_persistent_context(
        user_data_dir=str(PROFIL_NAVIGATEUR), headless=not visible,
        viewport={"width": 1280, "height": 900}, locale="fr-FR",
        timezone_id="Indian/Antananarivo",
        args=["--disable-blink-features=AutomationControlled"],
    )


def ouvrir_connexion(stop) -> bool:
    """Ouvre Facebook en grand ; la fenêtre se referme dès la connexion détectée."""
    from playwright.sync_api import sync_playwright
    connecte = False
    with sync_playwright() as pw:
        ctx = _contexte(pw, visible=True)
        try:
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            with contextlib.suppress(Exception):
                page.goto("https://www.facebook.com/", wait_until="domcontentloaded")
            base.logguer("Fenêtre Facebook ouverte — connectez-vous ; elle se fermera toute "
                         "seule une fois la session enregistrée.", "info")
            limite = time.time() + 300
            while time.time() < limite and not stop.is_set():
                try:
                    if "c_user" in {c["name"] for c in ctx.cookies("https://www.facebook.com")}:
                        connecte = True
                        break
                    if not ctx.pages:
                        break
                    page.wait_for_timeout(1000)
                except Exception:
                    break
        finally:
            with contextlib.suppress(Exception):
                ctx.close()
    base.ecrire_etat(CLE_SESSION, "1" if connecte else "0")
    base.logguer("Compte Facebook connecté." if connecte else
                 "Connexion non aboutie : la session n'a pas été enregistrée.",
                 "succes" if connecte else "erreur")
    return connecte


def parcourir_sources(sources: list[dict], cfg: dict, stop, sur_publication, sur_source_finie,
                      toucher_verrou) -> None:
    """Ouvre Chromium UNE fois, visite chaque source, appelle `sur_publication(pub, source)`.

    `pub` : {texte, permalien, images, heure, auteur, sites, publie_le (date|None)}.
    `sur_publication` rend True si la publication a été retenue.
    """
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        ctx = _contexte(pw, visible=bool(cfg.get("navigateur_visible", True)))
        try:
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            for rang, source in enumerate(sources):
                if stop.is_set():
                    break
                examines = retenues = 0
                erreur = None
                try:
                    examines, retenues = _parcourir(page, source, cfg, stop, sur_publication)
                except Exception as e:                       # noqa: BLE001
                    erreur = f"{type(e).__name__}: {str(e)[:120]}"
                    base.logguer(f"« {source['nom']} » (Facebook) : {erreur}", "erreur")
                sur_source_finie(source, examines, retenues, erreur)
                toucher_verrou()
                if rang < len(sources) - 1 and not stop.is_set():
                    time.sleep(random.uniform(*cfg.get("pause_entre_sources", [10, 25])))
        finally:
            with contextlib.suppress(Exception):
                ctx.close()


def _parcourir(page, source: dict, cfg: dict, stop, sur_publication) -> tuple[int, int]:
    base.logguer(f"Facebook « {source['nom']} » — ouverture.", "info")
    page.goto(adresse_de_visite(source), wait_until="domcontentloaded", timeout=60_000)
    page.wait_for_timeout(4000)
    vus: set[str] = set()
    examines = retenues = 0
    steriles = 0
    plafond = int(cfg.get("posts_max_par_source", 15))
    for _ in range(int(cfg.get("scrolls_max_par_source", 6))):
        if stop.is_set():
            break
        with contextlib.suppress(Exception):
            page.evaluate(JS_DEPLIER)
            page.wait_for_timeout(800)
        try:
            lot = page.evaluate(JS_EXTRAIRE_FIL, int(cfg.get("largeur_photo_min", 400)))
        except Exception as e:
            base.logguer(f"Lecture du fil impossible sur « {source['nom']} » "
                         f"({type(e).__name__}: {str(e)[:100]}) — le DOM Facebook a-t-il changé ?",
                         "erreur")
            lot = []
        inedits = 0
        for pub in lot:
            cle = pub.get("permalien") or pub["texte"][:120]
            if cle in vus:
                continue
            vus.add(cle)
            inedits += 1
            examines += 1
            pub["publie_le"] = fraicheur.date_de_publication(pub.get("heure", ""))
            if sur_publication(pub, source):
                retenues += 1
        steriles = steriles + 1 if inedits == 0 else 0
        if steriles >= 2 or retenues >= plafond:
            break
        page.mouse.wheel(0, random.randint(700, 1400))
        time.sleep(random.uniform(*cfg.get("pause_entre_scrolls", [2.0, 4.0])))
    base.logguer(f"« {source['nom']} » : {examines} publication(s) vue(s), {retenues} retenue(s).", "info")
    return examines, retenues


def est_facebook(url: str) -> bool:
    return "facebook.com" in urlsplit(url).netloc.lower() or "fb.com" in urlsplit(url).netloc.lower()
