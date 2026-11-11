// 3D digital twin of the ACTIVE scenario, built from live state (not a static model): terrain seeded by the scenario,
// water or landslide debris from the hazard polygons, villages sized by population (dark in silent zones, with a red
// beacon), shelters coloured by status, depots, incident pins by priority and trucks moving along their routes.
import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { CSS2DObject, CSS2DRenderer } from "three/examples/jsm/renderers/CSS2DRenderer.js";
import { PageHeader } from "../components/Layout";
import { useApi } from "../hooks/useApi";

// The view is re-centred on every scenario: centre and scale come from the scenario's world (Scenario Lab worlds span
// a few km in a city to ~150 km in a desert), the river is the Cauvery for Kodagu and, for water-related disasters
// elsewhere, a schematic channel through the affected places (labelled schematic in the legend).
let K = 100; // world units per degree
let C = { lat: 12.40, lng: 75.76 };
const xz = (lat: number, lng: number) => new THREE.Vector3((lng - C.lng) * K, 0, -(lat - C.lat) * K);
const KODAGU_RIVER = [[12.387, 75.50], [12.387, 75.532], [12.34, 75.62], [12.305, 75.701], [12.33, 75.80], [12.354, 75.884], [12.41, 75.93], [12.458, 75.959], [12.50, 76.02]];
let RIVER: number[][] = KODAGU_RIVER;
function setView(sc: any, zones: any[] | null) {
  const world = sc?.world ?? "kodagu";
  if (world === "kodagu" || !sc?.center) { C = { lat: 12.40, lng: 75.76 }; K = 100; RIVER = KODAGU_RIVER; return; }
  C = { lat: sc.center[0], lng: sc.center[1] };
  K = 100 * Math.pow(2, (sc.zoom ?? 10) - 10);
  const wet = ["flood", "cyclone", "tsunami"].includes(sc.disaster);
  RIVER = wet && zones?.length ? [...zones].sort((a, b) => a.lng - b.lng).map((z) => [z.lat - 0.004, z.lng]) : [];
}
const SCOL: Record<string, number> = { open: 0x14c48a, full: 0xf5b800, inaccessible: 0xe11d48, unconfirmed: 0xff8a3d, closed: 0x150a2e };
const PCOL = (s: number) => (s >= 70 ? 0xe11d48 : s >= 50 ? 0xf97316 : s >= 30 ? 0xeab308 : 0x3b82f6);

function rng(seed: number) { let s = seed; return () => ((s = (s * 1664525 + 1013904223) % 4294967296) / 4294967296); }
function hash(str: string) { let h = 7; for (const c of str) h = (h * 31 + c.charCodeAt(0)) >>> 0; return h; }
function distToRiver(x: number, z: number) {
  let best = 1e9;
  for (let i = 1; i < RIVER.length; i++) {
    const a = xz(RIVER[i - 1][0], RIVER[i - 1][1]), b = xz(RIVER[i][0], RIVER[i][1]);
    if (a.distanceTo(b) < 1e-6) continue;
    const dx = b.x - a.x, dz = b.z - a.z, t = Math.max(0, Math.min(1, ((x - a.x) * dx + (z - a.z) * dz) / (dx * dx + dz * dz)));
    best = Math.min(best, Math.hypot(x - (a.x + t * dx), z - (a.z + t * dz)));
  }
  return best;
}

