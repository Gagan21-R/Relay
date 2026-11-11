import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import CommandMap from "./pages/CommandMap";
import Planned from "./pages/Planned";

// [path, nav key, page key, phase that fills it]
const PLANNED: [string, string, string, number][] = [
  ["feed", "feed", "feed", 4],
  ["phone", "phone", "phone", 4],
  ["incidents", "incidents", "incidents", 5],
  ["fast-verify", "fastVerify", "fastVerify", 5],
  ["resources", "resources", "resources", 6],
  ["shelters", "shelters", "shelters", 6],
  ["plans", "plans", "plans", 7],
  ["dispatch", "dispatch", "dispatch", 7],
  ["alerts", "alerts", "alerts", 8],
  ["scenario", "scenario", "scenario", 10],
  ["twin3d", "twin3d", "twin3d", 10],
  ["metrics", "metrics", "metrics", 11],
  ["audit", "audit", "audit", 2],
  ["field", "field", "field", 3],
];

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<CommandMap />} />
        {PLANNED.map(([path, nav, page, phase]) => (
          <Route key={path} path={path} element={<Planned navKey={nav} pageKey={page} phase={phase} />} />
        ))}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
