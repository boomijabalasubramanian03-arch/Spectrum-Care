import { request } from "./http.js";

const BASE = "/api/auth";

export async function register({ firstName, middleName, lastName, email, password }) {
  const { data } = await request(
    `${BASE}/register`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        first_name: firstName.trim(),
        middle_name: middleName?.trim() || null,
        last_name: lastName.trim(),
        email: email.trim().toLowerCase(),
        password,
      }),
    },
    { auth: false }
  );
  return data;
}

export async function login({ email, password }) {
  const { data } = await request(
    `${BASE}/login`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: email.trim().toLowerCase(), password }),
    },
    { auth: false }
  );
  localStorage.setItem("access_token", data.access_token);
  localStorage.setItem("user", JSON.stringify(data.user));
  return data;
}

export async function logout() {
  const token = localStorage.getItem("access_token");
  if (token) {
    await fetch(`${BASE}/logout`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    }).catch(() => {});
  }
  localStorage.removeItem("access_token");
  localStorage.removeItem("user");
}

export function getStoredUser() {
  try {
    const raw = localStorage.getItem("user");
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function isAuthenticated() {
  return Boolean(localStorage.getItem("access_token"));
}
