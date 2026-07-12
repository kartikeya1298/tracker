# Pinned to bookworm (Debian 12), not the floating python:3.12-slim tag: that tag
# recently moved to trixie (Debian 13), which playwright==1.49.1 doesn't recognize -
# it falls back to an Ubuntu 20.04 dependency mapping whose font package names
# (ttf-unifont, ttf-ubuntu-font-family) don't exist in trixie's repos, so
# `playwright install --with-deps chromium` fails with "no installation candidate".
FROM python:3.12-slim-bookworm

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && playwright install --with-deps chromium

COPY app ./app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
