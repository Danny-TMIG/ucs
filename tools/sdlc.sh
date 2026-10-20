#!/usr/bin/env bash
set -euo pipefail
trap 'echo "SDLC FAIL at line $LINENO" >&2' ERR
SDLC_REPO="${SDLC_REPO:-$PWD}"
SDLC_MAIN="${SDLC_MAIN:-main}"
SDLC_REMOTE="${SDLC_REMOTE:-origin}"
SDLC_TEST="${SDLC_TEST:-python3 spec/parallel_check.py}"
SDLC_LINT="${SDLC_LINT:-bash -n tools/sdlc.sh}"
SDLC_IMPORT="${SDLC_IMPORT:-spec}"
SDLC_ADMIN="${SDLC_ADMIN:-1}"
SDLC_SKIP_GATES="${SDLC_SKIP_GATES:-0}"
_sdlc_info() { echo "SDLC: $*"; }
_sdlc_err()  { echo "SDLC ERR: $*" >&2; }
_sdlc_die()  { _sdlc_err "$*"; return 1; }

sdlc_init() {
    cd "$SDLC_REPO" || _sdlc_die "cannot cd $SDLC_REPO"
    local missing=()
    for t in git gh python3 curl; do
        command -v "$t" >/dev/null 2>&1 || missing+=("$t")
    done
    [ ${#missing[@]} -eq 0 ] || _sdlc_die "missing tools: ${missing[*]}"
    git rev-parse --git-dir >/dev/null 2>&1 || _sdlc_die "not a git repo"
    _sdlc_info "init OK ($(git rev-parse --abbrev-ref HEAD) @ $(git log --oneline -1 | cut -c1-7))"
}

_sdlc_gate_lint()   { _sdlc_info "gate: lint";   if ! eval "$SDLC_LINT";   then _sdlc_die "lint failed";   fi; }
_sdlc_gate_import() {
    _sdlc_info "gate: import"
    if [ -d "$SDLC_IMPORT" ]; then
        for f in "$SDLC_IMPORT"/*.py; do
            [ -f "$f" ] || continue
            local mod; mod=$(basename "$f" .py)
            if ! python3 -c "import sys; sys.path.insert(0,'$SDLC_IMPORT'); import $mod"; then
                _sdlc_die "import $mod failed"
            fi
        done
    fi
}
_sdlc_gate_test()   { _sdlc_info "gate: test";   if ! eval "$SDLC_TEST";   then _sdlc_die "test failed";   fi; }
_sdlc_gate_sig()    { _sdlc_info "gate: sig";    git verify-commit HEAD >/dev/null 2>&1 || _sdlc_die "HEAD unsigned"; }

sdlc_gate() {
    [ "$SDLC_SKIP_GATES" = "1" ] && { _sdlc_info "gates SKIPPED"; return 0; }
    _sdlc_gate_lint; _sdlc_gate_import; _sdlc_gate_test
}

sdlc_stage() {
    local msg="${1:?sdlc_stage needs message}"
    cd "$SDLC_REPO"
    local before; before=$(git rev-parse HEAD)
    git add -A
    [ -n "$(git diff --cached --name-only)" ] || _sdlc_die "nothing staged"
    echo "--- staging preview ---"; git diff --cached --stat
    git commit -S -s -m "$msg"
    local after; after=$(git rev-parse HEAD)
    [ "$before" != "$after" ] || _sdlc_die "commit did not produce new HEAD"
    _sdlc_info "committed $(git log --oneline -1)"
}

sdlc_pr() {
    local title="${1:?sdlc_pr needs title}"
    local body="${2:-}"
    cd "$SDLC_REPO"
    local branch; branch=$(git rev-parse --abbrev-ref HEAD)
    if [ "$branch" = "$SDLC_MAIN" ]; then branch="feat/auto-$(date +%s)"; git checkout -B "$branch"; fi
    git push -u "$SDLC_REMOTE" "$branch"
    if [ -n "$body" ] && [ -f "$body" ] && [ -s "$body" ]; then
        gh pr create --base "$SDLC_MAIN" --head "$branch" --title "$title" --body-file "$body"
    else
        gh pr create --base "$SDLC_MAIN" --head "$branch" --title "$title" --fill
    fi
}

sdlc_merge() {
    cd "$SDLC_REPO"
    local branch; branch=$(git rev-parse --abbrev-ref HEAD)
    if [ "$SDLC_ADMIN" = "1" ]; then gh pr merge --squash --delete-branch --admin
    else gh pr merge --squash --delete-branch; fi
    _sdlc_info "merged $branch"
}

sdlc_verify() {
    cd "$SDLC_REPO"
    git fetch "$SDLC_REMOTE" >/dev/null
    git reset --hard "$SDLC_REMOTE/$SDLC_MAIN"
    [ "$(git rev-parse HEAD)" = "$(git rev-parse "$SDLC_REMOTE/$SDLC_MAIN")" ] \
        || _sdlc_die "HEAD != origin/$SDLC_MAIN"
    _sdlc_info "synced: $(git log --oneline -1)"
    sdlc_gate
    _sdlc_info "post-merge verify OK"
}

sdlc_rollback() {
    local target="${1:?sdlc_rollback needs SHA}"
    cd "$SDLC_REPO"
    sdlc_verify
    git revert --no-edit "$target"
    git commit --amend -S -s -m "revert: $target (sdlc_rollback)"
    _sdlc_info "revert committed; use sdlc_pr then sdlc_merge"
}

sdlc_full() {
    local msg="${1:?sdlc_full needs message}"
    local title="${2:-$msg}"
    local body="${3:-}"
    sdlc_init; sdlc_gate; sdlc_stage "$msg"; sdlc_pr "$title" "$body"; sdlc_merge; sdlc_verify
}

sdlc_status() {
    cd "$SDLC_REPO"
    echo "repo:   $SDLC_REPO"
    echo "branch: $(git rev-parse --abbrev-ref HEAD)"
    echo "head:   $(git log --oneline -1)"
    echo "dirty:  $(git status --porcelain | wc -l | tr -d ' ') file(s)"
    echo "ahead:  $(git rev-list --count "$SDLC_REMOTE/$SDLC_MAIN..HEAD" 2>/dev/null || echo ?) commit(s)"
    command -v gh >/dev/null 2>&1 && { gh pr status 2>/dev/null | head -5 || true; }
}
