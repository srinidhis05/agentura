FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY . .

RUN uv sync

EXPOSE 8097

CMD ["uv", "run", "src/metabase_mcp_server.py", "--transport", "streamable-http", "--host", "0.0.0.0", "--port", "8097"]
