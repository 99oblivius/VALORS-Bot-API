#!/bin/bash
while true; do eval "$(cat /srv/ValorsLeague/VALORS-Bot-API/pipe/apipipe)" &> /srv/ValorsLeague/VALORS-Bot-API/pipe/log.txt; done