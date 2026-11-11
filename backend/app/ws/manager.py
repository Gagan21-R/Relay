"""WebSocket hub for /ws/live: every agent and human action is pushed to connected dashboards as a typed event."""
import asyncio
import json
from datetime import datetime, timezone
from typing import Any

from fastapi import WebSocket

EVENT_TYPES = {"hello", "report", "incident", "plan", "dispatch", "alert", "network", "sim", "audit", "sms", "signal",
               "shelter", "inventory", "zone", "recon", "demo", "refresh"}


class LiveHub:
    def __init__(self) -> None:
        self._clients: set[WebSocket] = set()
        self._lock = asyncio.Lock()
        self.sent = 0

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self._clients.add(ws)
        await ws.send_text(json.dumps(self._envelope("hello", {"clients": len(self._clients)})))

    async def disconnect(self, ws: WebSocket) -> None:
        async with self._lock:
            self._clients.discard(ws)

    @property
    def clients(self) -> int:
        return len(self._clients)

    @staticmethod
    def _envelope(kind: str, data: Any) -> dict:
        if kind not in EVENT_TYPES:
            raise ValueError(f"unknown event type {kind}")
        return {"type": kind, "at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "data": data}

    async def broadcast(self, kind: str, data: Any) -> None:
        msg = json.dumps(self._envelope(kind, data), default=str, ensure_ascii=False)
        dead = []
        for ws in list(self._clients):
            try:
                await ws.send_text(msg)
            except Exception:  # noqa: BLE001 - a dropped client is removed, never breaks the broadcast
                dead.append(ws)
        for ws in dead:
            await self.disconnect(ws)
        self.sent += 1


hub = LiveHub()
_loop: asyncio.AbstractEventLoop | None = None
_muted = False


def bind_loop(loop: asyncio.AbstractEventLoop) -> None:
    global _loop
    _loop = loop


def mute(on: bool) -> None:
    """Bulk operations (seeding a whole scenario) mute per-row events and send one summary instead."""
    global _muted
    _muted = on


def emit(kind: str, data: Any) -> None:
    """Push an event from synchronous code (agents run in worker threads). Never raises, never blocks."""
    if _muted or _loop is None or not hub.clients:
        return
    try:
        running = asyncio.get_running_loop()
    except RuntimeError:
        running = None
    try:
        if running is _loop:
            _loop.create_task(hub.broadcast(kind, data))
        else:
            asyncio.run_coroutine_threadsafe(hub.broadcast(kind, data), _loop)
    except Exception:  # noqa: BLE001 - live push is best effort; the database is the source of truth
        pass
