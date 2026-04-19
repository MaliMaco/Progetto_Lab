FROM python:3.13.12-slim

WORKDIR /app

COPY src /app
COPY templates /app/templates

RUN pip install -r requirements.txt

EXPOSE 8004

CMD ["uvicorn", "frontend:app", "--host", "0.0.0.0", "--port", "8004"]