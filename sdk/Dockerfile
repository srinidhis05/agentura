FROM python:3.12-slim AS builder

WORKDIR /build
COPY pyproject.toml .
COPY agentura_sdk/ agentura_sdk/

RUN pip install --no-cache-dir ".[server,sandbox]" && \
    pip install --no-cache-dir graphifyy 2>/dev/null || true

FROM python:3.12-slim

# git is required for the git_codebase tool
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*

# No Node.js needed — Claude Code runs in isolated worker pods
RUN groupadd --gid 1000 agentura && \
    useradd --uid 1000 --gid agentura --create-home agentura

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin/agentura-server /usr/local/bin/agentura-server
COPY --from=builder /build/agentura_sdk/ /app/agentura_sdk/

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh \
    && mkdir -p /data/.agentura /skills /codebase/vance-android /codebase/vance-ios \
    && chown -R 1000:1000 /data

ENV SKILLS_DIR=/skills/skills \
    AGENTURA_KNOWLEDGE_DIR=/data/.agentura \
    HOST=0.0.0.0 \
    PORT=8000 \
    UVICORN_WORKERS=4

EXPOSE 8000

USER agentura

ENTRYPOINT ["/entrypoint.sh"]
