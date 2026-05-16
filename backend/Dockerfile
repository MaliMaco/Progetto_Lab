FROM python:3.13.12-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN apt-get update && apt-get install -y \
    gcc libmariadb-dev \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -r requirements.txt
RUN crawl4ai-setup

COPY gs_data/ ./gs_data/
COPY backend/src/ ./backend/src/
COPY domains.json .

EXPOSE 8003

ENV PYTHONPATH=/app/backend/src

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8003"]