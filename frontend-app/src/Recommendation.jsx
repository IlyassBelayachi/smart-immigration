import React from "react";
import { COUNTRIES, VERDICT } from "./labels.js";

export default function Recommendation({ rec }) {
  if (!rec || !rec.summary) return null;
  return (
    <div className="rec">
      <p><strong>Avis de l'assistant :</strong> {rec.summary}</p>
      {rec.provided_fields && <dl className="facts-list">
        {Object.entries(rec.provided_fields).map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}
      </dl>}
      {rec.missing_fields?.length > 0 && <p>Points à préciser selon le dossier · {rec.missing_fields.join(", ")}</p>}
      {rec.suggestions?.length > 0 && <section>
        <h4>Destinations à explorer</h4>
        <ul>{rec.suggestions.map(({ code, reasons }) => <li key={code}><strong>{COUNTRIES[code]}</strong> · {reasons.join(" · ")}</li>)}</ul>
      </section>}
      {rec.results?.length > 0 && (
        <>
        <p className="hint">{rec.results.length} critères vérifiés · {rec.counts?.UNKNOWN ?? 0} à préciser · {rec.counts?.DOES_NOT_MEET ?? 0} non remplis</p>
        <ul>
          {rec.results.map((r) => (
            <li key={r.rule_id} className={"v-" + r.verdict}>
              <span className="badge">{VERDICT[r.verdict] || r.verdict}</span> {r.title}
              <div className="muted">{r.explanation}</div>
              {r.source_urls?.map(url => <div key={url}><a href={url} target="_blank" rel="noreferrer">Source officielle</a></div>)}
            </li>
          ))}
        </ul>
        </>
      )}
    </div>
  );
}
