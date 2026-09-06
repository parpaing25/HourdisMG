/* ═══════════════════════════════════════════════════════════════════════════
   Bot de veille Hourdis — interface
   ═══════════════════════════════════════════════════════════════════════════
   Une seule page, neuf vues, aucun cadre applicatif. L'état vient de /api/etat
   toutes les 3 secondes ; le reste est demandé quand une vue s'ouvre.
   Les réglages se lisent et s'écrivent par les attributs data-cle / data-type
   des champs : ajouter un réglage = une clé dans config.py + un champ ici.
   ═══════════════════════════════════════════════════════════════════════════ */

const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];

const etat = {
  vue: "bord",
  config: {},
  sources: [],
  trouvailles: [],
  selection: new Set(),
  selectionCandidats: new Set(),
  ouvert: null,
  dateOuverte: null,
  dernierEtat: null,
  publicationEnCours: null,   // id de la trouvaille qu'un « Publier en un clic » traite
};

const GENRES = { video: "Vidéo", article: "Article", actualite: "Actualité", pdf: "Guide PDF", post_fb: "Publication FB" };
const GENRES_ICO = { video: "🎥", article: "📄", actualite: "📰", pdf: "📕", post_fb: "📘" };
const GENRES_SOURCE = {
  recherche_web: "Recherche web", youtube_recherche: "Recherche YouTube", youtube_chaine: "Chaîne YouTube",
  flux: "Flux RSS", site: "Site", page_fb: "Page Facebook", groupe_fb: "Groupe Facebook",
};
const STATUTS = { nouvelle: "À trier", gardee: "Gardée", programmee: "Programmée", publiee: "Publiée", ecartee: "Écartée" };
const ORIGINES_DATE = { jsonld: "balise", meta: "balise", time: "balise", url: "adresse", url_mois: "≈ mois", texte: "texte",
  flux: "flux", youtube: "YouTube", facebook: "Facebook", manuelle: "saisie" };

// ── Utilitaires ────────────────────────────────────────────────────────────
function echapper(t) {
  return String(t ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
function heure(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  return isNaN(d) ? "" : d.toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });
}
function dateCourte(iso) {
  if (!iso) return "—";
  const d = new Date(iso.length === 10 ? iso + "T00:00:00" : iso);
  return isNaN(d) ? iso : d.toLocaleDateString("fr-FR", { day: "2-digit", month: "2-digit", year: "numeric" });
}
function nombre(n) { return n === null || n === undefined ? "—" : String(n).replace(/\B(?=(\d{3})+(?!\d))/g, " "); }
function duree(s) {
  if (!s) return "";
  const m = Math.floor(s / 60), r = s % 60;
  return m >= 60 ? `${Math.floor(m / 60)} h ${String(m % 60).padStart(2, "0")}` : m ? `${m} min` : `${r} s`;
}
function surClic(selecteur, fonction) { const el = $(selecteur); if (el) el.onclick = fonction; return el; }

let minuterieToast;
function toast(message, genre = "") {
  const boite = $("#toast");
  boite.textContent = message; boite.className = "toast " + genre; boite.hidden = false;
  clearTimeout(minuterieToast);
  minuterieToast = setTimeout(() => { boite.hidden = true; }, 5200);
}

async function api(chemin, options = {}) {
  const reponse = await fetch(chemin, {
    headers: { "Content-Type": "application/json" }, ...options,
    body: options.corps ? JSON.stringify(options.corps) : undefined,
  });
  const brut = await reponse.text();
  let donnees = null;
  try { donnees = brut ? JSON.parse(brut) : null; } catch { donnees = null; }
  if (!reponse.ok) throw new Error((donnees && (donnees.detail || donnees.message)) || brut || "Erreur");
  return donnees;
}
async function agir(promesse, ok) {
  try { const r = await promesse; if (ok) toast(typeof ok === "function" ? ok(r) : ok, "succes"); return r; }
  catch (e) { toast(e.message, "erreur"); return null; }
}

// ── Navigation ─────────────────────────────────────────────────────────────
const TITRES = { bord: "Tableau de bord", trouvailles: "Trouvailles", publication: "Publication", dossiers: "Dossiers",
  sources: "Sources", candidats: "Nouvelles sources", automatisation: "Automatisation", reglages: "Réglages", journal: "Journal" };

function afficher(vue) {
  etat.vue = vue;
  $$(".onglet").forEach((b) => b.classList.toggle("actif", b.dataset.vue === vue));
  $$(".vue").forEach((s) => s.classList.toggle("active", s.id === "vue-" + vue));
  $("#titre-vue").textContent = TITRES[vue] || vue;
  $("#nav").classList.remove("ouverte"); $("#nav-voile").hidden = true;
  ({ trouvailles: chargerTrouvailles, publication: chargerPublication, dossiers: chargerDossiers,
     sources: chargerSources, candidats: chargerCandidats, automatisation: chargerConfig,
     reglages: chargerConfig, journal: chargerJournal }[vue] || (() => {}))();
  try { localStorage.setItem("hourdis-vue", vue); } catch {}
}
$$(".onglet").forEach((b) => (b.onclick = () => afficher(b.dataset.vue)));
surClic("#btn-nav", () => { $("#nav").classList.add("ouverte"); $("#nav-voile").hidden = false; });
surClic("#nav-voile", () => { $("#nav").classList.remove("ouverte"); $("#nav-voile").hidden = true; });

