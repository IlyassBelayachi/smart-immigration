import React, { useRef, useState } from "react";
import { api } from "./api.js";
import Signup from "./Signup.jsx";
import { usePanelMotion } from "./usePanelMotion.js";

const TITLES = { candidate: "Espace candidat", consultant: "Espace consultant" };

export default function AuthScreen({ space, onLogin, onBack }) {
  const root = useRef(null);
  const [mode, setMode] = useState("login"); // login | signup | register | forgot
  const [form, setForm] = useState({ email: "", password: "", full_name: "", invitation: "" });
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });
  const go = (m) => { setMode(m); setError(""); setInfo(""); };

  usePanelMotion(root, mode);

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setInfo("");
    setBusy(true);
    try {
      if (mode === "forgot") {
        await api.forgotPassword(form.email);
        setInfo("Si un compte existe pour cette adresse, un email avec un lien vient d'être envoyé.");
      } else {
        if (mode === "register") {
          await api.register({ email: form.email, password: form.password, full_name: form.full_name, role: "consultant", invitation: form.invitation });
        }
        const user = await api.login({ email: form.email, password: form.password });
        if (user.role !== space) {
          await api.logout();
          throw new Error(space === "candidate" ? "Ce compte est un compte consultant : choisissez l'espace consultant." : "Ce compte est un compte candidat : choisissez l'espace candidat.");
        }
        onLogin(user);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className={"auth " + space}>
      <button className="link back" onClick={onBack}>Changer d'espace</button>
      <h1 className="auth-title">{TITLES[space]}</h1>
      {mode === "signup" ? (
        <Signup onBack={() => go("login")} />
      ) : (
        <div ref={root} className="auth-body">
          <div className="panel">
            <div className="tabs" role="tablist">
              <button role="tab" aria-selected={mode !== "register"} className={mode !== "register" ? "on" : ""} onClick={() => go("login")}>Connexion</button>
              {space === "candidate"
                ? <button role="tab" aria-selected="false" onClick={() => go("signup")}>Créer un compte</button>
                : <button role="tab" aria-selected={mode === "register"} className={mode === "register" ? "on" : ""} onClick={() => go("register")}>Créer un compte</button>}
            </div>
            <form onSubmit={submit}>
              {mode === "register" && <label>Nom complet <input value={form.full_name} onChange={set("full_name")} required maxLength={120} /></label>}
              <label>Adresse email <input type="email" value={form.email} onChange={set("email")} required autoComplete="email" /></label>
              {mode !== "forgot" && (
                <label>Mot de passe {mode === "register" && <small>10 caractères minimum</small>}
                  <input type="password" value={form.password} onChange={set("password")} required minLength={mode === "register" ? 10 : 1}
                         autoComplete={mode === "login" ? "current-password" : "new-password"} /></label>
              )}
              {mode === "register" && <label>Code d'invitation <input value={form.invitation} onChange={set("invitation")} required /></label>}
              {info && <p className="ok" role="status">{info}</p>}
              {error && <p className="error" role="alert">{error}</p>}
              <button className="primary" disabled={busy}>
                {busy ? "Patientez…" : mode === "forgot" ? "Envoyer le lien" : mode === "register" ? "Créer mon compte" : "Se connecter"}
              </button>
            </form>
            {mode === "login" && <button className="link" onClick={() => go("forgot")}>Mot de passe oublié ?</button>}
            {mode === "forgot" && <button className="link" onClick={() => go("login")}>Retour à la connexion</button>}
          </div>
        </div>
      )}
    </section>
  );
}
