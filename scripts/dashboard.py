from __future__ import annotations

import argparse
import html
import json
import math
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOGS = ROOT / "data" / "logs.jsonl"
DEFAULT_CONFIG = ROOT / "config" / "dashboard.yaml"
COLORS = ("#2563eb", "#e11d48", "#059669", "#9333ea")
CSS = """
:root { font-family: Segoe UI, Arial, sans-serif; color: #142033; background: #eef2f7; }
* { box-sizing: border-box; }
body { margin: 0; }
header { padding: 22px max(24px, calc((100vw - 1440px) / 2)); background: #12243a; color: #f8fafc; }
header h1 { margin: 0 0 8px; font-size: 24px; }
header p { margin: 4px 0; color: #cbd5e1; font-size: 13px; }
main { max-width: 1440px; margin: 20px auto; padding: 0 20px 30px; }
.overview { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 16px; }
.overview span { background: white; border: 1px solid #dbe3ee; border-radius: 8px; padding: 9px 12px; font-size: 12px; color: #475569; }
.grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; }
.panel { min-width: 0; background: white; border: 1px solid #dbe3ee; border-radius: 12px; padding: 16px 18px 12px; box-shadow: 0 2px 8px #0f172a0a; }
.panel h2 { margin: 0 0 2px; font-size: 17px; }
.unit { color: #64748b; font-size: 12px; }
.metrics { display: flex; flex-wrap: wrap; gap: 8px; margin: 14px 0 4px; }
.metric { background: #f1f5f9; border-radius: 7px; padding: 7px 10px; min-width: 105px; }
.metric strong { display: block; color: #0f172a; font-size: 16px; font-variant-numeric: tabular-nums; }
.metric small { color: #64748b; font-size: 10px; text-transform: uppercase; letter-spacing: .04em; }
.chart { width: 100%; overflow: hidden; }
.chart svg { display: block; width: 100%; height: auto; }
.thresholds { display: flex; flex-wrap: wrap; gap: 7px; margin: 5px 0 0; }
.threshold { border: 1px solid #dbe3ee; border-radius: 999px; padding: 4px 8px; color: #475569; font-size: 11px; }
.meta { margin: 10px 0 0; color: #94a3b8; font-size: 10px; }
footer { color: #64748b; font-size: 11px; margin-top: 16px; }
@media (max-width: 920px) { .grid { grid-template-columns: 1fr; } main { margin-top: 12px; padding: 0 12px 20px; } }
"""


def timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return (parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)).astimezone(timezone.utc)


