"""Structured JSON logging middleware for FastAPI."""

import datetime
import json
import logging
import time
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("api.access")


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """Log HTTP access events in structured JSON format."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        start_time = time.perf_counter()
        response: Response | None = None
        error_msg: str | None = None

        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            error_msg = str(exc)
            raise
        finally:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            request_id = getattr(request.state, "request_id", None) or request.headers.get(
                "X-Request-ID", "unknown"
            )
            client_ip = request.client.host if request.client else "unknown"
            status_code = response.status_code if response else 500

            log_record = {
                "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query": str(request.url.query),
                "status_code": status_code,
                "duration_ms": duration_ms,
                "client_ip": client_ip,
            }
            if error_msg:
                log_record["error"] = error_msg

            logger.info(json.dumps(log_record))
