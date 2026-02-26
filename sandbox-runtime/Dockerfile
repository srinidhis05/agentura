FROM python:3.12-slim

RUN groupadd --gid 1000 sandbox && \
    useradd --uid 1000 --gid sandbox --create-home sandbox

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

RUN mkdir -p /home/sandbox /home/user && \
    chown sandbox:sandbox /home/sandbox /home/user

EXPOSE 8080

USER sandbox

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
