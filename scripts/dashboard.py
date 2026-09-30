"""Dashboard 6 panel dựng trực tiếp từ data/logs.jsonl theo contract config/dashboard.yaml.

Ví dụ:
    python scripts/dashboard.py --out data/dashboard.html          # render 1 lần
    python scripts/dashboard.py --serve --port 8050                # tự render lại mỗi lần refresh (30s)
    python scripts/dashboard.py --summary                          # in số liệu 6 panel ra terminal
"""
from __future__ import annotations

import argparse
import html
import json
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from statistics import mean

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.cli import configure_utf8_stdio
from app.metrics import percentile

DEFAULT_CONFIG = REPO_ROOT / "config" / "dashboard.yaml"


def parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def load_records(path: Path) -> list[dict]:
    if not path.exists():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(record, dict) and "ts" in record:
            record["_ts"] = parse_ts(record["ts"])
            records.append(record)
    return records


@dataclass
class Window:
    start: datetime
    end: datetime
    minutes: list[datetime] = field(default_factory=list)

    @classmethod
    def ending_at(cls, end: datetime, range_minutes: int) -> "Window":
        end_minute = end.replace(second=0, microsecond=0)
        minutes = [end_minute - timedelta(minutes=i) for i in range(range_minutes - 1, -1, -1)]
        return cls(start=minutes[0], end=end, minutes=minutes)

    def contains(self, ts: datetime) -> bool:
        return self.start <= ts <= self.end


def bucket(ts: datetime) -> datetime:
    return ts.replace(second=0, microsecond=0)


def compute(records: list[dict], window: Window) -> dict:
    """Tính đúng các aggregation mà config/dashboard.yaml mô tả trong field `query`."""
    in_window = [r for r in records if window.contains(r["_ts"])]
    received = [r for r in in_window if r.get("event") == "request_received"]
    sent = [r for r in in_window if r.get("event") == "response_sent"]
    failed = [r for r in in_window if r.get("event") == "request_failed"]
    tool_events = [r for r in in_window if r.get("tool_success") is not None]

    per_min: dict[str, dict[datetime, list]] = defaultdict(lambda: defaultdict(list))
    for r in received:
        per_min["traffic"][bucket(r["_ts"])].append(1)
    for r in failed:
        per_min["failed"][bucket(r["_ts"])].append(1)
    for r in sent:
        b = bucket(r["_ts"])
        per_min["latency"][b].append(r.get("latency_ms", 0))
        per_min["ttft"][b].append(r.get("ttft_ms", 0))
        per_min["cost"][b].append(r.get("cost_usd", 0.0))
        per_min["tokens_in"][b].append(r.get("tokens_in", 0))
        per_min["tokens_out"][b].append(r.get("tokens_out", 0))
        per_min["quality"][b].append(r.get("quality_score", 0.0))

    def series(name: str, agg) -> list[float | None]:
        return [agg(per_min[name][m]) if per_min[name].get(m) else None for m in window.minutes]

    latencies = [r.get("latency_ms", 0) for r in sent]
    ttfts = [r.get("ttft_ms", 0) for r in sent]
    error_rate = (len(failed) / len(received) * 100) if received else 0.0
    tool_success = (
        sum(1 for r in tool_events if r["tool_success"] is True) / len(tool_events) * 100
        if tool_events
        else None
    )
    active_minutes = [m for m in window.minutes if per_min["traffic"].get(m)]

    return {
        "window": window,
        "counts": {"received": len(received), "sent": len(sent), "failed": len(failed)},
        "latency": {
            "p50": percentile(latencies, 50),
            "p95": percentile(latencies, 95),
            "p99": percentile(latencies, 99),
            "ttft_p95": percentile(ttfts, 95),
            "series_p95": series("latency", lambda v: percentile(v, 95)),
            "series_ttft_p95": series("ttft", lambda v: percentile(v, 95)),
        },
        "traffic": {
            "count": len(received),
            "rate_per_minute": (len(received) / len(active_minutes)) if active_minutes else 0.0,
            "series": series("traffic", len),
        },
        "errors": {
            "error_rate_pct": error_rate,
            "count_by_value": dict(Counter(r.get("error_type") or "unknown" for r in failed)),
            "tool_success_rate_pct": tool_success,
            "series": [
                (len(per_min["failed"].get(m, [])) / len(per_min["traffic"][m]) * 100)
                if per_min["traffic"].get(m)
                else None
                for m in window.minutes
            ],
        },
        "cost": {
            "total": sum(r.get("cost_usd", 0.0) for r in sent),
            "series": series("cost", sum),
        },
        "tokens": {
            "tokens_in": sum(r.get("tokens_in", 0) for r in sent),
            "tokens_out": sum(r.get("tokens_out", 0) for r in sent),
            "series_in": series("tokens_in", sum),
            "series_out": series("tokens_out", sum),
        },
        "quality": {
            "mean": mean(r.get("quality_score", 0.0) for r in sent) if sent else None,
            "series": series("quality", mean),
        },
    }


