"""Observe routing identity for transparently intercepted sandbox requests."""

import json
from urllib.parse import urlsplit

from mitmproxy import ctx, http


def _address(connection: object) -> str | None:
    """Return the transparent-mode destination as host:port, when available."""
    address = getattr(connection, "address", None)
    if not address:
        return None
    host, port = address
    return f"{host}:{port}"


def _sni(flow: http.HTTPFlow) -> str | None:
    """Prefer client TLS SNI; retain a server-side fallback for compatibility."""
    return getattr(flow.client_conn, "sni", None) or getattr(flow.server_conn, "sni", None)


def request(flow: http.HTTPFlow) -> None:
    """Log routing identity without changing the request or destination."""
    tls_sni = _sni(flow)
    http_host = flow.request.headers.get("host")
    if tls_sni:
        hostname, hostname_source = tls_sni, "tls_sni"
    elif http_host:
        hostname, hostname_source = http_host, "http_host"
    else:
        hostname, hostname_source = flow.request.host, "request_host"

    flow.metadata["sandbox.hostname"] = hostname
    flow.metadata["sandbox.hostname_source"] = hostname_source
    ctx.log.info(
        "sandbox_request="
        + json.dumps(
            {
                "hostname": hostname,
                "hostname_source": hostname_source,
                "http_host": http_host,
                "method": flow.request.method,
                "original_destination": _address(flow.server_conn),
                "path": urlsplit(flow.request.path).path,
                "tls_sni": tls_sni,
            },
            sort_keys=True,
        )
    )
