#!/bin/zsh
set -euo pipefail
cd "$(dirname "$0")/.."
fail() { echo "VERIFY-FAIL: $*"; exit 1 }
[ -f "$UCS_CHAIN_DIR/allwares/chain.json" ] || fail "allwares chain.json missing"
[ -f "$UCS_CHAIN_DIR/hood_compilers/chain/chain.json" ] || fail "chain chain.json missing"
python3 -c "import json; d=json.load(open(\"$UCS_CHAIN_DIR/allwares/chain.json\")); assert \"KEY\" not in d, \"KEY leaked into chain.json\""
python3 -c "import json; d=json.load(open(\"$UCS_CHAIN_DIR/hood_compilers/chain/chain.json\")); assert \"KEY\" not in d, \"KEY leaked into chain.json\""
git ls-files | grep -E "(^|/)KEY$|\.sig$" && fail "signing material tracked"
echo "VERIFY-OK"
