.PHONY: rotate verify precommit clean
rotate:
	./spec/run.sh
verify:
	./spec/verify.sh
precommit:
	pre-commit run --all-files
clean:
	rm -rf spec/audit/*

SUPPORT_BODY := $(shell python3 -c "import urllib.parse,pathlib; print(urllib.parse.quote(pathlib.Path('docs/support-ticket.md').read_text()))")

support-ticket:
	@open "https://support.github.com/contact?subject=Request+to+purge+cached+objects+for+Danny-TMIG%2Fucs&body=$(SUPPORT_BODY)"

revoke:
	@echo "1. Revoke leaked key at issuer (KMS/HSM/Vault/local)"
	@echo "2. Confirm revoked, then run: make rotate-issuer"

rotate-issuer:
	@test -n "$$UCS_ISSUER" || { echo "set UCS_ISSUER (kms|vault|hsm|local)"; exit 1; }
	./spec/rotate-issuer.sh
