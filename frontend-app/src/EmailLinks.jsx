import React, { useEffect, useState } from "react";
import { api } from "./api.js";

// Pages ouvertes depuis les liens reçus par email : ?verify=... et ?reset=...
export function VerifyEmail({ token, onDone }) {
  const [msg, setMsg] = useState("Vérification du lien…");
  const [ok, setOk] = useState(false);
  useEffect(() => {
    api.verifyEmail(token).then((r) => { setMsg(r.message); setOk(true); }).catch((e) => setMsg(e.message));
  }, [token]);
  return (
    <section className="auth"><div className="panel">
      <h2>Confirmation de l'email</h2>
      <p className={ok ? "ok" : "error"}>{msg}</p>
      <button className="primary" onClick={onDone}>Aller à la connexion</button>
    </div></section>
  );
}

export function ResetPassword({ token, onDone }) {
  const [password, setPassword] = useState("");
  const [msg, setMsg] = useState("");
  const [ok, setOk] = useState(false);
  const submit = async (e) => {
    e.preventDefault();
    try { setMsg((await api.resetPassword(token, password)).message); setOk(true); } catch (err) { setMsg(err.message); }
  };
  return (
    <section className="auth"><div className="panel">
      <h2>Nouveau mot de passe</h2>
      {!ok && (
        <form onSubmit={submit}>
          <label>Nouveau mot de passe <small>(10 caractères minimum)</small>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={10} autoComplete="new-password" /></label>
          <button className="primary">Enregistrer</button>
        </form>
      )}
      {msg && <p className={ok ? "ok" : "error"}>{msg}</p>}
      {ok && <button className="primary" onClick={onDone}>Aller à la connexion</button>}
    </div></section>
  );
}