export default function Twin3D() {
  const { t } = useTranslation();
  const host = useRef<HTMLDivElement>(null);
  const sim = useApi<any>("/api/sim/scenarios", ["sim", "refresh"], 400);
  const state = useApi<any>("/api/state", ["sim", "signal", "refresh"], 400);
  const zones = useApi<any[]>("/api/zones/blackout", ["zone", "signal", "recon", "refresh"], 800);
  const shelters = useApi<any[]>("/api/shelters", ["shelter", "refresh"], 600);
  const depots = useApi<any[]>("/api/depots", ["refresh"], 1000);
  const incidents = useApi<any[]>("/api/incidents", ["incident", "refresh"], 600);
  const dispatches = useApi<any[]>("/api/dispatches", ["dispatch", "refresh"], 400);
  const three = useRef<{ scene: THREE.Scene; dyn: THREE.Group; terrain: THREE.Group; trucks: { obj: THREE.Object3D; route: THREE.Vector3[]; d: any }[]; key: string; heightAt: (x: number, z: number) => number } | null>(null);
  const [info, setInfo] = useState("");
  const scenarioId: string = state.data?.scenario?.id ?? sim.data?.active?.id ?? "kodagu_flood";
  const hazardKind: string = state.data?.scenario?.disaster ?? sim.data?.active?.hazard ?? "flood";
  setView(state.data?.scenario, zones.data);

  // renderer, camera, controls, loop: once
  useEffect(() => {
    const el = host.current!;
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setPixelRatio(Math.min(2, window.devicePixelRatio));
    renderer.setSize(el.clientWidth, el.clientHeight);
    renderer.shadowMap.enabled = true;
    el.appendChild(renderer.domElement);
    const labels = new CSS2DRenderer();
    labels.setSize(el.clientWidth, el.clientHeight);
    Object.assign(labels.domElement.style, { position: "absolute", top: "0", pointerEvents: "none" });
    el.appendChild(labels.domElement);
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xfff2df);
    scene.fog = new THREE.Fog(0xfff2df, 60, 140);
    const camera = new THREE.PerspectiveCamera(45, el.clientWidth / el.clientHeight, 0.1, 500);
    camera.position.set(-10, 42, 48);
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.maxPolarAngle = Math.PI * 0.47;
    controls.target.set(2, 0, 0);
    scene.add(new THREE.HemisphereLight(0xffffff, 0x8a6a4a, 1.1));
    const sun = new THREE.DirectionalLight(0xffffff, 1.6);
    sun.position.set(-30, 60, 20);
    sun.castShadow = true;
    scene.add(sun);
    const terrain = new THREE.Group(), dyn = new THREE.Group();
    scene.add(terrain, dyn);
    three.current = { scene, dyn, terrain, trucks: [], key: "", heightAt: () => 0 };
    let raf = 0;
    const clock = new THREE.Clock();
    const loop = () => {
      const tt = clock.getElapsedTime();
      controls.update();
      dyn.traverse((o: any) => {
        if (o.userData.water) o.position.y = o.userData.baseY + Math.sin(tt * 1.4 + o.userData.phase) * 0.08;
        if (o.userData.beacon) { (o.material as THREE.MeshBasicMaterial).opacity = 0.35 + 0.35 * Math.sin(tt * 3); }
        if (o.userData.pin) o.position.y = o.userData.baseY + Math.sin(tt * 2 + o.userData.phase) * 0.25;
      });
      for (const tr of three.current?.trucks ?? []) {
        const d = tr.d; const now = (window as any).__relayClock ?? 0;
        const f = Math.max(0, Math.min(1, (now - (d.dispatched_at ?? now)) / Math.max(0.01, (d.eta ?? now) - (d.dispatched_at ?? now))));
        const wobble = (Math.sin(tt * 0.6 + d.id) + 1) * 0.02;
        const g = Math.min(1, d.status === "delivered" ? 1 : f + wobble);
        const total = tr.route.length - 1;
        const seg = Math.min(total - 1, Math.floor(g * total));
        const local = g * total - seg;
        if (total >= 1) {
          const p = tr.route[seg].clone().lerp(tr.route[seg + 1], local);
          tr.obj.position.set(p.x, (three.current?.heightAt(p.x, p.z) ?? 0) + 0.7, p.z);
          tr.obj.lookAt(tr.route[seg + 1].x, tr.obj.position.y, tr.route[seg + 1].z);
        }
      }
      renderer.render(scene, camera);
      labels.render(scene, camera);
      raf = requestAnimationFrame(loop);
    };
    loop();
    const ro = new ResizeObserver(() => { renderer.setSize(el.clientWidth, el.clientHeight); labels.setSize(el.clientWidth, el.clientHeight); camera.aspect = el.clientWidth / el.clientHeight; camera.updateProjectionMatrix(); });
    ro.observe(el);
    return () => { cancelAnimationFrame(raf); ro.disconnect(); controls.dispose(); renderer.dispose(); el.innerHTML = ""; three.current = null; };
  }, []);

  // terrain: rebuilt per scenario (different seed, hillier for landslides)
  useEffect(() => {
    const T = three.current;
    const key = `${scenarioId}:${(zones.data ?? []).map((z) => z.code).join(",")}`;
    if (!T || T.key === key) return;
    T.key = key;
    T.terrain.clear();
    const r = rng(hash(scenarioId));
    const bumps = Array.from({ length: 26 }, () => ({ x: (r() - 0.5) * 56, z: (r() - 0.5) * 46, h: 1.5 + r() * (hazardKind === "landslide" ? 6 : 3.5), s: 4 + r() * 6 }));
    const heightAt = (x: number, z: number) => {
      let h = 1.2 + 0.6 * Math.sin(x * 0.15 + hash(scenarioId) % 7) * Math.cos(z * 0.13);
      for (const b of bumps) h += b.h * Math.exp(-((x - b.x) ** 2 + (z - b.z) ** 2) / (2 * b.s * b.s));
      const d = distToRiver(x, z);
      if (d < 3) h -= (3 - d) * 0.9;
      return Math.max(-0.4, h);
    };
    T.heightAt = heightAt;
    const geo = new THREE.PlaneGeometry(64, 54, 128, 108);
    geo.rotateX(-Math.PI / 2);
    const pos = geo.attributes.position as THREE.BufferAttribute;
    const colors: number[] = [];
    const cLow = new THREE.Color(hazardKind === "landslide" ? 0x9a7b4f : 0x8fbf6a), cHigh = new THREE.Color(hazardKind === "landslide" ? 0x5e7a3a : 0x2f6e3a);
    for (let i = 0; i < pos.count; i++) {
      const h = heightAt(pos.getX(i), pos.getZ(i));
      pos.setY(i, h);
      const c = cLow.clone().lerp(cHigh, Math.min(1, h / 6));
      colors.push(c.r, c.g, c.b);
    }
    geo.setAttribute("color", new THREE.Float32BufferAttribute(colors, 3));
    geo.computeVertexNormals();
    const mesh = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ vertexColors: true, flatShading: true, roughness: 0.95 }));
    mesh.receiveShadow = true;
    T.terrain.add(mesh);
    if (RIVER.length >= 2) {
      const river = new THREE.CatmullRomCurve3(RIVER.map(([a, b]) => { const v = xz(a, b); v.y = heightAt(v.x, v.z) + 0.15; return v; }));
      T.terrain.add(new THREE.Mesh(new THREE.TubeGeometry(river, 120, 0.45, 6), new THREE.MeshStandardMaterial({ color: 0x3d7bff, emissive: 0x1e3a8a, emissiveIntensity: 0.3 })));
    }
    const base = new THREE.Mesh(new THREE.BoxGeometry(64, 2, 54), new THREE.MeshStandardMaterial({ color: 0x150a2e }));
    base.position.y = -1.4;
    T.terrain.add(base);
  }, [scenarioId, hazardKind, sim.data, zones.data]);

  // dynamic layer: rebuilt whenever the live state changes
  useEffect(() => {
    const T = three.current;
    if (!T || !zones.data) return;
    (window as any).__relayClock = state.data?.clock ?? 0;
    T.dyn.traverse((o: any) => { if (o.isCSS2DObject) o.element.remove(); });
    T.dyn.clear();
    T.trucks = [];
    const H = T.heightAt;
    const label = (text: string, cls: string) => { const d = document.createElement("div"); d.className = cls; d.textContent = text; return new CSS2DObject(d); };
    // hazard polygons: water (flood) or debris (landslide)
    (state.data?.flood_extent ?? []).forEach((poly: number[][], i: number) => {
      const shape = new THREE.Shape(poly.map(([la, ln]) => { const v = xz(la, ln); return new THREE.Vector2(v.x, -v.z); }));
      const g = new THREE.ShapeGeometry(shape);
      g.rotateX(-Math.PI / 2);
      const cx = poly.reduce((a, p) => a + p[0], 0) / poly.length, cy = poly.reduce((a, p) => a + p[1], 0) / poly.length;
      const c = xz(cx, cy);
      const water = new THREE.Mesh(g, new THREE.MeshStandardMaterial({ color: hazardKind === "landslide" ? 0x7a4a22 : 0x2e5bff, transparent: true, opacity: hazardKind === "landslide" ? 0.85 : 0.55, roughness: 0.2, metalness: 0.1 }));
      const y = Math.max(H(c.x, c.z), 0.4) + 0.5;
      water.position.y = y;
      Object.assign(water.userData, { water: true, baseY: y, phase: i });
      T.dyn.add(water);
    });
    // villages: houses scale with population; silent zones go dark with a red beacon
    for (const z of zones.data) {
      const c = xz(z.lat, z.lng);
      const r = rng(hash(z.code));
      const n = Math.min(140, Math.round(z.population / 160));
      const dark = z.blackout_flag;
      const houses = new THREE.InstancedMesh(new THREE.BoxGeometry(0.45, 0.45, 0.45), new THREE.MeshStandardMaterial({ color: dark ? 0x3a3a46 : 0xfff0d8, emissive: dark ? 0x000000 : 0xffb347, emissiveIntensity: dark ? 0 : 0.35 }), n);
      const m = new THREE.Matrix4();
      for (let k = 0; k < n; k++) {
        const a = r() * Math.PI * 2, d = Math.sqrt(r()) * (1 + z.population / 9000) * 1.6;
        const x = c.x + Math.cos(a) * d, zz = c.z + Math.sin(a) * d;
        m.makeScale(1, 1 + r() * 1.6, 1);
        m.setPosition(x, H(x, zz) + 0.3, zz);
        houses.setMatrixAt(k, m);
      }
      houses.castShadow = true;
      T.dyn.add(houses);
      const l = label(`${z.name}${dark ? " · SILENT" : ""}`, `twin-label${dark ? " twin-silent" : ""}`);
      l.position.set(c.x, H(c.x, c.z) + 3.4, c.z);
      T.dyn.add(l);
      if (dark) {
        const beam = new THREE.Mesh(new THREE.CylinderGeometry(0.5, 1.6, 14, 18, 1, true), new THREE.MeshBasicMaterial({ color: 0xe11d48, transparent: true, opacity: 0.5, side: THREE.DoubleSide }));
        beam.position.set(c.x, H(c.x, c.z) + 7, c.z);
        beam.userData.beacon = true;
        T.dyn.add(beam);
      }
    }
    for (const s of shelters.data ?? []) {
      const c = xz(s.lat, s.lng);
      const box = new THREE.Mesh(new THREE.BoxGeometry(1.4, 1.1, 1.4), new THREE.MeshStandardMaterial({ color: SCOL[s.status] ?? 0xffffff }));
      box.position.set(c.x + 1.2, H(c.x + 1.2, c.z) + 0.7, c.z);
      box.castShadow = true;
      T.dyn.add(box);
      const roof = new THREE.Mesh(new THREE.ConeGeometry(1.1, 0.8, 4), new THREE.MeshStandardMaterial({ color: 0x150a2e }));
      roof.position.set(box.position.x, box.position.y + 0.95, box.position.z);
      roof.rotation.y = Math.PI / 4;
      T.dyn.add(roof);
    }
    for (const d of depots.data ?? []) {
      const c = xz(d.lat, d.lng);
      const dm = new THREE.Mesh(new THREE.OctahedronGeometry(0.9), new THREE.MeshStandardMaterial({ color: 0x9a5cff, emissive: 0x5718b3, emissiveIntensity: 0.4 }));
      dm.position.set(c.x - 1.2, H(c.x - 1.2, c.z) + 1.2, c.z + 0.8);
      T.dyn.add(dm);
    }
    (incidents.data ?? []).filter((i) => i.lat != null && i.confidence_level !== "false" && i.status !== "resolved").forEach((i, n) => {
      const c = xz(i.lat, i.lng);
      const pin = new THREE.Mesh(new THREE.ConeGeometry(0.35, 1.3, 12), new THREE.MeshStandardMaterial({ color: PCOL(i.priority_score), emissive: PCOL(i.priority_score), emissiveIntensity: 0.4 }));
      pin.rotation.x = Math.PI;
      const y = H(c.x, c.z) + 2.2 + (n % 3) * 0.3;
      pin.position.set(c.x + (n % 4) * 0.25, y, c.z - (n % 3) * 0.25);
      Object.assign(pin.userData, { pin: true, baseY: y, phase: n });
      T.dyn.add(pin);
    });
    for (const d of (dispatches.data ?? []).filter((x) => ["dispatched", "delivered"].includes(x.status))) {
      const route = d.route.map(([la, ln]: number[]) => xz(la, ln));
      const line = new THREE.Line(new THREE.BufferGeometry().setFromPoints(route.map((v: THREE.Vector3) => new THREE.Vector3(v.x, H(v.x, v.z) + 0.4, v.z))), new THREE.LineBasicMaterial({ color: 0x7c3aed }));
      T.dyn.add(line);
      const truck = new THREE.Group();
      const body = new THREE.Mesh(new THREE.BoxGeometry(0.9, 0.5, 0.5), new THREE.MeshStandardMaterial({ color: d.overdue ? 0xff2e86 : 0xc8ff2e }));
      const cab = new THREE.Mesh(new THREE.BoxGeometry(0.35, 0.4, 0.5), new THREE.MeshStandardMaterial({ color: 0x150a2e }));
      cab.position.x = 0.6;
      truck.add(body, cab);
      T.dyn.add(truck);
      T.trucks.push({ obj: truck, route, d });
    }
    setInfo(`${zones.data.length} villages · ${(state.data?.flood_extent ?? []).length} hazard areas · ${zones.data.filter((z) => z.blackout_flag).length} silent · ${T.trucks.length} trucks · ${(incidents.data ?? []).filter((i) => i.confidence_level !== "false").length} incidents`);
  }, [zones.data, shelters.data, depots.data, incidents.data, dispatches.data, state.data, hazardKind]);

  return (
    <div className="space-y-4">
      <PageHeader title={t("nav.twin3d")} sub={t("pages.twin3d")} kicker={`${sim.data?.active?.name ?? ""} · T+${(state.data?.clock ?? 0).toFixed(1)} h`} tone="bg-sun-400" section="twin3d.page">
        <span className="badge bg-white">{info}</span>
      </PageHeader>
      <div className="relative h-[72vh] min-h-[460px] overflow-hidden rounded-3xl border-2 border-ink shadow-hard-lg">
        <div ref={host} className="absolute inset-0" />
        <div className="pointer-events-none absolute bottom-3 left-3 rounded-2xl border-2 border-ink bg-white/95 p-2.5 text-[11px] font-bold shadow-hard-sm">
          <p>{hazardKind === "landslide" ? "🟫 landslide debris" : "🟦 flood water"} · 🏠 lit = reporting, dark + red beam = silent · ▣ shelters (green open, red inaccessible) · ◆ depots · ▼ incidents by priority · 🟩 trucks</p>
          <p className="text-ink/50">drag to orbit · scroll to zoom · launch any scenario in the Scenario Lab and the twin re-centres and rebuilds{state.data?.scenario?.world && state.data.scenario.world !== "kodagu" ? " · river channel schematic" : ""}</p>
        </div>
      </div>
    </div>
  );
}
