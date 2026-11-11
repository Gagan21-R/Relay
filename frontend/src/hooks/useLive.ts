// One WebSocket to /ws/live for the whole app, with automatic reconnect. Components subscribe to typed events.
import { useEffect, useState } from "react";

export type LiveEvent = { type: string; at: string; data: any };
type Listener = (e: LiveEvent) => void;
export type LiveStatus = "connecting" | "live" | "offline";

const listeners = new Set<Listener>();
const statusListeners = new Set<(s: LiveStatus) => void>();
let status: LiveStatus = "connecting";
let socket: WebSocket | null = null;
let retry = 1000;

function setStatus(s: LiveStatus) { status = s; statusListeners.forEach((f) => f(s)); }

export function connectLive() {
  if (socket && socket.readyState <= 1) return;
  const proto = location.protocol === "https:" ? "wss" : "ws";
  socket = new WebSocket(`${proto}://${location.host}/ws/live`);
  setStatus("connecting");
  socket.onopen = () => { retry = 1000; setStatus("live"); };
  socket.onmessage = (m) => {
    try { const e = JSON.parse(m.data) as LiveEvent; listeners.forEach((f) => f(e)); } catch { /* ignore malformed */ }
  };
  socket.onclose = () => {
    setStatus("offline");
    setTimeout(connectLive, retry);
    retry = Math.min(retry * 2, 15000);
  };
}

export function useLiveStatus() {
  const [s, setS] = useState<LiveStatus>(status);
  useEffect(() => { statusListeners.add(setS); return () => { statusListeners.delete(setS); }; }, []);
  return s;
}

/** Subscribe to live events (optionally of some types). */
export function useLiveEvents(onEvent: Listener, types?: string[]) {
  useEffect(() => {
    const f: Listener = (e) => { if (!types || types.includes(e.type)) onEvent(e); };
    listeners.add(f);
    return () => { listeners.delete(f); };
  }, [onEvent, types]);
}
