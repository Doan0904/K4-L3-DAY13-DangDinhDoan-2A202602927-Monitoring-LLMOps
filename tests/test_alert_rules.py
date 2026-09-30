from __future__ import annotations

import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
REQUIRED = ("name", "severity", "condition", "duration", "type", "channel", "owner", "runbook")


def test_three_complete_symptom_based_alerts_with_runbooks() -> None:
    alerts = yaml.safe_load((REPO_ROOT / "config" / "alert_rules.yaml").read_text(encoding="utf-8"))["alerts"]
    runbook = (REPO_ROOT / "docs" / "alerts.md").read_text(encoding="utf-8")

    assert len(alerts) == 3
    for alert in alerts:
        for field in REQUIRED:
            assert alert.get(field), f"{alert.get('name')}.{field}"
            assert "TODO" not in str(alert[field])
        assert alert["type"] == "symptom-based"
        assert alert["channel"] == "slack" and alert["slack_channel"].startswith("#")
        assert alert["severity"] in {"info", "warning", "critical"}
        assert re.fullmatch(r"\d+[smh]", alert["duration"])
        path, anchor = alert["runbook"].split("#")
        assert path == "docs/alerts.md"
        heading = "## " + anchor.replace("-", " ").title()
        assert heading in runbook
        assert alert["name"] in runbook


def test_slo_error_budget_matches_target() -> None:
    slo = yaml.safe_load((REPO_ROOT / "config" / "slo.yaml").read_text(encoding="utf-8"))["primary_slo"]
    assert round(100 - slo["target_percent"], 6) == slo["error_budget_percent"]