// ── État (toutes les 3 s) ──────────────────────────────────────────────────
async function rafraichirEtat() {
  let e;
  try { e = await api("/api/etat"); } catch { $("#barre-etat").textContent = "Serveur injoignable…"; return; }
  etat.dernierEtat = e;
  const c = e.compteurs;
  const pastille = (id, n) => { const p = $(id); p.textContent = n; p.classList.toggle("zero", !n); };
  pastille("#pastille-trier", c.nouvelle);
  pastille("#pastille-file", e.publication.en_file);
  pastille("#pastille-candidats", e.candidats);

  const col = e.collecte;
  const enCours = col.actif || (e.tache.actif && e.tache.type === "collecte");
  const ec = $("#etat-collecte");
  ec.className = "etat " + (enCours ? "actif" : "");
  ec.querySelector("span").textContent = enCours ? `Tournée : ${col.source || "…"}` : "Bot au repos";
  const ef = $("#etat-fb");
  ef.className = "etat " + (e.session_fb ? "vert" : "");
  ef.querySelector("span").textContent = e.session_fb ? "Facebook : compte connecté" : "Facebook : non connecté";
  const ep = $("#etat-pub");
  ep.className = "etat " + (e.publication.active ? "vert" : "jaune");
  ep.querySelector("span").textContent = e.publication.active ? "Publication : active" : "Publication : préparée seulement";
  $("#barre-etat").textContent = enCours
    ? `${col.examines} examinée(s) · ${col.trouvees} gardée(s)` + (e.tache.type && e.tache.type !== "collecte" ? ` · ${e.tache.type}` : "")
    : (e.tache.actif ? `Tâche : ${e.tache.type}` : (e.planning.prochain ? `Prochaine tournée ${e.planning.prochain}` : ""));

  // La publication en un clic : son avancement dans le panneau, et la fin annoncée.
  const pub = e.tache.actif && e.tache.type === "publication";
  const ucProg = $("#p-uc-progression");
  if (pub && etat.ouvert && (!e.tache.cible || e.tache.cible === etat.ouvert.id)) {
    ucProg.hidden = false; ucProg.textContent = e.tache.detail || "En cours…";
  }
  if (!pub && etat.publicationEnCours) {
    const id = etat.publicationEnCours; etat.publicationEnCours = null;
    const derniere = (e.journal || []).find((l) => /Publiée en un clic|À blanc|refusé la publication|publication :/.test(l.message));
    toast(derniere ? derniere.message : "Publication terminée.", derniere && /refus|erreur/.test(derniere.message) ? "erreur" : "succes");
    if (etat.ouvert && etat.ouvert.id === id) ouvrirPanneau(id); else rafraichirVue();
  }
  $("#btn-collecte").hidden = enCours; $("#btn-arret").hidden = !enCours;
  const prog = $("#progression");
  prog.hidden = !enCours && !col.fin;
  if (!prog.hidden) {
    prog.innerHTML = (enCours ? `<b>En cours</b> — ${echapper(col.source || "préparation")}<br>` : `<b>Dernière tournée</b> terminée à ${heure(col.fin)}<br>`)
      + `${col.examines} examinée(s) · <b>${col.trouvees} gardée(s)</b> · ${col.rangees} rangée(s) · ${col.ecartees_hors_sujet} hors sujet · ${col.ecartees_score} sous le score · ${col.ecartees_doublons} doublon(s) · ${col.ecartees_anciennes} anciennes · ${col.ecartees_sans_contenu || 0} sans contenu`
      + (col.relues_ia ? ` · ${col.relues_ia} relue(s) IA` : "") + (col.facebook ? ` · Facebook : ${echapper(col.facebook)}` : "");
  }
  $("#chemin-collecte").textContent = e.dossier_collecte;

  if (etat.vue === "bord") rendreBord(e);
}

function rendreBord(e) {
  const c = e.compteurs;
  $("#tuiles").innerHTML = [
    ["nouvelle", c.nouvelle, "à trier", "terre"], ["gardee", c.gardee, "gardées", "vert"], ["programmee", c.programmee, "programmées", "bleu"],
    ["publiee", c.publiee, "publiées", ""], ["video", c.videos, "vidéos", ""], ["article", c.articles, "articles", ""],
    ["pdf", c.pdf, "guides PDF", ""], ["dates", c.dates, "dates (dossiers)", ""], ["ecartee", c.ecartee, "écartées", ""],
  ].map(([cle, n, lib, coul]) => `<div class="tuile ${coul}" data-tuile="${cle}"><b>${nombre(n)}</b><span>${lib}</span></div>`).join("");
  $$("#tuiles .tuile").forEach((t) => (t.onclick = () => {
    const cle = t.dataset.tuile;
    if (cle === "dates") return afficher("dossiers");
    if (["video", "article", "pdf"].includes(cle)) { $("#f-genre").value = cle; $("#f-statut").value = "actives"; }
    else { $("#f-statut").value = cle; $("#f-genre").value = ""; }
    afficher("trouvailles");
  }));
  const p = e.planning;
  $("#planning-bord").innerHTML = [
    ["Tournées automatiques", p.actif ? `oui — ${p.heures.join(", ")}` : "éteintes (Automatisation)"],
    ["Prochaine tournée", p.prochain || "—"],
    ["Gardables aujourd'hui", `${p.trouves}${p.objectif ? ` / objectif ${p.objectif}` : ""}${p.atteint ? " ✓" : ""}`],
    ["Publication programmée", p.publication_auto ? `oui — ${p.heures_publication.join(", ")}` : "non"],
    ["Sources actives", e.sources_actives],
    ["Session Claude sur ce PC", p.session_claude ? "oui — la partie Facebook attend" : "non"],
    ["Modèle (IA)", e.llm_actif ? "allumé" : "éteint"],
  ].map(([k, v]) => `<div><span>${k}</span><span>${echapper(v)}</span></div>`).join("");
  rendreJournal("#journal-bord", e.journal);
  if (!rendreBord.dernieres || Date.now() - rendreBord.dernieres > 15000) {
    rendreBord.dernieres = Date.now();
    api("/api/trouvailles?statut=actives&tri=collecte&limite=6").then((r) => {
      $("#dernieres").innerHTML = r.trouvailles.length ? r.trouvailles.map((t) => carteTrouvaille(t, true)).join("")
        : `<p class="aide">Rien encore — lancez la tournée.</p>`;
      brancherCartes("#dernieres");
    }).catch(() => {});
  }
}

