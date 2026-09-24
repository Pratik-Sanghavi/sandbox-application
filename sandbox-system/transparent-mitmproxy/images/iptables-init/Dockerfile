FROM alpine@sha256:4bcff63911fcb4448bd4fdacec207030997caf25e9bea4045fa6c8c44de311d1
RUN apk add --no-cache iptables
USER 65532:65532
ENTRYPOINT ["sh", "-c", "iptables -t nat -A OUTPUT -p tcp --dport 443 -m owner ! --uid-owner 1001 -j REDIRECT --to-ports 8080"]
