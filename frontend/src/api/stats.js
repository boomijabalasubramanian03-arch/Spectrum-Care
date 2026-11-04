import { request, authHeaders } from "./http.js";

export async function getStats() {
  const { data } = await request("/api/analysis/stats", { headers: authHeaders() });
  return data;
}
