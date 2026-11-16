import React, { useEffect, useRef, useState } from "react";
import { api } from "./api.js";
import { COUNTRIES, MOTIVES, STATUS } from "./labels.js";
import Recommendation from "./Recommendation.jsx";
import StatusTrack from "./StatusTrack.jsx";
import { useEnter, usePanelMotion } from "./usePanelMotion.js";

const tri = (v) => (v === "yes" ? true : v === "no" ? false : undefined);

export default function Candidate({ user, onUser }) {
  const root = useRef(null);
  const [tab, setTab] = useState("requests");
  const [requests, setRequests] = useState([]);
  const [editing, setEditing] = useState(false);
  const [profile, setProfile] = useState({ full_name: user.full_name, passport: "" });
  const [profileMsg, setProfileMsg] = useState("");
  const [f, setF] = useState({ motive: "study", destination: "CA", passport: "", level_of_study: "", has_letter_of_acceptance: "",
    destination_province: "", family_size: "1", funds_available_cad: "", tuition_first_year_cad: "", application_date: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });

  const load = () => api.myRequests().then(setRequests).catch((e) => setError(e.message));
  useEffect(() => { load(); }, []);

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
    setError("");
    setBusy(true);
    try {
      const p = {};
      if (f.motive === "study" && f.destination === "CA") {
        if (f.level_of_study) p.level_of_study = f.level_of_study;
        if (tri(f.has_letter_of_acceptance) !== undefined) p.has_letter_of_acceptance = tri(f.has_letter_of_acceptance);
        if (f.destination_province) p.destination_province = f.destination_province;
        if (f.family_size) p.family_size = Number(f.family_size);
        if (f.funds_available_cad !== "") p.funds_available_cad = Number(f.funds_available_cad);
        if (f.tuition_first_year_cad !== "") p.tuition_first_year_cad = Number(f.tuition_first_year_cad);
        if (f.application_date) p.application_date = f.application_date;
      }
      const body = { motive: f.motive, destination: f.destination, profile: p };
      if (f.passport) body.passport = f.passport;
      await api.createRequest(body);
      onUser(await api.me());
      setF({ ...f, passport: "" });
      await load();
      setTab("requests");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const ca = f.motive === "study" && f.destination === "CA";

  return (
    <div ref={root} className="candidate">
      <div className="welcome">
        <h1>Bonjour {user.full_name.split(" ")[0]}</h1>
        <p><span className="chip ok">Identité vérifiée</span> CIN {user.cin_masked}</p>
      </div>

      <nav className="subnav" role="tablist">
        {[["requests", `Mes demandes${requests.length ? ` (${requests.length})` : ""}`], ["new", "Nouvelle demande"], ["profile", "Mon profil"]].map(([k, v]) => (
          <button key={k} role="tab" aria-selected={tab === k} className={tab === k ? "on" : ""} onClick={() => setTab(k)}>{v}</button>
        ))}
      </nav>

      <section className="panel">
        {tab === "requests" && (
          <>
            <h2>Mes demandes</h2>
            {requests.length === 0 && (
              <p className="empty">Aucune demande pour l'instant. <button className="link" onClick={() => setTab("new")}>Créer ma première demande</button></p>
            )}
            {requests.map((r) => (
              <article key={r.id} className="req">
                <h3>{MOTIVES[r.motive]} · {COUNTRIES[r.destination] || r.destination} <span className={"status s-" + r.status}>{STATUS[r.status]}</span></h3>
                <StatusTrack status={r.status} />
                <Recommendation rec={r.recommendation} />
                {r.decisions.map((d, i) => <p key={i} className="decision"><strong>Consultant :</strong> {STATUS[d.decision]}. {d.reason}</p>)}
              </article>
            ))}
          </>
        )}

        {tab === "new" && (
          <form onSubmit={submit}>
            <h2>Nouvelle demande</h2>
            <div className="grid2">
              <label>Motif
                <select value={f.motive} onChange={set("motive")}>{Object.entries(MOTIVES).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select>
              </label>
              <label>Pays de destination
                <select value={f.destination} onChange={set("destination")}>{Object.entries(COUNTRIES).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select>
              </label>
            </div>
            {ca ? (
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
                <label>Date de dépôt prévue<input type="date" value={f.application_date} onChange={set("application_date")} /></label>
              </div>
            ) : (
              <p className="hint">Pour ce pays et ce motif, il n'y a pas encore de règles automatiques : un consultant examinera toute la demande.</p>
            )}
            <label>Numéro de passeport <small>facultatif, vous pouvez l'ajouter plus tard</small>
              <input value={f.passport} onChange={set("passport")} placeholder={user.has_passport ? "Déjà enregistré" : ""} />
            </label>
            {error && <p className="error" role="alert">{error}</p>}
            <button className="primary" disabled={busy}>{busy ? "Envoi…" : "Envoyer ma demande"}</button>
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
