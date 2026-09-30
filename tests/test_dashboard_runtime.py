from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import yaml

from scripts import dashboard

REPO_ROOT = Path(__file__).resolve().parents[1]


def _write_logs(path: Path) -> None:
    base = "2026-09-30T10:0{m}:{s:02d}Z"
    records = []
    for i in range(4):
        ts = base.format(m=1, s=i)
        records.append({"ts": ts, "event": "request_received", "service": "api"})
        records.append(
            {
                "ts": ts,
                "event": "response_sent",
                "service": "api",
                "latency_ms": 100 * (i + 1),
                "ttft_ms": 50,
                "tokens_in": 10,
                "tokens_out": 100,
                "cost_usd": 0.001,
                "quality_score": 0.8,
                "tool_success": True,
            }
        )
    records.append({"ts": base.format(m=2, s=0), "event": "request_received", "service": "api"})
    records.append(
        {"ts": base.format(m=2, s=1), "event": "request_failed", "service": "api",
         "error_type": "RuntimeError", "tool_success": False}
    )
    # Ngoài cửa sổ 60 phút: không được tính.
    records.append({"ts": "2026-09-30T08:00:00Z", "event": "request_received", "service": "api"})
    path.write_text("\n".join(json.dumps(r) for r in records), encoding="utf-8")


def test_dashboard_computes_contract_aggregations(tmp_path: Path) -> None:
    log_path = tmp_path / "logs.jsonl"
    _write_logs(log_path)
    config_path = REPO_ROOT / "config" / "dashboard.yaml"
    end = datetime(2026, 9, 30, 10, 5, tzinfo=timezone.utc)

    config, data = dashboard.build(config_path, log_path, end)

    assert data["counts"] == {"received": 5, "sent": 4, "failed": 1}
    assert data["latency"]["p99"] == 400
    assert data["latency"]["ttft_p95"] == 50
    assert data["errors"]["error_rate_pct"] == 20.0
    assert data["errors"]["count_by_value"] == {"RuntimeError": 1}
    assert data["errors"]["tool_success_rate_pct"] == 80.0
    assert data["tokens"] == {**data["tokens"], "tokens_in": 40, "tokens_out": 400}
    assert round(data["cost"]["total"], 6) == 0.004
    assert data["quality"]["mean"] == 0.8

    errors_panel = next(p for p in config["dashboard"]["panels"] if p["id"] == "errors")
    ok = dashboard.threshold_ok(dashboard.threshold_value(data, errors_panel), errors_panel["threshold"])
    assert ok is False

    page = dashboard.render_html(config, data, Path("data/logs.jsonl"))
    for panel in yaml.safe_load(config_path.read_text(encoding="utf-8"))["dashboard"]["panels"]:
        assert panel["title"] in page
    assert "last 60 min" in page