def threshold_value(data: dict, panel: dict) -> list[float | None]:
    """Giá trị được so với threshold; tokens kiểm tra từng field (sum_by_field)."""
    pid, agg = panel["id"], panel["threshold"]["aggregation"]
    if pid == "tokens":
        return [data["tokens"]["tokens_in"], data["tokens"]["tokens_out"]]
    return [data[pid].get(agg)]


def threshold_ok(values: list[float | None], threshold: dict) -> bool | None:
    present = [v for v in values if v is not None]
    if not present:
        return None
    if threshold["operator"] == "lte":
        return all(v <= threshold["value"] for v in present)
    return all(v >= threshold["value"] for v in present)


# ---------------------------------------------------------------- rendering

COLORS = {"a": "#2563eb", "b": "#d97706", "threshold": "#dc2626"}


def svg_chart(
    minutes: list[datetime],
    series: list[tuple[str, list[float | None], str]],
    threshold: float | None,
    kind: str = "line",
) -> str:
    width, height, pad_l, pad_r, pad_t, pad_b = 520, 170, 52, 12, 12, 26
    values = [v for _, s, _ in series for v in s if v is not None]
    top = max(values + ([threshold] if threshold is not None else []) + [1e-9]) * 1.15
    n = len(minutes)
    plot_w, plot_h = width - pad_l - pad_r, height - pad_t - pad_b

    def x(i: int) -> float:
        return pad_l + (i + 0.5) * plot_w / n

    def y(v: float) -> float:
        return pad_t + plot_h - (v / top) * plot_h

    parts = [f'<svg viewBox="0 0 {width} {height}" class="chart" role="img">']
    for frac in (0, 0.5, 1):
        gy = pad_t + plot_h - frac * plot_h
        parts.append(f'<line x1="{pad_l}" x2="{width - pad_r}" y1="{gy:.1f}" y2="{gy:.1f}" class="grid"/>')
        parts.append(f'<text x="{pad_l - 6}" y="{gy + 4:.1f}" class="tick" text-anchor="end">{fmt_num(top * frac)}</text>')
    for i in range(0, n, 15):
        parts.append(f'<text x="{x(i):.1f}" y="{height - 6}" class="tick" text-anchor="middle">{minutes[i]:%H:%M}</text>')
    parts.append(f'<text x="{x(n - 1):.1f}" y="{height - 6}" class="tick" text-anchor="end">{minutes[-1]:%H:%M}</text>')

    bar_w = max(1.5, plot_w / n / max(1, len(series)) - 1)
    for s_idx, (_, s, color) in enumerate(series):
        if kind == "bar":
            for i, v in enumerate(s):
                if v:
                    bx = x(i) - (plot_w / n) / 2 + s_idx * bar_w
                    parts.append(f'<rect x="{bx:.1f}" y="{y(v):.1f}" width="{bar_w:.1f}" height="{pad_t + plot_h - y(v):.1f}" fill="{color}"/>')
        else:
            points = [(x(i), y(v)) for i, v in enumerate(s) if v is not None]
            # Chỉ nối các phút liền nhau; phút không có dữ liệu làm đứt đường để không "nội suy" giả.
            segment: list[tuple[float, float]] = []
            for v, i in [(v, i) for i, v in enumerate(s)] + [(None, n)]:
                if v is not None:
                    segment.append((x(i), y(v)))
                    continue
                if len(segment) > 1:
                    d = " ".join(f"{px:.1f},{py:.1f}" for px, py in segment)
                    parts.append(f'<polyline points="{d}" fill="none" stroke="{color}" stroke-width="2"/>')
                segment = []
            for px, py in points:
                parts.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="2.5" fill="{color}"/>')
    if threshold is not None:
        ty = y(threshold)
        parts.append(f'<line x1="{pad_l}" x2="{width - pad_r}" y1="{ty:.1f}" y2="{ty:.1f}" class="threshold"/>')
    parts.append("</svg>")
    return "".join(parts)


