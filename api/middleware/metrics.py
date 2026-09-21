"""Prometheus metrics collector and middleware."""

import threading
import time
from collections import defaultdict
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

_lock = threading.Lock()
_request_counts: dict[tuple[str, str, int], int] = defaultdict(int)
_request_durations: dict[tuple[str, str], list[float]] = defaultdict(list)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Collect HTTP request metrics for Prometheus exposition."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        start_time = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            duration = time.perf_counter() - start_time
            endpoint = request.url.path
            method = request.method
            with _lock:
                _request_counts[(method, endpoint, status_code)] += 1
                durations = _request_durations[(method, endpoint)]
                # Keep last 500 observations to bound memory
                if len(durations) >= 500:
                    durations.pop(0)
                durations.append(duration)


def render_prometheus_metrics() -> str:
    """Render metrics in standard Prometheus text format."""
    lines: list[str] = [
        "# HELP http_requests_total Total number of HTTP requests processed",
        "# TYPE http_requests_total counter",
    ]
    with _lock:
        for (method, endpoint, status), count in sorted(_request_counts.items()):
            metric_label = f'method="{method}",endpoint="{endpoint}",status="{status}"'
            lines.append(f"http_requests_total{{{metric_label}}} {count}")

        lines.append(
            "# HELP http_request_duration_seconds HTTP request latencies in seconds (average)"
        )
        lines.append("# TYPE http_request_duration_seconds gauge")
        for (method, endpoint), durations in sorted(_request_durations.items()):
            if durations:
                avg_duration = sum(durations) / len(durations)
                label = f'method="{method}",endpoint="{endpoint}"'
                lines.append(f"http_request_duration_seconds{{{label}}} {avg_duration:.6f}")

    lines.append("")
    return "\n".join(lines)


def reset_metrics() -> None:
    """Reset in-memory metrics (primarily for test isolation)."""
    with _lock:
        _request_counts.clear()
        _request_durations.clear()