function rendreJournal(sel, lignes) {
  $(sel).innerHTML = lignes.map((l) => `<li class="n-${l.niveau}"><time>${heure(l.ts)}</time><span>${echapper(l.message)}</span></li>`).join("");
}

// ── Tableau de bord : actions ──────────────────────────────────────────────
surClic("#btn-collecte", () => agir(api("/api/collecte", { method: "POST" }), "Tournée lancée."));
surClic("#btn-arret", () => agir(api("/api/collecte/arret", { method: "POST" }), "Arrêt demandé."));
surClic("#btn-ouvrir-racine", () => agir(api("/api/dossiers/ouvrir", { method: "POST", corps: { chemin: "" } }), (r) => `Ouvert : ${r.chemin}`));
surClic("#btn-importer", async () => {
  const url = $("#import-url").value.trim();
  if (!url) return toast("Collez une adresse.", "erreur");
  if (await agir(api("/api/importer", { method: "POST", corps: { url } }), "Import lancé — suivez le journal.")) $("#import-url").value = "";
});

// ── Trouvailles ────────────────────────────────────────────────────────────
function badgeDate(t) {
  if (!t.publie_le) return `<span class="badge date-douteuse" title="La page ne dit pas de quand elle date">date inconnue</span>`;
  const origine = ORIGINES_DATE[t.date_origine] || "";
  const douteuse = ["url_mois", "texte"].includes(t.date_origine);
  return `<span class="badge ${douteuse ? "date-douteuse" : ""}" title="Date lue : ${echapper(origine)}">${dateCourte(t.publie_le)}${douteuse ? " ?" : ""}</span>`;
}
function badgeScore(s) { return `<span class="badge score ${s >= 65 ? "haut" : s < 45 ? "bas" : ""}">${s}</span>`; }

function carteTrouvaille(t, mini = false) {
  const image = t.images && t.images.length ? `/media/${t.id}/${encodeURIComponent(t.images[0].replace(/^images\//, ""))}` : "";
  const coche = mini ? "" : `<input type="checkbox" class="coche" data-id="${t.id}" ${etat.selection.has(t.id) ? "checked" : ""}>`;
  const themes = (t.themes || []).filter((x) => x !== "prix").slice(0, 4).map((x) => `<span class="badge theme">${x}</span>`).join("");
  const statut = t.statut !== "nouvelle" ? `<span class="badge statut-${t.statut}">${STATUTS[t.statut]}</span>` : "";
  const avert = t.avertissements && t.avertissements.length ? `<span class="badge rouge" title="${echapper(t.avertissements.join(" · "))}">⚠ à vérifier</span>` : "";
  const actions = mini ? "" : `<div class="actions">
      ${t.statut !== "publiee" && t.statut !== "ecartee" ? `<button class="btn petit un-clic-btn" data-act="un-clic" data-id="${t.id}" title="Refait le texte, importe les médias, publie sur la page">🚀 Publier</button>` : ""}
      ${t.statut === "nouvelle" || t.statut === "ecartee" ? `<button class="btn petit" data-act="garder" data-id="${t.id}">Garder</button>` : ""}
      ${t.statut !== "ecartee" ? `<button class="btn petit" data-act="ecarter" data-id="${t.id}">Écarter</button>` : ""}
      ${t.statut === "gardee" ? `<button class="btn petit" data-act="programmer" data-id="${t.id}">Programmer</button>` : ""}
      <button class="btn petit" data-act="detail" data-id="${t.id}">Détail / post</button>
      ${t.dossier ? `<button class="btn petit" data-act="ouvrir" data-id="${t.id}">Dossier</button>` : ""}
    </div>`;
  return `<article class="fiche ${mini ? "mini" : ""} ${etat.selection.has(t.id) ? "selectionnee" : ""}" data-id="${t.id}">
    <div class="vignette" style="${image ? `background-image:url('${image}')` : ""}">${coche}
      <span class="genre-ico">${GENRES_ICO[t.genre] || ""} ${GENRES[t.genre] || t.genre}${t.duree_s ? " · " + duree(t.duree_s) : ""}</span></div>
    <div class="corps">
      <div class="meta">${badgeScore(t.score)}${t.score_ia ? `<span class="badge" title="score du modèle">IA ${t.score_ia}</span>` : ""}${badgeDate(t)}${statut}${avert}${t.langue ? `<span class="badge">${t.langue}</span>` : ""}</div>
      <h3><a href="${echapper(t.url)}" target="_blank" rel="noopener">${echapper(t.titre)}</a></h3>
      <div class="meta">${echapper(t.auteur || "")}${t.auteur && t.source_nom ? " · " : ""}<span title="source">${echapper(t.source_nom || "")}</span>${t.vues ? ` · ${nombre(t.vues)} vues` : ""}</div>
      ${mini ? "" : `<div class="extrait">${echapper(t.resume || "")}</div>`}
      <div class="meta">${themes}${t.motif_ecart ? `<span class="badge rouge" title="${echapper(t.motif_ecart)}">écartée : ${echapper(t.motif_ecart.slice(0, 40))}</span>` : ""}</div>
      ${actions}
    </div></article>`;
}

