#!/bin/bash
set -e

cd /srv/ValorsLeague/bot/VALORS-Match-Making-Bot

# Fetch the latest changes
git fetch origin main

# Check if there are any updates
if git status -uno | grep -q 'Your branch is behind'; then
    echo "Updates found for valorsbot. Pulling changes..."
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
    fi
    
    echo "valorsbot updated successfully."
    date >> /srv/ValorsLeague/VALORS-Bot-API/last_update.txt
else
    echo "No updates found for valorsbot. Skipping."
fi