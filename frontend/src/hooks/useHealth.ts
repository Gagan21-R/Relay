import { useEffect, useState } from "react";
import { api, Health } from "../services/api";

export function useHealth(everyMs = 15000) {
  const [health, setHealth] = useState<Health | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    let alive = true;
    const load = () => api<Health>("/api/health")
      .then((h) => { if (alive) { setHealth(h); setError(null); } })
      .catch((e) => { if (alive) setError(e.message); });
    load();
    const t = window.setInterval(load, everyMs);
    return () => { alive = false; window.clearInterval(t); };
  }, [everyMs]);
  return { health, error };
}
