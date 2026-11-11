"""Explain-me assistant endpoints (read-only)."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db import get_db
from app.services import assistant

router = APIRouter(prefix="/api/assistant", tags=["assistant"])


class Ask(BaseModel):
    section: str = "map.page"
    question: str | None = Field(None, max_length=500)
    lang: str = "en"
    context: dict | None = None


@router.post("")
def ask(body: Ask, db: Session = Depends(get_db)):
    return assistant.explain(db, body.section, body.question, body.lang, body.context)


@router.get("/sections")
def sections():
    return [{"id": k, "title": v["title"]} for k, v in assistant.S.items()]
