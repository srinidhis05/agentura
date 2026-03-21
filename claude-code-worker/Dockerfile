FROM python:3.12-slim

# Node.js 20 for Claude Code CLI (bundled with claude-agent-sdk) + git + gh
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates git && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" > /etc/apt/sources.list.d/github-cli.list && \
    apt-get update && apt-get install -y --no-install-recommends gh && \
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
