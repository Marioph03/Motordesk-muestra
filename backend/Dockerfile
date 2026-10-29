FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python scripts/check_text_encoding.py

EXPOSE 8000

CMD ["sh", "-c", "python -m app.database.bootstrap && exec uvicorn app.main:app --host 0.0.0.0 --port 8000"]
