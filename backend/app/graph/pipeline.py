"""The LangGraph state graph. One node per agent; edges and conditional routing are explicit; the shared state is
PostgreSQL (the graph state only carries ids and decisions). The database session travels in the run config.

    report_received:  intake ─┬─(blocked by network)──────────────────────────────► END
                              └► trust ► triage ► resource ► blackout ► monitor ─┬─(triggers)► coordination ► END
                                                                      └──────────────────────────► END
    tick / event:     resource ► blackout ► monitor ► (coordination) ► END       (time passing, signals, what-if events)
"""
from typing import Any, TypedDict

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, StateGraph
from sqlalchemy.orm import Session

from app.agents import blackout, coordination, intake, monitor, resource, triage, trust
from app.api.common import row
from app.models import Report, Zone
from app.ws.manager import emit

AGENTS = ["intake", "trust", "triage", "resource", "blackout", "monitor", "coordination"]
FROM_INSIDE_ZONE = {"web", "social_feed", "field_app"}      # channels that need the zone's own internet


class RelayState(TypedDict, total=False):
    event: str
    report_ids: list[int]
    incident_ids: list[int]
    blocked: bool
    triggers: list[dict]
    plan_id: int | None
    alerts: list[dict]
    trace: list[dict]


def _db(config: RunnableConfig) -> Session:
    return config["configurable"]["db"]


def _trace(st: RelayState, agent: str, summary: str, **out) -> list[dict]:
    return [*st.get("trace", []), {"agent": agent, "summary": summary, **out}]


def n_intake(st: RelayState, config: RunnableConfig) -> dict[str, Any]:
    db = _db(config)
    blocked = False
    for rid in st.get("report_ids", []):
        r = db.get(Report, rid)
        intake.process(db, r)
        z = db.get(Zone, r.zone_id) if r.zone_id else None
        if z and z.internet_down and r.channel in FROM_INSIDE_ZONE:
            r.status, blocked = "blocked", True
        elif r.status != "clarifying":
            r.status = "processed"
        db.flush()
        emit("report", row(r))
        if r.status == "blocked":
            emit("network", {"zone": z.code, "name": z.name, "internet_down": True, "blocked_report": r.ref, "channel": r.channel})
    return {"blocked": blocked, "trace": _trace(st, "intake", f"{len(st.get('report_ids', []))} report(s) extracted", blocked=blocked)}


def _agent_node(name: str, mod):
    def node(st: RelayState, config: RunnableConfig) -> dict[str, Any]:
        out = dict(mod.run(_db(config), dict(st)) or {})
        summary = out.pop("summary", "done")
        return {**out, "trace": _trace(st, name, summary)}
    return node


def build_graph():
    g = StateGraph(RelayState)
    g.add_node("intake", n_intake)
    g.add_node("trust", _agent_node("trust", trust))
    g.add_node("triage", _agent_node("triage", triage))
    g.add_node("resource", _agent_node("resource", resource))
    g.add_node("blackout", _agent_node("blackout", blackout))
    g.add_node("monitor", _agent_node("monitor", monitor))
    g.add_node("coordination", _agent_node("coordination", coordination))
    g.set_conditional_entry_point(
        lambda st: "intake" if st.get("report_ids") else "triage" if st.get("incident_ids") else "resource",
        {"intake": "intake", "triage": "triage", "resource": "resource"})
    g.add_conditional_edges("intake", lambda st: END if st.get("blocked") else "trust", {END: END, "trust": "trust"})
    g.add_edge("trust", "triage")
    g.add_edge("triage", "resource")
    g.add_edge("resource", "blackout")
    g.add_edge("blackout", "monitor")
    g.add_conditional_edges("monitor", lambda st: "coordination" if st.get("triggers") else END,
                            {"coordination": "coordination", END: END})
    g.add_edge("coordination", END)
    return g.compile()


GRAPH = build_graph()


def run(db: Session, event: str, **kw) -> RelayState:
    return GRAPH.invoke({"event": event, "trace": [], **kw}, config={"configurable": {"db": db}})
