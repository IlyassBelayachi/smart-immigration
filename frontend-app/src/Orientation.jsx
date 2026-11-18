import React, { useState } from "react";
import { api } from "./api.js";
import { COUNTRIES } from "./labels.js";

const opening = "Parlez-moi de votre projet. Que voulez-vous faire à l’étranger et dans quel délai ?";

export default function Orientation({ onChoose }) {
  const [turns, setTurns] = useState([]);
  const [state, setState] = useState({ question: opening });
  const [draft, setDraft] = useState("");
  const [extra, setExtra] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function advance(confirmed = false) {
    const answer = draft.trim();
    if (!confirmed && !answer) return;
    const answers = [...turns.map(turn => turn.answer), ...(confirmed ? [] : [answer])];
    setBusy(true);
    setError("");
    try {
      const result = await api.interview(answers, confirmed);
      if (!confirmed && result.accepted === answers.length) {
        setTurns([...turns, { question: state.question, answer }]);
        setDraft("");
      }
      setState(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  function revise(index) {
    setDraft(turns[index].answer);
    setState({ question: turns[index].question });
    setTurns(turns.slice(0, index));
    setError("");
  }

  function choose(code) {
    const context = [state.transcript.projet, extra.trim()].filter(Boolean).join("\n");
    onChoose(code, state.motive, state.preferences, context, state.transcript);
  }

  return (
    <section aria-labelledby="orientation-title">
      <h2 id="orientation-title">Entretien d’orientation</h2>
      <p className="hint">Répondez avec vos mots. Si une information est encore inconnue, indiquez-le. Évitez de partager vos numéros de documents.</p>
      <div className="orientation-chat" aria-live="polite">
        {turns.map(({ question, answer }, index) => (
          <div key={index}>
            <p className="chat-question">{question}</p>
            <p className="chat-answer">{answer}</p>
            <button type="button" className="link" disabled={busy} onClick={() => revise(index)}>Reprendre à cette réponse</button>
          </div>
        ))}
        {state.question && <p className="chat-question">{state.question}</p>}
      </div>
      {!state.ready && !state.suggestions && (
        <form onSubmit={event => { event.preventDefault(); advance(); }}>
          <label>Votre réponse<textarea required maxLength={1500} value={draft} onChange={event => setDraft(event.target.value)} /></label>
          <button className="primary" disabled={busy}>Envoyer ma réponse</button>
        </form>
      )}
      {state.ready && <dl className="facts-list">
        {Object.entries(state.summary).map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}
      </dl>}
      {state.ready && <button className="primary" disabled={busy} onClick={() => advance(true)}>Confirmer mes réponses et voir les pistes</button>}
      {busy && <p role="status">Analyse de votre réponse…</p>}
      {error && <p className="error" role="alert">{error}</p>}
      {state.suggestions && (
        <>
          <h3>Destinations à explorer</h3>
          <p className="hint">Le classement se fonde sur les langues, les préférences géographiques et les contacts identifiés. Le budget et les contraintes restent à examiner avec le consultant.</p>
          {state.suggestions.length === 0 && <p>Aucune piste ne ressort des préférences indiquées. Vous pouvez préparer votre dossier sans choisir de pays.</p>}
          <label>Autres précisions pour le consultant (facultatif)
            <textarea value={extra} maxLength={1000} onChange={event => setExtra(event.target.value)} />
          </label>
          {state.suggestions.map(({ code, reasons }) => (
            <article key={code} className="req">
              <h4>{COUNTRIES[code]}</h4>
              <ul>{reasons.map(reason => <li key={reason}>{reason}</li>)}</ul>
              <button onClick={() => choose(code)}>Préparer une demande</button>
            </article>
          ))}
          <button onClick={() => choose("ZZ")}>Continuer sans choisir de pays</button>
        </>
      )}
    </section>
  );
}
