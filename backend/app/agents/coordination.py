"""Coordination agent — implemented in a later phase. run() returns its contribution to the shared graph state."""
from sqlalchemy.orm import Session


def run(db: Session, st: dict) -> dict:
    return {}


def handle_confirmation_reply(db: Session, phone_hash: str, body: str) -> dict | None:
    """Phase 7 fills this in (YES/NO delivery confirmation)."""
    return None
