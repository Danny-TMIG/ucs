#!/bin/zsh
set -e
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
cd /tmp/ucs-clean
command -v pre-commit >/dev/null 2>&1 || brew install pre-commit
cat > .pre-commit-config.yaml <<'YAML'
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: forbid-submodules
      - id: check-added-large-files
        args: ["--maxkb=512"]
  - repo: local
    hooks:
      - id: block-signing-material
        name: block signing keys and chain files
        entry: sh -c 'for p in allwares/KEY allwares/chain.sig allwares/chain.json hood_compilers/chain/KEY hood_compilers/chain/chain.sig; do git diff --cached --name-only | grep -qx "$p" && { echo "BLOCKED: $p"; exit 1; }; done; exit 0'
        language: system
        pass_filenames: false
        always_run: true
YAML
pre-commit install
pre-commit install --hook-type pre-push
git add .pre-commit-config.yaml
git commit -m "chore: tracked pre-commit config blocking signing material" || true
git push origin main || true
echo "01 done: tracked hook installed and pushed"
