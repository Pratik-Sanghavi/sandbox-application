# The upstream mitmproxy 12.2.3 image mirrored into the local development registry.
# The digest prevents a tag from silently changing what this image is built from.
FROM localhost:5000/sandbox/base-mitmproxy@sha256:7f61d2d79f9c9901a47a8e6dcbf6d7ca1dd47d460f894fdc079655a010747fbb

# Keep the image ready for the non-root runtime used by the Deployment.
USER root
RUN mkdir -p /home/mitmproxy/.mitmproxy \
    && chown -R 1000:1000 /home/mitmproxy

USER 1000:1000
