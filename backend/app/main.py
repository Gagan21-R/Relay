"""RELAY backend: FastAPI app, routers and the /ws/live WebSocket."""
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import assistant, incidents, intake, metrics, plans, resources, signals, sim, system, world
from app.channels import voice
from app.core.config import get_settings
from app.sim.seed import seed
from app.ws.manager import bind_loop, hub


@asynccontextmanager
async def lifespan(_: FastAPI):
    bind_loop(asyncio.get_running_loop())
    # Auto-seed on first start (no-op when data exists). On PostgreSQL, Alembic has already created the schema.
    if get_settings().auto_seed:
        await asyncio.to_thread(seed)
    task = asyncio.create_task(sim.clock_loop())
    yield
    task.cancel()


app = FastAPI(title="RELAY API", version="0.2.0", lifespan=lifespan,
              description="Resilient Emergency Logistics & Adaptive Yield: multi-agent disaster response coordination.")
app.add_middleware(CORSMiddleware, allow_origins=get_settings().cors_list, allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])
app.include_router(system.router)
app.include_router(world.router)
app.include_router(intake.router)
app.include_router(sim.router)
app.include_router(incidents.router)
app.include_router(resources.router)
app.include_router(plans.router)
app.include_router(signals.router)
app.include_router(assistant.router)
app.include_router(metrics.router)
voice.MEDIA_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=voice.MEDIA_DIR), name="media")


@app.websocket("/ws/live")
async def live(ws: WebSocket):
    await hub.connect(ws)
    try:
        while True:
            msg = await ws.receive_text()
            if msg == "ping":
                await ws.send_text('{"type":"pong"}')
    except WebSocketDisconnect:
        await hub.disconnect(ws)
