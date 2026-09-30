from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path

import httpx

from app import logging_config
from app.logging_config import scrub_event
from app.main import app


def _post(client_kwargs: dict, payload: dict) -> httpx.Response:
    async def send() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.post("/chat", json=payload, **client_kwargs)

    return asyncio.run(send())


PAYLOAD = {
    "user_id": "student-01",
    "session_id": "session-01",
    "feature": "qa",
    "message": "Email student@vinuni.edu.vn, phone 0987654321, card 4111 1111 1111 1111",
}


def test_generates_correlation_id_and_returns_headers(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(logging_config, "LOG_PATH", tmp_path / "logs.jsonl")

    response = _post({}, PAYLOAD)

    correlation_id = response.headers["x-request-id"]
    assert re.fullmatch(r"req-[0-9a-f]{8}", correlation_id)
    assert response.json()["correlation_id"] == correlation_id
    assert float(response.headers["x-response-time-ms"]) >= 0


def test_reuses_incoming_request_id_and_enriches_logs(monkeypatch, tmp_path: Path) -> None:
    log_path = tmp_path / "logs.jsonl"
    monkeypatch.setattr(logging_config, "LOG_PATH", log_path)

    response = _post({"headers": {"x-request-id": "req-abcdef12"}}, PAYLOAD)

    assert response.headers["x-request-id"] == "req-abcdef12"
    records = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    api_records = [r for r in records if r.get("service") == "api"]
    assert {r["event"] for r in api_records} == {"request_received", "response_sent"}
    for record in api_records:
        assert record["correlation_id"] == "req-abcdef12"
        for field in ("user_id_hash", "session_id", "feature", "model", "env"):
            assert record[field]
        assert "student-01" not in json.dumps(record)


def test_rejects_unsafe_incoming_request_id(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(logging_config, "LOG_PATH", tmp_path / "logs.jsonl")

    response = _post({"headers": {"x-request-id": "bad id\ninjected"}}, PAYLOAD)

    assert re.fullmatch(r"req-[0-9a-f]{8}", response.headers["x-request-id"])


def test_context_does_not_leak_between_requests(monkeypatch, tmp_path: Path) -> None:
    log_path = tmp_path / "logs.jsonl"
    monkeypatch.setattr(logging_config, "LOG_PATH", log_path)

    _post({}, PAYLOAD)
    _post({}, {**PAYLOAD, "session_id": "session-02", "feature": "summary"})

    records = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    by_id: dict[str, set[str]] = {}
    for record in records:
        if record.get("service") == "api":
            by_id.setdefault(record["correlation_id"], set()).add(record["session_id"])
    assert len(by_id) == 2
    assert all(len(sessions) == 1 for sessions in by_id.values())


def test_logged_payload_has_no_raw_pii(monkeypatch, tmp_path: Path) -> None:
    log_path = tmp_path / "logs.jsonl"
    monkeypatch.setattr(logging_config, "LOG_PATH", log_path)

    _post({}, PAYLOAD)

    raw = log_path.read_text(encoding="utf-8")
    for secret in ("student@vinuni.edu.vn", "0987654321", "4111 1111 1111 1111"):
        assert secret not in raw


def test_scrub_event_handles_nested_values() -> None:
    event = {
        "event": "request_failed",
        "payload": {"detail": "user a@b.com", "items": ["0901234567"]},
        "exception": "ValueError: 079201234567",
    }

    scrubbed = scrub_event(None, "error", event)

    assert "a@b.com" not in json.dumps(scrubbed)
    assert "0901234567" not in json.dumps(scrubbed)
    assert "079201234567" not in scrubbed["exception"]


def test_failed_request_returns_correlation_id_and_logs_tool_failure(monkeypatch, tmp_path: Path) -> None:
    from app import incidents

    log_path = tmp_path / "logs.jsonl"
    monkeypatch.setattr(logging_config, "LOG_PATH", log_path)
    monkeypatch.setitem(incidents.STATE, "tool_fail", True)

    response = _post({"headers": {"x-request-id": "req-0000dead"}}, PAYLOAD)

    assert response.status_code == 500
    assert response.json() == {"detail": "RuntimeError", "correlation_id": "req-0000dead"}
    records = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    failed = next(r for r in records if r["event"] == "request_failed")
    assert failed["correlation_id"] == "req-0000dead"
    assert failed["tool_success"] is False
    assert failed["error_type"] == "RuntimeError"
