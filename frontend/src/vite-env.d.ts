/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Full WebSocket URL of the backend's live feed, for hosts that cannot proxy WebSockets (Netlify). */
  readonly VITE_WS_URL?: string;
}
