# syntax=docker/dockerfile:1

FROM python:3.14-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt ./

# requirements.txt currently doesn't include fastapi, but the app imports it.
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir fastapi

COPY api.py ./
COPY convertToJSON.py ./
COPY dashboard.py ./
COPY seed_mongo.py ./
COPY data ./data

EXPOSE 8000

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
