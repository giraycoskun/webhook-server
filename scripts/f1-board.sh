#!/bin/bash
set -e  # Exit immediately if any command fails

DOCKER_COMPOSE_FILENAME="docker-compose.prod.yml"

export PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

echo "--- Changing directory to f1-board ---"
cd /home/giraycoskun/Code/f1-board

echo "--- Stopping existing Docker containers ---"
docker-compose -f $DOCKER_COMPOSE_FILENAME down

echo "--- Pulling latest Docker images ---"
docker-compose -f $DOCKER_COMPOSE_FILENAME pull

echo "--- Starting Docker containers ---"
docker-compose -f $DOCKER_COMPOSE_FILENAME up -d

docker-compose -f $DOCKER_COMPOSE_FILENAME ps

echo "--- f1-board is Updated ---"
