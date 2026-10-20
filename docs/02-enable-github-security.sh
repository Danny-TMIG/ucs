#!/bin/zsh
set -e
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
REPO="Danny-TMIG/ucs"
gh api -X PATCH "repos/$REPO" -f 'security_and_analysis[secret_scanning][status]=enabled' 2>/dev/null || echo "WARN: secret scanning requires admin token or public repo"
gh api -X PATCH "repos/$REPO" -f 'security_and_analysis[secret_scanning_push_protection][status]=enabled' 2>/dev/null || echo "WARN: push protection requires admin token or public repo"
gh api -X PUT "repos/$REPO/branches/main/protection" --input - <<'JSON' 2>/dev/null || echo "WARN: branch protection requires admin token"
{"required_status_checks":null,"enforce_admins":false,"required_pull_request_reviews":null,"restrictions":null,"allow_force_pushes":false,"allow_deletions":false}
JSON
gh api "repos/$REPO" --jq '.security_and_analysis' 2>/dev/null || true
echo "02 done"
