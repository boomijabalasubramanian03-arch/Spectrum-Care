import { request, authHeaders } from "./http.js";

const BASE = "/api/admin";

export async function getAdminOverview() {
  const { data } = await request(`${BASE}/overview`, {
    headers: authHeaders(),
  });
  return data;
}

export async function getAdminUsers() {
  const { data } = await request(`${BASE}/users`, {
    headers: authHeaders(),
  });
  return data;
}

export async function updateUserStatus(userId, status) {
  const { data } = await request(`${BASE}/users/${userId}/status`, {
    method: "PATCH",
    headers: {
      ...authHeaders(),
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ status }),
  });
  return data;
}

export async function updateUserRole(userId, role) {
  const { data } = await request(`${BASE}/users/${userId}/role`, {
    method: "PATCH",
    headers: {
      ...authHeaders(),
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ role }),
  });
  return data;
}

export async function getServicesStatus() {
  const { data } = await request(`${BASE}/services`, {
    headers: authHeaders(),
  });
  return data;
}

export async function getModelInfo() {
  const { data } = await request(`${BASE}/models`, {
    headers: authHeaders(),
  });
  return data;
}

export async function updateModelConfig(config) {
  const { data } = await request(`${BASE}/models/config`, {
    method: "POST",
    headers: {
      ...authHeaders(),
      "Content-Type": "application/json",
    },
    body: JSON.stringify(config),
  });
  return data;
}

export async function getAuditLogs(limit = 40) {
  const { data } = await request(`${BASE}/audit-logs?limit=${limit}`, {
    headers: authHeaders(),
  });
  return data;
}

export async function validateAnalysisTask(anaId, status) {
  const { data } = await request(`${BASE}/analyses/${anaId}/validate`, {
    method: "PATCH",
    headers: {
      ...authHeaders(),
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ status }),
  });
  return data;
}
