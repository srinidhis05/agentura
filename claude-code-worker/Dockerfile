FROM python:3.12-slim

# Node.js 20 for Claude Code CLI (bundled with claude-agent-sdk)
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN groupadd --gid 1000 worker && \
    useradd --uid 1000 --gid worker --create-home worker

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py .

RUN mkdir -p /home/worker/workspace && chown -R worker:worker /home/worker

EXPOSE 8080

USER worker

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
