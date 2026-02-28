FROM python:3.12-slim

RUN groupadd --gid 1000 worker && \
    useradd --uid 1000 --gid worker --create-home worker

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py .

EXPOSE 8080

USER worker

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
