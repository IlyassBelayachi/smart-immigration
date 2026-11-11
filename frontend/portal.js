"use strict";

const element = id => document.getElementById(id);
const roleNames = { candidate: "Candidat", consultant: "Consultant" };
const caseStates = { submitted: "À examiner", needs_changes: "Complément demandé", completed: "Examen terminé", ready_to_send: "Autorisé pour envoi" };
const eventNames = { submitted: "Dossier transmis", request_changes: "Complément demandé", assign: "Attribution", complete: "Examen terminé", note: "Observation interne", approve_transmission: "Envoi autorisé" };
const profileFields = {
  province: "destination_province", level: "level_of_study", acceptance: "has_letter_of_acceptance",
  pal: "pal_provided", caq: "caq_provided", "public-dli": "dli_is_public",
  "application-date": "application_date", funds: "funds_available_cad",
  tuition: "tuition_first_year_cad", transport: "transport_cost_cad"
};
let selectedRole = "candidate";
let signupMode = false;
let account = null;
let loadedCase = null;
let intakeCatalog = null;
let detailedStudy = false;
let candidateView = "overview";
let candidateRecord = null;
let consultantFilter = "all";
const consultantFilters = {
  all: "Tous les dossiers", submitted: "Dossiers à examiner",
  needs_changes: "Dossiers en attente de complément", closed: "Examens clôturés"
};

function consultantCategory(status) {
  return ["completed", "ready_to_send"].includes(status) ? "closed" : status;
}

function filterConsultantCases() {
  let visible = 0;
  for (const card of element("portal-cases").querySelectorAll("[data-case-category]")) {
    card.hidden = consultantFilter !== "all" && card.dataset.caseCategory !== consultantFilter;
    if (!card.hidden) visible += 1;
  }
  element("consultant-list-title").textContent = consultantFilters[consultantFilter];
  element("consultant-empty").hidden = visible > 0;
  for (const button of document.querySelectorAll("[data-consultant-filter]")) {
    button.setAttribute("aria-pressed", String(button.dataset.consultantFilter === consultantFilter));
  }
}

for (const button of document.querySelectorAll("[data-consultant-filter]")) {
  button.addEventListener("click", () => {
    if (!element("consultant-empty")) return;
    consultantFilter = button.dataset.consultantFilter;
    filterConsultantCases();
    element("consultant-list-title").focus();
  });
}

function setPage(page) {
  for (const name of ["home", "auth", "workspace"]) element("portal-" + name).hidden = name !== page;
  if (page !== "workspace") showCandidateForm(false);
}

function showCandidateForm(visible) {
  element("general-workflow").hidden = !visible || detailedStudy;
  element("candidate-banner").hidden = !visible || !detailedStudy;
  element("candidate-workflow").hidden = !visible || !detailedStudy;
}

function showCandidateView(view) {
  candidateView = view;
  for (const name of ["overview", "documents", "profile"]) element("candidate-" + name).hidden = view !== name;
  for (const button of document.querySelectorAll(".candidate-nav button")) {
    if (button.dataset.candidateView === view) button.setAttribute("aria-current", "page");
    else button.removeAttribute("aria-current");
  }
  const editable = !candidateRecord || candidateRecord.status === "needs_changes";
  const unavailable = element("candidate-form-unavailable");
  unavailable.hidden = view !== "form" || editable;
  if (!unavailable.hidden) unavailable.textContent = "Votre dossier a été transmis. Retrouvez son statut dans Mes candidatures.";
  element("portal-cases").hidden = view !== "cases";
  showCandidateForm(view === "form" && editable);
}

for (const button of document.querySelectorAll("[data-candidate-view]")) {
  button.addEventListener("click", () => showCandidateView(button.dataset.candidateView));
}

