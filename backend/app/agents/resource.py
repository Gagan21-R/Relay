"""Resource agent — implemented in a later phase. run() returns its contribution to the shared graph state."""
from sqlalchemy.orm import Session


def run(db: Session, st: dict) -> dict:
    return {}
