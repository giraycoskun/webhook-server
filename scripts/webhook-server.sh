#!/bin/bash
set -euo pipefail

export PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/home/giraycoskun/.local/bin/"

PROJECT_DIR="/home/giraycoskun/Code/webhook-server"
SERVICE_NAME="webhook-server.service"
WATCH_DIR="app"

cd "$PROJECT_DIR"

echo "Fetching latest changes from git..."
git fetch https://${GITHUB_TOKEN}@github.com/giraycoskun/webhook-server.git main

# Save current commit
OLD_COMMIT=$(git rev-parse HEAD)

echo "Pulling latest changes..."
git pull https://${GITHUB_TOKEN}@github.com/giraycoskun/webhook-server.git main

# New commit after pull
NEW_COMMIT=$(git rev-parse HEAD)

# Check if app/ changed
if git diff --name-only "$OLD_COMMIT" "$NEW_COMMIT" | grep -q "^${WATCH_DIR}/"; then
    echo "Changes detected in ${WATCH_DIR}/"

    echo "Syncing dependencies with uv..."
    uv sync

    echo "Restarting $SERVICE_NAME service..."
    sudo systemd-run \
        --on-active=5s \
        --unit=webhook-restart-timer \
        --description="Restart Webhook" \
        /bin/systemctl restart "$SERVICE_NAME"

    echo "--- webhook-server restarted ---"
else
    echo "No changes in ${WATCH_DIR}/ — skipping systemd restart"
fi