function brancherCartes(conteneur) {
  $$(`${conteneur} [data-act]`).forEach((b) => (b.onclick = (ev) => { ev.stopPropagation(); actionTrouvaille(b.dataset.act, b.dataset.id); }));
  $$(`${conteneur} .coche`).forEach((c) => (c.onchange = () => {
    c.checked ? etat.selection.add(c.dataset.id) : etat.selection.delete(c.dataset.id);
    c.closest(".fiche").classList.toggle("selectionnee", c.checked);
    rendreLot();
  }));
  $$(`${conteneur} .fiche.mini`).forEach((f) => (f.onclick = () => ouvrirPanneau(f.dataset.id)));
}

async function actionTrouvaille(act, id) {
  const statuts = { garder: "gardee", ecarter: "ecartee", programmer: "programmee" };
  if (statuts[act]) {
    if (await agir(api(`/api/trouvailles/${id}`, { method: "PATCH", corps: { statut: statuts[act] } }), `→ ${STATUTS[statuts[act]]}`)) {
      if (etat.ouvert && etat.ouvert.id === id) ouvrirPanneau(id); else rafraichirVue();
    }
  } else if (act === "detail") ouvrirPanneau(id);
  else if (act === "ouvrir") agir(api(`/api/trouvailles/${id}/ouvrir`, { method: "POST" }), (r) => `Ouvert : ${r.chemin}`);
  else if (act === "un-clic") publierEnUnClic(id, {});
}

/** Le bouton « Publier en un clic » : texte refait + médias + envoi, dans un fil du serveur.
 *  Si la publication est éteinte, on propose de l'allumer et on recommence — c'est
 *  Andry qui vient de cliquer, la décision est prise. */
async function publierEnUnClic(id, options) {
  const corps = { a_blanc: !!options.a_blanc, message: options.message || "",
    refaire_texte: options.refaire_texte ?? null, avec_video: options.avec_video ?? null };
  if (!corps.a_blanc && !confirm("Publier cette trouvaille sur la page Hourdis Madagascar, avec ses médias ?")) return;
  try {
    await api(`/api/publication/${id}/un-clic`, { method: "POST", corps });
  } catch (e) {
    if (/éteinte/.test(e.message)) {
      if (!confirm("La publication est éteinte. L'allumer maintenant et publier ?")) return;
      const r = await agir(api(`/api/publication/${id}/un-clic`, { method: "POST", corps: { ...corps, allumer: true } }));
      if (!r) return;
    } else { toast(e.message, "erreur"); return; }
  }
  etat.publicationEnCours = id;
  toast(corps.a_blanc ? "Essai à blanc lancé — suivez l'avancement." : "Publication lancée — le texte, les médias, puis l'envoi. Suivez l'avancement.", "succes");
  if (etat.ouvert && etat.ouvert.id === id) { const p = $("#p-uc-progression"); p.hidden = false; p.textContent = "Démarrage…"; }
}
function rafraichirVue() {
  ({ trouvailles: chargerTrouvailles, publication: chargerPublication, dossiers: () => chargerDossiers(true) }[etat.vue] || rafraichirEtat)();
}

async function chargerTrouvailles() {
  const p = new URLSearchParams({
    statut: $("#f-statut").value, genre: $("#f-genre").value, theme: $("#f-theme").value,
    source_id: $("#f-source").value, q: $("#f-q").value.trim(), tri: $("#f-tri").value, limite: 300,
  });
  let r;
  try { r = await api("/api/trouvailles?" + p); } catch (e) { return toast(e.message, "erreur"); }
  etat.trouvailles = r.trouvailles;
  const selTheme = $("#f-theme"), valeur = selTheme.value;
  selTheme.innerHTML = `<option value="">Tous les thèmes</option>` + r.themes.map(([t, n]) => `<option value="${t}">${t} (${n})</option>`).join("");
  selTheme.value = valeur;
  if (!etat.sources.length) await chargerSources(true);
  const selSrc = $("#f-source"), vs = selSrc.value;
  selSrc.innerHTML = `<option value="0">Toutes les sources</option>` + etat.sources.map((s) => `<option value="${s.id}">${echapper(s.nom)}</option>`).join("");
  selSrc.value = vs;
  $("#trouvailles-aide").textContent = `${r.trouvailles.length} trouvaille(s). Cochez pour agir en lot ; « Détail / post » ouvre le brouillon de publication.`;
  $("#grille-trouvailles").innerHTML = r.trouvailles.length ? r.trouvailles.map((t) => carteTrouvaille(t)).join("")
    : `<p class="aide">Rien avec ces filtres.</p>`;
  brancherCartes("#grille-trouvailles");
  rendreLot();
}
["#f-statut", "#f-genre", "#f-theme", "#f-source", "#f-tri"].forEach((s) => ($(s).onchange = chargerTrouvailles));
let minuterieQ; $("#f-q").oninput = () => { clearTimeout(minuterieQ); minuterieQ = setTimeout(chargerTrouvailles, 350); };

