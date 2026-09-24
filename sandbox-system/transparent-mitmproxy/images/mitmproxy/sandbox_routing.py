"""Observe and route transparently intercepted sandbox requests."""

import json
import re
from urllib.parse import urlsplit

from mitmproxy import ctx, http


MOCKED_HOSTS_PATH = "/etc/sandbox-mock-routing/mocked-hosts"
MOCK_NAMESPACE = "mock-servers-ns-1"
CLUSTER_DOMAIN = "cluster.local"
MOCK_PORT = 8080


def _address(connection: object) -> str | None:
    """Return a server address as host:port, when available."""
    address = getattr(connection, "address", None)
    if not address:
        return None
    host, port = address
    return f"{host}:{port}"


def _sni(flow: http.HTTPFlow) -> str | None:
    """Prefer client TLS SNI; retain a server-side fallback for compatibility."""
    return getattr(flow.client_conn, "sni", None) or getattr(flow.server_conn, "sni", None)


def _normalize_hostname(value: str | None) -> str | None:
    """Normalize an SNI or Host value into a DNS hostname."""
    if not value:
        return None
    hostname = value.lower().rstrip(".").split(":", 1)[0]
    if not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)*", hostname):
        return None
    return hostname


def _mocked_hosts() -> frozenset[str]:
    """Read the ConfigMap-mounted allowlist; blank lines and comments are ignored."""
    try:
        with open(MOCKED_HOSTS_PATH, encoding="utf-8") as host_file:
            configured_hosts = (
                _normalize_hostname(line.split("#", 1)[0].strip())
                for line in host_file
            )
            return frozenset(host for host in configured_hosts if host)
    except OSError as error:
        ctx.log.warn(f"sandbox mock routing config unavailable: {error}")
        return frozenset()


def _hostname(flow: http.HTTPFlow) -> tuple[str, str]:
    """Choose the hostname used for observation and mock routing."""
    tls_sni = _normalize_hostname(_sni(flow))
    http_host = _normalize_hostname(flow.request.headers.get("host"))
    if tls_sni:
        return tls_sni, "tls_sni"
    if http_host:
        return http_host, "http_host"
    return flow.request.host, "request_host"


def _mock_upstream(hostname: str) -> str:
    """Derive a mock Service FQDN from the intercepted external hostname."""
    service_name = hostname.replace(".", "-")
    return f"{service_name}.{MOCK_NAMESPACE}.svc.{CLUSTER_DOMAIN}"


def _route_to_mock(flow: http.HTTPFlow, hostname: str) -> str:
    """Send a decrypted request to its convention-derived in-cluster mock."""
    upstream = _mock_upstream(hostname)
    flow.request.scheme = "http"
    flow.request.host = upstream
    flow.request.port = MOCK_PORT
    flow.request.headers["Host"] = f"{upstream}:{MOCK_PORT}"
    flow.request.headers["X-Sandbox-Original-Host"] = hostname
    flow.request.headers["X-Sandbox-Original-Scheme"] = "https"
    return f"{upstream}:{MOCK_PORT}"


def request(flow: http.HTTPFlow) -> None:
    """Observe every request and route ConfigMap-allowlisted hosts in-cluster."""
    original_destination = _address(flow.server_conn)
    tls_sni = _normalize_hostname(_sni(flow))
    http_host = _normalize_hostname(flow.request.headers.get("host"))
    hostname, hostname_source = _hostname(flow)
    route = "passthrough"
    mock_upstream = None
    if hostname in _mocked_hosts():
        mock_upstream = _route_to_mock(flow, hostname)
        route = "mock"

    flow.metadata["sandbox.hostname"] = hostname
    flow.metadata["sandbox.hostname_source"] = hostname_source
    flow.metadata["sandbox.route"] = route
    ctx.log.info(
        "sandbox_request="
        + json.dumps(
            {
                "hostname": hostname,
                "hostname_source": hostname_source,
                "http_host": http_host,
                "method": flow.request.method,
                "mock_upstream": mock_upstream,
                "original_destination": original_destination,
                "path": urlsplit(flow.request.path).path,
                "route": route,
                "tls_sni": tls_sni,
            },
            sort_keys=True,
        )
    )
