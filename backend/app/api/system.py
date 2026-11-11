"""Health, configuration and language endpoints."""
from fastapi import APIRouter

from app.channels.sms import get_sms_provider
from app.core.config import get_settings
from app.db import db_ok
from app.graph.pipeline import AGENTS
from app.i18n.languages import LANGUAGES
from app.services.llm import get_embedder, get_llm
from app.ws.manager import hub

router = APIRouter(prefix="/api", tags=["system"])


@router.get("/health")
def health():
    s = get_settings()
    return {
        "status": "ok" if db_ok() else "degraded",
        "database": "postgresql" if not s.is_sqlite else "sqlite (local fallback)",
        "database_ok": db_ok(),
        "mock_mode": s.mock,
        "llm": get_llm().name,
        "embeddings": get_embedder().name,
        "sms_provider": get_sms_provider().name,
        "ws_clients": hub.clients,
        "agents": AGENTS,
    }


@router.get("/languages")
def languages():
    return {"languages": [{"code": k, **v} for k, v in LANGUAGES.items()]}