function rendreLot() {
  const n = etat.selection.size;
  $("#lot").hidden = !n;
  $("#lot-n").textContent = `${n} sélectionnée${n > 1 ? "s" : ""}`;
}
$$("[data-lot]").forEach((b) => (b.onclick = async () => {
  const ids = [...etat.selection];
  if (!ids.length) return;
  if (b.dataset.lot === "supprimer" && !confirm(`Supprimer ${ids.length} trouvaille(s) et leurs dossiers ?`)) return;
  if (await agir(api("/api/trouvailles/lot", { method: "POST", corps: { ids, action: b.dataset.lot } }), (r) => `${r.n} traitée(s).`)) {
    etat.selection.clear(); chargerTrouvailles();
  }
}));
surClic("#lot-vider", () => { etat.selection.clear(); chargerTrouvailles(); });
surClic("#btn-renoter", async () => {
  if (!confirm("Recalculer la note de toute la pile à trier avec les règles d'aujourd'hui ?\n\nCe que vous avez gardé, programmé ou publié n'est pas touché.")) return;
  if (await agir(api("/api/trouvailles/renoter", { method: "POST" }), "Renotation lancée — le journal dira ce qui a changé.")) {
    setTimeout(() => { chargerTrouvailles(); }, 4000);
  }
});

// ── Panneau de détail ──────────────────────────────────────────────────────
async function ouvrirPanneau(id) {
  let t;
  try { t = await api(`/api/trouvailles/${id}`); } catch (e) { return toast(e.message, "erreur"); }
  etat.ouvert = t;
  $("#p-genre").textContent = `${GENRES_ICO[t.genre] || ""} ${GENRES[t.genre] || t.genre}`;
  $("#p-score").textContent = `${t.score}/100${t.score_ia ? ` · IA ${t.score_ia}` : ""}`;
  $("#p-date").innerHTML = badgeDate(t).replace(/^<span[^>]*>|<\/span>$/g, "");
  $("#p-titre").innerHTML = `<a href="${echapper(t.url)}" target="_blank" rel="noopener">${echapper(t.titre)}</a>`;
  $("#p-meta").textContent = [t.auteur, t.source_nom, STATUTS[t.statut], t.langue, t.duree_s ? duree(t.duree_s) : "", t.vues ? `${nombre(t.vues)} vues` : "",
    t.dossier ? `dossier : ${t.dossier}` : "pas de dossier (écartée)"].filter(Boolean).join(" · ");
  $("#p-images").innerHTML = (t.images || []).map((i) => `<img src="/media/${t.id}/${encodeURIComponent(i.replace(/^images\//, ""))}" alt="">`).join("");
  $("#p-post").value = t.post || "";
  $("#p-publie-le").value = t.publie_le || "";
  $("#p-note").value = t.note || "";
  $("#p-conseils").innerHTML = (t.conseils && t.conseils.length ? `<ul>${t.conseils.map((c) => `<li>${echapper(c)}</li>`).join("")}</ul>` : `<p class="aide">Aucun conseil extrait (le modèle est éteint ou n'a pas relu).</p>`)
    + (t.avertissements && t.avertissements.length ? `<ul class="avert">${t.avertissements.map((a) => `<li>⚠ ${echapper(a)}</li>`).join("")}</ul>` : "");
  $("#p-motifs").textContent = (t.motifs || []).join(" · ") + (t.motif_ecart ? ` — écartée : ${t.motif_ecart}` : "");
  $("#p-texte").textContent = t.texte || "(aucun texte)";
  const pub = etat.dernierEtat && etat.dernierEtat.publication.active;
  $("#p-publication-aide").textContent = pub ? "La publication est active : « Publier maintenant » envoie sur la page." : "Publication éteinte : copiez le texte, ou allumez-la dans Réglages. « À blanc » montre ce qui partirait.";
  const ucp = $("#p-uc-progression");
  ucp.hidden = !(etat.publicationEnCours === t.id); ucp.textContent = "";
  $("#p-uc-aide").textContent = t.statut === "publiee"
    ? `Déjà publiée sur la page${t.publie_fb_id ? ` (${t.publie_fb_id})` : ""}.`
    : (t.genre === "video" ? "Refait le texte, télécharge la vidéo YouTube (720p max) et la publie en vidéo native, source citée. Si la vidéo est refusée ou trop longue : vignette + lien."
      : "Refait le texte, importe les images de la page, et publie un album avec le texte et le lien.");
  $("#p-uc-video").closest("label").hidden = t.genre !== "video";
  const dans10 = new Date(Date.now() + 3600 * 1000); dans10.setSeconds(0, 0);
  $("#p-quand").value = dans10.toISOString().slice(0, 16);
  $("#panneau").hidden = false; $("#voile").hidden = false;
}
function fermerPanneau() { $("#panneau").hidden = true; $("#voile").hidden = true; etat.ouvert = null; }
surClic("#p-fermer", fermerPanneau); surClic("#voile", fermerPanneau);
document.addEventListener("keydown", (e) => { if (e.key === "Escape" && !$("#panneau").hidden) fermerPanneau(); });

