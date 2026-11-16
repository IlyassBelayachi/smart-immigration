// Durées et courbes en un seul endroit ; on n'anime que transform, opacity et le tracé SVG.
export const D = { fast: 0.25, base: 0.45, slow: 0.8 };
export const EASE = { out: "power3.out", inOut: "power2.inOut" };
export const reduced = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches;
