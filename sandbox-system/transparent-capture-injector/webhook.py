"""Inject the transparent outbound-capture components into sandbox Pods."""
import base64
import json
import os
import ssl
from http.server import BaseHTTPRequestHandler, HTTPServer


RUNTIME_VOLUME = {"name": "sandbox-mitmproxy-runtime", "emptyDir": {}}
CA_VOLUME = {
    "name": "sandbox-mitmproxy-ca",
    "secret": {"secretName": "sandbox-mitmproxy-ca"},
}
IPTABLES_INIT = {
    "name": "sandbox-iptables",
    "image": "localhost:5000/sandbox/transparent-iptables-init:0.1.0",
    "securityContext": {
        "runAsUser": 0,
        "allowPrivilegeEscalation": False,
        "capabilities": {"add": ["NET_ADMIN"]},
    },
}
CA_INIT = {
    "name": "sandbox-install-ca",
    "image": "localhost:5000/sandbox/transparent-mitmproxy:0.1.0",
    "command": [
        "sh",
        "-c",
        "cp /ca/mitmproxy-ca.pem /runtime/mitmproxy-ca.pem && chmod 0400 /runtime/mitmproxy-ca.pem",
    ],
    "securityContext": {"runAsUser": 0, "allowPrivilegeEscalation": False},
    "volumeMounts": [
        {"name": "sandbox-mitmproxy-ca", "mountPath": "/ca", "readOnly": True},
        {"name": "sandbox-mitmproxy-runtime", "mountPath": "/runtime"},
    ],
}
PROXY = {
    "name": "sandbox-mitmproxy",
    "image": "localhost:5000/sandbox/transparent-mitmproxy:0.1.0",
    "volumeMounts": [
        {"name": "sandbox-mitmproxy-runtime", "mountPath": "/var/run/sandbox-mitmproxy"}
    ],
}


def add_array(patches, spec, field, values):
    if field in spec:
        patches.extend({"op": "add", "path": f"/spec/{field}/-", "value": value} for value in values)
    else:
        patches.append({"op": "add", "path": f"/spec/{field}", "value": values})


def mutation_for(pod):
    spec = pod.get("spec", {})
    containers = spec.get("containers", [])
    if any(container.get("name") == PROXY["name"] for container in containers):
        return []
    patches = []
    add_array(patches, spec, "volumes", [RUNTIME_VOLUME, CA_VOLUME])
    add_array(patches, spec, "initContainers", [IPTABLES_INIT, CA_INIT])
    patches.append({"op": "add", "path": "/spec/containers/-", "value": PROXY})
    return patches


class AdmissionHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        review = json.loads(self.rfile.read(length))
        request = review["request"]
        patches = mutation_for(request["object"])
        response = {"uid": request["uid"], "allowed": True}
        if patches:
            response["patchType"] = "JSONPatch"
            response["patch"] = base64.b64encode(json.dumps(patches).encode()).decode()
        body = json.dumps({"apiVersion": "admission.k8s.io/v1", "kind": "AdmissionReview", "response": response}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        return


server = HTTPServer(("0.0.0.0", 8443), AdmissionHandler)
context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain("/tls/tls.crt", "/tls/tls.key")
server.socket = context.wrap_socket(server.socket, server_side=True)
server.serve_forever()
