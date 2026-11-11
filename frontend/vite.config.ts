/// <reference types="vitest" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const API = process.env.RELAY_API ?? "http://127.0.0.1:8010";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5180,
    host: true,
    proxy: {
      "/api": { target: API, changeOrigin: true },
      "/ws": { target: API.replace(/^http/, "ws"), ws: true },
    },
  },
  build: { chunkSizeWarningLimit: 1200, rollupOptions: { output: { manualChunks: { map: ["leaflet", "react-leaflet"], motion: ["framer-motion"] } } } },
  test: { environment: "jsdom", globals: true },
});
