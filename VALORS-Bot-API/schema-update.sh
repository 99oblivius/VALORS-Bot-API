#!/bin/bash

cd /srv/ValorsLeague/bot/discord_ValorsBot

git pull origin main

OLD_IMAGE_ID=$(docker images -q valorsbot:latest)

docker-compose stop valorsbot

alembic revision --autogenerate -m "ValorsBot model"
alembic upgrade head

docker-compose build valorsbot
docker-compose up -d valorsbot

if [ ! -z "$OLD_IMAGE_ID" ]; then
    NEW_IMAGE_ID=$(docker images -q valorsbot:latest)
    if [ "$OLD_IMAGE_ID" != "$NEW_IMAGE_ID" ]; then
        docker rmi $OLD_IMAGE_ID
    fi
fi

date >> /srv/ValorsLeague/botapi/last_schema_update.txt