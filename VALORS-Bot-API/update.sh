#!/bin/bash
set -e

cd /srv/ValorsLeague/bot/VALORS-Match-Making-Bot
git checkout main
git pull origin main
cd ../..

OLD_IMAGE_ID=$(docker images -q valorsbot:latest)

docker-compose build --parallel
docker-compose up -d

if [ ! -z "$OLD_IMAGE_ID" ]; then
    NEW_IMAGE_ID=$(docker images -q valorsbot:latest)
    if [ "$OLD_IMAGE_ID" != "$NEW_IMAGE_ID" ]; then
        docker rmi $OLD_IMAGE_ID
    fi
fi

date >> /srv/ValorsLeague/VALORS-Bot-API/last_update.txt