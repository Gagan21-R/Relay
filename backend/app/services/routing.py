"""Disruption-aware routing between zones (Dijkstra over usable roads, haversine lengths).

Rules (deterministic, no LLM):
- Flooded, blocked or damaged roads are never used. An UNVERIFIED report that a road is blocked closes it for planning
  (caution first) and asks a person to verify; an unverified report that a road is OPEN never reopens it.
- A road is usable only by the vehicles it allows (a ferry needs a boat; an unpaved track needs a 4x4 or two-wheeler).
- The recommended route is the SAFEST, not the shortest: unverified or stale road segments cost extra, so a slightly
  longer verified route wins. The shortest route is shown next to it with the reason it was not chosen.
- A route is labelled "verified passable" only when every road on it has a verified observation fresher than
  ROAD_FRESH_H; otherwise "unverified — verify before dispatch". ETAs on unverified routes are marked unreliable.
  Dispatch requires a Duty Officer to verify the route (enforced in the coordination agent)."""
import heapq

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import geo, state
from app.models import Road, RoadReport, Shelter, Zone

SPEED_KMH = {"truck": 25.0, "4x4": 30.0, "ambulance": 35.0, "two_wheeler": 30.0, "boat": 12.0}
KIND_FACTOR = {"road": 1.0, "bridge": 1.0, "causeway": 0.8, "ghat": 0.6, "ferry": 1.25}
SURFACE_FACTOR = {"paved": 1.0, "unpaved": 0.6}
DEFAULT_VEHICLE = "truck"
LAST_MILE_H = 0.3          # loading and the last stretch inside the zone
ROAD_FRESH_H = 6.0         # a verified observation older than this no longer counts as verified
UNVERIFIED_PENALTY = 0.5   # +50% cost per km on unverified / stale segments
OFFICIAL_SOURCES = {"official", "sensor", "field_team", "operator", "seed"}


def road_km(r: Road) -> float:
    return sum(geo.haversine_m(*a, *b) for a, b in zip(r.points, r.points[1:])) / 1000


def road_condition(db: Session, r: Road) -> dict:
    now = state.now(db)
    age = round(max(0.0, now - (r.updated_at or 0.0)), 1)
    last = db.scalars(select(RoadReport).where(RoadReport.road_id == r.id).order_by(RoadReport.reported_at.desc(), RoadReport.id.desc())).first()
    pending = db.scalars(select(RoadReport).where(RoadReport.road_id == r.id, RoadReport.verified.is_(False))).all()
    verified_fresh = r.status_verified and age <= ROAD_FRESH_H
    return {"code": r.code, "name": r.name, "kind": r.kind, "surface": r.surface, "allowed_vehicles": r.allowed_vehicles,
            "status": r.status, "source": r.status_source, "verified": bool(r.status_verified), "age_h": age,
            "fresh_verified": bool(verified_fresh), "unverified_reports": len(pending),
            "last_report": {"status": last.status, "source": last.source, "source_type": last.source_type, "verified": last.verified,
                            "at": last.reported_at} if last else None}


def _usable(r: Road, vehicle: str) -> bool:
    return r.status == "open" and vehicle in (r.allowed_vehicles or [])


def _graph(db: Session, vehicle: str, exclude: set[str]) -> tuple[dict, dict]:
    zones = {z.code: z for z in db.scalars(select(Zone))}
    adj: dict[str, list] = {c: [] for c in zones}
    now = state.now(db)
    for r in db.scalars(select(Road)):
        if r.code in exclude or not _usable(r, vehicle):
            continue
        km = road_km(r)
        fresh = r.status_verified and now - (r.updated_at or 0) <= ROAD_FRESH_H
        cost = km * (1.0 if fresh else 1.0 + UNVERIFIED_PENALTY)
        adj[r.a].append((r.b, km, cost, r))
        adj[r.b].append((r.a, km, cost, r))
    return zones, adj


def _dijkstra(zones, adj, src: str, dst: str, use_cost: bool):
    best, prev, seen = {src: 0.0}, {}, set()
    pq = [(0.0, src)]
    while pq:
        d, u = heapq.heappop(pq)
        if u in seen:
            continue
        seen.add(u)
        if u == dst:
            break
        for v, km, cost, r in adj[u]:
            nd = d + (cost if use_cost else km)
            if nd < best.get(v, 1e18):
                best[v], prev[v] = nd, (u, r)
                heapq.heappush(pq, (nd, v))
    if dst not in best:
        return None
    path, roads, cur = [dst], [], dst
    while cur != src:
        u, r = prev[cur]
        roads.append(r)
        path.append(u)
        cur = u
    return path[::-1], roads[::-1]


def _describe(db: Session, zones: dict, path: list, roads: list, vehicle: str) -> dict:
    km = round(sum(road_km(r) for r in roads), 1)
    hours = sum(road_km(r) / (SPEED_KMH[vehicle] * KIND_FACTOR.get(r.kind, 1) * SURFACE_FACTOR.get(r.surface, 1)) for r in roads)
    cond = [road_condition(db, r) for r in roads]
    unverified = [c for c in cond if not c["fresh_verified"]]
    label = "verified passable" if not unverified else "unverified — verify before dispatch"
    return {"zones": path, "roads": [r.code for r in roads], "road_names": [r.name for r in roads], "km": km,
            "eta_h": round(hours + LAST_MILE_H, 2), "eta_reliable": not unverified, "vehicle": vehicle,
            "points": [[zones[c].lat, zones[c].lng] for c in path], "safety": label, "conditions": cond,
            "unverified_roads": [c["name"] + (f" (last verified {c['age_h']} h ago)" if c["verified"] else " (unverified source)") for c in unverified]}


