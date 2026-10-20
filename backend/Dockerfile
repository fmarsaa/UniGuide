FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PORT=8080
WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

# Code only. The trained model, the Firebase key and .env are never baked into the image
# (see .dockerignore): the server downloads the model at start from MODEL_URL and checks
# MODEL_SHA256, and the Firebase key arrives as the secret FIREBASE_SERVICE_ACCOUNT_JSON.
COPY *.py ./

RUN useradd --create-home appuser && chown -R appuser /app
USER appuser

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=120s \
  CMD python -c "import os,urllib.request;urllib.request.urlopen('http://127.0.0.1:%s/api/health' % os.environ.get('PORT','8080'))"

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
