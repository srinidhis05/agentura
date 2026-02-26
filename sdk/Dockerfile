FROM python:3.12-slim AS builder

WORKDIR /build
COPY pyproject.toml .
COPY agentura_sdk/ agentura_sdk/

RUN pip install --no-cache-dir ".[server,sandbox]"

FROM python:3.12-slim

RUN groupadd --gid 1000 agentura && \
    useradd --uid 1000 --gid agentura --create-home agentura

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin/agentura-server /usr/local/bin/agentura-server
COPY --from=builder /build/agentura_sdk/ /app/agentura_sdk/

VOLUME /skills
VOLUME /data/.agentura

ENV SKILLS_DIR=/skills \
    AGENTURA_KNOWLEDGE_DIR=/data/.agentura \
    HOST=0.0.0.0 \
    PORT=8000

EXPOSE 8000

USER agentura

ENTRYPOINT ["agentura-server"]
