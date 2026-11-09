FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir numpy==2.2.6

WORKDIR /app
COPY server.py /app/server.py
RUN mkdir -p /data

WORKDIR /data
ENTRYPOINT ["python3", "/app/server.py", "--data-dir=/data"]
