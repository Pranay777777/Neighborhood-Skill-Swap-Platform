"""Real SMTP delivery to a local Mailpit (docker compose up mailpit). Skipped unless
SWAP_MAILPIT_API is set, e.g. http://localhost:8025."""

import os

import httpx
import pytest

from app import mailer
from app.config import settings

API = os.environ.get("SWAP_MAILPIT_API")
pytestmark = pytest.mark.skipif(not API, reason="set SWAP_MAILPIT_API to run against Mailpit")


def test_verification_mail_arrives_in_mailpit(monkeypatch):
    httpx.delete(f"{API}/api/v1/messages")
    monkeypatch.setattr(settings, "mail_backend", "smtp")
    mailer.send_mail("neighbour@example.com", "Verify your Skill Swap email", "token=abc123")
    messages = httpx.get(f"{API}/api/v1/messages").json()["messages"]
    assert [m["Subject"] for m in messages] == ["Verify your Skill Swap email"]
    assert messages[0]["To"][0]["Address"] == "neighbour@example.com"