def fmt_num(v: float | None, digits: int = 0) -> str:
    if v is None:
        return "–"
    if isinstance(v, float) and digits:
        return f"{v:,.{digits}f}"
    if abs(v) < 1 and v != 0:
        return f"{v:.3f}"
    return f"{v:,.0f}"


def stat(label: str, value: str) -> str:
    return f'<div class="stat"><span class="v">{html.escape(value)}</span><span class="l">{html.escape(label)}</span></div>'


def legend(items: list[tuple[str, str]], with_threshold: bool = True) -> str:
    spans = "".join(f'<span><i style="background:{c}"></i>{html.escape(n)}</span>' for n, c in items)
    threshold = '<span><i class="th"></i>threshold</span>' if with_threshold else ""
    return f'<div class="legend">{spans}{threshold}</div>'


def render_panel(panel: dict, data: dict) -> str:
    pid, unit, th = panel["id"], panel["unit"], panel["threshold"]
    minutes = data["window"].minutes
    op = "≤" if th["operator"] == "lte" else "≥"
    ok = threshold_ok(threshold_value(data, panel), th)
    badge = {True: ("OK", "ok"), False: ("BREACH", "bad"), None: ("NO DATA", "na")}[ok]
    th_text = f'{th["aggregation"]} {op} {th["value"]} {unit}'

    if pid == "latency":
        d = data["latency"]
        stats = stat("P50 ms", fmt_num(d["p50"])) + stat("P95 ms", fmt_num(d["p95"])) + stat("P99 ms", fmt_num(d["p99"])) + stat("TTFT P95 ms", fmt_num(d["ttft_p95"]))
        chart = svg_chart(minutes, [("P95", d["series_p95"], COLORS["a"]), ("TTFT P95", d["series_ttft_p95"], COLORS["b"])], th["value"])
        leg = legend([("latency P95 / phút", COLORS["a"]), ("TTFT P95 / phút", COLORS["b"])])
    elif pid == "traffic":
        d = data["traffic"]
        stats = stat("requests (60m)", fmt_num(d["count"])) + stat("req/phút (phút có traffic)", fmt_num(d["rate_per_minute"], 1))
        chart = svg_chart(minutes, [("req", d["series"], COLORS["a"])], th["value"], kind="bar")
        leg = legend([("request_received / phút", COLORS["a"])])
    elif pid == "errors":
        d = data["errors"]
        breakdown = ", ".join(f"{k}: {v}" for k, v in d["count_by_value"].items()) or "không có lỗi"
        stats = stat("error rate %", fmt_num(d["error_rate_pct"], 2)) + stat("retrieval success %", fmt_num(d["tool_success_rate_pct"], 1)) + stat("breakdown", breakdown)
        chart = svg_chart(minutes, [("error %", d["series"], COLORS["threshold"] if ok is False else COLORS["a"])], th["value"])
        leg = legend([("error rate % / phút", COLORS["a"])])
    elif pid == "cost":
        d = data["cost"]
        stats = stat("total USD (60m)", f'${d["total"]:.4f}')
        chart = svg_chart(minutes, [("cost", d["series"], COLORS["a"])], None, kind="bar")
        leg = legend([("sum(cost_usd) / phút", COLORS["a"])], with_threshold=False)
    elif pid == "tokens":
        d = data["tokens"]
        stats = stat("tokens_in", fmt_num(d["tokens_in"])) + stat("tokens_out", fmt_num(d["tokens_out"]))
        chart = svg_chart(minutes, [("in", d["series_in"], COLORS["a"]), ("out", d["series_out"], COLORS["b"])], None, kind="bar")
        leg = legend([("tokens_in / phút", COLORS["a"]), ("tokens_out / phút", COLORS["b"])], with_threshold=False)
    else:
        d = data["quality"]
        stats = stat("mean quality", fmt_num(d["mean"], 3))
        chart = svg_chart(minutes, [("quality", d["series"], COLORS["a"])], th["value"])
        leg = legend([("mean(quality_score) / phút", COLORS["a"])])

    note = "" if pid not in ("cost", "tokens") else '<p class="note">Threshold áp dụng cho tổng cửa sổ 60m (không vẽ lên chart theo phút).</p>'
    return f"""
<section class="panel">
  <header><h2>{html.escape(panel["title"])}</h2><span class="badge {badge[1]}">{badge[0]}</span></header>
  <p class="meta">unit: <b>{html.escape(unit)}</b> · threshold: <b>{html.escape(th_text)}</b></p>
  <div class="stats">{stats}</div>
  {chart}
  {leg}{note}
</section>"""


