#!/bin/bash
cd $(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
bash -c ./codegen/generate_py.sh