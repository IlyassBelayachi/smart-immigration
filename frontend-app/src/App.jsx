import React, { useEffect, useState } from "react";
import { api } from "./api.js";
import Home from "./Home.jsx";
import AuthScreen from "./AuthScreen.jsx";
import Candidate from "./Candidate.jsx";
import Consultant from "./Consultant.jsx";
import { VerifyEmail, ResetPassword } from "./EmailLinks.jsx";

export default function App() {
  const [user, setUser] = useState(undefined); // undefined = chargement, null = déconnecté
  const [space, setSpace] = useState(null);
  const params = new URLSearchParams(window.location.search);
  const [link, setLink] = useState({ verify: params.get("verify"), reset: params.get("reset") });
  const leaveLink = () => { window.history.replaceState({}, "", window.location.pathname); setLink({}); };

  useEffect(() => { api.me().then(setUser).catch(() => setUser(null)); }, []);

  const logout = async () => {
    await api.logout().catch(() => {});
    setUser(null);
    setSpace(null);
  };

  const inLink = link.verify || link.reset;

  return (
    <div className="shell">
      <header className="top">
        <span className="brand"><i className="mark" aria-hidden="true" />Smart Immigration</span>
        {user && (
          <span className="who">
            <span>{user.full_name}</span>
            <button className="link" onClick={logout}>Se déconnecter</button>
          </span>
        )}
      </header>
      <main>
        {user === undefined && <p className="muted">Chargement…</p>}
        {link.verify && <VerifyEmail token={link.verify} onDone={leaveLink} />}
        {link.reset && <ResetPassword token={link.reset} onDone={leaveLink} />}
        {user === null && !inLink && (space
          ? <AuthScreen space={space} onLogin={setUser} onBack={() => setSpace(null)} />
          : <Home onChoose={setSpace} />)}
        {user && !inLink && user.role === "consultant" && <Consultant />}
        {user && !inLink && user.role === "candidate" && <Candidate user={user} onUser={setUser} />}
      </main>
      <footer className="foot">
        Projet PFA EMSI 2026-2027. L'assistant prépare le dossier ; la décision revient toujours à un consultant.
      </footer>
    </div>
  );
}
