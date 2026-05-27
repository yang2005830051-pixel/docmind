FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p knowledge_base chroma_db logs

EXPOSE 8501

ARG WORKERS=1
ENV WORKERS=${WORKERS}

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/health')" || exit 1

CMD ["sh", "-c", "uvicorn server:app --host 0.0.0.0 --port 8501 --workers ${WORKERS}"]
