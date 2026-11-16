import React, { useEffect, useRef, useState } from "react";
import gsap from "gsap";
import { useGSAP } from "@gsap/react";
import { api } from "./api.js";
import { D, EASE } from "./motion.js";

gsap.registerPlugin(useGSAP);

const COUNTDOWN = 3;
const RADIUS = 146;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

// Une seule photo prise en direct : on se place, puis un compte à rebours referme l'anneau et la photo est prise.
export default function LiveCheck({ onDone, onCancel }) {
  const root = useRef(null);
  const video = useRef(null);
  const stream = useRef(null);
  const challenge = useRef(null);
  const [phase, setPhase] = useState("idle"); // idle | ready | counting | error
  const [count, setCount] = useState(COUNTDOWN);
  const [error, setError] = useState("");

  const { contextSafe } = useGSAP({ scope: root });

  useEffect(() => () => stop(), []);

  function stop() {
    stream.current?.getTracks().forEach((t) => t.stop());
    stream.current = null;
  }

  const openCamera = async () => {
    setError("");
    try {
      challenge.current = await api.challenge();
      stream.current = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "user" }, audio: false });
      setPhase("ready");
      await new Promise((r) => setTimeout(r, 30));
      video.current.srcObject = stream.current;
      await video.current.play();
    } catch (err) {
      stop();
      setPhase("error");
      setError(err.name === "NotAllowedError" || err.name === "NotFoundError"
        ? "Caméra indisponible ou refusée. Autorisez la caméra dans votre navigateur, puis réessayez."
        : err.message);
    }
  };

  const fillRing = contextSafe(() => new Promise((resolve) => {
    gsap.fromTo(".ring-progress", { strokeDashoffset: CIRCUMFERENCE }, {
      strokeDashoffset: 0, duration: COUNTDOWN, ease: "none",
      onUpdate() { setCount(Math.max(1, Math.ceil(COUNTDOWN * (1 - this.progress())))); },
      onComplete: resolve,
    });
  }));

  const flash = contextSafe(() => gsap.fromTo(".flash", { opacity: 0.95 }, { opacity: 0, duration: D.base, ease: EASE.out }));

  const capture = async () => {
    setPhase("counting");
    await fillRing();
    const v = video.current;
    const canvas = document.createElement("canvas");
    canvas.width = v.videoWidth;
    canvas.height = v.videoHeight;
    canvas.getContext("2d").drawImage(v, 0, 0); // image non inversée ; l'aperçu à l'écran, lui, est en miroir
    flash();
    const blob = await new Promise((r) => canvas.toBlob(r, "image/jpeg", 0.92));
    stop();
    onDone({ token: challenge.current.token, frames: [new File([blob], "live.jpg", { type: "image/jpeg" })] });
  };

  const live = phase === "ready" || phase === "counting";

  return (
    <div ref={root} className="scan">
      <div className={"scan-frame" + (live ? " on" : "")}>
        <div className="scan-video">
          <video ref={video} autoPlay playsInline muted className="mirror" />
          {phase === "counting" && <span className="count" aria-live="polite">{count}</span>}
          <span className="flash" />
        </div>
        <svg className="ring" viewBox="0 0 300 300" aria-hidden="true">
          <circle className="ring-track" cx="150" cy="150" r={RADIUS} />
          <circle className="ring-progress" cx="150" cy="150" r={RADIUS}
                  strokeDasharray={CIRCUMFERENCE} strokeDashoffset={CIRCUMFERENCE} transform="rotate(-90 150 150)" />
        </svg>
      </div>
      {phase === "ready" && <p className="scan-tip">Placez votre visage dans le cercle, regardez la caméra, puis prenez la photo.</p>}
      {phase === "counting" && <p className="scan-tip">Ne bougez plus, regardez la caméra.</p>}
      {!live && phase !== "error" && <p className="scan-tip">Une seule photo, prise en direct. Bonne lumière, visage de face, sans lunettes de soleil.</p>}
      {error && <p className="error" role="alert">{error}</p>}
      <div className="row center">
        {!live && <button type="button" className="primary" onClick={openCamera}>{phase === "error" ? "Réessayer" : "Ouvrir la caméra"}</button>}
        {phase === "ready" && <button type="button" className="primary" onClick={capture}>Prendre la photo</button>}
        {phase !== "counting" && onCancel && <button type="button" onClick={onCancel}>Retour</button>}
      </div>
    </div>
  );
}
