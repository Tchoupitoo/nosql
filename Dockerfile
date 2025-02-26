FROM python:3.12 AS builder

RUN apt-get update && apt-get install -y \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.12-slim

RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid appuser --shell /bin/bash appuser \
    && mkdir -p /app/logs \
    && chown -R appuser:appuser /app \
    && apt-get update && apt-get install -y \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/

COPY --chown=appuser:appuser ./app/ /app/

VOLUME /app/logs

USER appuser

EXPOSE 5000

ENTRYPOINT ["python", "-m", "app"]