DIRS = core/ apis/ common/ conf/ deploy/ storages/ third_apis/ extensions/ scripts/ tests/ extensions/ entrypoint/ tasks/
# --disable-warnings
help:
	@echo "FastService development makefile"
	@echo
	@echo  "usage: make <target>"
	@echo  "Targets:"
	@echo  "    deps		Ensure dependencies are installed"
	@echo  "    up			Updates dependencies"
	@echo  "	test		run pytest"
	@echo  "    style		Auto-formats the code"
	@echo  "    check		Checks that build is sane"
	@echo  "	pre-commit	mannually execute pre-commit"


deps:
	@poetry install --no-root

up:
	@poetry update

style:
	isort --length-sort -src $(DIRS)
	black $(DIRS)

check:
	ruff check --fix .

pre-commit:
	pre-commit run --all-files

test:
	@pytest -p no:warnings
