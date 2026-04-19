FROM python:3.13.12-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install -r requirements.txt

COPY gs_data .
COPY backend/src ./backend/src
COPY domains.json .

EXPOSE 8003

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8003"]