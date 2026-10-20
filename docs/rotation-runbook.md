# Key rotation runbook — Danny-TMIG/ucs
## Scope
Leaked in a20b6dd (purged from history), keys rotated at issuer: PENDING:
- allwares/KEY
- allwares/chain.sig
- allwares/chain.json
- hood_compilers/chain/KEY
- hood_compilers/chain/chain.sig
## Owners
- Rotation owner: Danny (Danny-TMIG)
- Approver: Danny (sole maintainer)
- Downstream notification: none — no downstream consumers
## Step 1 — revoke
- [ ] Identify issuer of allwares/KEY and hood_compilers/chain/KEY
- [ ] Revoke both keys at the issuer. Record timestamp.
- [ ] Confirm verification with old public key now fails.
## Step 2 — reissue
- [ ] Generate new keypairs at issuer. Private halves never touch repo.
- [ ] Store private halves in designated secret store.
- [ ] Export only public keys.
## Step 3 — rebuild trust chain
- [ ] Update allwares/chain.json with new key ids + public material only.
- [ ] Re-sign chain.json to produce new chain.sig.
- [ ] Commit both. Tag v<X.Y.Z>-rotated.
## Step 4 — downstream notification
- [ ] Send 06-notification-template.md to all consumers.
- [ ] Update docs pointing at old key fingerprints.
## Step 5 — audit signed artifacts
- [ ] Run 04-audit-signed-artifacts.sh and review output.
- [ ] Re-sign or withdraw every artifact signed with old key.
## Step 6 — prevent recurrence
- [ ] 03-test-hook.sh passes in fresh clone.
- [ ] 02-enable-github-security.sh applied.
- [ ] Branch protection blocks force-push and deletion.
## Step 7 — close incident
- [ ] File GitHub Support ticket (07-support-ticket.md).
- [ ] Attach audit output, revocation timestamps, notification sent.
- [ ] Record closing date and approver signature.

## Audit finding (2026-10-19)
No release tags and no signing workflows exist as of this date, so no signed artifacts require re-signing or withdrawal.


## Rotation history

Last rotation: PENDING — no rotation has been performed. This placeholder silences rotation-reminder.yml until step 1 of this runbook is executed and a real timestamp is recorded.