def render_html(config: dict, data: dict, source: Path) -> str:
    dash = config["dashboard"]
    window: Window = data["window"]
    panels = "".join(render_panel(p, data) for p in dash["panels"])
    c = data["counts"]
    return f"""<!doctype html>
<html lang="vi"><head><meta charset="utf-8">
<meta http-equiv="refresh" content="{dash["refresh_seconds"]}">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(dash["title"])}</title>
<style>
:root {{ --bg:#f6f7f9; --card:#fff; --ink:#111827; --muted:#6b7280; --line:#e5e7eb; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; font:14px/1.4 system-ui,-apple-system,Segoe UI,Roboto,sans-serif; background:var(--bg); color:var(--ink); }}
.top {{ padding:16px 24px; border-bottom:1px solid var(--line); background:var(--card); display:flex; flex-wrap:wrap; gap:8px 24px; align-items:baseline; }}
.top h1 {{ font-size:18px; margin:0; }}
.top span {{ color:var(--muted); }}
.grid {{ display:grid; grid-template-columns:repeat(3, minmax(0,1fr)); gap:16px; padding:16px 24px; }}
@media (max-width:1100px) {{ .grid {{ grid-template-columns:1fr; }} }}
.panel {{ background:var(--card); border:1px solid var(--line); border-radius:8px; padding:14px 16px; }}
.panel header {{ display:flex; justify-content:space-between; align-items:center; }}
.panel h2 {{ font-size:15px; margin:0; }}
.meta {{ color:var(--muted); margin:4px 0 8px; font-size:12px; }}
.badge {{ font-size:11px; font-weight:600; padding:2px 8px; border-radius:999px; }}
.badge.ok {{ background:#dcfce7; color:#166534; }} .badge.bad {{ background:#fee2e2; color:#991b1b; }} .badge.na {{ background:#f3f4f6; color:#4b5563; }}
.stats {{ display:flex; flex-wrap:wrap; gap:6px 18px; margin-bottom:6px; }}
.stat {{ display:flex; flex-direction:column; }}
.stat .v {{ font-size:18px; font-weight:600; font-variant-numeric:tabular-nums; }}
.stat .l {{ font-size:11px; color:var(--muted); }}
.chart {{ width:100%; height:auto; }}
.chart .grid {{ stroke:var(--line); }} .chart .tick {{ font-size:10px; fill:var(--muted); }}
.chart .threshold {{ stroke:{COLORS["threshold"]}; stroke-dasharray:5 4; stroke-width:1.5; }}
.legend {{ display:flex; flex-wrap:wrap; gap:12px; font-size:11px; color:var(--muted); }}
.legend i {{ display:inline-block; width:10px; height:10px; margin-right:4px; vertical-align:-1px; border-radius:2px; }}
.legend i.th {{ height:0; border-top:2px dashed {COLORS["threshold"]}; border-radius:0; }}
.note {{ font-size:11px; color:var(--muted); margin:4px 0 0; }}
</style></head><body>
<div class="top">
  <h1>{html.escape(dash["title"])}</h1>
  <span>time range: <b>last {dash["time_range_minutes"]} min</b> ({window.start:%Y-%m-%d %H:%M} → {window.end:%H:%M:%S} UTC)</span>
  <span>refresh: {dash["refresh_seconds"]}s</span>
  <span>source: {html.escape(str(source))} · received={c["received"]} sent={c["sent"]} failed={c["failed"]}</span>
</div>
<main class="grid">{panels}</main>
</body></html>"""


