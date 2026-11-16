import React, { useEffect, useRef, useState } from "react";
import { api } from "./api.js";
import { COUNTRIES, MOTIVES, STATUS } from "./labels.js";
import Recommendation from "./Recommendation.jsx";
import StatusTrack from "./StatusTrack.jsx";
import { useEnter } from "./usePanelMotion.js";

const FILTERS = [["awaiting_review", "À examiner"], ["needs_info", "Complément demandé"], ["approved", "Approuvées"], ["rejected", "Refusées"], ["all", "Toutes"]];

export default function Consultant() {
  const root = useRef(null);
  const [filter, setFilter] = useState("awaiting_review");
  const [items, setItems] = useState([]);
  const [error, setError] = useState("");
  const [reasons, setReasons] = useState({});

  const load = () => api.consultantRequests().then(setItems).catch((e) => setError(e.message));
  useEffect(() => { load(); }, []);
  useEnter(root, ".counts > *");

  const decide = async (id, decision) => {
    setError("");
    try {
      await api.decide(id, { decision, reason: reasons[id] || "" });
      setReasons({ ...reasons, [id]: "" });
      await load();
    } catch (err) {
      setError(err.message);
    }
  };

  const count = (k) => (k === "all" ? items.length : items.filter((r) => r.status === k).length);
  const shown = items.filter((r) => filter === "all" || r.status === filter);

  return (
    <div ref={root} className="consultant">
      <h1>Demandes d'immigration</h1>
      <p className="muted">Les comptes sont vérifiés automatiquement. Ici, vous examinez les demandes et vous décidez.</p>
      <div className="counts" role="tablist">
        {FILTERS.map(([k, v]) => (
          <button key={k} role="tab" aria-selected={filter === k} className={"count-card" + (filter === k ? " on" : "")} onClick={() => setFilter(k)}>
            <strong>{count(k)}</strong><span>{v}</span>
          </button>
        ))}
      </div>
      <section className="panel">
        {error && <p className="error" role="alert">{error}</p>}
        {shown.length === 0 && <p className="empty">Aucune demande dans cette liste.</p>}
        {shown.map((r) => {
          const closed = r.status === "approved" || r.status === "rejected";
          return (
            <article key={r.id} className="req">
              <h3>Demande {r.id} · {MOTIVES[r.motive]} · {COUNTRIES[r.destination] || r.destination} <span className={"status s-" + r.status}>{STATUS[r.status]}</span></h3>
              <StatusTrack status={r.status} />
              <Recommendation rec={r.recommendation} />
              {r.decisions.map((d, i) => <p key={i} className="decision">{STATUS[d.decision]}. {d.reason}</p>)}
              {!closed && (
                <div className="decide">
                  <label>Motif de votre décision
                    <textarea rows="2" value={reasons[r.id] || ""} onChange={(e) => setReasons({ ...reasons, [r.id]: e.target.value })} />
                  </label>
                  <div className="row">
                    <button className="primary" onClick={() => decide(r.id, "approved")}>Approuver</button>
                    <button onClick={() => decide(r.id, "needs_info")}>Demander un complément</button>
                    <button className="danger" onClick={() => decide(r.id, "rejected")}>Refuser</button>
                  </div>
                </div>
              )}
            </article>
          );
        })}
      </section>
    </div>
  );
}
