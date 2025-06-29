#!/bin/bash
safe_args=""
[ "$1" = "--unsafe" ] && safe_args="--non-interactive --allow-unsafe"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

database_path="$(${SCRIPT_DIR}/utils/find_path.sh Database)"
[ $? -eq 0 ] || { echo "Error: Could not locate Database directory"; exit 1; }

source "${SCRIPT_DIR}/utils/export_envs.sh" GEL
[ $? -eq 0 ] || { echo "Error: Failed to export Gel environment variables"; exit 1; }


cd "$database_path"
gel migration extract || exit 1
gel migration create $safe_args || exit 1
gel migrate || exit 1

echo "Migration complete"