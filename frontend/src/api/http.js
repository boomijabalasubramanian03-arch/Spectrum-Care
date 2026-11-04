// Shared fetch helper. Supports local relative proxy or Vercel cloud deployment
// through VITE_API_URL environment variable.

export const API_BASE = (import.meta.env.VITE_API_URL || "").replace(/\/+$/, "");

export function resolveUrl(path) {
  if (!path) return "";
  if (path.startsWith("http://") || path.startsWith("https://")) return path;
  const cleanPath = path.startsWith("/") ? path : `/${path}`;
  return `${API_BASE}${cleanPath}`;
}

export function getToken() {
  return localStorage.getItem("access_token");
}

export function authHeaders() {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

function detailToText(detail) {
  if (!detail) return "";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((d) => {
        const field = Array.isArray(d.loc)
          ? d.loc.filter((x) => x !== "body" && x !== "query").join(".")
          : "";
        return field ? `${field}: ${d.msg}` : d.msg;
      })
      .join("; ");
  }
  return "";
}

export async function request(url, options = {}, { auth = true } = {}) {
  const targetUrl = resolveUrl(url);
  let res;
  try {
    res = await fetch(targetUrl, {
      ...options,
      headers: {
        Accept: "application/json",
        ...(options.headers || {}),
      },
    });
  } catch (err) {
    throw new Error(
      "Cannot reach the backend server. Please verify your connection or server status."
    );
  }

  const text = await res.text();
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = null;
  }

  if (res.ok) return { res, data, text };

  if ([502, 503, 504].includes(res.status)) {
    throw new Error(
      "The backend is not available. Start the backend and try again."
    );
  }

  if (res.status === 401 && auth) {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");
    if (!window.location.pathname.startsWith("/login")) {
      window.location.assign("/login");
    }
    throw new Error("Your session has expired. Please log in again.");
  }

  if (res.status === 409) {
    throw new Error(detailToText(data?.detail) || "This record already exists.");
  }

  throw new Error(
    detailToText(data?.detail) ||
      (res.status >= 500
        ? "The server encountered an error. Check the backend terminal for details."
        : `Request failed (HTTP ${res.status}). Please check your input.`)
  );
}

export async function checkBackend() {
  try {
    const res = await fetch("/api/health", { cache: "no-store" });
    if (!res.ok) return false;
    const data = await res.json();
    return data?.status === "ok";
  } catch {
    return false;
  }
}
