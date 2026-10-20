#!/bin/zsh
set -e
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
cd /tmp/ucs-clean
OUT=/tmp/ucs-hardening/audit-$(date +%Y%m%d-%H%M%S).txt
{
  echo "# Audit: artifacts possibly signed with leaked chain keys"
  echo "Date: $(date)"
  echo
  echo "## Historical references to chain.json in current history"
  git log --all --oneline -- allwares/chain.json hood_compilers/chain/chain.sig 2>/dev/null || echo "(none — purged)"
  echo
  echo "## Files in tree that reference chain.json or .sig paths"
  git grep -n -E 'chain\.(json|sig)|allwares/KEY|hood_compilers/chain/KEY' 2>/dev/null || echo "(none)"
  echo
  echo "## Release tags"
  git tag -l
  echo
  echo "## Actions workflows that produce signed output"
  ls .github/workflows 2>/dev/null || echo "(no workflows dir)"
  git grep -n -E 'sign|cosign|gpg|chain' -- .github 2>/dev/null || echo "(no signers in workflows)"
} > "$OUT"
echo "audit written to $OUT"
cat "$OUT"
