"""Lọc data/logs.jsonl để tìm request bất thường và correlation_id (bước Logs trong Metrics → Logs → Traces).

Ví dụ:
    python scripts/query_logs.py --event response_sent --min-latency 1500
    python scripts/query_logs.py --event request_failed --since 2026-09-30T02:44:00Z
    python scripts/query_logs.py --cid req-1a2b3c4d          # toàn bộ log của một request
    python scripts/query_logs.py --event response_sent --min-tokens-out 300 --fields correlation_id,tokens_out,cost_usd
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.cli import configure_utf8_stdio


def parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def matches(record: dict, args: argparse.Namespace) -> bool:
    if args.event and record.get("event") != args.event:
        return False
    if args.cid and record.get("correlation_id") != args.cid:
        return False
    if args.feature and record.get("feature") != args.feature:
        return False
    if args.error_type and record.get("error_type") != args.error_type:
        return False
    if args.min_latency is not None and (record.get("latency_ms") or 0) < args.min_latency:
        return False
    if args.min_tokens_out is not None and (record.get("tokens_out") or 0) < args.min_tokens_out:
        return False
    if args.since or args.until:
        if "ts" not in record:
            return False
        ts = parse_ts(record["ts"])
        if args.since and ts < parse_ts(args.since):
            return False
        if args.until and ts > parse_ts(args.until):
            return False
    return True


def main() -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--logs", type=Path, default=REPO_ROOT / "data" / "logs.jsonl")
    parser.add_argument("--event")
    parser.add_argument("--cid", help="correlation_id cần xem")
    parser.add_argument("--feature")
    parser.add_argument("--error-type")
    parser.add_argument("--min-latency", type=int)
    parser.add_argument("--min-tokens-out", type=int)
    parser.add_argument("--since", help="ISO timestamp UTC, ví dụ 2026-09-30T02:44:00Z")
    parser.add_argument("--until")
    parser.add_argument("--fields", help="Danh sách field cách nhau bởi dấu phẩy; mặc định in cả dòng")
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()

    if not args.logs.exists():
        print(f"Không tìm thấy {args.logs}")
        return 1

    shown = total = 0
    for line in args.logs.read_text(encoding="utf-8").splitlines():
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not matches(record, args):
            continue
        total += 1
        if shown < args.limit:
            if args.fields:
                record = {k: record.get(k) for k in args.fields.split(",")}
            print(json.dumps(record, ensure_ascii=False))
            shown += 1
    print(f"-- {total} dòng khớp (hiển thị {shown})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