function renderCandidateDashboard(record) {
  element("candidate-greeting").textContent = "Bonjour, " + account.name;
  const status = record ? caseStates[record.status] : "À préparer";
  element("dashboard-case-status").textContent = status;
  const next = {
    submitted: ["Votre dossier a été transmis. Vous pouvez suivre son examen ici.", "Suivre mon dossier", "cases"],
    needs_changes: ["Votre consultant attend un complément. Consultez son message avant de reprendre le formulaire.", "Voir le complément demandé", "cases"],
    completed: ["L’examen de votre dossier est terminé. Retrouvez son historique dans vos candidatures.", "Voir mon dossier", "cases"],
    ready_to_send: ["Votre consultant a autorisé l’envoi du dossier. Consultez le détail de sa décision.", "Voir la décision", "cases"]
  };
  const [message, action, view] = next[record?.status] ?? [
    "Renseignez votre projet, ajoutez vos pièces et transmettez votre dossier à un consultant.",
    "Commencer mon dossier", "form"
  ];
  element("candidate-next").textContent = message;
  const primary = element("candidate-primary");
  primary.textContent = action;
  primary.dataset.candidateView = view;

  const files = record?.files ?? [];
  const extracted = record ? (JSON.parse(record.payload).documents ?? []) : [];
  const count = files.length + extracted.length;
  element("dashboard-file-count").textContent = count ? count + (count === 1 ? " pièce au dossier" : " pièces au dossier") : "Aucune pièce transmise";
  const activity = element("candidate-activity");
  activity.replaceChildren();
  for (const event of (record?.events ?? []).slice(-3).reverse()) {
    const item = document.createElement("li");
    showText(item, "strong", eventNames[event.action]);
    showText(item, "span", event.message || event.author);
    activity.append(item);
  }
  if (!activity.childElementCount) showText(activity, "li", "Votre historique apparaîtra après le premier envoi.");

  const documentsList = element("candidate-document-list");
  documentsList.replaceChildren();
  for (const file of files) {
    const row = showText(documentsList, "p", intakeCatalog.file_kinds[file.kind] + " · ", "dashboard-file");
    const link = showText(row, "a", file.filename);
    link.href = "/portal/cases/" + record.id + "/files/" + file.id;
    link.download = "";
  }
  for (const piece of extracted) {
    showText(documentsList, "p", documentLabels[piece.document_type] + " · Champs confirmés", "dashboard-file");
  }
  if (!count) showText(documentsList, "p", "Les pièces transmises depuis le formulaire apparaîtront ici.", "muted");
}

element("candidate-profile-form").addEventListener("submit", async event => {
  event.preventDefault();
  const status = element("candidate-profile-status");
  const save = element("save-candidate-profile");
  save.disabled = true;
  try {
    const response = await fetch("/portal/me", {
      method: "PATCH", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: element("candidate-name").value.trim() })
    });
    const result = await response.json();
    if (!response.ok) throw new Error(typeof result.detail === "string" ? result.detail : "Vérifiez le nom saisi.");
    account = result;
    element("candidate-name").value = account.name;
    renderCandidateDashboard(candidateRecord);
    status.textContent = "Profil mis à jour.";
  } catch (error) {
    status.textContent = error.message;
  } finally {
    save.disabled = false;
  }
});

function setAuthMode(signup, clearStatus = true) {
  signupMode = signup;
  element("signup-name").hidden = !signup;
  element("account-name").required = signup;
  const identity = signup && selectedRole === "candidate";
  element("signup-identity").hidden = !identity;
  element("account-cin").required = identity;
  element("account-passport").required = identity;
  const invite = signup && selectedRole === "consultant";
  element("signup-invite").hidden = !invite;
  element("account-invite").required = invite;
  element("mode-signin").setAttribute("aria-pressed", String(!signup));
  element("mode-signup").setAttribute("aria-pressed", String(signup));
  element("account-password").autocomplete = signup ? "new-password" : "current-password";
  element("auth-submit").textContent = signup ? "Créer mon compte" : "Se connecter";
  if (clearStatus) element("auth-status").textContent = "";
}

for (const card of document.querySelectorAll("[data-role]")) {
  card.addEventListener("click", () => {
    selectedRole = card.dataset.role;
    element("auth-title").textContent = "Espace " + roleNames[selectedRole].toLowerCase();
    element("auth-form").reset();
    setAuthMode(false);
    setPage("auth");
    element("account-email").focus();
  });
}
element("choose-role").addEventListener("click", () => setPage("home"));
element("mode-signin").addEventListener("click", () => setAuthMode(false));
element("mode-signup").addEventListener("click", () => setAuthMode(true));

