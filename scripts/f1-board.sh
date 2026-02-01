#!/bin/bash
set -e  # Exit immediately if any command fails

DOCKER_COMPOSE_FILENAME="docker-compose.prod.yml"
PROJECT_DIR="/home/giraycoskun/Code/f1-board"
GIT_REPO="https://github.com/giraycoskun/f1-board.git"

export PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

echo "--- Ensuring project directory exists ---"
if [ ! -d "$PROJECT_DIR" ]; then
    echo "Directory does not exist. Creating and cloning repository..."
    mkdir -p "$PROJECT_DIR"
    git clone https://${GITHUB_TOKEN}@github.com/giraycoskun/f1-board.git "$PROJECT_DIR"
else
    echo "Directory exists."
fi

echo "--- Changing directory to f1-board ---"
cd "$PROJECT_DIR"

echo "--- Pulling latest changes from Git ---"
git pull "https://${GITHUB_TOKEN}@github.com/giraycoskun/f1-board.git" main

echo "--- Stopping existing Docker containers ---"
docker-compose -f $DOCKER_COMPOSE_FILENAME down

echo "--- Pulling latest Docker images ---"
docker-compose -f $DOCKER_COMPOSE_FILENAME pull

echo "--- Starting Docker containers ---"
docker-compose -f $DOCKER_COMPOSE_FILENAME up -d

docker-compose -f $DOCKER_COMPOSE_FILENAME ps

echo "--- f1-board is Updated ---"