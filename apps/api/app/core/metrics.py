"""Minimal, dependency-free in-process metrics (Prometheus text exposition).

Low-cardinality by design: labelled only by method + status class, never by raw
path, so the series count stays bounded. For multi-process deployments use this as
a per-instance signal or swap in prometheus_client with a multiprocess collector.
"""

from __future__ import annotations

import threading
from collections import defaultdict

_lock = threading.Lock()
_requests_total: dict[tuple[str, str], int] = defaultdict(int)
_duration_sum_ms: dict[str, float] = defaultdict(float)
_duration_count: dict[str, int] = defaultdict(int)


def record_request(method: str, status_code: int, duration_ms: float) -> None:
    status_class = f"{status_code // 100}xx"
    with _lock:
        _requests_total[(method, status_class)] += 1
        _duration_sum_ms[method] += duration_ms
        _duration_count[method] += 1


def render_prometheus() -> str:
    lines = [
        "# HELP http_requests_total Total HTTP requests by method and status class.",
        "# TYPE http_requests_total counter",
    ]
    with _lock:
        for (method, status_class), count in sorted(_requests_total.items()):
            lines.append(f'http_requests_total{{method="{method}",status="{status_class}"}} {count}')
        lines.append("# HELP http_request_duration_ms_sum Sum of request durations (ms) by method.")
        lines.append("# TYPE http_request_duration_ms_sum counter")
        for method, total in sorted(_duration_sum_ms.items()):
            lines.append(f'http_request_duration_ms_sum{{method="{method}"}} {total:.2f}')
        lines.append("# HELP http_request_duration_ms_count Request count by method.")
        lines.append("# TYPE http_request_duration_ms_count counter")
        for method, count in sorted(_duration_count.items()):
            lines.append(f'http_request_duration_ms_count{{method="{method}"}} {count}')
    return "\n".join(lines) + "\n"


def reset_metrics() -> None:
    with _lock:
        _requests_total.clear()
        _duration_sum_ms.clear()
        _duration_count.clear()
