#!/usr/bin/env bash
set -euo pipefail
fail() { echo "FAIL: $*" >&2; exit 1; }
[ -f runtime.json ] || fail "runtime.json missing"
python3 -c "import json,pathlib; json.loads(pathlib.Path('runtime.json').read_text())" || fail "runtime.json invalid"
echo "post-verify OK"
