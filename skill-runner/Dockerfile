FROM python:3.12-slim AS builder

WORKDIR /build
COPY sdk/pyproject.toml sdk/pyproject.toml
COPY sdk/agentura_sdk/ sdk/agentura_sdk/
COPY skill-runner/main.py skill-runner/main.py

RUN pip install --no-cache-dir "./sdk[server]"

FROM python:3.12-slim

RUN groupadd --gid 1000 agentura && \
    useradd --uid 1000 --gid agentura --create-home agentura

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /build/sdk/agentura_sdk/ /app/agentura_sdk/
COPY --from=builder /build/skill-runner/main.py /app/main.py

VOLUME /skills

ENV SKILLS_DIR=/skills

USER agentura

ENTRYPOINT ["python", "/app/main.py"]
