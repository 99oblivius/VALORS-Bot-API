#!/bin/bash

PIPE="/srv/ValorsLeague/VALORS-Bot-API/pipe/apipipe"
LOG="/srv/ValorsLeague/VALORS-Bot-API/pipe/log.txt"
SCRIPT_DIR="/srv/ValorsLeague/VALORS-Bot-API"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" >> "$LOG"
}

while true; do
    if read -r script_name; then
        full_path="$SCRIPT_DIR/$script_name"
        if [[ "$full_path" == "$SCRIPT_DIR"/*.sh && -f "$full_path" && -x "$full_path" ]]; then
            log "Executing: $full_path"
            if output=$("$full_path" 2>&1); then
                log "Script executed successfully"
                echo "$output" >> "$LOG"
            else
                log "Script failed with exit code $?"
                echo "$output" >> "$LOG"
            fi
        else
            log "Invalid script: $script_name"
        fi
    else
        sleep 1
    fi
done < "$PIPE"
