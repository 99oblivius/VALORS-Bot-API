#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

database_path="${SCRIPT_DIR}/../queries"
[ $? -eq 0 ] || { echo "Error: Could not locate Database directory"; exit 1; }

source_path="${SCRIPT_DIR}/../../crossplay/crossplaybot/components"
[ $? -eq 0 ] || { echo "Error: Could not locate source directory"; exit 1; }

source "${SCRIPT_DIR}/utils/export_envs.sh" GEL
[ $? -eq 0 ] || { echo "Error: Failed to export Gel environment variables"; exit 1; }

cd "${SCRIPT_DIR}/../.."
gel-py --tls-security insecure --target async --dir "queries" --file "${source_path}/gel_queries.py" || exit 1

echo "Gel Codegen completed for the DiscordBot and placed in ${source_path}!"