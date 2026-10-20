#!/bin/zsh
set -euo pipefail
cd "$(dirname "$0")/.."
gh api "repos/Danny-TMIG/ucs/git/refs/tags/$UCS_NEW_TAG" >/dev/null || { echo "POST-VERIFY-FAIL: tag not on origin"; exit 1 }
gh api "repos/Danny-TMIG/ucs/contents/allwares/chain.json" >/dev/null || { echo "POST-VERIFY-FAIL: chain.json not on main"; exit 1 }
gh api "repos/Danny-TMIG/ucs/contents/allwares/KEY" 2>/dev/null && { echo "POST-VERIFY-FAIL: KEY present on main"; exit 1 } || true
echo "POST-VERIFY-OK"
