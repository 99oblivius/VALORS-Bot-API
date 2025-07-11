#!/bin/bash
[ $# -eq 1 ] || { echo "Usage: $0 <env_prefix>" >&2; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
prefix="$1"

env_path="${SCRIPT_DIR}/../../../crossplay/crossplaybot/.env"
[ $? -eq 0 ] || { echo "Error: Could not locate $env_path" >&2; exit 1; }

while IFS= read -r line || [ -n "$line" ]; do
    [[ $line =~ ^${prefix}_.*$ ]] && export "$line"
done < "$env_path"