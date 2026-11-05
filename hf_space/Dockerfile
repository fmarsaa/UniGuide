FROM python:3.12-slim

# HF Spaces listens on port 7860
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=7860

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy only application code (model + secrets arrive as env vars at runtime)
COPY *.py ./

# Allow the HF Spaces user (UID 1000) to write the downloaded model file
RUN mkdir -p /app && chmod -R 777 /app

EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=10s --start-period=300s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:7860/api/health')"

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port 7860"]
