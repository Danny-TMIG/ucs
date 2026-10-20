.PHONY: rotate verify precommit clean
rotate:
	./spec/run.sh
verify:
	./spec/verify.sh
precommit:
	pre-commit run --all-files
clean:
	rm -rf spec/audit/*
