import { useCallback, useState } from "react";
import { useTranslation } from "react-i18next";
import "leaflet/dist/leaflet.css";
import { MapContainer, Rectangle, TileLayer, Tooltip } from "react-leaflet";
import { PageHeader } from "../components/Layout";
import { LiveEvent, useLiveEvents } from "../hooks/useLive";

// Kodagu (Coorg) district, Karnataka: flood- and landslide-prone (2018, 2019). Used only to place the synthetic scenario.
export const KODAGU_CENTER: [number, number] = [12.4244, 75.7382];
export const KODAGU_BOUNDS: [[number, number], [number, number]] = [[11.95, 75.42], [12.86, 76.2]];

export default function CommandMap() {
  const { t } = useTranslation();
  const [events, setEvents] = useState<LiveEvent[]>([]);
  const onEvent = useCallback((e: LiveEvent) => setEvents((x) => [e, ...x].slice(0, 8)), []);
  useLiveEvents(onEvent);
  return (
    <div className="space-y-4">
      <PageHeader title={t("map.title")} sub={t("map.sub")}>
        <span className="badge bg-amber-100 text-amber-800">{t("common.synthetic")}</span>
      </PageHeader>
      <div className="grid gap-4 xl:grid-cols-[1fr_300px]">
        <div className="card h-[70vh] min-h-[420px] overflow-hidden">
          <MapContainer center={KODAGU_CENTER} zoom={10} style={{ height: "100%", width: "100%" }}>
            <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" maxZoom={18}
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' />
            <Rectangle bounds={KODAGU_BOUNDS} pathOptions={{ color: "#7c3aed", weight: 2, dashArray: "6 6", fillOpacity: 0.04 }}>
              <Tooltip sticky>{t("map.district")}</Tooltip>
            </Rectangle>
          </MapContainer>
        </div>
        <section className="card p-3" aria-label="Live events">
          <h2 className="mb-2 text-sm font-semibold text-slate-700">Live events</h2>
          {!events.length && <p className="text-sm text-slate-500">Waiting for events on /ws/live…</p>}
          <ul className="space-y-1.5 text-xs">
            {events.map((e, i) => (
              <li key={i} className="rounded-lg bg-slate-50 px-2 py-1.5"><span className="font-semibold text-brand-700">{e.type}</span> · {e.at}</li>
            ))}
          </ul>
        </section>
      </div>
    </div>
  );
}
