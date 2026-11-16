import React, { useRef } from "react";
import gsap from "gsap";
import { useGSAP } from "@gsap/react";
import { D, EASE, reduced } from "./motion.js";

gsap.registerPlugin(useGSAP);

const STAGES = ["Envoyée", "En examen", "Décision"];
const STAGE_OF = { awaiting_review: 2, needs_info: 2, approved: 3, rejected: 3 };

// Suite réelle : la demande avance de l'envoi à la décision.
export default function StatusTrack({ status }) {
  const root = useRef(null);
  const stage = STAGE_OF[status] || 1;
  const done = status === "approved" || status === "rejected";

  useGSAP(() => {
    const to = (stage - (done ? 0 : 0.5)) / STAGES.length;
    if (reduced()) gsap.set(".track-fill", { scaleX: to });
    else gsap.fromTo(".track-fill", { scaleX: 0 }, { scaleX: to, duration: D.slow, ease: EASE.out });
  }, { scope: root, dependencies: [stage, done] });

  return (
    <div ref={root} className={"track s-" + status}>
      <div className="track-line"><span className="track-fill" /></div>
      <ol>
        {STAGES.map((label, i) => <li key={label} className={i + 1 <= stage ? "reached" : ""}>{label}</li>)}
      </ol>
    </div>
  );
}
