"""Agent message bus — how RELAY's agents talk to each other.

Agents do not only pass a shared state down the graph; they also send each other messages and act on the replies:
  inform    — "here is what I found, it is yours now"          (hand-offs: intake → trust → triage)
  request   — "I need something only you can work out"         (coordination → resource: "I am short of boats")
  propose   — "here is what I can offer"                       (resource → coordination: "Depot B has 6 boats")
  accept / decline — the asker decides on the offer            (coordination → resource)
  escalate  — "nobody here can solve it; a person must"        (resource → duty officer)
`ask()` delivers a request synchronously to the recipient's handler and returns its replies, so a conversation runs
inside one agent turn and is fully deterministic. Every message is stored (agent_messages), pushed over the WebSocket
and shown on the Agent conversations page. The LLM is not involved: messages carry facts and numbers, not prompts."""
import importlib

from sqlalchemy.orm import Session

from app.core import state
from app.models import AgentMessage
from app.ws.manager import emit

AGENTS = ("intake", "trust", "triage", "resource", "blackout", "monitor", "coordination", "duty_officer")
_HANDLERS = {"resource": "app.agents.resource", "coordination": "app.agents.coordination", "trust": "app.agents.trust"}


def _row(m: AgentMessage) -> dict:
    return {"id": m.id, "conversation": m.conversation, "sender": m.sender, "recipient": m.recipient, "performative": m.performative,
            "topic": m.topic, "summary": m.summary, "content": m.content, "in_reply_to": m.in_reply_to, "sim_time": m.sim_time}


def send(db: Session, sender: str, recipient: str, performative: str, topic: str, summary: str, content: dict | None = None,
         conversation: str | None = None, reply_to: int | None = None) -> AgentMessage:
    m = AgentMessage(conversation=conversation or f"{topic}:{state.now(db):.2f}:{sender}", sender=sender, recipient=recipient,
                     performative=performative, topic=topic, summary=summary, content=content or {}, in_reply_to=reply_to,
                     sim_time=state.now(db))
    db.add(m)
    db.flush()
    emit("agent_message", _row(m))
    return m


def ask(db: Session, sender: str, recipient: str, topic: str, summary: str, content: dict | None = None,
        conversation: str | None = None) -> list[AgentMessage]:
    """Send a request and let the recipient answer now. Returns the reply messages (propose / reply / decline / escalate)."""
    q = send(db, sender, recipient, "request", topic, summary, content, conversation)
    mod = importlib.import_module(_HANDLERS[recipient])
    replies = []
    for performative, rtopic, rsummary, rcontent in mod.handle(db, q) or []:
        to = rcontent.pop("_to", sender) if isinstance(rcontent, dict) else sender
        replies.append(send(db, recipient, to, performative, rtopic, rsummary, rcontent, q.conversation, q.id))
    return replies


def reply(db: Session, to: AgentMessage, performative: str, summary: str, content: dict | None = None) -> AgentMessage:
    return send(db, to.recipient, to.sender, performative, to.topic, summary, content, to.conversation, to.id)


def already(db: Session, conversation: str) -> bool:
    from sqlalchemy import select
    return db.scalar(select(AgentMessage.id).where(AgentMessage.conversation == conversation).limit(1)) is not None
