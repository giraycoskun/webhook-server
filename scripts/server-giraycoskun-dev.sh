#!/bin/bash
set -e  # Exit immediately if any command fails

# Define paths explicitly
GIT_CMD="/usr/bin/git"    # Update this based on 'which git' output
PNPM_CMD="/usr/local/bin/pnpm" # Update this based on 'which pnpm' output

cd /home/giraycoskun/Code/server.giraycoskun.dev

echo "--- Fetching latest changes ---"
$GIT_CMD fetch https://${GITHUB_TOKEN}@github.com/giraycoskun/server.giraycoskun.dev.git main

echo "--- Pulling latest changes ---"
$GIT_CMD pull https://${GITHUB_TOKEN}@github.com/giraycoskun/server.giraycoskun.dev.git main

echo "--- Installing deps ---"
$PNPM_CMD install

echo "--- Building project with local ---"
$PNPM_CMD build:local

echo "--- Building project with external ---"
$PNPM_CMD build:external

echo "--- Server is Updated ---"
