import React, { useRef } from "react";
import gsap from "gsap";
import { useGSAP } from "@gsap/react";
import { D, EASE } from "./motion.js";

gsap.registerPlugin(useGSAP);

// Vraie suite d'étapes : le trait se remplit quand on avance.
export default function Stepper({ labels, step }) {
  const root = useRef(null);
  useGSAP(() => {
    gsap.to(".steps-fill", { scaleX: step / labels.length, duration: D.base, ease: EASE.inOut });
  }, { scope: root, dependencies: [step] });

  return (
    <div ref={root} className="stepper">
      <div className="steps-track"><span className="steps-fill" /></div>
      <ol>
        {labels.map((label, i) => (
          <li key={label} className={i + 1 < step ? "done" : i + 1 === step ? "now" : ""} aria-current={i + 1 === step ? "step" : undefined}>
            {label}
          </li>
        ))}
      </ol>
    </div>
  );
}
