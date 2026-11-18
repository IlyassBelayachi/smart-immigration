import React, { useEffect, useRef, useState } from "react";
import { api } from "./api.js";
import { COUNTRIES, MOTIVES, STATUS } from "./labels.js";
import Recommendation from "./Recommendation.jsx";
import Orientation from "./Orientation.jsx";
import StatusTrack from "./StatusTrack.jsx";
import { useEnter, usePanelMotion } from "./usePanelMotion.js";

const stages = [
  ["Projet et calendrier", ["departure", "duration", "obstacles"]],
  ["Profil et expérience", ["nationality", "residence", "situation", "education", "career", "languages", "certifications"]],
  ["Parcours d’immigration", []],
  ["Financement et installation", ["funding", "budget", "accompanying", "housing", "local_support", "previous_applications"]],
  ["Justificatifs et envoi", []],
];

const longFields = new Set(["career", "obstacles", "previous_applications", "business_plan", "family_timeline"]);

const tri = (v) => (v === "yes" ? true : v === "no" ? false : undefined);

const initialForm = { motive: "study", destination: "ZZ", passport: "", level_of_study: "", has_letter_of_acceptance: "",
    destination_province: "", family_size: "1", funds_available_cad: "", tuition_first_year_cad: "", application_date: "",
    transport_cost_cad: "", project_description: "" };

