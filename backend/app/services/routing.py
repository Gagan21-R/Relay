"""Road routing between zones (Dijkstra over OPEN roads, haversine lengths). Flooded or blocked roads are never used."""
import heapq

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import geo
from app.models import Road, Shelter, Zone

SPEED_KMH = 25.0          # loaded relief truck on wet ghat roads
LAST_MILE_H = 0.3         # loading and the last stretch inside the zone


def _graph(db: Session) -> tuple[dict, dict]:
    zones = {z.code: z for z in db.scalars(select(Zone))}
    adj: dict[str, list] = {c: [] for c in zones}
    for r in db.scalars(select(Road)):
        if r.status != "open":
            continue
        km = sum(geo.haversine_m(*a, *b) for a, b in zip(r.points, r.points[1:])) / 1000
        adj[r.a].append((r.b, km, r))
        adj[r.b].append((r.a, km, r))
    return zones, adj


def route(db: Session, from_zone: str, to_zone: str) -> dict | None:
    """Shortest open route. Returns {zones, roads, km, eta_h, points} or None when cut off."""
    zones, adj = _graph(db)
    if from_zone not in zones or to_zone not in zones:
        return None
    if from_zone == to_zone:
        z = zones[from_zone]
        return {"zones": [from_zone], "roads": [], "km": 0.0, "eta_h": LAST_MILE_H, "points": [[z.lat, z.lng]]}
    dist, prev, seen = {from_zone: 0.0}, {}, set()
    pq = [(0.0, from_zone)]
    while pq:
        d, u = heapq.heappop(pq)
        if u in seen:
            continue
        seen.add(u)
        if u == to_zone:
            break
        for v, km, r in adj[u]:
            nd = d + km
            if nd < dist.get(v, 1e18):
                dist[v], prev[v] = nd, (u, r)
                heapq.heappush(pq, (nd, v))
    if to_zone not in dist:
        return None
    path, roads, cur = [to_zone], [], to_zone
    while cur != from_zone:
        u, r = prev[cur]
        roads.append(r.code)
        path.append(u)
        cur = u
    path.reverse()
    roads.reverse()
    km = round(dist[to_zone], 1)
    return {"zones": path, "roads": roads, "km": km, "eta_h": round(km / SPEED_KMH + LAST_MILE_H, 2),
            "points": [[zones[c].lat, zones[c].lng] for c in path]}


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
