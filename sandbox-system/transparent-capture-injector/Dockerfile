FROM python:3.13-alpine

WORKDIR /app
COPY webhook.py /app/webhook.py

USER 65532:65532
EXPOSE 8443
ENTRYPOINT ["python", "/app/webhook.py"]