export default function Candidate({ user, onUser }) {
  const root = useRef(null);
  const [tab, setTab] = useState("requests");
  const [requests, setRequests] = useState([]);
  const [editing, setEditing] = useState(false);
  const [profile, setProfile] = useState({ full_name: user.full_name, passport: "" });
  const [profileMsg, setProfileMsg] = useState("");
  const [f, setF] = useState(initialForm);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [formOptions, setFormOptions] = useState(null);
  const [details, setDetails] = useState({});
  const [step, setStep] = useState(0);
  const [interview, setInterview] = useState(null);
  const [orientation, setOrientation] = useState(null);
  const [reading, setReading] = useState(false);
  const [documentKind, setDocumentKind] = useState("acceptance");
  const [document, setDocument] = useState(null);
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });

  const load = () => api.myRequests().then(setRequests).catch((e) => setError(e.message));
  useEffect(() => { load(); }, []);
  useEffect(() => { api.formOptions().then(setFormOptions).catch(err => setError(err.message)); }, []);
  const fields = { ...formOptions?.common, ...formOptions?.by_motive?.[f.motive] };

  useEnter(root, ".welcome > *");
  usePanelMotion(root, tab, 18);

  const saveProfile = async (e) => {
    e.preventDefault();
    setProfileMsg("");
    try {
      const body = { full_name: profile.full_name };
      if (profile.passport) body.passport = profile.passport;
      onUser(await api.updateProfile(body));
      setProfile({ ...profile, passport: "" });
      setEditing(false);
      setProfileMsg("Profil mis à jour.");
    } catch (err) {
      setProfileMsg(err.message);
    }
  };

  const submit = async (e) => {
    e.preventDefault();
    if (step < stages.length - 1) {
      setStep(step + 1);
      return;
    }
    setError("");
    setBusy(true);
    try {
      const p = { project_description: f.project_description.trim(), ...(document ? { extracted_document: document } : {}) };
      for (const key of Object.keys(fields)) {
        if (details[key]?.trim()) p[key] = details[key].trim();
      }
      if (orientation) p.orientation = orientation;
      if (interview) p.orientation_interview = interview;
      if (f.motive === "study" && f.destination === "CA") {
        if (f.level_of_study) p.level_of_study = f.level_of_study;
        if (tri(f.has_letter_of_acceptance) !== undefined) p.has_letter_of_acceptance = tri(f.has_letter_of_acceptance);
        if (f.destination_province) p.destination_province = f.destination_province;
        if (f.family_size) p.family_size = Number(f.family_size);
        if (f.funds_available_cad !== "") p.funds_available_cad = Number(f.funds_available_cad);
        if (f.tuition_first_year_cad !== "") p.tuition_first_year_cad = Number(f.tuition_first_year_cad);
        if (f.application_date) p.application_date = f.application_date;
        if (f.transport_cost_cad !== "") p.transport_cost_cad = Number(f.transport_cost_cad);
      }
      const body = { motive: f.motive, destination: f.destination, profile: p };
      if (f.passport) body.passport = f.passport;
      await api.createRequest(body);
      setDocument(null);
      setDetails({});
      setOrientation(null);
      setInterview(null);
      setStep(0);
      onUser(await api.me());
      setF(initialForm);
      await load();
      setTab("requests");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const stepFields = step === 2 ? Object.keys(formOptions?.by_motive?.[f.motive] ?? {}) : stages[step][1];
  const ca = f.motive === "study" && f.destination === "CA";

  return (
    <div ref={root} className="candidate">
      <div className="welcome">
        <h1>Bonjour {user.full_name.split(" ")[0]}</h1>
        <p><span className="chip ok">Identité vérifiée</span> CIN {user.cin_masked}</p>
      </div>

      <nav className="subnav" role="tablist">
        {[["requests", `Mes demandes${requests.length ? ` (${requests.length})` : ""}`], ["new", "Nouvelle demande"], ["orientation", "Choisir une destination"], ["profile", "Mon profil"]].map(([k, v]) => (
          <button key={k} role="tab" aria-selected={tab === k} className={tab === k ? "on" : ""} onClick={() => setTab(k)}>{v}</button>
        ))}
      </nav>

      <section className="panel">
        {tab === "orientation" && <Orientation onChoose={(destination, motive, preferences, extra, transcript) => {
          setInterview(transcript);
          setStep(0);
          setOrientation(preferences);
          setF(current => ({ ...current, destination, motive, project_description: [current.project_description, extra].filter(Boolean).join("\n").slice(0, 2500) }));
          setTab("new");
        }} />}
        {tab === "requests" && (
          <>
            <h2>Mes demandes</h2>
            {error && <p className="error" role="alert">{error}</p>}
            {requests.length === 0 && (
              <p className="empty">Aucune demande pour l'instant. <button className="link" onClick={() => setTab("new")}>Créer ma première demande</button></p>
            )}
            {requests.map((r) => (
              <article key={r.id} className="req">
                <h3>{MOTIVES[r.motive]} · {COUNTRIES[r.destination] || r.destination} <span className={"status s-" + r.status}>{STATUS[r.status]}</span></h3>
                <StatusTrack status={r.status} />
                <Recommendation rec={r.recommendation} />
                {r.decisions.map((d, i) => <p key={i} className="decision"><strong>Consultant :</strong> {STATUS[d.decision]}. {d.reason}</p>)}
                {r.profile?.supplements?.map((message, i) => <p key={i}>Complément envoyé · {message}</p>)}
                {r.status === "needs_info" && <form onSubmit={async event => {
                  event.preventDefault();
                  const message = new FormData(event.currentTarget).get("supplement");
                  setBusy(true);
                  setError("");
                  try { await api.supplement(r.id, message); await load(); }
                  catch (err) { setError(err.message); }
                  finally { setBusy(false); }
                }}>
                  <label>Informations complémentaires<textarea name="supplement" required minLength={3} maxLength={2500} /></label>
                  <button disabled={busy}>Renvoyer au consultant</button>
                </form>}
              </article>
            ))}
          </>
        )}

        {tab === "new" && (
          <form onSubmit={submit}>
            <h2>Nouvelle demande</h2>
            <ol className="application-steps" aria-label="Étapes du dossier">
              {stages.map(([label], index) => <li key={label} aria-current={index === step ? "step" : undefined}>{label}</li>)}
            </ol>
            <h3>{stages[step][0]}</h3>
            {step === 0 && <>
            <div className="grid2">
              <label>Motif
                <select value={f.motive} onChange={set("motive")}>{Object.entries(MOTIVES).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select>
              </label>
              <label>Pays de destination
                <select value={f.destination} onChange={set("destination")}>{Object.entries(COUNTRIES).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select>
              </label>
            </div>
            {f.destination === "ZZ" && <button type="button" className="link" onClick={() => setTab("orientation")}>
              {orientation ? "Modifier mes préférences de destination" : "Indiquer mes préférences au chatbot"}
            </button>}
            <label>Votre projet<textarea value={f.project_description} onChange={set("project_description")} maxLength={2500} rows={5}
              placeholder="Pourquoi ce départ, quel objectif et quelles démarches avez-vous déjà entreprises ?" /></label>
            </>}
            <div className="grid2">
              {stepFields.filter(key => fields[key]).map(key => {
                const control = {
                  maxLength: longFields.has(key) ? 1200 : 240,
                  value: details[key] ?? "",
                  onChange: event => setDetails({ ...details, [key]: event.target.value }),
                };
                return <label key={key}>{fields[key]}
                  {longFields.has(key) ? <textarea {...control} rows={3} /> : <input {...control} />}
                </label>;
              })}
            </div>
            {step === 2 && ca && (
              <div className="grid2">
                <label>Niveau d'études visé
                  <select value={f.level_of_study} onChange={set("level_of_study")}>
                    <option value="">Non précisé</option><option value="secondary">Secondaire</option><option value="college">Collège</option>
                    <option value="bachelor">Licence</option><option value="master">Master</option><option value="phd">Doctorat</option>
                  </select>
                </label>
                <label>Lettre d'acceptation obtenue ?
                  <select value={f.has_letter_of_acceptance} onChange={set("has_letter_of_acceptance")}>
                    <option value="">Je ne sais pas</option><option value="yes">Oui</option><option value="no">Non</option>
                  </select>
                </label>
                <label>Province de destination
                  <select value={f.destination_province} onChange={set("destination_province")}>
                    <option value="">Non précisée</option><option value="QC">Québec</option><option value="ON">Ontario</option><option value="BC">Colombie-Britannique</option>
                    <option value="AB">Alberta</option><option value="NS">Nouvelle-Écosse</option><option value="MB">Manitoba</option><option value="NB">Nouveau-Brunswick</option>
                  </select>
                </label>
                <label>Personnes concernées (vous inclus)<input type="number" min="1" value={f.family_size} onChange={set("family_size")} /></label>
                <label>Fonds disponibles (CAD)<input type="number" min="0" value={f.funds_available_cad} onChange={set("funds_available_cad")} /></label>
                <label>Frais de scolarité, 1re année (CAD)<input type="number" min="0" value={f.tuition_first_year_cad} onChange={set("tuition_first_year_cad")} /></label>
                <label>Trajet aller-retour (CAD)<input type="number" min="0" step="0.01" value={f.transport_cost_cad} onChange={set("transport_cost_cad")} /></label>
                <label>Date de dépôt prévue<input type="date" value={f.application_date} onChange={set("application_date")} /></label>
              </div>
            )}
            {step === 4 && <>
            {interview && <p className="hint">Les réponses de votre entretien seront jointes au dossier.</p>}
            <details open>
              <summary>Récapitulatif des réponses</summary>
              <dl className="facts-list">
                <div><dt>Motif et destination</dt><dd>{MOTIVES[f.motive]} · {COUNTRIES[f.destination]}</dd></div>
                <div><dt>Votre projet</dt><dd>{f.project_description}</dd></div>
                {Object.entries(fields).filter(([key]) => details[key]?.trim()).map(([key, label]) =>
                  <div key={key}><dt>{label}</dt><dd>{details[key]}</dd></div>)}
              </dl>
            </details>
            {ca &&             <fieldset>
              <legend>Lire une pièce fictive</legend>
              <label>Type de pièce
                <select value={documentKind} onChange={event => setDocumentKind(event.target.value)} disabled={reading}>
                  <option value="acceptance">Lettre d’acceptation</option><option value="transcript">Relevé de notes</option>
                  <option value="financial">Justificatif financier</option>
                </select>
              </label>
              <p><a href={`/dossier/specimens/${documentKind}?format=pdf`}>Télécharger un spécimen PDF</a></p>
              <label>Spécimen PDF ou TXT
                <input type="file" accept=".pdf,.txt" disabled={reading} onChange={async event => {
                  const file = event.target.files[0];
                  if (!file) return;
                  setReading(true);
                  setDocument(null);
                  setError("");
                  try { setDocument(await api.readSpecimen(documentKind, file)); }
                  catch (err) { setError(err.message); }
                  finally { setReading(false); }
                }} />
              </label>
              {reading && <p role="status">Lecture de la pièce…</p>}
              {document && <>
                {document.fields.map((field, index) => <label key={field.field_name}>
                  {field.field_name.replaceAll("_", " ")}{field.page ? ` · page ${field.page}` : ""}
                  <input value={field.value ?? ""} maxLength={160} onChange={event => {
                    const value = event.target.value;
                    setDocument(current => ({ ...current, fields: current.fields.map((entry, i) =>
                      i === index ? { ...entry, value, reviewed_by_human: false } : entry) }));
                  }} />
                </label>)}
                <button type="button" onClick={() => setDocument(null)}>Retirer la pièce lue</button>
              </>}
            </fieldset>}
            <label>Numéro de passeport <small>facultatif, vous pouvez l'ajouter plus tard</small>
              <input value={f.passport} onChange={set("passport")} placeholder={user.has_passport ? "Déjà enregistré" : ""} />
            </label>
            </>}
            {error && <p className="error" role="alert">{error}</p>}
            <div className="row">
              {step > 0 && <button type="button" disabled={busy} onClick={() => setStep(step - 1)}>Précédent</button>}
              <button className="primary" disabled={busy || reading || !formOptions}>
                {busy ? "Envoi…" : step < stages.length - 1 ? "Continuer" : "Envoyer au consultant"}
              </button>
            </div>
          </form>
        )}

        {tab === "profile" && (
          !editing ? (
            <>
              <h2>Mon profil</h2>
              <dl className="facts-list">
                <div><dt>Nom</dt><dd>{user.full_name}</dd></div>
                <div><dt>Email</dt><dd>{user.email}</dd></div>
                <div><dt>CIN</dt><dd>{user.cin_masked}</dd></div>
                <div><dt>Passeport</dt><dd>{user.has_passport ? "Enregistré" : "Pas encore ajouté"}</dd></div>
              </dl>
              <button onClick={() => setEditing(true)}>Modifier mon profil</button>
              {profileMsg && <p className="muted">{profileMsg}</p>}
            </>
          ) : (
            <form onSubmit={saveProfile}>
              <h2>Modifier mon profil</h2>
              <label>Nom complet <input value={profile.full_name} onChange={(e) => setProfile({ ...profile, full_name: e.target.value })} required /></label>
              <label>Numéro de passeport <small>6 à 12 lettres ou chiffres, facultatif</small>
                <input value={profile.passport} onChange={(e) => setProfile({ ...profile, passport: e.target.value })} /></label>
              {profileMsg && <p className="error">{profileMsg}</p>}
              <div className="row"><button className="primary">Enregistrer</button><button type="button" onClick={() => setEditing(false)}>Annuler</button></div>
            </form>
          )
        )}
      </section>
    </div>
  );
}
