FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    API_URL=http://localhost:8000 \
    RAG_GENERATION_PROVIDER=gemini \
    GEMINI_MODEL=gemini-2.5-flash \
    STREAMLIT_SERVER_PORT=7860 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt pyproject.toml README.md ./
COPY configs ./configs
COPY src ./src
COPY scripts/start_hf_space.sh ./scripts/start_hf_space.sh

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir -e . \
    && chmod +x ./scripts/start_hf_space.sh

EXPOSE 7860

CMD ["./scripts/start_hf_space.sh"]
