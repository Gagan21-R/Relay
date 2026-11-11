"""RELAY backend: FastAPI app, routers and the /ws/live WebSocket."""
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.api import system
from app.core.config import get_settings
from app.db import Base, engine
from app.ws.manager import hub


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Alembic owns the schema on PostgreSQL; the local SQLite fallback creates tables directly.
    if get_settings().is_sqlite:
        Base.metadata.create_all(engine)
    yield


app = FastAPI(title="RELAY API", version="0.1.0", lifespan=lifespan,
              description="Resilient Emergency Logistics & Adaptive Yield: multi-agent disaster response coordination.")
app.add_middleware(CORSMiddleware, allow_origins=get_settings().cors_list, allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])
app.include_router(system.router)


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
