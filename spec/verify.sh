#!/usr/bin/env bash
set -euo pipefail
fail() { echo "FAIL: $*" >&2; exit 1; }
[ -d .git ] || fail "not a git repo"
if git ls-files | grep -E "(^|/)KEY$|\.sig$" ; then fail "signing material tracked"; fi
echo "spec verify OK"
