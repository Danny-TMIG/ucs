To: GitHub Support
Subject: Request purge of historical objects — Danny-TMIG/ucs
Repository: https://github.com/Danny-TMIG/ucs
Commits a20b6dd (initial import, contained signing keys) and c75dd26
(cosmetic removal) were rewritten out via git filter-repo on <DATE>.
Main is now 41a712a. Old SHAs 404 via REST API; no forks. Request:
1. Purge cached/dangling objects referencing a20b6dd or c75dd26.
2. Purge internal retention/reflog copies.
3. Confirm completion and any remaining PR refs to those commits.
Leaked paths (all 404 on main):
- allwares/KEY
- allwares/chain.sig
- allwares/chain.json
- hood_compilers/chain/KEY
- hood_compilers/chain/chain.sig
Keys rotated at issuer; secret scanning and push protection enabled on <DATE>.
