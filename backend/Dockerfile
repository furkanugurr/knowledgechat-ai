FROM python:3.12-slim

WORKDIR /workspace/backend

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY scripts ./scripts
COPY data ./data

CMD ["sh", "-c", "uvicorn app.main:app --host \"$HOST\" --port \"$PORT\""]
