---
id: ops.rotation
tier: 6
owner: "@Danny-TMIG"
not_about:
  - Creating the initial key
---

# Rotation runbook

1. Confirm issuer.
2. Revoke old key at issuer.
3. Regenerate public material.
4. Verify.

## Verify

`ops/verification/verify-rotation.sh`. Exit 0 = rotated.
