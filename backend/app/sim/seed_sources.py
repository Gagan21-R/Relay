"""Map the scenario's source keys (ksdma, ndrf2, vol_ravi, ...) to database ids."""
from sqlalchemy.orm import Session

from app.core import state


def source_key_map(db: Session) -> dict[str, int]:
    """Stored by load_world for whichever world is loaded."""
    return dict(state.get(db, "source_keys", {}) or {})
