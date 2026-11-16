import React, { useEffect, useRef, useState } from "react";
import { api } from "./api.js";
import LiveCheck from "./LiveCheck.jsx";
import Stepper from "./Stepper.jsx";
import { usePanelMotion } from "./usePanelMotion.js";

const LABELS = ["Informations", "Votre CIN", "Votre visage"];

export default function Signup({ onBack }) {
  const root = useRef(null);
  const [step, setStep] = useState(1);
  const [f, setF] = useState({ full_name: "", email: "", password: "", cin: "" });
  const [cinFile, setCinFile] = useState(null);
  const [preview, setPreview] = useState("");
  const [error, setError] = useState("");
  const [reasons, setReasons] = useState([]);
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(null);
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });

  usePanelMotion(root, step + (done ? "-done" : ""));

  useEffect(() => {
    if (!cinFile) return setPreview("");
    const url = URL.createObjectURL(cinFile);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [cinFile]);

  const submit = async ({ token, frames }) => {
    setBusy(true);
    setError("");
    setReasons([]);
    try {
      const form = new FormData();
      Object.entries(f).forEach(([k, v]) => form.append(k, v));
      form.append("token", token);
      form.append("cin_image", cinFile, cinFile.name || "cin.jpg");
      frames.forEach((fr, i) => form.append("frames", fr, `live${i}.jpg`));
      setDone(await api.signup(form));
    } catch (err) {
      setError(err.message);
      setReasons(err.reasons || []);
    } finally {
      setBusy(false);
    }
  };

  if (done) {
    return (
      <div ref={root} className="auth-body">
        <div className="panel success">
          <h2>Identité vérifiée, compte créé</h2>
          {done.email_confirmation_required
            ? <p>Un email de confirmation vient d'être envoyé. Ouvrez le lien qu'il contient, puis connectez-vous.</p>
            : <p>Vous pouvez maintenant vous connecter.</p>}
          <button className="primary" onClick={onBack}>Aller à la connexion</button>
        </div>
      </div>
    );
  }

  return (
    <div ref={root} className="auth-body">
      <Stepper labels={LABELS} step={step} />
      <div className="panel">
        {step === 1 && (
          <form onSubmit={(e) => { e.preventDefault(); setStep(2); }}>
            <h2>Vos informations</h2>
            <label>Nom complet <input value={f.full_name} onChange={set("full_name")} required maxLength={120} autoComplete="name" /></label>
            <label>Adresse email <input type="email" value={f.email} onChange={set("email")} required autoComplete="email" /></label>
            <label>Mot de passe <small>10 caractères minimum</small>
              <input type="password" value={f.password} onChange={set("password")} required minLength={10} autoComplete="new-password" /></label>
            <label>Numéro de CIN <small>1 à 3 lettres puis 6 à 8 chiffres, par exemple AB123456</small>
              <input value={f.cin} onChange={set("cin")} required maxLength={20} pattern="\s*[A-Za-z]{1,3}[\s\-]?[0-9]{6,8}\s*" title="Par exemple AB123456" /></label>
            <button className="primary">Continuer</button>
          </form>
        )}
        {step === 2 && (
          <div>
            <h2>Votre CIN</h2>
            <p>Envoyez une photo ou un scan net du recto : la photo du titulaire et le numéro doivent être lisibles. Utilisez uniquement votre propre carte.</p>
            {preview && <img src={preview} alt="Aperçu de la CIN" className="cin-preview" />}
            <label className="filebtn">
              {cinFile ? "Choisir une autre image" : "Choisir ou photographier la CIN"}
              <input type="file" accept="image/jpeg,image/png" capture="environment" hidden onChange={(e) => e.target.files[0] && setCinFile(e.target.files[0])} />
            </label>
            <div className="row">
              <button className="primary" disabled={!cinFile} onClick={() => setStep(3)}>Continuer</button>
              <button onClick={() => setStep(1)}>Retour</button>
            </div>
          </div>
        )}
        {step === 3 && (
          <div>
            <h2>Votre visage, en direct</h2>
            {reasons.length > 0 && (
              <div className="notice" role="alert">
                <strong>{error}</strong>
                <ul>{reasons.map((r) => <li key={r}>{r}</li>)}</ul>
              </div>
            )}
            {error && reasons.length === 0 && <p className="error" role="alert">{error}</p>}
            {busy ? <p className="muted">Vérification en cours…</p> : <LiveCheck key={reasons.length + error} onDone={submit} onCancel={() => setStep(2)} />}
            <p className="hint">Votre visage est comparé à la photo de la CIN. Ce contrôle automatique n'est pas une preuve absolue.</p>
          </div>
        )}
      </div>
      <button className="link" onClick={onBack}>Retour à la connexion</button>
    </div>
  );
}
