import React, { useRef } from "react";
import gsap from "gsap";
import { useGSAP } from "@gsap/react";
import { D, EASE, reduced } from "./motion.js";

gsap.registerPlugin(useGSAP);

export default function Home({ onChoose }) {
  const root = useRef(null);

  // Le seul mouvement spontané de la page : une séquence d'arrivée.
  useGSAP(() => {
    if (reduced()) return;
    gsap.timeline({ defaults: { ease: EASE.out } })
      .from(".hl", { yPercent: 110, duration: D.slow, stagger: 0.1 })
      .from(".home-intro", { opacity: 0, y: 14, duration: D.base }, "-=0.4")
      .from(".role-card", { opacity: 0, y: 40, duration: D.slow, stagger: 0.12 }, "-=0.3")
      .from(".facts li", { opacity: 0, y: 10, duration: D.base, stagger: 0.07 }, "-=0.4");
  }, { scope: root });

  return (
    <div ref={root} className="home">
      <h1>
        <span className="mask"><span className="hl">Préparez votre dossier d'immigration.</span></span>
        <span className="mask"><span className="hl hl-soft">Un consultant humain décide.</span></span>
      </h1>
      <p className="home-intro">
        Un assistant vérifie votre identité et contrôle les critères officiels. Vous gardez la main sur votre dossier, et
        un consultant prend la décision finale.
      </p>
      <div className="role-grid">
        <button className="role-card candidate" onClick={() => onChoose("candidate")}>
          <span className="role-body">
            <strong>Candidat</strong>
            <span>Créez votre compte, faites vérifier votre identité, puis déposez votre demande.</span>
            <span className="role-go">Entrer dans mon espace</span>
          </span>
        </button>
        <button className="role-card consultant" onClick={() => onChoose("consultant")}>
          <span className="role-body">
            <strong>Consultant</strong>
            <span>Examinez les demandes recommandées par l'assistant et rendez votre décision.</span>
            <span className="role-go">Entrer dans mon espace</span>
          </span>
        </button>
      </div>
      <ul className="facts">
        <li>Identité vérifiée automatiquement : CIN et visage en direct.</li>
        <li>Critères contrôlés par des règles officielles, avec leurs sources.</li>
        <li>Aucune demande n'est envoyée sans décision d'un consultant.</li>
      </ul>
    </div>
  );
}
