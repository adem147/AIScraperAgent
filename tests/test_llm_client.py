import types

import pytest

from LLM.llm_client import ask_groq


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_ask_groq_returns_content(monkeypatch):
    captured = {}

    def fake_post(url, headers=None, json=None, timeout=None):
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        return FakeResponse({
            "choices": [{"message": {"content": '{"ok": true}'}}]
        })

    monkeypatch.setattr("LLM.groq_client.requests.post", fake_post)
    monkeypatch.setenv("GROQ_API_KEY", "test-key")

    result = ask_groq("hello")

    assert result == '{"ok": true}'
    assert captured["headers"]["Authorization"] == "Bearer test-key"
