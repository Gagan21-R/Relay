// Prototype role switcher. The chosen role/actor travel as X-Role / X-Actor headers on every request; the backend
// enforces task-lifecycle permissions (403 unauthorised, 409 invalid transition). There is no login in this prototype.
import { useEffect, useState } from "react";
import { getRole, ROLES, setRole } from "../services/api";

export function RoleSwitcher() {
  const [r, setR] = useState(getRole());
  useEffect(() => { const f = () => setR(getRole()); window.addEventListener("relay-role", f); return () => window.removeEventListener("relay-role", f); }, []);
  return (
    <label className="flex items-center gap-1.5 rounded-xl border-2 border-ink bg-white px-2 py-0.5 shadow-hard-sm" title="Prototype role switch (no login): the backend checks this role on every lifecycle action">
      <span className="text-[11px] font-extrabold uppercase tracking-wider">acting as</span>
      <select value={`${r.role}|${r.actor}`} onChange={(e) => { const [role, actor] = e.target.value.split("|"); setRole(role, actor); }}
        aria-label="Acting role" className="rounded-lg bg-transparent py-0.5 text-xs font-extrabold focus:outline-none">
        {ROLES.map((x) => <option key={`${x.role}|${x.actor}`} value={`${x.role}|${x.actor}`}>{x.label}</option>)}
      </select>
    </label>
  );
}
