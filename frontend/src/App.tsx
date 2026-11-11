import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import CommandMap from "./pages/CommandMap";
import Planned from "./pages/Planned";
import LiveFeed from "./pages/LiveFeed";
import PhoneSimulator from "./pages/PhoneSimulator";
import FieldApp from "./pages/FieldApp";
import RadioConsole from "./pages/RadioConsole";
import About from "./pages/About";
import Incidents from "./pages/Incidents";
import FastVerify from "./pages/FastVerify";
import Resources from "./pages/Resources";
import Shelters from "./pages/Shelters";

// [path, nav key, page key, phase that fills it]
const PLANNED: [string, string, string, number][] = [
  ["plans", "plans", "plans", 7],
  ["dispatch", "dispatch", "dispatch", 7],
  ["alerts", "alerts", "alerts", 8],
  ["scenario", "scenario", "scenario", 10],
  ["twin3d", "twin3d", "twin3d", 10],
  ["metrics", "metrics", "metrics", 11],
  ["audit", "audit", "audit", 9],
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
        <Route path="about" element={<About />} />
        <Route path="incidents" element={<Incidents />} />
        <Route path="fast-verify" element={<FastVerify />} />
        <Route path="resources" element={<Resources />} />
        <Route path="shelters" element={<Shelters />} />
        {PLANNED.map(([path, nav, page, phase]) => (
          <Route key={path} path={path} element={<Planned navKey={nav} pageKey={page} phase={phase} />} />
        ))}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
