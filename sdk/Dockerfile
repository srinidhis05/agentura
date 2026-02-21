FROM python:3.12-slim AS builder

WORKDIR /build
COPY pyproject.toml .
COPY aspora_sdk/ aspora_sdk/

RUN pip install --no-cache-dir ".[server]"

FROM python:3.12-slim

RUN groupadd --gid 1000 aspora && \
    useradd --uid 1000 --gid aspora --create-home aspora

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin/aspora-server /usr/local/bin/aspora-server
COPY --from=builder /build/aspora_sdk/ /app/aspora_sdk/

VOLUME /skills
VOLUME /data/.aspora

ENV SKILLS_DIR=/skills \
    ASPORA_KNOWLEDGE_DIR=/data/.aspora \
    HOST=0.0.0.0 \
    PORT=8000

EXPOSE 8000

USER aspora

ENTRYPOINT ["aspora-server"]
