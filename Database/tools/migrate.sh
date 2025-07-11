#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/utils/export_envs.sh" GEL
[ $? -eq 0 ] || { echo "Error: Failed to export Gel environment variables"; exit 1; }

cd "${SCRIPT_DIR}/.."
gel --tls-security insecure migration extract || exit 1
gel --tls-security insecure migration apply --dev-mode || exit 1
echo "Migration complete"