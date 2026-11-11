import { useEffect, useState } from "react";
// REST client. Errors carry the backend's message so the UI can say what went wrong.
export class ApiError extends Error {
  constructor(public status: number, message: string) { super(message); }
}

export const ROLES = [
  { role: "duty_officer", actor: "Duty Officer", label: "Duty Officer" },
  { role: "volunteer", actor: "V-001", label: "Volunteer V-001" },
  { role: "volunteer", actor: "V-002", label: "Volunteer V-002" },
  { role: "volunteer", actor: "V-003", label: "Volunteer V-003" },
  { role: "volunteer", actor: "V-004", label: "Volunteer V-004" },
  { role: "volunteer", actor: "V-005", label: "Volunteer V-005" },
  { role: "volunteer", actor: "V-006", label: "Volunteer V-006" },
  { role: "volunteer", actor: "V-007", label: "Volunteer V-007" },
  { role: "viewer", actor: "Observer", label: "Observer (read-only)" },
];
export function getRole(): { role: string; actor: string } {
  try { const v = JSON.parse(localStorage.getItem("relay.role") || "null"); if (v?.role) return v; } catch { /* ignore */ }
  return { role: "duty_officer", actor: "Duty Officer" };
}
export function useRole() {
  const [r, setR] = useState(getRole());
  useEffect(() => { const f = () => setR(getRole()); window.addEventListener("relay-role", f); return () => window.removeEventListener("relay-role", f); }, []);
  return r;
}
export function setRole(role: string, actor: string) {
  try { localStorage.setItem("relay.role", JSON.stringify({ role, actor })); } catch { /* ignore */ }
  window.dispatchEvent(new Event("relay-role"));
}

export async function api<T = unknown>(path: string, init: RequestInit = {}): Promise<T> {
  let res: Response;
  const who = getRole();
  try {
    res = await fetch(path, { ...init, headers: { "Content-Type": "application/json", "X-Role": who.role, "X-Actor": who.actor, ...(init.headers ?? {}) } });
  } catch {
    throw new ApiError(0, "The RELAY backend is not reachable.");
  }
  if (!res.ok) {
    let msg = res.statusText;
    try { msg = (await res.json()).detail ?? msg; } catch { /* not json */ }
    throw new ApiError(res.status, String(msg));
  }
  return res.json() as Promise<T>;
}

export type Health = {
  status: string; database: string; database_ok: boolean; mock_mode: boolean; llm: string; embeddings: string;
  sms_provider: string; ws_clients: number; agents: string[];
};
