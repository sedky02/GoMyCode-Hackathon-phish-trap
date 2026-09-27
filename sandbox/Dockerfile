# Isolated browser for detonating phishing links.
FROM mcr.microsoft.com/playwright/python:v1.49.0-noble
WORKDIR /app
COPY sandbox/ /app/sandbox/
RUN useradd -m runner && mkdir -p /out && chown runner /out
USER runner
# Invoked as: docker run --rm --cap-drop ALL --security-opt no-new-privileges \
#   -v <shots>:/out phishtrap-sandbox python -m sandbox.worker <url> /out/<name>.png