element("auth-form").addEventListener("submit", async event => {
  event.preventDefault();
  const submit = element("auth-submit");
  const status = element("auth-status");
  const registering = signupMode;
  submit.disabled = true;
  status.textContent = "";
  const body = {
    email: element("account-email").value.trim(),
    password: element("account-password").value,
    role: selectedRole
  };
  if (registering) {
    body.name = element("account-name").value.trim();
    body.invitation = element("account-invite").value;
    if (selectedRole === "candidate") {
      body.cin = element("account-cin").value.trim();
      body.passport = element("account-passport").value.trim();
    }
  }
  try {
    const result = await post(registering ? "/portal/signup" : "/portal/signin", JSON.stringify(body));
    element("account-password").value = "";
    element("account-invite").value = "";
    element("account-cin").value = "";
    element("account-passport").value = "";
    if (registering) {
      setAuthMode(false);
      status.textContent = result.message;
    } else {
      await openWorkspace(result);
    }
  } catch (error) {
    status.textContent = error.message;
  } finally {
    submit.disabled = false;
  }
});

function restoreCandidateDossier(dossier) {
  for (const [id, key] of Object.entries(profileFields)) {
    element(id).value = dossier.profile[key] == null ? "" : String(dossier.profile[key]);
  }
  const size = dossier.profile.family_size;
  element("travel-party").value = size > 1 ? "accompanied" : size === 1 ? "alone" : "";
  element("companions").value = size > 1 ? size - 1 : "";
  updateTravelParty();
  for (const name of Object.keys(checkLabels)) element("check-" + name).value = dossier.document_checks?.[name] ?? "";
  documents.splice(0, documents.length, ...dossier.documents);
  renderDocuments();
  invalidateDraft();
}

function renderCaseDetails(container, dossier) {
  if (dossier.kind === "general") {
    const country = intakeCatalog.countries.find(item => item.code === dossier.destination);
    showText(container, "p", country.name + " · " + intakeCatalog.purposes[dossier.purpose]);
    if (dossier.planned_date) showText(container, "p", "Date envisagée · " + dossier.planned_date);
    const labels = { ...intakeCatalog.common_fields, ...intakeCatalog.purpose_fields[dossier.purpose] };
    const details = document.createElement("dl");
    details.className = "intake-summary";
    for (const [name, value] of Object.entries(dossier.details ?? {})) {
      showText(details, "dt", labels[name] ?? name);
      showText(details, "dd", value);
    }
    container.append(details);
    showText(container, "p", dossier.description);
    return;
  }
  const profile = dossier.profile;
  const rows = [
    ["Nationalité", profile.nationality], ["Pays de résidence", profile.residence_country],
    ["Province", profile.destination_province], ["Niveau", profile.level_of_study],
    ["Date de demande", profile.application_date], ["Personnes qui voyagent", profile.family_size],
    ["Fonds déclarés (CAD)", profile.funds_available_cad], ["Scolarité (CAD)", profile.tuition_first_year_cad],
    ["Trajet (CAD)", profile.transport_cost_cad], ["Lettre d’acceptation", profile.has_letter_of_acceptance],
    ["PAL/TAL", profile.pal_provided], ["CAQ", profile.caq_provided],
    ["Établissement public", profile.dli_is_public], ["Exemption PAL/TAL déclarée", profile.pal_exemption_claimed]
  ];
  const list = document.createElement("ul");
  for (const [label, value] of rows) {
    if (value != null) showText(list, "li", label + " · " + (typeof value === "boolean" ? (value ? "Oui" : "Non") : value));
  }
  container.append(list);
  for (const [key, value] of Object.entries(dossier.document_checks ?? {})) {
    showText(list, "li", checkLabels[key] + " · " + ({ ready: "Terminé", missing: "À compléter", not_required: "Non applicable" })[value]);
  }
  for (const piece of dossier.documents) {
    showText(container, "h3", documentLabels[piece.document_type]);
    const fields = document.createElement("ul");
    for (const field of piece.fields) {
      const provenance = field.page ? " · page " + field.page : "";
      const review = field.reviewed_by_human ? " · confirmé par le candidat" : "";
      showText(fields, "li", fieldLabels[field.field_name] + " · " + (field.value ?? "Non renseigné") + provenance + review);
    }
    container.append(fields);
  }
}

