FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/data

# Railway uses PORT environment variable
EXPOSE $PORT

CMD uvicorn main:app --host 0.0.0.0 --port $PORT