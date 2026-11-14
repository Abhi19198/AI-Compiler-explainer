# Backend only: FastAPI + Claude-powered code explainer.
FROM python:3.12-slim

WORKDIR /app

COPY ai-code-explainer/backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ai-code-explainer/backend/ .

# The app reads ANTHROPIC_API_KEY at request time (never baked into the image).
ENV ANTHROPIC_API_KEY=""
ENV CORS_ORIGINS="http://localhost:5500,http://127.0.0.1:5500"

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