function addCaseActions(card, record, consultants) {
  if (["completed", "ready_to_send"].includes(record.status)) return;
  const actions = document.createElement("div");
  actions.className = "case-actions";
  const assignee = document.createElement("select");
  assignee.setAttribute("aria-label", "Consultant à qui attribuer le dossier");
  assignee.append(new Option("Choisir un consultant", ""));
  for (const consultant of consultants) assignee.append(new Option(consultant.name, consultant.id));
  assignee.value = String(record.consultant_id ?? "");
  const assign = showText(actions, "button", record.consultant_id ? "Réattribuer" : "Attribuer");
  actions.prepend(assignee);
  assign.addEventListener("click", () => act({ action: "assign", consultant_id: Number(assignee.value) }));
  const message = document.createElement("textarea");
  message.maxLength = 2000;
  message.setAttribute("aria-label", "Observation ou motif");
  message.placeholder = "Saisissez votre observation, le complément demandé ou le motif de votre décision";
  actions.append(message);
  const note = showText(actions, "button", "Ajouter une note interne");
  note.addEventListener("click", () => act({ action: "note", message: message.value }));
  if (record.status === "submitted") {
    const complete = showText(actions, "button", "Terminer l’examen");
    complete.addEventListener("click", () => act({ action: "complete" }));
    const request = showText(actions, "button", "Demander un complément");
    request.addEventListener("click", () => act({ action: "request_changes", message: message.value }));
    const approve = showText(actions, "button", "Autoriser l’envoi");
    approve.addEventListener("click", () => {
      if (!message.value.trim()) {
        element("workspace-status").textContent = "Renseignez le motif de la décision.";
        message.focus();
        return;
      }
      if (window.confirm("Consigner l’autorisation d’envoi et clôturer l’examen de ce dossier ?")) {
        act({ action: "approve_transmission", message: message.value });
      }
    });
  }
  card.append(actions);

  async function act(body) {
    for (const button of actions.querySelectorAll("button")) button.disabled = true;
    try {
      await post("/portal/cases/" + record.id + "/actions", JSON.stringify(body));
      await window.portalRefresh();
    } catch (error) {
      element("workspace-status").textContent = error.message;
      for (const button of actions.querySelectorAll("button")) button.disabled = false;
    }
  }
}

function renderReviewSummary(container, record, dossier) {
  const general = dossier.kind === "general";
  const manual = general
    ? Object.values({ destination: dossier.destination, purpose: dossier.purpose, date: dossier.planned_date,
      description: dossier.description, ...dossier.details })
    : [...Object.values(dossier.profile), ...Object.values(dossier.document_checks ?? {})];
  const extracted = (dossier.documents ?? []).flatMap(piece => piece.fields);
  const files = record.files ?? [];
  const counts = [
    [manual.filter(value => value !== null && value !== "").length, "Champs saisis"],
    [files.length + (dossier.documents?.length ?? 0), "Pièces au dossier"],
    [extracted.filter(field => field.reviewed_by_human).length, "Champs extraits confirmés"],
    [record.events.filter(event => event.action === "note").length, "Notes internes"]
  ];
  const grid = document.createElement("div");
  grid.className = "review-stats";
  for (const [value, label] of counts) {
    const metric = document.createElement("div");
    showText(metric, "strong", String(value));
    showText(metric, "span", label);
    grid.append(metric);
  }
  container.append(grid);
  if (!files.length && !dossier.documents?.length) {
    showText(container, "p", "Aucune pièce au dossier. Demandez un complément si une preuve est nécessaire.", "muted");
  } else if (general) {
    showText(container, "p", "Les fichiers de ce parcours sont à examiner manuellement.", "muted");
  }
}

