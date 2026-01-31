#!/bin/bash
set -e

PROJECT=$1

if [ -z "$PROJECT" ]; then
    echo "Error: Project name is required"
    exit 1
fi

echo "Deploying project: $PROJECT"

# Add your project-specific deployment logic here
# Example:
# cd /var/www/$PROJECT
# git pull origin main
# ./build.sh

echo "Deployment complete for: $PROJECT"
