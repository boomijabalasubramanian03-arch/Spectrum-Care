import { request, authHeaders } from "./http.js";

export async function getProfile() {
  const { data } = await request("/api/profile", { headers: authHeaders() });
  return data;
}

export async function saveProfile(profile) {
  const { data } = await request("/api/profile", {
    method: "PUT",
    headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(profile),
  });
  return data;
}

export async function getCvdProfile() {
  const { data } = await request("/api/profile/cvd", { headers: authHeaders() });
  return data;
}

export async function saveCvdProfile({ type, severity }) {
  const { data } = await request("/api/profile/cvd", {
    method: "PUT",
    headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ type, severity }),
  });
  return data;
}