window.portalRefresh = async function () {
  const response = await fetch("/portal/cases", { cache: "no-store" });
  if (!response.ok) throw new Error("Impossible de charger les dossiers.");
  const data = await response.json();
  const target = element("portal-cases");
  target.replaceChildren();
  element("workspace-status").textContent = "";
  if (account.role === "candidate") {
    const record = data.cases[0];
    candidateRecord = record ?? null;
    if (record?.status === "needs_changes" && loadedCase !== record.id) {
      const dossier = JSON.parse(record.payload);
      detailedStudy = dossier.kind !== "general";
      if (detailedStudy) {
        restoreCandidateDossier(dossier);
      } else {
        element("intake-country").value = dossier.destination;
        element("intake-purpose").value = dossier.purpose;
        element("intake-date").value = dossier.planned_date ?? "";
        element("intake-description").value = dossier.description;
        updateIntakeSource();
        for (const input of activeIntakeInputs()) input.value = dossier.details?.[input.name] ?? "";
        setIntakeStep(0);
      }
      loadedCase = record.id;
    }
    if (record && record.status !== "needs_changes" && candidateView === "form") candidateView = "cases";
    renderCandidateDashboard(candidateRecord);
    showCandidateView(candidateView);
    if (!record) showText(target, "p", "Vous n’avez encore transmis aucun dossier.", "card dashboard-panel");
  } else {
    const counts = { submitted: 0, needs_changes: 0, closed: 0 };
    for (const record of data.cases) counts[consultantCategory(record.status)] += 1;
    element("consultant-greeting").textContent = "Bonjour, " + account.name;
    element("consultant-next").textContent = counts.submitted
      ? counts.submitted + (counts.submitted === 1 ? " dossier attend votre examen." : " dossiers attendent votre examen.")
      : "Aucun dossier en attente d’examen.";
    for (const [category, count] of Object.entries(counts)) {
      element("consultant-" + category).textContent = count + (count === 1 ? " dossier" : " dossiers");
    }
    showText(target, "p", "Aucun dossier dans cette vue.", "card").id = "consultant-empty";
  }
  for (const record of data.cases) {
    const card = document.createElement("article");
    card.className = "card";
    if (account.role === "consultant") card.dataset.caseCategory = consultantCategory(record.status);
    showText(card, "h2", account.role === "consultant" ? record.candidate : "Mon dossier");
    showText(card, "p", caseStates[record.status], "tag tag-warn");
    if (record.consultant) showText(card, "p", "Consultant · " + record.consultant);
    const events = document.createElement("ul");
    for (const event of record.events) {
      const date = event.created_at ? " · " + event.created_at.slice(0, 10) : "";
      showText(events, "li", event.author + date + " · " + eventNames[event.action] + (event.message ? " · " + event.message : ""));
    }
    card.append(events);
    if (account.role === "candidate" && record.status === "needs_changes") {
      const resume = showText(card, "button", "Répondre au complément", "portal-secondary");
      resume.addEventListener("click", () => showCandidateView("form"));
    }
    const details = document.createElement("details");
    showText(details, "summary", account.role === "consultant" ? "Ouvrir le rapport d’examen" : "Consulter le dossier et les pièces");
    const dossier = JSON.parse(record.payload);
    if (account.role === "consultant") renderReviewSummary(details, record, dossier);
    showText(details, "h3", "Informations du candidat");
    renderCaseDetails(details, dossier);
    if (record.files?.length) showText(details, "h3", "Fichiers originaux");
    for (const file of record.files ?? []) {
      const row = showText(details, "p", intakeCatalog.file_kinds[file.kind] + " · ");
      const link = showText(row, "a", file.filename);
      link.href = "/portal/cases/" + record.id + "/files/" + file.id;
      link.download = "";
    }
    if (account.role === "consultant" && dossier.kind !== "general") {
      const checklist = document.createElement("ul");
      showText(details, "h3", "Checklist du dossier");
      details.append(checklist);
      details.addEventListener("toggle", async () => {
        if (!details.open || checklist.childElementCount) return;
        showText(checklist, "li", "Chargement…");
        try {
          const report = await post("/dossier/report", record.payload);
          checklist.replaceChildren();
          const pending = report.checklist.items.filter(item => item.status !== "declared").length;
          showText(checklist, "li", pending + " contrôle(s) à compléter, confirmer ou examiner sur " + report.checklist.items.length);
          for (const conflict of report.contradictions) showText(checklist, "li", conflict.message, "error");
          for (const item of report.checklist.items) {
            const row = showText(checklist, "li", item.title + " · " + checklistLabels[item.status] + " · " + item.message);
            for (const url of item.source_urls) {
              const link = showText(row, "a", " Source");
              link.href = url;
              link.target = "_blank";
              link.rel = "noopener noreferrer";
            }
          }
        } catch (error) {
          checklist.replaceChildren();
          element("workspace-status").textContent = error.message;
        }
      });
    }
    card.append(details);
    if (account.role === "consultant") addCaseActions(card, record, data.consultants);
    target.append(card);
  }
  if (account.role === "consultant") filterConsultantCases();
};