$$("[data-p]").forEach((b) => (b.onclick = async () => {
  const t = etat.ouvert; if (!t) return;
  const id = t.id, act = b.dataset.p;
  if (["garder", "ecarter", "programmer"].includes(act)) return actionTrouvaille(act, id);
  if (act === "un-clic" || act === "un-clic-blanc") {
    return publierEnUnClic(id, {
      a_blanc: act === "un-clic-blanc",
      refaire_texte: $("#p-uc-texte").checked,
      avec_video: $("#p-uc-video").checked,
      // Le texte du panneau est imposé seulement si Andry a décoché « refaire » : sinon on le refait.
      message: $("#p-uc-texte").checked ? "" : $("#p-post").value,
    });
  }
  if (act === "ouvrir") return actionTrouvaille("ouvrir", id);
  if (act === "supprimer") {
    if (!confirm("Supprimer cette trouvaille et son dossier ?")) return;
    if (await agir(api(`/api/trouvailles/${id}`, { method: "DELETE" }), "Supprimée.")) { fermerPanneau(); rafraichirVue(); }
    return;
  }
  if (act === "relire") return agir(api(`/api/trouvailles/${id}/relire`, { method: "POST" }), "Relecture lancée — le panneau se mettra à jour dans le journal.");
  if (act.startsWith("rediger-")) {
    const r = await agir(api(`/api/trouvailles/${id}/rediger`, { method: "POST", corps: { langue: act.split("-")[1] } }), "Brouillon rédigé.");
    if (r) $("#p-post").value = r.post;
    return;
  }
  if (act === "post-enregistrer") return agir(api(`/api/trouvailles/${id}`, { method: "PATCH", corps: { post: $("#p-post").value } }), "Texte enregistré (et post-facebook.txt réécrit).");
  if (act === "copier") {
    try { await navigator.clipboard.writeText($("#p-post").value); toast("Copié.", "succes"); } catch { toast("Copie refusée par le navigateur.", "erreur"); }
    return;
  }
  if (act === "meta-enregistrer") {
    const r = await agir(api(`/api/trouvailles/${id}`, { method: "PATCH", corps: { publie_le: $("#p-publie-le").value.trim(), note: $("#p-note").value } }), "Enregistré — le dossier a suivi la date.");
    if (r) { ouvrirPanneau(id); rafraichirVue(); }
    return;
  }
  if (act === "publier" || act === "programmer-fb" || act === "a-blanc") {
    const corps = { message: $("#p-post").value, a_blanc: act === "a-blanc" };
    if (act === "programmer-fb") corps.quand = $("#p-quand").value;
    if (act === "publier" && !confirm("Publier maintenant sur la page Hourdis Madagascar ?")) return;
    const r = await agir(api(`/api/publication/${id}`, { method: "POST", corps }),
      (r) => r.a_blanc ? `À blanc : ${r.photo ? "photo + légende" : "texte + lien"}, ${r.message.length} caractères — rien envoyé.` : (r.programme ? `Programmée pour ${dateCourte(r.programme)} ${heure(r.programme)}.` : `Publiée (${r.fb_id}).`));
    if (r && !r.a_blanc) { ouvrirPanneau(id); rafraichirVue(); }
  }
}));

// ── Publication ────────────────────────────────────────────────────────────
async function chargerPublication() {
  let r;
  try { r = await api("/api/publication"); } catch (e) { return toast(e.message, "erreur"); }
  $("#publication-mode").textContent = r.active
    ? `Publication ACTIVE${r.auto ? " · programmation automatique des « programmées » allumée" : ""}. Chaque envoi reste un clic de votre part (ou une trouvaille que vous avez passée en programmée).`
    : "Publication éteinte : les brouillons sont prêts dans chaque dossier (post-facebook.txt) et dans le panneau de détail — à copier-coller. Allumez-la dans Réglages pour publier d'ici.";
  $("#grille-file").innerHTML = r.file.length ? r.file.map((t) => carteTrouvaille(t)).join("") : `<p class="aide">Rien en file : gardez des trouvailles dans l'onglet Trouvailles.</p>`;
  brancherCartes("#grille-file");
  $("#table-historique tbody").innerHTML = r.historique.map((h) => `<tr><td>${dateCourte(h.quand)} ${heure(h.quand)}</td><td>${echapper(h.titre || h.trouvaille)}</td><td>${h.a_blanc ? "à blanc" : echapper(h.resultat)}${h.fb_id ? ` <span class="badge vert">${echapper(h.fb_id)}</span>` : ""}</td><td>${h.programme ? dateCourte(h.programme) + " " + heure(h.programme) : ""}</td></tr>`).join("")
    || `<tr><td colspan="4" class="aide">Aucune publication encore.</td></tr>`;
}
surClic("#btn-page-verifier", async () => {
  const r = await agir(api("/api/facebook/page?force=true"));
  if (!r) return;
  $("#page-etat").textContent = r.ok ? `Page « ${r.nom} » — ${nombre(r.abonnes)} abonnés — jeton valide.` : `Jeton refusé : ${r.erreur}`;
  $("#page-etat").className = "aide " + (r.ok ? "" : "n-erreur");
});

