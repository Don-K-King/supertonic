FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    SUPERTONIC_CACHE_DIR=/models/supertonic3

RUN pip install --no-cache-dir "supertonic[serve]==1.3.1"

EXPOSE 7788

CMD ["supertonic", "serve", "--host", "0.0.0.0", "--port", "7788", "--model", "supertonic-3"]
