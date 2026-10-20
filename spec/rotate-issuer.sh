#!/bin/zsh
set -euo pipefail
cd "$(dirname "$0")/.."
: "${UCS_ISSUER:?set UCS_ISSUER}"
: "${UCS_ISSUER_REF:=default}"
: "${UCS_CHAIN_DIR:=$HOME/.config/ucs}"

log() { echo "[$(date +%H:%M:%S)] $*"; }
abort() { log "ABORT: $*"; exit 1; }

case "$UCS_ISSUER" in
  local)
    mkdir -p "$UCS_CHAIN_DIR/allwares" "$UCS_CHAIN_DIR/hood_compilers/chain"
    chmod 700 "$UCS_CHAIN_DIR"; umask 077
    python3 -c "import secrets,pathlib; p=pathlib.Path('$UCS_CHAIN_DIR/allwares/KEY'); p.write_bytes(secrets.token_bytes(32)); p.chmod(0o600)"
    log "local key written to $UCS_CHAIN_DIR/allwares/KEY"
    ;;
  kms|vault|hsm)
    # issue_key <ref>   -> write new key material to $UCS_CHAIN_DIR/allwares/KEY (mode 0600)
    # revoke_key <ref>  -> revoke previously issued key
    # attest <ref>      -> print issuer receipt / key id for audit log
    abort "adapter for UCS_ISSUER=$UCS_ISSUER not implemented"
    ;;
  *)
    abort "unknown UCS_ISSUER=$UCS_ISSUER (want local|kms|vault|hsm)"
    ;;
esac

python3 allwares.py rekey
python3 hood_compilers/chain.py rekey
spec/verify.sh
log "DONE"
