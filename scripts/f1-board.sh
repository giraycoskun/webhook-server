#!/bin/bash
set -e  # Exit immediately if any command fails

source .env

DOCKER_COMPOSE_FILENAME="docker-compose.localhost.yml"
PROJECT_DIR="/home/giraycoskun/Code/f1-board"

export PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

echo "--- Changing directory to f1-board ---"
cd "$PROJECT_DIR"

echo "--- Fetching latest changes ---"
git fetch https://${GITHUB_TOKEN}@github.com/giraycoskun/f1-board.git main

echo "--- Pulling latest changes ---"
git pull https://${GITHUB_TOKEN}@github.com/giraycoskun/f1-board.git main

echo "--- Logging into GitHub Container Registry ---"
echo "$GITHUB_TOKEN" | docker login ghcr.io -u giraycoskun --password-stdin

echo "--- Stopping existing Docker containers ---"
docker-compose -f $DOCKER_COMPOSE_FILENAME down

echo "--- Building Docker images from scratch ---"
docker-compose -f $DOCKER_COMPOSE_FILENAME build --no-cache

echo "--- Starting Docker containers ---"
docker-compose -f $DOCKER_COMPOSE_FILENAME up -d --force-recreate

docker-compose -f $DOCKER_COMPOSE_FILENAME ps

echo "--- f1-board is Updated ---"