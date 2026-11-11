"""Simulation controls: scenarios, clock, network, what-if events, the 12-step Run Demo, phone simulator samples."""
import asyncio

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import state
from app.db import SessionLocal, get_db
from app.models import Zone
from app.sim import demo, engine
from app.sim.samples import PHONES, SAMPLES
from app.sim.scenarios import SCENARIOS
from app.ws.manager import emit

router = APIRouter(prefix="/api/sim", tags=["simulation"])


class NetworkChange(BaseModel):
    zone_code: str
    internet_down: bool


@router.post("/network")
def network(body: NetworkChange, db: Session = Depends(get_db)):
    """Internet DOWN in a zone: web, social and field-app reports from inside it stop; SMS, voice and radio continue."""
    z = db.scalar(select(Zone).where(Zone.code == body.zone_code))
    if not z:
        raise HTTPException(404, f"zone {body.zone_code} not found")
    z.internet_down = body.internet_down
    state.audit(db, "Simulation", "network_changed", f"Internet {'DOWN' if body.internet_down else 'restored'} in {z.name}",
                actor_type="system", object_type="zone", object_id=z.id)
    db.commit()
    emit("network", {"zone": z.code, "name": z.name, "internet_down": z.internet_down})
    return {"zone": z.code, "internet_down": z.internet_down}


@router.get("/samples")
def samples():
    return {"messages": SAMPLES, "phones": PHONES}


@router.get("/scenarios")
def scenarios(db: Session = Depends(get_db)):
    cur = state.get(db, "scenario", {}) or {}
    return {"active": cur, "clock": state.now(db), "timeline": engine.timeline_info(db),
            "scenarios": [{"id": k, "name": v["name"], "hazard": v["hazard"], "colour": v["colour"], "description": v["description"]} for k, v in SCENARIOS.items()]}


class Start(BaseModel):
    scenario: str = "kodagu_flood"
    replay_until: float = Field(0.0, ge=0, le=48)
    speed: float = Field(0.0, ge=0, le=2)      # simulated hours per real second (0 = paused)


@router.post("/scenario/start")
def start(body: Start, db: Session = Depends(get_db)):
    try:
        out = engine.start_scenario(db, body.scenario, body.replay_until, body.speed, fresh=True)
    except ValueError as e:
        raise HTTPException(404, str(e)) from e
    db.commit()
    return out


class ClockCmd(BaseModel):
    action: str = Field(pattern="^(play|pause|step|speed)$")
    hours: float = Field(0.5, gt=0, le=12)
    speed: float = Field(0.05, ge=0, le=2)


@router.post("/clock")
def clock(body: ClockCmd, db: Session = Depends(get_db)):
    sc = state.get(db, "scenario", {}) or {}
    if body.action == "step":
        engine.advance_to(db, state.now(db) + body.hours)
    else:
        sc = {**sc, "running": body.action != "pause", "speed": body.speed if body.action != "pause" else sc.get("speed", body.speed)}
        state.put(db, "scenario", sc)
    db.commit()
    emit("sim", {"clock": state.now(db), "scenario": state.get(db, "scenario")})
    return {"clock": state.now(db), "scenario": state.get(db, "scenario")}


class Event(BaseModel):
    type: str
    params: dict = {}


@router.post("/event")
def event(body: Event, db: Session = Depends(get_db)):
    """What-if: close_road, reopen_road, flood_shelter, drop_inventory, cut_internet, restore_internet, spike_reports, silence_village."""
    try:
        changes = engine.what_if(db, body.type, body.params)
    except (ValueError, KeyError) as e:
        raise HTTPException(422, f"bad event: {e}") from e
    db.commit()
    return {"changes": changes, "clock": state.now(db)}


@router.get("/demo")
def demo_steps():
    return demo.info()


class DemoStep(BaseModel):
    who: str = "Duty officer"


@router.post("/demo/step/{n}")
def demo_step(n: int, body: DemoStep, db: Session = Depends(get_db)):
    if not 1 <= n <= len(demo.STEPS):
        raise HTTPException(404, "steps are 1-12")
    out = demo.run_step(db, n, body.who)
    db.commit()
    emit("demo", out)
    return out


async def clock_loop() -> None:
    """Background clock: when the scenario is playing, advance simulated time by speed × elapsed real seconds."""
    while True:
        await asyncio.sleep(1.0)
        try:
            await asyncio.to_thread(_tick_once)
        except Exception:  # noqa: BLE001 - the clock must never die
            pass


def _tick_once() -> None:
    with SessionLocal() as db:
        sc = state.get(db, "scenario", {}) or {}
        if sc.get("running") and sc.get("speed", 0) > 0:
            engine.advance_to(db, state.now(db) + sc["speed"])
            db.commit()
