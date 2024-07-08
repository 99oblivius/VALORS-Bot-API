#!/bin/bash
while true; do eval "$(cat /srv/ValorsLeague/botapi/pipe/apipipe)" &> /srv/ValorsLeague/botapi/pipe/log.txt; done