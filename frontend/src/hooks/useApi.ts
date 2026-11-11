// Fetch an endpoint and re-fetch (debounced) whenever a related live event arrives over /ws/live.
import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../services/api";
import { LiveEvent, useLiveEvents } from "./useLive";

export function useApi<T>(path: string | null, refreshOn: string[] = [], debounceMs = 400) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const timer = useRef<number>();
  const load = useCallback(() => {
    if (!path) return Promise.resolve();
    return api<T>(path)
      .then((d) => { setData(d); setError(null); })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [path]);
  useEffect(() => { setLoading(true); load(); }, [load]);
  const types = useRef(refreshOn).current;
  const onEvent = useCallback((_e: LiveEvent) => {
    window.clearTimeout(timer.current);
    timer.current = window.setTimeout(load, debounceMs);
  }, [load, debounceMs]);
  useLiveEvents(onEvent, types.length ? [...types, "refresh"] : ["__none__"]);
  return { data, error, loading, reload: load, setData };
}
