#!/bin/bash
set -euo pipefail

export PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/home/giraycoskun/.local/bin/"


PROJECT_DIR="/home/giraycoskun/Code/webhook-server"
SERVICE_NAME="webhook-server.service"

cd "$PROJECT_DIR"

echo "Fetching and Pulling latest changes from git..."
git fetch https://${GITHUB_TOKEN}@github.com/giraycoskun/webhook-server.git main
git pull https://${GITHUB_TOKEN}@github.com/giraycoskun/webhook-server.git main

echo "Syncing dependencies with uv..."
uv sync

echo "Restarting $SERVICE_NAME service..."
sudo systemd-run --on-active=5s --unit=webhook-restart-timer --description="Restart Webhook" /bin/systemctl restart webhook-server

echo "--- webhook-server is updated ---"