// ── Dossiers ───────────────────────────────────────────────────────────────
async function chargerDossiers(garderDate = false) {
  let r;
  try { r = await api("/api/dossiers"); } catch (e) { return toast(e.message, "erreur"); }
  $("#dossiers-racine").textContent = r.racine;
  if (!garderDate || !etat.dateOuverte) etat.dateOuverte = r.dates.length ? r.dates[0].date : null;
  $("#liste-dates").innerHTML = r.dates.map((d) => `<li data-date="${d.date}" class="${d.date === etat.dateOuverte ? "actif" : ""}"><span>${d.date ? dateCourte(d.date) : "date inconnue"}</span><small>${d.n} · max ${d.meilleur}</small></li>`).join("")
    || `<li class="aide">Aucun dossier encore.</li>`;
  $$("#liste-dates li[data-date]").forEach((li) => (li.onclick = () => { etat.dateOuverte = li.dataset.date; chargerDossiers(true); }));
  if (etat.dateOuverte === null) { $("#grille-date").innerHTML = ""; return; }
  const f = await api(`/api/trouvailles?statut=&date_pub=${etat.dateOuverte || "inconnue"}&tri=score&limite=300`);
  const fiches = f.trouvailles.filter((t) => t.dossier);
  $("#titre-date").textContent = `${etat.dateOuverte ? dateCourte(etat.dateOuverte) : "Date inconnue"} — ${fiches.length} fiche(s)`;
  $("#grille-date").innerHTML = fiches.map((t) => carteTrouvaille(t)).join("");
  brancherCartes("#grille-date");
}
surClic("#btn-dossiers-ouvrir", () => agir(api("/api/dossiers/ouvrir", { method: "POST", corps: { chemin: etat.dateOuverte || "" } }), (r) => `Ouvert : ${r.chemin}`));

// ── Sources ────────────────────────────────────────────────────────────────
async function chargerSources(silencieux = false) {
  try { etat.sources = await api("/api/sources"); } catch (e) { if (!silencieux) toast(e.message, "erreur"); return; }
  if (silencieux) return;
  const corps = $("#table-sources tbody");
  corps.innerHTML = etat.sources.map((s) => `<tr class="${s.actif ? "" : "inactif"}" data-id="${s.id}">
      <td><button class="bascule ${s.actif ? "on" : ""}" data-src="actif" title="${s.actif ? "Active" : "En pause"}"></button></td>
      <td><strong>${echapper(s.nom)}</strong><div class="url">${echapper(s.requete || s.url)}</div></td>
      <td><span class="badge">${GENRES_SOURCE[s.genre] || s.genre}</span></td>
      <td class="num">${nombre(s.nb_examines)}</td>
      <td class="num">${nombre(s.nb_gardees)}</td>
      <td>${s.derniere_collecte ? dateCourte(s.derniere_collecte) + " " + heure(s.derniere_collecte) : "jamais"}</td>
      <td>${s.echecs ? `<span class="badge rouge" title="${echapper(s.dernier_echec)}">${s.echecs} échec(s)</span>` : (s.derniere_collecte ? `<span class="badge vert">ok</span>` : "")}</td>
      <td><div class="rangee" style="gap:4px"><button class="btn petit" data-src="collecter">Collecter</button><button class="btn petit danger" data-src="supprimer">×</button></div></td>
    </tr>`).join("") || `<tr><td colspan="8" class="aide">Aucune source.</td></tr>`;
  $$("#table-sources [data-src]").forEach((b) => (b.onclick = async () => {
    const id = b.closest("tr").dataset.id, s = etat.sources.find((x) => String(x.id) === id);
    if (b.dataset.src === "actif") await agir(api(`/api/sources/${id}`, { method: "PATCH", corps: { actif: !s.actif } }));
    else if (b.dataset.src === "collecter") return agir(api(`/api/sources/${id}/collecter`, { method: "POST" }), `Tournée lancée sur « ${s.nom} ».`);
    else if (b.dataset.src === "supprimer") { if (!confirm(`Supprimer la source « ${s.nom} » ?`)) return; await agir(api(`/api/sources/${id}`, { method: "DELETE" }), "Supprimée."); }
    chargerSources();
  }));
}
surClic("#btn-src-conseillees", async () => {
  const r = await agir(api("/api/sources/conseillees", { method: "POST" }),
    (r) => r.ajoutees ? `${r.ajoutees} source(s) ajoutée(s) : ${r.noms.slice(0, 3).join(", ")}${r.noms.length > 3 ? "…" : ""}` : "Rien à ajouter, vous les avez déjà toutes.");
  if (r) chargerSources();
});
surClic("#btn-src-ajouter", async () => {
  const entree = $("#src-entree").value.trim();
  if (!entree) return toast("Collez une adresse ou tapez des mots.", "erreur");
  const r = await agir(api("/api/sources", { method: "POST", corps: { entree, nom: $("#src-nom").value.trim(), aussi_youtube: $("#src-youtube").checked } }),
    (r) => `${r.sources.length} source(s) ajoutée(s).`);
  if (r) { $("#src-entree").value = ""; $("#src-nom").value = ""; chargerSources(); }
});

