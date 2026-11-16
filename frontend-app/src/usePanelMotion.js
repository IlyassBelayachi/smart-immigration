import gsap from "gsap";
import { useGSAP } from "@gsap/react";
import { D, EASE, reduced } from "./motion.js";

gsap.registerPlugin(useGSAP);

// Répond à une action de la personne : le nouveau panneau glisse en place. `key` change => on rejoue.
export const usePanelMotion = (scope, key, fromX = 24) =>
  useGSAP(() => {
    if (reduced()) return;
    gsap.from(".panel", { x: fromX, opacity: 0, duration: D.base, ease: EASE.out });
  }, { scope, dependencies: [key] });

// Arrivée des blocs d'une vue, une seule fois.
export const useEnter = (scope, selector, deps = []) =>
  useGSAP(() => {
    if (reduced()) return;
    gsap.from(selector, { opacity: 0, y: 18, duration: D.base, stagger: 0.07, ease: EASE.out });
  }, { scope, dependencies: deps });
