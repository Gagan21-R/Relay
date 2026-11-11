"""SMS provider interface. The built-in mock records outgoing messages (the Phone Simulator reads them); real
providers (Twilio, Exotel, MSG91) implement the same `send`. Inbound webhooks are parsed by `parse_inbound`."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol

from app.core.config import get_settings


@dataclass
class OutboundSms:
    to: str
    body: str
    provider: str
    ref: str
    sent_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds"))


class SmsProvider(Protocol):
    name: str

    def send(self, to: str, body: str) -> OutboundSms: ...


class MockSmsProvider:
    name = "mock"

    def __init__(self) -> None:
        self.outbox: list[OutboundSms] = []

    def send(self, to: str, body: str) -> OutboundSms:
        msg = OutboundSms(to=to, body=body, provider=self.name, ref=f"MOCK-{len(self.outbox) + 1:05d}")
        self.outbox.append(msg)
        return msg


class TwilioSmsProvider:  # pragma: no cover - needs credentials and network
    name = "twilio"

    def __init__(self, sid: str, token: str, sender: str) -> None:
        self.sid, self.token, self.sender = sid, token, sender

    def send(self, to: str, body: str) -> OutboundSms:
        import httpx
        r = httpx.post(f"https://api.twilio.com/2010-04-01/Accounts/{self.sid}/Messages.json",
                       data={"To": to, "From": self.sender, "Body": body}, auth=(self.sid, self.token), timeout=10)
        r.raise_for_status()
        return OutboundSms(to=to, body=body, provider=self.name, ref=r.json().get("sid", ""))


def parse_inbound(form: dict) -> dict:
    """Normalise a Twilio-style (From, Body) or Exotel/MSG91-style (from/sender, text/message) webhook payload."""
    sender = form.get("From") or form.get("from") or form.get("sender") or ""
    body = form.get("Body") or form.get("body") or form.get("text") or form.get("message") or ""
    return {"from": str(sender).strip(), "body": str(body).strip(), "provider_ref": form.get("MessageSid") or form.get("id")}


_provider: SmsProvider | None = None


def get_sms_provider() -> SmsProvider:
    global _provider
    if _provider is None:
        s = get_settings()
        if s.sms_provider == "twilio" and s.twilio_account_sid and not s.mock:
            _provider = TwilioSmsProvider(s.twilio_account_sid, s.twilio_auth_token, s.sms_from_number)
        else:
            _provider = MockSmsProvider()
    return _provider
