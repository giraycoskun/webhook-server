#!/bin/bash
set -e  # Exit immediately if any command fails

echo "--- Fetching latest changes ---"
git fetch https://${GITHUB_TOKEN}@github.com/giraycoskun/server.giraycoskun.dev.git main

echo "--- Pulling latest changes ---"
git pull https://${GITHUB_TOKEN}@github.com/giraycoskun/server.giraycoskun.dev.git main

echo "--- Installing deps ---"
pnpm install

echo "--- Building project with local ---"
pnpm build:local

echo "--- Building project with external ---"
pnpm build:external

echo "--- Server is Updated ---"
