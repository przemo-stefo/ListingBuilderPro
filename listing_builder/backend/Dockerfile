# listing_builder/backend/Dockerfile
# Purpose: Production image for Render deployment
# NOT for: Local development (use uvicorn --reload directly)

FROM python:3.11-slim

WORKDIR /app

# WHY: System deps for psycopg2-binary
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# WHY: Skip Playwright — scraping runs via n8n, not in this API
RUN grep -v 'playwright' requirements.txt > requirements-prod.txt && \
    pip install --no-cache-dir -r requirements-prod.txt

COPY . .

EXPOSE ${PORT:-8000}

# WHY: Render sets $PORT at runtime
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
