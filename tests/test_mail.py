from notification.notifications import _format_opportunities
from notification.notifications import get_smtp_settings,send_new_opportunities_email

import smtplib
import pytest


class FakeOpportunity:
    def __init__(self, title, description, submission_deadline, url):
        self.title = title
        self.description = description
        self.submission_deadline = submission_deadline
        self.url = url


def test_format_opportunities():
    opps = [
        FakeOpportunity(
            "AI Project",
            "Build AI system",
            "2026-09-01",
            "http://example.com"
        )
    ]

    result = _format_opportunities(opps)

    assert "AI Project" in result
    assert "Build AI system" in result
    assert "2026-09-01" in result
    assert "http://example.com" in result


def test_get_smtp_settings(monkeypatch):
    # Set fake environment variables
    monkeypatch.setenv("SMTP_HOST", "smtp.test.com")
    monkeypatch.setenv("SMTP_PORT", "2525")
    monkeypatch.setenv("SMTP_USERNAME", "test_user")
    monkeypatch.setenv("SMTP_PASSWORD", "secret")
    monkeypatch.setenv("SMTP_FROM", "from@test.com")
    monkeypatch.setenv("OPPORTUNITIES_EMAIL_TO", "to@test.com")
    monkeypatch.setenv("SMTP_USE_SSL", "true")
    monkeypatch.setenv("SMTP_PROVIDER", "gmail")

    settings = get_smtp_settings()

    assert settings["host"] == "smtp.test.com"
    assert settings["port"] == 2525
    assert settings["username"] == "test_user"
    assert settings["has_password"] is True
    assert settings["sender"] == "from@test.com"
    assert settings["recipient"] == "to@test.com"
    assert settings["use_ssl"] is True


def test_send_email(monkeypatch):
    # ✅ Step 1: fake env
    monkeypatch.setenv("SMTP_HOST", "smtp.test.com")
    monkeypatch.setenv("SMTP_PORT", "465")
    monkeypatch.setenv("SMTP_USERNAME", "user")
    monkeypatch.setenv("SMTP_PASSWORD", "pass")
    monkeypatch.setenv("SMTP_FROM", "from@test.com")
    monkeypatch.setenv("OPPORTUNITIES_EMAIL_TO", "to@test.com")
    monkeypatch.setenv("SMTP_USE_SSL", "true")

    # ✅ Step 2: capture what gets sent
    captured = {}

    class FakeSMTP:
        def __init__(self, host, port, context=None):
            self.host = host
            self.port = port

        def login(self, user, password):
            captured["login"] = (user, password)

        def send_message(self, msg):
            captured["message"] = msg

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    # ✅ Step 3: replace real SMTP with fake
    monkeypatch.setattr(smtplib, "SMTP_SSL", FakeSMTP)

    opps = [
        FakeOpportunity("Test Title", "Desc", "2026-01-01", "http://url")
    ]

    result = send_new_opportunities_email(opps)

    assert result == 1
    assert "message" in captured
    assert captured["login"] == ("user", "pass")
    assert "Test Title" in captured["message"].get_content()