async function openWorkspace(user) {
  account = user;
  const isCandidate = user.role === "candidate";
  element("workspace-title").textContent = isCandidate ? "Espace candidat" : "Espace consultant · " + user.name;
  element("candidate-dashboard").hidden = !isCandidate;
  element("consultant-dashboard").hidden = isCandidate;
  element("candidate-name").value = isCandidate ? user.name : "";
  element("candidate-email").value = isCandidate ? user.email : "";
  element("portal-cases").hidden = isCandidate;
  setPage("workspace");
  try {
    await loadIntakeCatalog();
    await window.portalRefresh();
  } catch (error) {
    element("workspace-status").textContent = error.message;
  }
}

async function loadIntakeCatalog() {
  if (intakeCatalog) return;
  const response = await fetch("/portal/catalog");
  if (!response.ok) throw new Error("Impossible de charger les destinations.");
  intakeCatalog = await response.json();
  const country = element("intake-country");
  const purpose = element("intake-purpose");
  country.append(new Option("Choisir un pays", ""));
  purpose.append(new Option("Choisir un motif", ""));
  for (const item of intakeCatalog.countries) country.append(new Option(item.name, item.code));
  for (const [value, label] of Object.entries(intakeCatalog.purposes)) purpose.append(new Option(label, value));
  addIntakeFields(element("intake-common-fields"), intakeCatalog.common_fields, "common");
  for (const [key, fields] of Object.entries(intakeCatalog.purpose_fields)) {
    const group = document.createElement("div");
    group.className = "fields purpose-group";
    group.dataset.purpose = key;
    group.hidden = true;
    addIntakeFields(group, fields, key);
    element("intake-purpose-fields").append(group);
  }
}

function addIntakeFields(group, fields, prefix) {
  for (const [name, label] of Object.entries(fields)) {
    const row = document.createElement("div");
    const input = document.createElement("input");
    input.id = "intake-" + prefix + "-" + name;
    input.name = name;
    input.maxLength = 240;
    showText(row, "label", label).htmlFor = input.id;
    row.append(input);
    group.append(row);
  }
}

function updateIntakeSource() {
  const country = intakeCatalog.countries.find(item => item.code === element("intake-country").value);
  const target = element("intake-source");
  target.replaceChildren();
  if (country) {
    const link = showText(target, "a", "Consulter les démarches officielles · " + country.name);
    link.href = country.url;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
  }
  element("study-path").hidden = country?.code !== "CA" || element("intake-purpose").value !== "study";
  for (const group of element("intake-purpose-fields").children) {
    group.hidden = group.dataset.purpose !== element("intake-purpose").value;
  }
}

element("intake-country").addEventListener("change", updateIntakeSource);
element("intake-purpose").addEventListener("change", updateIntakeSource);
element("study-path").addEventListener("click", () => {
  detailedStudy = true;
  showCandidateForm(true);
  element("candidate-workflow").scrollIntoView();
});
element("back-to-intake").addEventListener("click", () => {
  detailedStudy = false;
  showCandidateForm(true);
  element("general-workflow").scrollIntoView();
});

const intakeFiles = element("intake-files");
const addFile = element("add-intake-file");
const intakeSteps = [...document.querySelectorAll(".intake-step")];
let intakeStep = 0;

function activeIntakeInputs() {
  return document.querySelectorAll("#intake-common-fields input, .purpose-group:not([hidden]) input");
}

function intakeDraft() {
  return {
    destination: element("intake-country").value, purpose: element("intake-purpose").value,
    planned_date: element("intake-date").value || null, description: element("intake-description").value.trim(),
    details: Object.fromEntries([...activeIntakeInputs()].map(input => [input.name, input.value.trim()]).filter(([, value]) => value))
  };
}

