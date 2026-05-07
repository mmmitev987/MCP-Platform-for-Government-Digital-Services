#!/bin/bash
# ─────────────────────────────────────────────────────────────
# GovMCP startup script
# ─────────────────────────────────────────────────────────────
#
# Development (single worker, auto-reload):
#   bash start.sh
#
# Production (multiple workers, no reload):
#   PRODUCTION=true bash start.sh
#
# Number of workers = (2 × CPU cores) + 1  is the standard formula.
# Adjust WORKERS below to match your server.
# ─────────────────────────────────────────────────────────────

WORKERS=${WORKERS:-4}

if [ "$PRODUCTION" = "true" ]; then
  echo "Starting in PRODUCTION mode with $WORKERS workers..."
  exec uvicorn backend.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers "$WORKERS" \
    --proxy-headers \
    --forwarded-allow-ips="*"
else
  echo "Starting in DEVELOPMENT mode (single worker, auto-reload)..."
  exec uvicorn backend.main:app \
    --host 127.0.0.1 \
    --port 8000 \
    --reload
fi