def route(db: Session, from_zone: str, to_zone: str, vehicle: str | None = None, exclude: set[str] | None = None) -> dict | None:
    """Recommended (safest) route for one vehicle type. Returns None when the destination is cut off for it."""
    vehicle = vehicle or DEFAULT_VEHICLE
    zones, adj = _graph(db, vehicle, set(exclude or ()))
    if from_zone not in zones or to_zone not in zones:
        return None
    if from_zone == to_zone:
        z = zones[from_zone]
        return {"zones": [from_zone], "roads": [], "road_names": [], "km": 0.0, "eta_h": LAST_MILE_H, "eta_reliable": True,
                "vehicle": vehicle, "points": [[z.lat, z.lng]], "safety": "verified passable", "conditions": [], "unverified_roads": []}
    found = _dijkstra(zones, adj, from_zone, to_zone, use_cost=True)
    return _describe(db, zones, *found, vehicle) if found else None


def plan_route(db: Session, from_zone: str, to_zone: str, vehicles: list[str] | None = None) -> dict | None:
    """Recommended route + the shortest route + up to two alternatives, trying the given vehicles in order.
    Each option says why it was or was not recommended."""
    for v in vehicles or [DEFAULT_VEHICLE, "4x4", "boat"]:
        best = route(db, from_zone, to_zone, v)
        if not best:
            continue
        zones, adj = _graph(db, v, set())
        sp = _dijkstra(zones, adj, from_zone, to_zone, use_cost=False)
        shortest = _describe(db, zones, *sp, v) if sp else None
        alts = []
        for code in best["roads"]:
            alt = route(db, from_zone, to_zone, v, exclude={code})
            if alt and alt["roads"] != best["roads"] and all(a["roads"] != alt["roads"] for a in alts):
                alt["why"] = f"avoids {alt_name(db, code)}; {alt['km']} km, {alt['safety']}"
                alts.append(alt)
            if len(alts) == 2:
                break
        if shortest and shortest["roads"] != best["roads"]:
            best["why"] = (f"safest option: {best['km']} km vs {shortest['km']} km shortest — the shortest uses unverified road(s): "
                           + ", ".join(shortest["unverified_roads"]))
        else:
            best["why"] = "shortest route is also the safest available" + ("" if best["eta_reliable"] else " (but not verified)")
        best["shortest"] = None if not shortest or shortest["roads"] == best["roads"] else \
            {k: shortest[k] for k in ("roads", "road_names", "km", "eta_h", "safety", "unverified_roads")}
        best["alternatives"] = [{k: a[k] for k in ("roads", "road_names", "km", "eta_h", "safety", "why", "points")} for a in alts]
        return best
    return None


def alt_name(db: Session, code: str) -> str:
    r = db.scalar(select(Road).where(Road.code == code))
    return r.name if r else code


def report_road(db: Session, road: Road, status: str, source: str, source_type: str, verified: bool | None = None,
                note: str | None = None, verified_by: str | None = None) -> RoadReport:
    """Record an observation and apply it with caution-first rules."""
    verified = (source_type in OFFICIAL_SOURCES) if verified is None else verified
    rr = RoadReport(road_id=road.id, status=status, source=source, source_type=source_type, verified=verified,
                    verified_by=verified_by if verified else None, reported_at=state.now(db), note=note)
    db.add(rr)
    apply_report(db, road, rr)
    db.flush()
    return rr


def apply_report(db: Session, road: Road, rr: RoadReport) -> None:
    now = state.now(db)
    if rr.status != "open":
        # closing is always applied (caution), verified or not
        road.status, road.status_source, road.updated_at, road.status_verified = rr.status, rr.source, now, rr.verified
    elif rr.verified:
        road.status, road.status_source, road.updated_at, road.status_verified = "open", rr.source, now, True
    # an unverified "open" report never reopens or re-verifies a road


def verify_report(db: Session, rr: RoadReport, who: str, confirmed: bool) -> RoadReport:
    road = db.get(Road, rr.road_id)
    if confirmed:
        rr.verified, rr.verified_by = True, who
        apply_report(db, road, rr)
    else:  # the report was wrong: drop it; reopen only if this report was the reason the road is closed
        rr.verified, rr.verified_by, rr.note = False, who, f"rejected by {who}"
        if road.status == rr.status and road.status_source == rr.source and not road.status_verified:
            road.status, road.status_source, road.updated_at, road.status_verified = "open", f"verified open by {who}", state.now(db), True
        db.delete(rr)
    db.flush()
    return rr


def shelter_access(db: Session, s: Shelter) -> dict:
    """A shelter is cut off when every one of its access roads is closed."""
    if not s.access_road_ids:
        return {"accessible": True, "closed_roads": [], "why": "on the town road network"}
    roads = {r.code: r for r in db.scalars(select(Road).where(Road.code.in_(s.access_road_ids)))}
    closed = [c for c in s.access_road_ids if roads.get(c) and roads[c].status != "open"]
    ok = len(closed) < len(s.access_road_ids)
    return {"accessible": ok, "closed_roads": closed,
            "why": "all access roads closed: " + ", ".join(roads[c].name for c in closed) if not ok else
                   (f"{len(closed)} of {len(s.access_road_ids)} access roads closed" if closed else "access roads open")}