def number(row: dict[str, Any], key: str) -> float | None:
    value = row.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def percentile(values: list[float], percent: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    rank = max(1, math.ceil(percent * len(ordered) / 100))
    return ordered[min(rank, len(ordered)) - 1]


def average(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def read_records(path: Path, now: datetime) -> list[tuple[dict[str, Any], datetime]]:
    if not path.exists():
        return []
    start = now - timedelta(minutes=60)
    result = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(row, dict):
            continue
        ts = timestamp(row.get("ts"))
        if ts is not None and start <= ts <= now:
            result.append((row, ts))
    return result


def aggregate(records: list[tuple[dict[str, Any], datetime]], now: datetime):
    start = (now - timedelta(minutes=60)).replace(second=0, microsecond=0)
    end = now.replace(second=0, microsecond=0)
    minute_count = int((end - start).total_seconds() // 60) + 1
    minutes = [start + timedelta(minutes=i) for i in range(minute_count)]
    by_minute: dict[datetime, list[dict[str, Any]]] = defaultdict(list)
    for row, ts in records:
        by_minute[ts.replace(second=0, microsecond=0)].append(row)

    responses = [row for row, _ in records if row.get("event") == "response_sent"]
    requests = [row for row, _ in records if row.get("event") == "request_received"]
    failures = [row for row, _ in records if row.get("event") == "request_failed"]
    tool_events = [row for row, _ in records if isinstance(row.get("tool_success"), bool)]
    tool_successes = [row for row in tool_events if row.get("tool_success") is True]

    def values(bucket: datetime, event: str, field: str) -> list[float]:
        return [
            val
            for row in by_minute.get(bucket, [])
            if row.get("event") == event
            if (val := number(row, field)) is not None
        ]

    traffic, p50, p95, p99, ttft = [], [], [], [], []
    error_rate, retrieval_rate, cost, token_in, token_out, quality = [], [], [], [], [], []
    for minute in minutes:
        items = by_minute.get(minute, [])
        request_count = sum(row.get("event") == "request_received" for row in items)
        failure_count = sum(row.get("event") == "request_failed" for row in items)
        tools = [row for row in items if isinstance(row.get("tool_success"), bool)]
        latency_values = values(minute, "response_sent", "latency_ms")
        ttft_values = values(minute, "response_sent", "ttft_ms")
        traffic.append(float(request_count))
        p50.append(percentile(latency_values, 50))
        p95.append(percentile(latency_values, 95))
        p99.append(percentile(latency_values, 99))
        ttft.append(percentile(ttft_values, 95))
        error_rate.append(100 * failure_count / request_count if request_count else None)
        retrieval_rate.append(
            100 * sum(row.get("tool_success") is True for row in tools) / len(tools)
            if tools else None
        )
        cost.append(sum(values(minute, "response_sent", "cost_usd")))
        token_in.append(sum(values(minute, "response_sent", "tokens_in")))
        token_out.append(sum(values(minute, "response_sent", "tokens_out")))
        quality.append(average(values(minute, "response_sent", "quality_score")))

    cumulative_cost, cumulative_in, cumulative_out = [], [], []
    cost_sum = in_sum = out_sum = 0.0
    for minute_cost, minute_in, minute_out in zip(cost, token_in, token_out):
        cost_sum += minute_cost
        in_sum += minute_in
        out_sum += minute_out
        cumulative_cost.append(cost_sum)
        cumulative_in.append(in_sum)
        cumulative_out.append(out_sum)

    latency_all = [v for row in responses if (v := number(row, "latency_ms")) is not None]
    ttft_all = [v for row in responses if (v := number(row, "ttft_ms")) is not None]
    quality_all = [v for row in responses if (v := number(row, "quality_score")) is not None]
    summary = {
        "latency": {
            "P50": percentile(latency_all, 50), "P95": percentile(latency_all, 95),
            "P99": percentile(latency_all, 99), "TTFT P95": percentile(ttft_all, 95),
        },
        "traffic": {"Requests": len(requests), "Average rate": len(requests) / 60},
        "errors": {
            "Error rate": 100 * len(failures) / len(requests) if requests else None,
            "Retrieval success": 100 * len(tool_successes) / len(tool_events) if tool_events else None,
        },
        "cost": {"Window total": cost_sum},
        "tokens": {"Input total": in_sum, "Output total": out_sum},
        "quality": {"Window mean": average(quality_all)},
    }
    charts = {
        "latency": [("P50", p50), ("P95", p95), ("P99", p99), ("TTFT P95", ttft)],
        "traffic": [("Requests/min", traffic)],
        "errors": [("Error rate", error_rate), ("Retrieval success", retrieval_rate)],
        "cost": [("Cumulative cost", cumulative_cost)],
        "tokens": [("Input tokens", cumulative_in), ("Output tokens", cumulative_out)],
        "quality": [("Mean quality", quality)],
    }
    return minutes, charts, summary


def fmt(value: float | int | None, unit: str) -> str:
    if value is None:
        return "—"
    if unit == "usd":
        return "$" + format(value, ".4f")
    if unit == "percent":
        return f"{value:.1f}%"
    if unit == "tokens":
        return f"{value:,.0f}"
    if unit == "score_0_to_1":
        return f"{value:.2f}"
    if unit == "requests_per_minute":
        return f"{value:.2f}"
    if unit == "requests":
        return f"{value:.0f}"
    return f"{value:,.0f}"


def axis_fmt(value: float, unit: str) -> str:
    if unit == "usd":
        return "$" + format(value, ".3f")
    if unit == "percent":
        return f"{value:.0f}%"
    if unit == "tokens":
        return f"{value / 1000:.0f}k" if value >= 1000 else f"{value:.0f}"
    if unit == "score_0_to_1":
        return f"{value:.2f}"
    return f"{value:.1f}" if unit == "requests_per_minute" else f"{value:.0f}"


def svg_chart(minutes, series, thresholds, unit: str) -> str:
    width, height, left, right, top, bottom = 760, 245, 60, 130, 18, 42
    plot_width, plot_height = width - left - right, height - top - bottom
    data_values = [float(v) for _, values_ in series for v in values_ if v is not None]
    data_values.extend(float(item["value"]) for item in thresholds)
    ymax = max(data_values, default=1.0)
    ymin = min(data_values, default=0.0)
    if unit == "score_0_to_1":
        ymin, ymax = 0.0, 1.0
    else:
        ymin = min(0.0, ymin)
        ymax = ymax * 1.12 if ymax > 0 else 1.0
    if ymax <= ymin:
        ymax = ymin + 1
    x = lambda index: left + plot_width * index / max(1, len(minutes) - 1)
    y = lambda value: top + plot_height * (ymax - value) / (ymax - ymin)
    out = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="Metric trend">']
    for tick in range(5):
        value = ymin + (ymax - ymin) * tick / 4
        yy = y(value)
        out.append(f'<line x1="{left}" y1="{yy:.1f}" x2="{left + plot_width}" y2="{yy:.1f}" stroke="#e2e8f0"/>')
        out.append(f'<text x="{left - 8}" y="{yy + 4:.1f}" text-anchor="end" fill="#64748b" font-size="10">{html.escape(axis_fmt(value, unit))}</text>')
    for threshold in thresholds:
        yy = y(float(threshold["value"]))
        out.append(f'<line x1="{left}" y1="{yy:.1f}" x2="{left + plot_width}" y2="{yy:.1f}" stroke="#dc2626" stroke-width="1.5" stroke-dasharray="6 5"/>')
    for series_index, (name, points) in enumerate(series):
        color, segment, segments = COLORS[series_index % len(COLORS)], [], []
        for index, value in enumerate(points):
            if value is None:
                if segment:
                    segments.append(segment)
                    segment = []
                continue
            segment.append(f"{x(index):.1f},{y(float(value)):.1f}")
        if segment:
            segments.append(segment)
        for coordinates in segments:
            if len(coordinates) == 1:
                xx, yy = coordinates[0].split(",")
                out.append(f'<circle cx="{xx}" cy="{yy}" r="3" fill="{color}"/>')
            else:
                out.append(f'<polyline points="{" ".join(coordinates)}" fill="none" stroke="{color}" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/>')
    for index in sorted({0, len(minutes) // 4, len(minutes) // 2, 3 * len(minutes) // 4, len(minutes) - 1}):
        if minutes:
            out.append(f'<text x="{x(index):.1f}" y="{height - 12}" text-anchor="middle" fill="#64748b" font-size="10">{minutes[index].strftime("%H:%MZ")}</text>')
    legend_y = top + 12
    for index, (name, _) in enumerate(series):
        yy, color = legend_y + index * 17, COLORS[index % len(COLORS)]
        out.append(f'<line x1="{width - right + 12}" y1="{yy}" x2="{width - right + 28}" y2="{yy}" stroke="{color}" stroke-width="2.5"/>')
        out.append(f'<text x="{width - right + 34}" y="{yy + 4}" fill="#475569" font-size="10">{html.escape(name)}</text>')
    if thresholds:
        yy = legend_y + len(series) * 17
        out.append(f'<line x1="{width - right + 12}" y1="{yy}" x2="{width - right + 28}" y2="{yy}" stroke="#dc2626" stroke-width="1.5" stroke-dasharray="5 4"/>')
        out.append(f'<text x="{width - right + 34}" y="{yy + 4}" fill="#475569" font-size="10">Threshold</text>')
    out.append("</svg>")
    return "".join(out)


def metrics_for(panel_id: str, summary: dict[str, Any]):
    keys = {
        "latency": [("P50", "P50", "ms"), ("P95", "P95", "ms"), ("P99", "P99", "ms"), ("TTFT P95", "TTFT P95", "ms")],
        "traffic": [("Requests", "Requests", "requests"), ("Average rate", "Average rate", "requests_per_minute")],
        "errors": [("Error rate", "Error rate", "percent"), ("Retrieval success", "Retrieval success", "percent")],
        "cost": [("Window cost", "Window total", "usd")],
        "tokens": [("Input total", "Input total", "tokens"), ("Output total", "Output total", "tokens")],
        "quality": [("Window mean", "Window mean", "score_0_to_1")],
    }
    return [(label, summary[panel_id].get(key), unit) for label, key, unit in keys[panel_id]]


def threshold_label(item: dict[str, Any], unit: str) -> str:
    op = "≤" if item["operator"] == "lte" else "≥"
    return f'{item["aggregation"]}: {op} {fmt(float(item["value"]), unit)}'


def render_panel(panel, minutes, charts, summary) -> str:
    panel_id, unit = panel["id"], panel["unit"]
    thresholds = [panel["threshold"], *panel.get("additional_thresholds", [])]
    metrics = "".join(
        f'<div class="metric"><strong>{html.escape(fmt(value, metric_unit))}</strong><small>{html.escape(label)}</small></div>'
        for label, value, metric_unit in metrics_for(panel_id, summary)
    )
    threshold_html = "".join(
        f'<span class="threshold">Threshold: {html.escape(threshold_label(t, unit))}</span>'
        for t in thresholds
    )
    return (
        f'<section class="panel"><h2>{html.escape(panel["title"])}</h2>'
        f'<div class="unit">Unit: {html.escape(unit)}</div><div class="metrics">{metrics}</div>'
        f'<div class="chart">{svg_chart(minutes, charts[panel_id], thresholds, unit)}</div>'
        f'<div class="thresholds">{threshold_html}</div>'
        f'<p class="meta">Source: {html.escape(panel["source"])} · Window: 60 minutes · Refresh: 30 seconds · UTC</p></section>'
    )


def make_page(log_path: Path, config_path: Path, now: datetime | None = None) -> str:
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))["dashboard"]
    records = read_records(log_path, now)
    minutes, charts, summary = aggregate(records, now)
    panels = "".join(render_panel(p, minutes, charts, summary) for p in config["panels"])
    updated = now.strftime("%Y-%m-%d %H:%M:%S UTC")
    log_label = str(log_path.relative_to(ROOT)) if log_path.is_relative_to(ROOT) else str(log_path)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="{int(config['refresh_seconds'])}"><title>{html.escape(config['title'])}</title>
<style>{CSS}</style></head><body><header><h1>{html.escape(config['title'])}</h1>
<p>Structured-log operational view · Updated {updated}</p>
<p>Time range: {int(config['time_range_minutes'])} minutes · Refresh: {int(config['refresh_seconds'])} seconds · Timestamps are UTC</p></header>
<main><div class="overview"><span>Records in window: <strong>{len(records)}</strong></span>
<span>Requests: <strong>{summary['traffic']['Requests']}</strong></span><span>Source: <strong>{html.escape(log_label)}</strong></span></div>
<div class="grid">{panels}</div><footer>Percentiles use nearest-rank. Retrieval success uses every event with a boolean tool_success field, including response_sent and request_failed.</footer></main>
</body></html>"""


class DashboardHandler(BaseHTTPRequestHandler):
    log_path = DEFAULT_LOGS
    config_path = DEFAULT_CONFIG

    def do_GET(self) -> None:
        route = urlparse(self.path).path
        if route == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return
        if route != "/":
            self.send_error(404)
            return
        try:
            body = make_page(self.log_path, self.config_path).encode("utf-8")
            status = 200
        except (OSError, KeyError, TypeError, yaml.YAMLError) as exc:
            body = ("<!doctype html><meta charset='utf-8'><h1>Dashboard error</h1><pre>"
                    + html.escape(str(exc)) + "</pre>").encode("utf-8")
            status = 500
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format_string: str, *args: Any) -> None:
        return


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve the six-panel structured-log dashboard")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8050)
    parser.add_argument("--logs", type=Path, default=DEFAULT_LOGS)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args()
    DashboardHandler.log_path = args.logs.resolve()
    DashboardHandler.config_path = args.config.resolve()
    server = ThreadingHTTPServer((args.host, args.port), DashboardHandler)
    print(f"Dashboard: http://{args.host}:{args.port}/")
    print(f"Logs: {DashboardHandler.log_path}")
    print("Press Ctrl+C to stop; the page refreshes every 30 seconds.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping dashboard.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
