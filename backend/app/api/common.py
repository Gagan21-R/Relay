"""Shared API helpers: row serialisation and lookups that 404 cleanly."""
from datetime import datetime
from typing import Any

from fastapi import HTTPException
from sqlalchemy import inspect
from sqlalchemy.orm import Session


def row(obj: Any, exclude: set[str] | None = None) -> dict:
    """Serialise a SQLAlchemy row (columns only). Phone hashes never leave the server."""
    if obj is None:
        return {}
    out = {}
    for c in inspect(obj).mapper.column_attrs:
        k = c.key
        if k in (exclude or set()) or k.endswith("phone_hash"):
            continue
        v = getattr(obj, k)
        out[k] = v.isoformat() if isinstance(v, datetime) else v
    return out


def rows(objs, exclude: set[str] | None = None) -> list[dict]:
    return [row(o, exclude) for o in objs]


def get_or_404(db: Session, model, id_: int):
    obj = db.get(model, id_)
    if obj is None:
        raise HTTPException(404, f"{model.__name__} {id_} not found")
    return obj
