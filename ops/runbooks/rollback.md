# Rollback

## One command

    source tools/sdlc.sh
    sdlc_init
    sdlc_rollback <bad-sha>

`sdlc_rollback` does exactly four things:
1. `sdlc_verify` — sync to origin/main and confirm HEAD == origin/main
2. `git revert --no-edit <bad-sha>` — creates a revert commit
3. `git commit --amend -S -s -m "revert: <bad-sha> (sdlc_rollback)"` — sign the revert
4. prints "revert committed; use sdlc_pr then sdlc_merge"

Then:

    sdlc_pr "revert: <bad-sha>" /tmp/revert-body.txt
    sdlc_merge
    sdlc_verify

## Finding the bad SHA

    git bisect start
    git bisect bad HEAD
    git bisect good <last-known-good>
    git bisect run python3 spec/parallel_check.py
    git bisect reset

## Break-glass (GitHub API down)

    git fetch origin main
    git checkout main
    git revert --no-edit <bad-sha>
    git commit --amend -S -s -m "revert: <bad-sha> (break-glass)"
    git push origin main
    sdlc_verify

Record break-glass in `decisions/closed/` with the SHA and the reason.

## Invariants

- Never force-push main.
- Never amend a pushed commit except the revert itself (immediately after `git revert`, before push).
- Every revert is signed.
- Every revert cites the original SHA in its message.
