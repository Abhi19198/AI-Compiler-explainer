"""Unit tests for services.llm_client.

No real Anthropic call is made: the client factory is stubbed, and the
missing-key path is exercised with the env var removed.
"""

import asyncio
import json
from types import SimpleNamespace

import pytest

from services import llm_client


def _fake_client(raw_text):
    """Mimic AsyncAnthropic: messages.create returns text blocks."""

    async def _create(**kwargs):
        return SimpleNamespace(content=[SimpleNamespace(type="text", text=raw_text)])

    return SimpleNamespace(messages=SimpleNamespace(create=_create))


def test_strip_json_fences_plain_json():
    assert llm_client._strip_json_fences('{"a": 1}') == '{"a": 1}'


def test_strip_json_fences_json_fence():
    assert llm_client._strip_json_fences('```json\n{"a": 1}\n```') == '{"a": 1}'


def test_strip_json_fences_bare_fence():
    assert llm_client._strip_json_fences('```\n{"a": 1}\n```') == '{"a": 1}'


def test_strip_json_fences_trims_whitespace():
    assert llm_client._strip_json_fences('  {"a": 1}  \n') == '{"a": 1}'


def test_explain_code_missing_key_raises_before_any_call(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY is missing"):
        asyncio.run(llm_client.explain_code("x = 1", "python"))


def test_explain_code_parses_llm_json(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-key")
    payload = {"language_detected": "python", "summary": "ok"}
    monkeypatch.setattr(llm_client, "_get_client", lambda: _fake_client(json.dumps(payload)))
    result = asyncio.run(llm_client.explain_code("x = 1", "python"))
    assert result == payload


def test_explain_code_strips_fences_from_llm_output(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-key")
    payload = {"language_detected": "python"}
    monkeypatch.setattr(
        llm_client, "_get_client", lambda: _fake_client("```json\n" + json.dumps(payload) + "\n```")
    )
    result = asyncio.run(llm_client.explain_code("x = 1"))
    assert result == payload


def test_explain_code_invalid_json_raises_value_error(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-key")
    monkeypatch.setattr(llm_client, "_get_client", lambda: _fake_client("this is not json"))
    with pytest.raises(ValueError, match="LLM did not return valid JSON"):
        asyncio.run(llm_client.explain_code("x = 1"))


def test_explain_code_sends_hint_and_code(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-key")
    calls = {}

    async def _create(**kwargs):
        calls.update(kwargs)
        return SimpleNamespace(
            content=[SimpleNamespace(type="text", text=json.dumps({"language_detected": "java"}))]
        )

    fake = SimpleNamespace(messages=SimpleNamespace(create=_create))
    monkeypatch.setattr(llm_client, "_get_client", lambda: fake)
    asyncio.run(llm_client.explain_code("int x = 1;", "java"))
    user_text = calls["messages"][0]["content"]
    assert "Language hint: java" in user_text
    assert "int x = 1;" in user_text


def test_module_imports_without_api_key(monkeypatch):
    """Regression test: importing the app must not need ANTHROPIC_API_KEY."""
    import importlib

    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    importlib.reload(llm_client)
    assert llm_client._client is None  # client is lazy, not built at import
    importlib.reload(llm_client)
