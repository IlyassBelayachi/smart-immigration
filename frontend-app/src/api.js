// Petit client pour l'API. Le cookie de session part automatiquement (même origine).
async function call(path, options = {}) {
  const res = await fetch(path, { credentials: "same-origin", ...options });
  if (res.status === 204) return null;
  let data = null;
  try {
    data = await res.json();
  } catch {
    /* pas de JSON */
  }
  if (!res.ok) {
    const err = new Error(messageFrom(res.status, data));
    err.reasons = (data && data.reasons) || [];
    throw err;
  }
  return data;
}

function messageFrom(status, data) {
  const d = data && data.detail;
  if (status === 404 && d === "Not Found") return "La route demandée est indisponible. Vérifiez que le serveur correspond à cette version de l’application.";
  if (typeof d === "string") return d;
  if (Array.isArray(d) && d.length) {
    // Erreurs de validation : on affiche le premier message lisible.
    const first = d[0];
    const msg = (first.msg || "").replace(/^Value error, /, "");
    return msg || "Données invalides.";
  }
  return `Erreur ${status}`;
}

const json = (body) => ({
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});

export const api = {
  me: () => call("/auth/me"),
  register: (body) => call("/auth/register", { method: "POST", ...json(body) }),
  login: (body) => call("/auth/login", { method: "POST", ...json(body) }),
  logout: () => call("/auth/logout", { method: "POST" }),
  updateProfile: (body) => call("/auth/me", { method: "PATCH", ...json(body) }),
  challenge: () => call("/auth/signup/challenge"),
  signup: (form) => call("/auth/signup", { method: "POST", body: form }),
  verifyEmail: (token) => call("/auth/verify-email", { method: "POST", ...json({ token }) }),
  resendConfirmation: (email) => call("/auth/resend-confirmation", { method: "POST", ...json({ email }) }),
  forgotPassword: (email) => call("/auth/forgot-password", { method: "POST", ...json({ email }) }),
  resetPassword: (token, password) => call("/auth/reset-password", { method: "POST", ...json({ token, password }) }),
  myRequests: () => call("/requests"),
  formOptions: () => call("/requests/form-options"),
  orientation: (answers) => call("/requests/orientation", { method: "POST", ...json(answers) }),
  interview: (answers, confirmed = false) => call("/requests/orientation/interview", { method: "POST", ...json({ answers, confirmed }) }),
  readSpecimen: (kind, file) => call(`/dossier/documents/${kind}`, {
    method: "POST", headers: { "Content-Type": file.name.toLowerCase().endsWith(".pdf") ? "application/pdf" : "text/plain" }, body: file
  }),
  supplement: (id, message) => call(`/requests/${id}/supplement`, { method: "POST", ...json({ message }) }),
  createRequest: (body) => call("/requests", { method: "POST", ...json(body) }),
  consultantRequests: () => call("/consultant/requests"),
  decide: (id, body) => call(`/consultant/requests/${id}/decision`, { method: "POST", ...json(body) }),
};