def display_path(path: Path) -> Path:
    resolved = path.resolve()
    return resolved.relative_to(REPO_ROOT) if resolved.is_relative_to(REPO_ROOT) else path


def build(config_path: Path, log_path: Path, end: datetime | None) -> tuple[dict, dict]:
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    window = Window.ending_at(end or datetime.now(timezone.utc), config["dashboard"]["time_range_minutes"])
    return config, compute(load_records(log_path), window)


def summary_text(config: dict, data: dict) -> str:
    w: Window = data["window"]
    lines = [f"Window: {w.start:%Y-%m-%d %H:%M} -> {w.end:%Y-%m-%d %H:%M:%S} UTC", f"Counts: {data['counts']}"]
    for panel in config["dashboard"]["panels"]:
        ok = threshold_ok(threshold_value(data, panel), panel["threshold"])
        values = {k: (round(v, 4) if isinstance(v, float) else v) for k, v in data[panel["id"]].items() if not k.startswith("series")}
        lines.append(f"[{'OK' if ok else 'BREACH' if ok is False else 'NO DATA'}] {panel['id']}: {values}")
    return "\n".join(lines)


def main() -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--logs", type=Path, default=REPO_ROOT / "data" / "logs.jsonl")
    parser.add_argument("--out", type=Path, default=REPO_ROOT / "data" / "dashboard.html")
    parser.add_argument("--end", help="Mốc cuối cửa sổ (ISO, UTC). Mặc định: bây giờ.")
    parser.add_argument("--summary", action="store_true", help="In số liệu 6 panel ra terminal")
    parser.add_argument("--serve", action="store_true", help="Chạy HTTP server, render lại mỗi request")
    parser.add_argument("--port", type=int, default=8050)
    args = parser.parse_args()
    end = parse_ts(args.end) if args.end else None

    if args.serve:
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # noqa: N802
                config, data = build(args.config, args.logs, end)
                body = render_html(config, data, display_path(args.logs)).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        print(f"Dashboard: http://127.0.0.1:{args.port}")
        ThreadingHTTPServer(("127.0.0.1", args.port), Handler).serve_forever()
        return 0

    config, data = build(args.config, args.logs, end)
    if args.summary:
        print(summary_text(config, data))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(render_html(config, data, display_path(args.logs)), encoding="utf-8")
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
