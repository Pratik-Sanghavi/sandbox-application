FROM localhost:5000/sandbox/mitmproxy:0.1.0
COPY sandbox_routing.py /addons/sandbox_routing.py
USER 1001:1001
ENTRYPOINT ["mitmdump", "--mode", "transparent", "--listen-host", "127.0.0.1", "--listen-port", "8080", "--set", "confdir=/var/run/sandbox-mitmproxy", "--set", "connection_strategy=lazy", "-s", "/addons/sandbox_routing.py"]
