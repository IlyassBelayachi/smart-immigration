import React from "react";
import { VERDICT } from "./labels.js";

export default function Recommendation({ rec }) {
  if (!rec || !rec.summary) return null;
  return (
    <div className="rec">
      <p><strong>Avis de l'assistant :</strong> {rec.summary}</p>
      {rec.coverage === "not_covered" && <p className="hint">Pas encore de règles automatiques pour ce pays et ce motif.</p>}
      {rec.results?.length > 0 && (
        <ul>
          {rec.results.map((r) => (
            <li key={r.rule_id} className={"v-" + r.verdict}>
              <span className="badge">{VERDICT[r.verdict] || r.verdict}</span> {r.title}
              <div className="muted">{r.explanation}</div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
