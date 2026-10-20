#!/bin/zsh
set -euo pipefail
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"
UCS_CHAIN_DIR="${UCS_CHAIN_DIR:-$HOME/.config/ucs}"
UCS_ISSUER="${UCS_ISSUER:-local}"
UCS_ISSUER_REF="${UCS_ISSUER_REF:-default}"
UCS_NEW_TAG="${UCS_NEW_TAG:-v$(date +%Y.%m.%d)-rotated}"
export UCS_CHAIN_DIR UCS_ISSUER UCS_ISSUER_REF UCS_NEW_TAG
AUDIT_DIR="$SCRIPT_DIR/audit"
mkdir -p "$AUDIT_DIR"
AUDIT="$AUDIT_DIR/$(date +%Y%m%d-%H%M%S).txt"
log() { echo "[$(date +%H:%M:%S)] $*" | tee -a "$AUDIT" }
abort() { log "ABORT: $*"; exit 1 }
log "intent: rotate signing material autonomously"
log "issuer=$UCS_ISSUER ref=$UCS_ISSUER_REF tag=$UCS_NEW_TAG chain_dir=$UCS_CHAIN_DIR"
log "step 1: validate inputs"
command -v gh >/dev/null || abort "gh missing"
command -v pre-commit >/dev/null || abort "pre-commit missing"
command -v python3 >/dev/null || abort "python3 missing"
[ -f allwares.py ] || abort "allwares.py missing"
[ -f hood_compilers/chain.py ] || abort "chain.py missing"
log "step 2: prepare chain dir"
mkdir -p "$UCS_CHAIN_DIR/allwares" "$UCS_CHAIN_DIR/hood_compilers/chain"
chmod 700 "$UCS_CHAIN_DIR"
umask 077
log "step 3: generate new keypair at issuer"
if [ "$UCS_ISSUER" = "local" ]; then
  python3 -c "import secrets,pathlib; p=pathlib.Path(\"$UCS_CHAIN_DIR/allwares/KEY\"); p.write_bytes(secrets.token_bytes(32)); p.chmod(0o600); print(\"key generated\")"
else
  abort "issuer $UCS_ISSUER not wired: set UCS_ISSUER=local or implement adapter"
fi
log "step 4: rekey"
python3 allwares.py rekey >>"$AUDIT" 2>&1 || abort "allwares rekey failed"
python3 hood_compilers/chain.py rekey >>"$AUDIT" 2>&1 || abort "chain rekey failed"
log "step 5: pre-commit gate"
pre-commit run --all-files >>"$AUDIT" 2>&1 || abort "pre-commit blocked"
log "step 6: verify"
if [ -x spec/verify.sh ]; then spec/verify.sh >>"$AUDIT" 2>&1 || abort "verify failed"; fi
log "step 7: copy public material"
cp "$UCS_CHAIN_DIR/allwares/chain.json" allwares/chain.json
cp "$UCS_CHAIN_DIR/hood_compilers/chain/chain.json" hood_compilers/chain/chain.json
if [ -f "$UCS_CHAIN_DIR/allwares/chain.sig" ]; then cp "$UCS_CHAIN_DIR/allwares/chain.sig" allwares/chain.sig; fi
if [ -f "$UCS_CHAIN_DIR/hood_compilers/chain/chain.sig" ]; then cp "$UCS_CHAIN_DIR/hood_compilers/chain/chain.sig" hood_compilers/chain/chain.sig; fi
log "step 8: commit"
git add allwares/chain.json hood_compilers/chain/chain.json 2>/dev/null || true
git add allwares/chain.sig hood_compilers/chain/chain.sig 2>/dev/null || true
if ! git diff --cached --quiet; then git commit -m "chore(rotation): $UCS_NEW_TAG" >>"$AUDIT" 2>&1 || abort "commit failed"; fi
log "step 9: tag + push"
git tag -a "$UCS_NEW_TAG" -m "rotation $UCS_NEW_TAG" 2>/dev/null || log "tag exists, skipping"
BRANCH="$(git rev-parse --abbrev-ref HEAD)"
git push origin "$BRANCH" >>"$AUDIT" 2>&1 || log "push branch failed (may need PR)"
git push origin "$UCS_NEW_TAG" >>"$AUDIT" 2>&1 || log "push tag failed"
log "step 10: open PR if needed"
if ! git push origin "$BRANCH" >>/dev/null 2>&1; then
  gh pr create --title "chore(rotation): $UCS_NEW_TAG" --body "Autonomous rotation via spec/run.sh" --base main 2>/dev/null || true
fi
log "step 11: post-verify"
if [ -x spec/post-verify.sh ]; then spec/post-verify.sh >>"$AUDIT" 2>&1 || abort "post-verify failed"; fi
log "step 12: audit + runbook"
printf "%s\nLast rotation: %s (issuer=%s ref=%s)\n" "" "$(date -u +%FT%TZ)" "$UCS_ISSUER" "$UCS_ISSUER_REF" >> docs/rotation-runbook.md
git add docs/rotation-runbook.md spec/audit 2>/dev/null || true
git commit -m "chore(rotation): audit $UCS_NEW_TAG" >>"$AUDIT" 2>&1 || true
git push origin "$BRANCH" >>"$AUDIT" 2>&1 || true
log "DONE tag=$UCS_NEW_TAG audit=$AUDIT"
