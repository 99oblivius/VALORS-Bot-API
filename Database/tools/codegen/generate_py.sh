#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

database_path="$(${SCRIPT_DIR}/../utils/find_path.sh Database)"
[ $? -eq 0 ] || { echo "Error: Could not locate Database directory"; exit 1; }

source_path="$(${SCRIPT_DIR}/../utils/find_path.sh DiscordBot/components/database)"
[ $? -eq 0 ] || { echo "Error: Could not locate source directory"; exit 1; }

source "${SCRIPT_DIR}/../utils/export_envs.sh" GEL
[ $? -eq 0 ] || { echo "Error: Failed to export Gel environment variables"; exit 1; }

cd "$database_path"
gel-py --target async --dir ./queries --file "$source_path/queries.py" || exit 1

echo "Gel Codegen completed for the DiscordBot and placed in $source_path!"