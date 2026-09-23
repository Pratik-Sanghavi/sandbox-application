"""Sandbox routing hook. WireMock routes are added in the next step."""

from mitmproxy import http


def request(flow: http.HTTPFlow) -> None:
    """Observe requests; transparent mode preserves the original destination."""
    flow.metadata["sandbox.host"] = flow.request.pretty_host
