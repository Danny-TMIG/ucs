Subject: [Danny-TMIG/ucs] Signing key rotation — action required
The chain signing keys referenced by allwares/chain.json and
hood_compilers/chain/chain.sig were exposed in a historical commit
and rotated on <DATE>.
What changed:
- Old fingerprints (do not trust): <fp1> <fp2>
- New fingerprints (trust): <fp1> <fp2>
- Release tag: v<X.Y.Z>-rotated
What you must do:
1. Re-pull ucs at or after v<X.Y.Z>-rotated.
2. Remove old fingerprints from your trust store.
3. Re-verify artifacts consumed before <DATE>; fetch re-signed replacements.
4. If you maintain a fork, rebase onto rotated history and drop a20b6dd / c75dd26.
Contact: <rotation owner email>