// ── Nouvelles sources ──────────────────────────────────────────────────────
async function chargerCandidats() {
  let r;
  try { r = await api("/api/candidats"); } catch (e) { return toast(e.message, "erreur"); }
  $("#candidats-aide").textContent = `${r.candidats.length} candidat(s) au-dessus de la note ${r.seuil}${r.sous_le_seuil ? ` (${r.sous_le_seuil} en dessous, cachés)` : ""} · ${r.compteurs.adopte || 0} adopté(s), ${r.compteurs.ecarte || 0} écarté(s) au total.`;
  $("#table-candidats tbody").innerHTML = r.candidats.map((c) => `<tr data-cle="${echapper(c.cle)}">
      <td><input type="checkbox" class="coche-cand" ${etat.selectionCandidats.has(c.cle) ? "checked" : ""}></td>
      <td><strong>${echapper(c.nom)}</strong><div class="url"><a href="${echapper(c.url)}" target="_blank" rel="noopener">${echapper(c.url)}</a></div></td>
      <td><span class="badge">${GENRES_SOURCE[c.genre] || c.genre}</span></td>
      <td class="num">${c.note}</td><td class="aide">${echapper(c.raison)}</td></tr>`).join("")
    || `<tr><td colspan="5" class="aide">Aucun candidat. Cliquez « Chercher maintenant » après quelques tournées.</td></tr>`;
  $$("#table-candidats .coche-cand").forEach((c) => (c.onchange = () => {
    const cle = c.closest("tr").dataset.cle;
    c.checked ? etat.selectionCandidats.add(cle) : etat.selectionCandidats.delete(cle);
    $("#lot-candidats").hidden = !etat.selectionCandidats.size;
    $("#lot-candidats-n").textContent = `${etat.selectionCandidats.size} coché(s)`;
  }));
  $("#lot-candidats").hidden = !etat.selectionCandidats.size;
}
surClic("#btn-decouvrir", () => agir(api("/api/candidats/decouvrir", { method: "POST" }), "Découverte lancée — revenez dans quelques secondes."));
$$("[data-cand]").forEach((b) => (b.onclick = async () => {
  const cles = [...etat.selectionCandidats]; if (!cles.length) return;
  if (await agir(api(`/api/candidats/${b.dataset.cand}`, { method: "POST", corps: { cles } }), (r) => `${r.n} ${b.dataset.cand === "adopter" ? "adopté(s)" : "écarté(s)"}.`)) {
    etat.selectionCandidats.clear(); chargerCandidats(); chargerSources(true);
  }
}));

// ── Réglages et automatisation (liaison générique) ─────────────────────────
function lireChamp(el) {
  const type = el.dataset.type;
  if (type === "bool") return el.checked;
  if (type === "int") return parseInt(el.value, 10) || 0;
  if (type === "float") return parseFloat(el.value) || 0;
  if (type === "liste") return el.value.split(/[,;\n]/).map((x) => x.trim()).filter(Boolean);
  if (type === "lignes") return el.value.split(/\n/).map((x) => x.trim()).filter(Boolean);
  return el.value;
}
function ecrireChamp(el, valeur) {
  const type = el.dataset.type;
  if (type === "bool") el.checked = !!valeur;
  else if (type === "liste") el.value = (valeur || []).join(", ");
  else if (type === "lignes") el.value = (valeur || []).join("\n");
  else el.value = valeur ?? "";
}
async function chargerConfig() {
  try { etat.config = await api("/api/config"); } catch (e) { return toast(e.message, "erreur"); }
  $$("[data-cle]").forEach((el) => { if (el.dataset.cle in etat.config) ecrireChamp(el, etat.config[el.dataset.cle]); });
  const fb = etat.dernierEtat && etat.dernierEtat.session_fb;
  $("#reglages-fb-etat").textContent = fb ? "Un compte est connecté (session enregistrée)." : "Aucun compte connecté.";
}
$$("[data-enregistrer]").forEach((b) => (b.onclick = async () => {
  const vue = $(`#vue-${b.dataset.enregistrer}`);
  const config = {};
  $$("[data-cle]", vue).forEach((el) => { config[el.dataset.cle] = lireChamp(el); });
  if (await agir(api("/api/config", { method: "PUT", corps: { config } }), "Réglages enregistrés.")) chargerConfig();
}));
surClic("#btn-llm-test", async () => {
  $("#llm-test-resultat").textContent = "Test en cours…";
  const r = await agir(api("/api/llm/test", { method: "POST" }));
  if (!r) return;
  $("#llm-test-resultat").textContent = r.ok ? `OK — ${r.transport} / ${r.modele} : score ${r.score_ia}, « ${r.resume} »` : `Échec : ${r.erreur}`;
});
surClic("#btn-fb-connexion", () => agir(api("/api/facebook/connexion", { method: "POST" }), "Fenêtre Facebook ouverte — connectez-vous, elle se fermera seule."));
surClic("#btn-fb-oublier", () => { if (confirm("Effacer la session Facebook enregistrée ?")) agir(api("/api/facebook/oublier", { method: "POST" }), "Session effacée."); });

// ── Journal ────────────────────────────────────────────────────────────────
async function chargerJournal() {
  const r = await agir(api(`/api/journal?limite=300&niveau=${$("#j-niveau").value}`));
  if (r) rendreJournal("#journal-complet", r);
}
$("#j-niveau").onchange = chargerJournal;
surClic("#btn-journal-rafraichir", chargerJournal);

// ── Démarrage ──────────────────────────────────────────────────────────────
(async function demarrer() {
  await rafraichirEtat();
  let vue = "bord";
  try { vue = localStorage.getItem("hourdis-vue") || "bord"; } catch {}
  afficher(TITRES[vue] ? vue : "bord");
  setInterval(rafraichirEtat, 3000);
  setInterval(() => { if (etat.vue === "trouvailles" && etat.dernierEtat && etat.dernierEtat.collecte.actif) chargerTrouvailles(); }, 15000);
})();
