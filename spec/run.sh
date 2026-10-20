#!/usr/bin/env bash
set -euo pipefail
python3 orchestrate.py stage
python3 orchestrate.py verify
echo "run OK"
