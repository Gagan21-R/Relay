import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import CommandMap from "./pages/CommandMap";
import LiveFeed from "./pages/LiveFeed";
import PhoneSimulator from "./pages/PhoneSimulator";
import FieldApp from "./pages/FieldApp";
import RadioConsole from "./pages/RadioConsole";
import About from "./pages/About";
import Incidents from "./pages/Incidents";
import FastVerify from "./pages/FastVerify";
import Resources from "./pages/Resources";
import Shelters from "./pages/Shelters";
import Plans from "./pages/Plans";
import Dispatch from "./pages/Dispatch";
import Blackout from "./pages/Blackout";
import Alerts from "./pages/Alerts";
import PublicCorrections from "./pages/PublicCorrections";
import Audit from "./pages/Audit";
import ScenarioControl from "./pages/ScenarioControl";
import Twin3D from "./pages/Twin3D";
import Metrics from "./pages/Metrics";


export default function App() {
  return (
    <Routes>
      <Route path="public" element={<PublicCorrections />} />
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
        <Route path="plans" element={<Plans />} />
        <Route path="dispatch" element={<Dispatch />} />
        <Route path="blackout" element={<Blackout />} />
        <Route path="alerts" element={<Alerts />} />
        <Route path="audit" element={<Audit />} />
        <Route path="scenario" element={<ScenarioControl />} />
        <Route path="twin3d" element={<Twin3D />} />
        <Route path="metrics" element={<Metrics />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