function setIntakeStep(step, focus = false) {
  intakeStep = step;
  intakeSteps.forEach((panel, index) => { panel.hidden = index !== step; });
  document.querySelectorAll(".intake-progress li").forEach((item, index) => {
    item.classList.toggle("is-complete", index < step);
    if (index === step) item.setAttribute("aria-current", "step");
    else item.removeAttribute("aria-current");
  });
  element("intake-previous").hidden = step === 0;
  element("intake-next").hidden = step === intakeSteps.length - 1;
  element("intake-submit").hidden = step !== intakeSteps.length - 1;
  if (step === intakeSteps.length - 1) {
    const summary = element("intake-summary");
    summary.replaceChildren();
    renderCaseDetails(summary, { kind: "general", ...intakeDraft() });
    showText(summary, "h4", "Pièces de cet envoi");
    const files = document.createElement("ul");
    for (const row of intakeFiles.children) {
      const file = row.querySelector("input").files[0];
      if (file) showText(files, "li", intakeCatalog.file_kinds[row.querySelector("select").value] + " · " + file.name);
    }
    if (files.childElementCount) summary.append(files);
    else showText(summary, "p", "Aucune nouvelle pièce jointe.");
  }
  if (focus) {
    const heading = intakeSteps[step].querySelector("h3");
    heading.tabIndex = -1;
    heading.focus();
  }
}

function validateIntakeStep(step) {
  const invalid = [...intakeSteps[step].querySelectorAll("input, select, textarea")]
    .find(input => !input.checkValidity());
  if (!invalid) return true;
  setIntakeStep(step);
  invalid.reportValidity();
  return false;
}

function nextIntakeStep() {
  if (validateIntakeStep(intakeStep)) setIntakeStep(intakeStep + 1, true);
}

element("intake-next").addEventListener("click", nextIntakeStep);
element("intake-previous").addEventListener("click", () => setIntakeStep(intakeStep - 1, true));
addFile.addEventListener("click", () => {
  if (intakeFiles.childElementCount >= 3) return;
  const row = document.createElement("fieldset");
  row.className = "intake-file";
  showText(row, "legend", "Pièce jointe");
  const kind = document.createElement("select");
  kind.setAttribute("aria-label", "Type de pièce");
  for (const [value, label] of Object.entries(intakeCatalog.file_kinds)) kind.append(new Option(label, value));
  kind.value = "other";
  const input = document.createElement("input");
  input.type = "file";
  input.accept = ".pdf,.docx,.jpg,.jpeg,.png";
  input.required = true;
  input.setAttribute("aria-label", "Choisir le fichier");
  row.append(kind, input);
  const remove = showText(row, "button", "Retirer");
  remove.type = "button";
  remove.className = "portal-secondary";
  remove.addEventListener("click", () => { row.remove(); addFile.disabled = false; });
  intakeFiles.append(row);
  addFile.disabled = intakeFiles.childElementCount >= 3;
});

function encodeFile(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result.split(",", 2)[1]);
    reader.onerror = () => reject(new Error("Impossible de lire " + file.name));
    reader.readAsDataURL(file);
  });
}

element("general-form").addEventListener("submit", async event => {
  event.preventDefault();
  if (intakeStep < intakeSteps.length - 1) {
    nextIntakeStep();
    return;
  }
  if (![0, 1, 2].every(validateIntakeStep)) return;
  const status = element("intake-status");
  const submit = element("intake-submit");
  submit.disabled = true;
  status.textContent = "Transmission…";
  try {
    const body = { ...intakeDraft(), files: [] };
    for (const row of intakeFiles.children) {
      const file = row.querySelector("input").files[0];
      if (file.size > 4 * 1024 * 1024) throw new Error(file.name + " dépasse 4 Mio.");
      body.files.push({ kind: row.querySelector("select").value, filename: file.name, data: await encodeFile(file) });
    }
    await post("/portal/intake", JSON.stringify(body));
    intakeFiles.replaceChildren();
    addFile.disabled = false;
    status.textContent = "Dossier transmis.";
    await window.portalRefresh();
  } catch (error) {
    status.textContent = error.message;
  } finally {
    submit.disabled = false;
  }
});

element("signout").addEventListener("click", async () => {
  try {
    const response = await fetch("/portal/signout", { method: "POST" });
    if (!response.ok) throw new Error("La déconnexion a échoué. Réessayez.");
    window.location.reload();
  } catch (error) {
    element("workspace-status").textContent = error.message;
  }
});

element("refresh-cases").addEventListener("click", () => {
  window.portalRefresh().catch(error => { element("workspace-status").textContent = error.message; });
});

fetch("/portal/me", { cache: "no-store" }).then(response => {
  if (response.ok) return response.json().then(openWorkspace);
}).catch(() => {});
