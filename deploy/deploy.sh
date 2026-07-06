#!/bin/bash
set -e

echo "=== TMV Auto-Deploy ==="
echo "Zeitpunkt: $(date)"

cd /app

echo "Git Pull..."
git pull origin main

echo "Docker Compose rebuild (web)..."
docker compose up -d --build --remove-orphans web

echo "Docker cleanup..."
docker image prune -f

echo "=== Deploy abgeschlossen ==="
