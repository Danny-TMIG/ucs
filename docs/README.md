# ucs incident hardening package
Run in order:
1. 01-install-tracked-hook.sh
2. 02-enable-github-security.sh
3. 03-test-hook.sh
4. 04-audit-signed-artifacts.sh
Then follow 05-rotation-runbook.md, 06-notification-template.md, 07-support-ticket.md.
01/02 need admin rights. 03 briefly mutates index. 04 writes audit-<ts>.txt.
Manual steps in 05 are the real rotation.
