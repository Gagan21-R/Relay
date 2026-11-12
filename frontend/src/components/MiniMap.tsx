// A compact live map for previews (plan routes, dispatches). Real OSM tiles, Kodagu framing.
import { ReactNode } from "react";
import "leaflet/dist/leaflet.css";
import { CircleMarker, MapContainer, Polyline, TileLayer, Tooltip } from "react-leaflet";

export type MiniRoute = { id: string | number; points: number[][]; color?: string; dashed?: boolean; label?: string; end?: number[] };

export default function MiniMap({ routes, height = 320, children }: { routes: MiniRoute[]; height?: number; children?: ReactNode }) {
  return (
    <div className="overflow-hidden rounded-2xl border-2 border-ink" style={{ height }}>
      <MapContainer center={[12.42, 75.78]} zoom={10} style={{ height: "100%", width: "100%" }} scrollWheelZoom={false}>
        <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" maxZoom={18} attribution='&copy; OpenStreetMap contributors' />
        {routes.map((r) => (
          <Polyline key={r.id} positions={r.points as [number, number][]} pathOptions={{ color: r.color ?? "#000000", weight: 5, opacity: 0.9, dashArray: r.dashed ? "8 8" : undefined }}>
            {r.label && <Tooltip sticky>{r.label}</Tooltip>}
          </Polyline>
        ))}
        {routes.map((r) => r.points.length > 0 && (
          <CircleMarker key={`e${r.id}`} center={(r.end ?? r.points[r.points.length - 1]) as [number, number]} radius={7}
            pathOptions={{ color: "#000000", weight: 2, fillColor: r.color ?? "#000000", fillOpacity: 1 }}>
            {r.label && <Tooltip>{r.label}</Tooltip>}
          </CircleMarker>
        ))}
        {children}
      </MapContainer>
    </div>
  );
}
