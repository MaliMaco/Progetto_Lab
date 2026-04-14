FROM python:3.14-slim

WORKDIR /app

COPY src /app

RUN pip install -r requirements.txt

EXPOSE 8003

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8003"]