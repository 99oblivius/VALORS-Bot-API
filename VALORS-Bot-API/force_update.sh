#!/bin/bash
set -e
UPDATE_IP="$1"

cd /srv/ValorsLeague/bot/VALORS-Match-Making-Bot

# Fetch the latest changes
git fetch origin main

git pull origin main
    
cd ../..

# Store the old image ID
OLD_IMAGE_ID=$(docker images -q valorsbot:latest)

# Build and restart valorsbot
docker-compose build valorsbot
docker-compose up -d valorsbot

# Remove the old image if it's different
NEW_IMAGE_ID=$(docker images -q valorsbot:latest)
if [ "$OLD_IMAGE_ID" != "$NEW_IMAGE_ID" ] && [ ! -z "$OLD_IMAGE_ID" ]; then
    echo "Removing old valorsbot image..."
    docker rmi $OLD_IMAGE_ID || true
else
    docker-compose restart valorsbot
fi

echo "valorsbot forcibly updated successfully."
echo "$(date) | $UPDATE_IP | Force update" >> /srv/ValorsLeague/VALORS-Bot-API/last_update.txt