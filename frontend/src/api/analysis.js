import { request, authHeaders, resolveUrl } from "./http.js";

const BASE = "/api/analysis";

export async function uploadImage(file) {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await request(`${BASE}/upload`, {
    method: "POST",
    headers: authHeaders(), // no Content-Type: the browser sets the multipart boundary
    body: formData,
  });
  return data;
}

export async function getAnalysis(anaId) {
  const { data } = await request(`${BASE}/${anaId}`, { headers: authHeaders() });
  return data;
}

export async function getHistory() {
  const { data } = await request(`${BASE}/history`, { headers: authHeaders() });
  return data;
}

export function reportUrl(anaId, fmt) {
  return `${BASE}/${anaId}/report?fmt=${fmt}`;
}

export async function downloadReport(anaId, fmt) {
  let res;
  try {
    res = await fetch(resolveUrl(reportUrl(anaId, fmt)), { headers: authHeaders() });
  } catch {
    throw new Error("Can't reach the server to generate that report.");
  }
  if (!res.ok) throw new Error("Could not generate that report.");
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `report-${anaId}.${fmt}`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
