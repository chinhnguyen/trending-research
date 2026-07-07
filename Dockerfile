FROM node:22-bookworm-slim AS web-build
WORKDIR /app/web

COPY web/package.json web/package-lock.json ./
RUN npm ci

COPY web/ ./
RUN npm run build


FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src ./src
COPY config ./config
COPY specs ./specs
COPY --from=web-build /app/web/dist ./web/dist

RUN pip install --no-cache-dir .

RUN mkdir -p /app/data

ENV WILLBE_WEB_DIST=/app/web/dist

EXPOSE 8000

CMD ["uvicorn", "willbe_trends.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
