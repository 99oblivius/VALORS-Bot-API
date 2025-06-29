#!/bin/bash
if [ $# -ne 1 ]; then
    echo "Usage: $0 <path/to/find>" >&2
    exit 1
fi

target_path="${1#./}"
target_path="${target_path%/}"

current_path="$PWD"

if [ -e "$current_path/$target_path" ]; then
    echo "$current_path/$target_path"
    exit 0
fi

while [ "$current_path" != "/" ]; do
    if [ -e "$current_path/$target_path" ]; then
        echo "$current_path/$target_path"
        exit 0
    fi
    current_path="$(dirname "$current_path")"
done

if [ -e "/$target_path" ]; then
    echo "/$target_path"
    exit 0
fi

echo "Could not find: $target_path" >&2
exit 1