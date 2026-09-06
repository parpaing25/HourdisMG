/* HOURDIS MADAGASCAR — script unique, sans dépendance.
   Sections : mesure (sans cookie) · navigation · calculateur · visionneuse · formulaire · apparitions.
   Contraintes : CSP script-src 'self' (aucun code en ligne), aucun style en ligne posé par
   setAttribute('style') — on bascule des classes, et element.style.x reste permis par la CSP. */
(function () {
  'use strict';

  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------- Mesure première partie : un événement, zéro identifiant, zéro cookie ---------- */
  var stat = {
    envoyer: function (e, extra) {
      try {
        if (navigator.globalPrivacyControl) return;           // le visiteur refuse la mesure
        var corps = JSON.stringify(Object.assign({
          e: e, p: location.pathname, r: document.referrer ? new URL(document.referrer).hostname : '',
          w: window.innerWidth, l: navigator.language || ''
        }, extra || {}));
        if (navigator.sendBeacon) { navigator.sendBeacon('/stat.php', new Blob([corps], { type: 'application/json' })); }
        else { fetch('/stat.php', { method: 'POST', body: corps, keepalive: true, headers: { 'Content-Type': 'application/json' } }); }
      } catch (err) { /* la mesure ne doit jamais casser la page */ }
    }
  };

  /* ---------- Navigation ---------- */
  function Navigation() {
    var header = document.querySelector('.header');
    var toggle = document.getElementById('navToggle');
    var menu = document.getElementById('navMenu');
    if (!header || !toggle || !menu) return;

    function ouvrir(etat) {
      menu.classList.toggle('is-open', etat);
      toggle.setAttribute('aria-expanded', String(etat));
      if (etat) { header.classList.remove('is-hidden'); }
    }
    toggle.addEventListener('click', function () { ouvrir(!menu.classList.contains('is-open')); });
    menu.addEventListener('click', function (e) { if (e.target.closest('a')) ouvrir(false); });
    document.addEventListener('click', function (e) { if (!e.target.closest('.nav-container')) ouvrir(false); });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && menu.classList.contains('is-open')) { ouvrir(false); toggle.focus(); }
    });

    // L'en-tête se replie quand on descend, revient dès qu'on remonte ; jamais pendant que le menu est ouvert.
    var dernier = window.scrollY;
    window.addEventListener('scroll', function () {
      var y = window.scrollY;
      if (menu.classList.contains('is-open')) { dernier = y; return; }
      header.classList.toggle('is-hidden', y > dernier && y > 160);
      dernier = y;
    }, { passive: true });

    // Section courante dans le menu (aria-current), utile au lecteur d'écran et à l'œil.
    var liens = Array.prototype.slice.call(menu.querySelectorAll('a[href^="#"]'));
    if ('IntersectionObserver' in window && liens.length) {
      var parId = {};
      liens.forEach(function (a) { parId[a.getAttribute('href').slice(1)] = a; });
      var obs = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) {
          if (!en.isIntersecting) return;
          liens.forEach(function (a) { a.removeAttribute('aria-current'); });
          var a = parId[en.target.id]; if (a) a.setAttribute('aria-current', 'page');
        });
      }, { rootMargin: '-40% 0px -55% 0px' });
      Object.keys(parId).forEach(function (id) { var s = document.getElementById(id); if (s) obs.observe(s); });
    }
  }

  /* ---------- Dialogues : <dialog> natif = focus enfermé, Échap, retour du focus ---------- */
  function ouvrirDialog(dlg, declencheur) {
    if (typeof dlg.showModal !== 'function') { dlg.setAttribute('open', ''); return; }
    dlg.__retour = declencheur || document.activeElement;
    dlg.showModal();
    document.body.classList.add('has-dialog');
  }
  function fermerDialog(dlg) {
    if (dlg.open) dlg.close();
    document.body.classList.remove('has-dialog');
    if (dlg.__retour && dlg.__retour.focus) dlg.__retour.focus();
  }
  function brancherFermeture(dlg) {
    dlg.querySelectorAll('[data-close]').forEach(function (b) { b.addEventListener('click', function () { fermerDialog(dlg); }); });
    dlg.addEventListener('click', function (e) { if (e.target === dlg) fermerDialog(dlg); }); // clic sur le fond
    dlg.addEventListener('close', function () { document.body.classList.remove('has-dialog'); });
  }

  /* ---------- Calculateur de quantités ---------- */
  function Calculator() {
    var dlg = document.getElementById('calculatorModal');
    if (!dlg) return;
    var input = document.getElementById('calcSurface');
    var result = document.getElementById('calculatorResult');
    var titre = document.getElementById('calculatorTitle');
    var sousTitre = document.getElementById('calcProduct');
    var versDevis = document.getElementById('calcToQuote');
    var produit = null;
    var fmt = function (n) { return Math.round(n).toLocaleString('fr-FR'); };
    brancherFermeture(dlg);

    document.querySelectorAll('.calculator-btn').forEach(function (btn) {
      btn.addEventListener('click', function () {
        produit = { prix: +btn.dataset.price, pcs: +btn.dataset.pcs, nom: btn.dataset.name, unite: btn.dataset.unit || 'm²' };
        titre.textContent = 'Calculer mes quantités';
        sousTitre.textContent = produit.nom + ' — ' + produit.pcs + ' pièces par ' + produit.unite + ', ' + fmt(produit.prix) + ' Ar la pièce';
        input.value = ''; result.className = 'calculator-result'; result.innerHTML = '';
        versDevis.hidden = true;
        ouvrirDialog(dlg, btn);
        input.focus();
        stat.envoyer('calc_ouvert', { x: produit.nom });
      });
    });

    function calculer() {
      var surface = parseFloat(String(input.value).replace(',', '.'));
      if (!produit || !isFinite(surface) || surface <= 0) { result.className = 'calculator-result'; versDevis.hidden = true; return; }
      surface = Math.min(surface, 10000); // au-delà, c'est un devis, pas un calculateur
      var pieces = Math.ceil(surface * produit.pcs);
      var total = pieces * produit.prix;
      result.innerHTML =
        '<div class="result-item"><span>Surface</span><strong>' + fmt(surface) + ' ' + produit.unite + '</strong></div>' +
        '<div class="result-item"><span>Pièces nécessaires</span><strong>' + fmt(pieces) + ' pcs</strong></div>' +
        '<div class="result-item"><span>Prix unitaire</span><strong>' + fmt(produit.prix) + ' Ar</strong></div>' +
        '<div class="result-item total"><span>Prix total estimé</span><span>' + fmt(total) + ' Ar</span></div>' +
        '<p class="result-note">Estimation hors livraison et hors casse (prévoir 3 à 5 % de pièces en plus). Le devis écrit fait foi.</p>';
      result.className = 'calculator-result is-visible';
      versDevis.hidden = false;
      versDevis.onclick = function () {
        fermerDialog(dlg);
        var surf = document.getElementById('surface'), msg = document.getElementById('message');
        if (surf && !surf.value) surf.value = surface;
        if (msg && !msg.value) msg.value = 'Demande de devis : ' + fmt(pieces) + ' × ' + produit.nom + ' (' + fmt(surface) + ' ' + produit.unite + ').';
        var cible = document.getElementById('contact');
        if (cible) cible.scrollIntoView({ behavior: reduceMotion ? 'auto' : 'smooth' });
        var nom = document.getElementById('name'); if (nom) setTimeout(function () { nom.focus({ preventScroll: true }); }, reduceMotion ? 0 : 500);
        stat.envoyer('calc_vers_devis', { x: produit.nom });
      };
    }
    input.addEventListener('input', calculer);
  }

  /* ---------- Visionneuse de la galerie ---------- */
  function Lightbox() {
    var dlg = document.getElementById('lightbox');
    if (!dlg) return;
    var img = document.getElementById('lightboxImage');
    var cap = document.getElementById('lightboxCaption');
    brancherFermeture(dlg);
    document.querySelectorAll('.gallery-item').forEach(function (item) {
      item.addEventListener('click', function () {
        var source = item.querySelector('img');
        img.src = item.dataset.image || source.src;
        img.alt = source.alt;
        cap.textContent = source.alt;
        ouvrirDialog(dlg, item);
        dlg.querySelector('.lightbox-close').focus();
      });
    });
  }

  /* ---------- Formulaire de devis : envoi réel, validation en ligne, repli WhatsApp ---------- */
  function ContactForm() {
    var form = document.getElementById('contactForm');
    if (!form) return;
    var submit = form.querySelector('button[type="submit"]');
    var t0 = document.getElementById('formStartedAt');
    if (t0) t0.value = String(Date.now());

    var regles = {
      name: function (v) { return v.trim().length >= 2 ? '' : 'Indiquez votre nom (2 caractères minimum).'; },
      phone: function (v) {
        var n = v.replace(/[\s.\-()]/g, '');
        return /^(?:\+?261|0)3[2-9]\d{7}$/.test(n) ? '' : 'Numéro malgache attendu, ex. 034 12 345 67.';
      },
      email: function (v) { return !v || /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v) ? '' : 'Adresse e-mail invalide.'; },
      location: function (v) { return v.trim().length >= 2 ? '' : 'Indiquez la ville ou le quartier du chantier.'; },
      surface: function (v) { return !v || (+v > 0 && +v <= 100000) ? '' : 'Surface entre 1 et 100 000 m².'; }
    };
    function afficherErreur(champ, message) {
      var err = document.getElementById(champ.id + 'Error');
      champ.setAttribute('aria-invalid', message ? 'true' : 'false');
      if (err) { err.textContent = message; err.classList.toggle('is-visible', !!message); }
      return !message;
    }
    function valider() {
      var ok = true, premier = null;
      Object.keys(regles).forEach(function (id) {
        var champ = form.elements[id]; if (!champ) return;
        if (!afficherErreur(champ, regles[id](champ.value))) { ok = false; premier = premier || champ; }
      });
      if (premier) premier.focus();
      return ok;
    }
    Object.keys(regles).forEach(function (id) {
      var champ = form.elements[id]; if (!champ) return;
      champ.addEventListener('blur', function () { if (champ.value) afficherErreur(champ, regles[id](champ.value)); });
      champ.addEventListener('input', function () { if (champ.getAttribute('aria-invalid') === 'true') afficherErreur(champ, regles[id](champ.value)); });
    });

    function message(type, html) {
      var ancien = form.parentNode.querySelector('.form-message'); if (ancien) ancien.remove();
      var el = document.createElement('div');
      el.className = 'form-message is-' + type; el.setAttribute('role', type === 'error' ? 'alert' : 'status');
      el.innerHTML = html;
      form.insertAdjacentElement('afterend', el);
      el.scrollIntoView({ behavior: reduceMotion ? 'auto' : 'smooth', block: 'nearest' });
      return el;
    }
    function texteWhatsApp() {
      var d = new FormData(form);
      return encodeURIComponent('Bonjour, demande de devis Hourdis :\n' +
        'Nom : ' + d.get('name') + '\nTéléphone : ' + d.get('phone') + '\nLieu : ' + d.get('location') +
        (d.get('surface') ? '\nSurface : ' + d.get('surface') + ' m²' : '') +
        (d.get('message') ? '\nDétails : ' + d.get('message') : ''));
    }
    function repli() {
      return '<div class="form-fallback">' +
        '<a class="btn btn-whatsapp" href="https://wa.me/261324704143?text=' + texteWhatsApp() + '" target="_blank" rel="noopener">Envoyer par WhatsApp</a>' +
        '<a class="btn btn-outline" href="tel:+261324704143">Appeler le 032 47 041 43</a>' +
        '<a class="btn btn-outline" href="https://m.me/HourdisMG" target="_blank" rel="noopener">Messenger</a></div>';
    }

    var enCours = false;
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      if (enCours || !valider()) return;
      enCours = true;
      var texte = submit.textContent;
      submit.disabled = true; submit.innerHTML = '<span class="spinner" aria-hidden="true"></span> Envoi en cours…';
      var ctrl = new AbortController(); var minuterie = setTimeout(function () { ctrl.abort(); }, 15000);

      fetch(form.action, { method: 'POST', body: new FormData(form), headers: { 'Accept': 'application/json' }, signal: ctrl.signal })
        .then(function (r) { return r.json().then(function (j) { return { status: r.status, j: j }; }); })
        .then(function (res) {
          if (res.status === 200 && res.j && res.j.ok) {
            stat.envoyer('devis_envoye');
            window.location.assign('/merci');
            return;
          }
          var raison = (res.j && res.j.error) || 'Envoi impossible pour le moment.';
          message('error', '<p>' + raison + ' Vous pouvez nous joindre directement :</p>' + repli());
          stat.envoyer('devis_erreur', { x: String(res.status) });
        })
        .catch(function () {
          message('error', '<p>Le réseau n’a pas répondu. Votre demande est prête à partir par WhatsApp :</p>' + repli());
          stat.envoyer('devis_erreur', { x: 'reseau' });
        })
        .finally(function () { clearTimeout(minuterie); enCours = false; submit.disabled = false; submit.textContent = texte; });
    });
  }

  /* ---------- Apparitions au défilement ---------- */
  function Reveal() {
    var cibles = document.querySelectorAll('.reveal');
    if (reduceMotion || !('IntersectionObserver' in window)) { cibles.forEach(function (el) { el.classList.add('is-visible'); }); return; }
    var obs = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { if (en.isIntersecting) { en.target.classList.add('is-visible'); obs.unobserve(en.target); } });
    }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });
    cibles.forEach(function (el) { obs.observe(el); });
  }

  /* ---------- Clics de contact mesurés (téléphone, WhatsApp, Messenger, e-mail) ---------- */
  function Contacts() {
    document.addEventListener('click', function (e) {
      var a = e.target.closest('a[href^="tel:"], a[href*="wa.me"], a[href*="m.me"], a[href^="mailto:"]');
      if (!a) return;
      var h = a.getAttribute('href');
      stat.envoyer(h.indexOf('tel:') === 0 ? 'clic_tel' : h.indexOf('mailto:') === 0 ? 'clic_email' : h.indexOf('wa.me') > -1 ? 'clic_whatsapp' : 'clic_messenger');
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    Navigation(); Calculator(); Lightbox(); ContactForm(); Reveal(); Contacts();
    var an = document.getElementById('annee'); if (an) an.textContent = String(new Date().getFullYear());
    stat.envoyer('page');
  });
})();
