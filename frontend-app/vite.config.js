import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// En développement, Vite relaie les appels vers l'API (port 8000) : même origine, donc le cookie de session fonctionne.
const API = process.env.SMART_IMMIGRATION_API_URL || "http://127.0.0.1:8000";
const proxy = Object.fromEntries(
  ["/auth", "/identity", "/requests", "/consultant", "/dossier"].map((p) => [p, { target: API, changeOrigin: true }])
);

export default defineConfig(({ command }) => ({
  plugins: [react()],
  base: command === "build" ? "/app/" : "/",
  server: { port: 5173, proxy },
}));
