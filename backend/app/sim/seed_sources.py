"""Map the scenario's source keys (ksdma, ndrf2, vol_ravi, ...) to database ids."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Source
from app.sim.kodagu_world import SOURCES

_BY_NAME = {name: key for key, _, name, _, _ in SOURCES}


def source_key_map(db: Session) -> dict[str, int]:
    return {_BY_NAME[s.name]: s.id for s in db.scalars(select(Source).where(Source.name.in_(list(_BY_NAME))))}
