#!/bin/bash
set -euo pipefail

PROJECT_DIR="/home/giraycoskun/Code/webhook-server"
SERVICE_NAME="webhook-server"

cd "$PROJECT_DIR"

echo "Pulling latest changes from git..."
git fetch origin
git reset --hard origin/main

echo "Syncing dependencies with uv..."
uv sync

echo "Restarting $SERVICE_NAME service..."
sudo systemctl restart "$SERVICE_NAME"

echo "Done. Service status:"
sudo systemctl status "$SERVICE_NAME" --no-pager
