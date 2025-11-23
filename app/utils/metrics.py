"""Prometheus metrics for monitoring."""

from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response

# Define metrics
request_count = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

request_duration = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)

chat_requests = Counter(
    "chat_requests_total",
    "Total chat requests",
    ["provider", "model"],
)

chat_tokens = Counter(
    "chat_tokens_total",
    "Total tokens used",
    ["provider", "model"],
)

error_count = Counter(
    "errors_total",
    "Total errors",
    ["error_type"],
)


def get_metrics() -> Response:
    """Get Prometheus metrics."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
