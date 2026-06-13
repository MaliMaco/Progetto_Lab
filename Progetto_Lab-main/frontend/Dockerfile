FROM python:3.13.12-slim

WORKDIR /app

COPY frontend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY frontend/src ./frontend/src
COPY frontend/templates ./frontend/templates

EXPOSE 8004

CMD ["uvicorn", "frontend.src.frontend:app", "--host", "0.0.0.0", "--port", "8004"]