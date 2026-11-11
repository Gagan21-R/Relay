"""SQLAlchemy models. Importing this package registers every table on Base.metadata."""
from app.models.tables import (  # noqa: F401
    Alert, Approval, AuditLog, Depot, Dispatch, Gazetteer, Incident, InventoryItem, Plan, ReconTask, Report, Road,
    Shelter, Signal, SimState, SmsMessage, Source, Zone,
)
from app.models.ops import AgentMessage, Communication, Hospital, Precedent, RoadReport, Volunteer  # noqa: F401,E402
