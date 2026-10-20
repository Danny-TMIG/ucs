#!/bin/zsh
set -e
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
cd /tmp/ucs-clean
mkdir -p allwares
touch allwares/KEY
git add -f allwares/KEY 2>/dev/null || git add allwares/KEY
if pre-commit run block-signing-material 2>&1 | grep -q BLOCKED; then
  echo "PASS: hook blocks the path"
else
  echo "FAIL: hook did not block"
fi
git restore --staged allwares/KEY 2>/dev/null || git reset HEAD allwares/KEY 2>/dev/null || true
rm -f allwares/KEY
rmdir allwares 2>/dev/null || true
echo "03 done"
