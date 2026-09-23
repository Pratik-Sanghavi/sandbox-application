# Sandbox mitmproxy

This is the explicit-proxy baseline for the outbound API sandbox. It does not alter DNS or transparently capture traffic. A later workload test will opt in with `HTTPS_PROXY` and the sandbox public CA.

## Local image delivery

The encrypted `sandbox-ca.secret.sops.yaml` contains the private sandbox CA. It is rendered only by the Argo CD SOPS plugin and mounted read-only; the init container copies it into a writable mitmproxy runtime directory with mode `0400`.
