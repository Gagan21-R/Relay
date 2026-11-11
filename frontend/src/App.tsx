import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import CommandMap from "./pages/CommandMap";
import Planned from "./pages/Planned";
import LiveFeed from "./pages/LiveFeed";
import PhoneSimulator from "./pages/PhoneSimulator";
import FieldApp from "./pages/FieldApp";
import RadioConsole from "./pages/RadioConsole";

// [path, nav key, page key, phase that fills it]
const PLANNED: [string, string, string, number][] = [
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
  ["blackout", "blackout", "blackout", 8],
];

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<CommandMap />} />
        <Route path="feed" element={<LiveFeed />} />
        <Route path="phone" element={<PhoneSimulator />} />
        <Route path="field" element={<FieldApp />} />
        <Route path="radio" element={<RadioConsole />} />
        {PLANNED.map(([path, nav, page, phase]) => (
          <Route key={path} path={path} element={<Planned navKey={nav} pageKey={page} phase={phase} />} />
        ))}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
