#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

database_path="$(${SCRIPT_DIR}/../utils/find_path.sh Database)"
[ $? -eq 0 ] || { echo "Error: Could not locate Database directory"; exit 1; }

source_path="$(${SCRIPT_DIR}/../utils/find_path.sh API/src/lib/server/models)"
[ $? -eq 0 ] || { echo "Error: Could not locate source directory"; exit 1; }

source "${SCRIPT_DIR}/../utils/export_envs.sh" GEL
[ $? -eq 0 ] || { echo "Error: Failed to export Gel environment variables"; exit 1; }

cd "$database_path"
npx @gel/generate queries --target ts --file "$source_path/queries" || exit 1
# npx @gel/generate interfaces --file "$models_path/interfaces"
# npx @gel/generate edgeql-js --output-dir "$models_path/query_builders" --target ts --force-overwrite

echo "Gel Codegen completed for the API and placed in $source_path!"