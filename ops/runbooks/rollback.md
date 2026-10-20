# Rollback

One source, one command:

    source tools/sdlc.sh
    sdlc_init
    sdlc_rollback <bad-sha>
    sdlc_pr "revert: <bad-sha>" /tmp/revert-body.txt
    sdlc_merge
    sdlc_verify

Find the bad SHA with `git bisect run python3 spec/parallel_check.py`.

Never force-push main. The revert is a new signed commit.
