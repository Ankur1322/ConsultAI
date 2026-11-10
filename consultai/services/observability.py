import logging
import time
from collections.abc import Awaitable, Callable

from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("consultai")
_metrics: dict[str, int | float] = {
    "requests_total": 0,
    "model_calls_total": 0,
    "retrieval_calls_total": 0,
    "citation_supported_total": 0,
    "citation_unsupported_total": 0,
    "human_reviews_total": 0,
}


def increment(name: str, amount: int = 1) -> None:
    _metrics[name] = int(_metrics.get(name, 0)) + amount


def metrics_snapshot() -> dict[str, int | float]:
    return dict(_metrics)


async def request_metrics(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    started = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - started) * 1000, 2)
    increment("requests_total")
    logger.info(
        "request_complete method=%s path=%s status=%s duration_ms=%s",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response
