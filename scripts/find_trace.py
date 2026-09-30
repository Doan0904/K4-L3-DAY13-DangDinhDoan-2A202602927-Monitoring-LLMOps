"""Tìm trace Langfuse theo correlation_id (bước Traces trong Metrics → Logs → Traces).

    python scripts/find_trace.py --cid req-1a2b3c4d
    python scripts/find_trace.py --recent 15          # liệt kê trace gần nhất

Dùng Observations API v2 (project tạo sau 16/09/2026 không còn GET /api/public/traces).
Không in metadata do SDK tự thêm (ví dụ public key).
"""
from __future__ import annotations

import argparse
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.cli import configure_utf8_stdio

ROOT_KEYS = ("correlation_id", "feature", "prompt_name", "prompt_label", "prompt_version", "prompt_source")


def fetch_observations(hours: float) -> list[dict]:
    load_dotenv(REPO_ROOT / ".env")
    base_url = os.getenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com").rstrip("/")
    auth = (os.environ["LANGFUSE_PUBLIC_KEY"], os.environ["LANGFUSE_SECRET_KEY"])
    now = datetime.now(timezone.utc)
    params = {
        "fromStartTime": (now - timedelta(hours=hours)).isoformat().replace("+00:00", "Z"),
        "toStartTime": (now + timedelta(minutes=1)).isoformat().replace("+00:00", "Z"),
        "fields": "core,basic,metadata,prompt,usage,model",
        "limit": 100,
    }
    observations: list[dict] = []
    cursor = None
    while True:
        if cursor:
            params["cursor"] = cursor
        r = httpx.get(f"{base_url}/api/public/v2/observations", params=params, auth=auth, timeout=30)
        r.raise_for_status()
        body = r.json()
        observations.extend(body.get("data", []))
        cursor = (body.get("meta") or {}).get("cursor")
        if not cursor or len(observations) >= 2000:
            return observations


def ms(obs: dict) -> str:
    start, end = obs.get("startTime"), obs.get("endTime")
    if not (start and end):
        return "?"
    parse = lambda v: datetime.fromisoformat(v.replace("Z", "+00:00"))  # noqa: E731
    return f"{(parse(end) - parse(start)).total_seconds() * 1000:.0f}ms"


def describe(trace_id: str, obs: list[dict], base_url: str) -> None:
    root = next((o for o in obs if o.get("name") == "lab-agent-run"), obs[0])
    md = root.get("metadata") or {}
    print(f"trace_id={trace_id}  start={root.get('startTime')}")
    print("  " + "  ".join(f"{k}={md.get(k)}" for k in ROOT_KEYS))
    for o in sorted(obs, key=lambda o: (o.get("name") != "lab-agent-run", o.get("startTime") or "")):
        extra = ""
        if o.get("type") == "GENERATION":
            extra = f" usage={o.get('usageDetails')} cost={o.get('costDetails')} prompt={o.get('promptName')} v{o.get('promptVersion')}"
        print(f"  - {o.get('name')} ({o.get('type')}) {ms(o)} level={o.get('level')}{extra}")
    print(f"  {base_url}/project/{root.get('projectId')}/traces/{trace_id}")


def main() -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--cid", help="correlation_id cần tìm")
    parser.add_argument("--recent", type=int, help="Số trace gần nhất cần liệt kê")
    parser.add_argument("--hours", type=float, default=6, help="Tìm trong N giờ gần nhất")
    args = parser.parse_args()

    traces: dict[str, list[dict]] = defaultdict(list)
    for obs in fetch_observations(args.hours):
        traces[obs["traceId"]].append(obs)
    base_url = os.getenv("LANGFUSE_BASE_URL", "").rstrip("/")

    if args.cid:
        matched = [t for t, obs in traces.items() if any((o.get("metadata") or {}).get("correlation_id") == args.cid for o in obs)]
        if not matched:
            print(f"Chưa thấy trace cho {args.cid} (đợi vài giây để SDK flush rồi thử lại)")
            return 1
        for trace_id in matched:
            describe(trace_id, traces[trace_id], base_url)
        return 0

    ordered = sorted(traces.items(), key=lambda kv: min(o.get("startTime") or "" for o in kv[1]), reverse=True)
    for trace_id, obs in ordered[: args.recent or 15]:
        root = next((o for o in obs if o.get("name") == "lab-agent-run"), obs[0])
        md = root.get("metadata") or {}
        print(f"{trace_id}  {root.get('startTime')}  {md.get('correlation_id')}  prompt=v{md.get('prompt_version')}/{md.get('prompt_label')}  {ms(root)}  obs={len(obs)}")
    print(f"-- {len(traces)} traces trong {args.hours}h gần nhất")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
