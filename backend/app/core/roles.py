"""Who is acting. Prototype only: the role and actor arrive as X-Role / X-Actor headers (the dashboard's role
switcher); there is no login. The backend enforces every lifecycle permission from them:
  duty_officer — approves plans, assigns, verifies routes, dispatches, marks delivered, confirms, sends public messages
  volunteer    — may dispatch / mark delivered ONLY the tasks assigned to them (actor = their volunteer code, e.g. V-001)
  viewer       — read-only
Missing headers default to duty_officer so scripts and the existing API keep working; the UI always sends them."""
from dataclasses import dataclass

from fastapi import Header, HTTPException

ROLES = ("duty_officer", "volunteer", "viewer")


@dataclass
class Actor:
    role: str
    name: str

    @property
    def is_officer(self) -> bool:
        return self.role == "duty_officer"


def current_actor(x_role: str | None = Header(None), x_actor: str | None = Header(None)) -> Actor:
    role = (x_role or "duty_officer").strip().lower()
    if role not in ROLES:
        raise HTTPException(403, f"unknown role '{role}'")
    return Actor(role, (x_actor or ("Duty Officer" if role == "duty_officer" else role)).strip())


def require_officer(a: Actor, action: str) -> None:
    if not a.is_officer:
        raise HTTPException(403, f"only a Duty Officer can {action} (you are acting as {a.role} {a.name})")
