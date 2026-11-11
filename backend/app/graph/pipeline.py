"""The LangGraph state graph. Phase 1 wires the shape: one node per agent, explicit edges, a typed shared state.
Each node is filled in by its phase (intake: 3, trust: 5, triage/resource: 6, coordination: 7, monitor/blackout: 8)."""
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

AGENTS = ["intake", "trust", "triage", "resource", "coordination", "monitor"]


class RelayState(TypedDict, total=False):
    event: str                 # what started this run: report_received, scenario_event, delivery_update, tick
    report_ids: list[int]
    incident_ids: list[int]
    plan_id: int | None
    alerts: list[dict]
    trace: list[dict]          # one entry per node: agent, summary, inputs, outputs (mirrored to audit_log)


def _stub(name: str):
    def node(state: RelayState) -> dict[str, Any]:
        return {"trace": [*state.get("trace", []), {"agent": name, "summary": "not implemented yet (scaffold)"}]}
    return node


def build_graph():
    g = StateGraph(RelayState)
    for a in AGENTS:
        g.add_node(a, _stub(a))
    g.set_entry_point("intake")
    for a, b in zip(AGENTS, AGENTS[1:]):
        g.add_edge(a, b)
    g.add_edge(AGENTS[-1], END)
    return g.compile()


GRAPH = build_graph()


def run(event: str, **kw) -> RelayState:
    return GRAPH.invoke({"event": event, "trace": [], **kw})
