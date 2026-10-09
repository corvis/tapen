VIRTUAL_ENV_PATH=venv

SHELL := /bin/bash
PYTHON := python3.14
UV := uv
UV_PROJECT_ENVIRONMENT := $(CURDIR)/$(VIRTUAL_ENV_PATH)
export UV_PROJECT_ENVIRONMENT

PYPI_API_KEY :=
PYPI_REPOSITORY_URL :=
ALPHA_VERSION :=
SRC_ROOT := ./src
ROOT_PACKAGE := tapen
FORMAT_PATH := $(SRC_ROOT)

.DEFAULT_GOAL := pre_commit

pre_commit: pre_commit_hook lint

UNAME_S := $(shell uname -s)

ifeq ($(UNAME_S),Darwin)
    SED_COMMAND := gsed
else
    SED_COMMAND := sed
endif

pre_commit_hook:
	@( \
		$(UV) run pre-commit run --all --hook-stage=commit; \
	)

verify-prerequisites:
	@(development/ensure-dependencies.sh)

setup: verify-prerequisites deps
	@( \
		$(UV) run pre-commit install; \
		echo "Pre-commit hooks installed"; \
		echo "DONE: setup"; \
	)

copyright:
	@( \
       echo "Applying copyright..."; \
       for p in $(FORMAT_PATH); do \
	       	 $(UV) run licenseheaders -t ./development/copyright.tmpl -E ".py" -cy -d $$p; \
       done; \
       echo "DONE: copyright"; \
    )

mypy:
	@( \
       set -e; \
       echo "Running MyPy checks..."; \
       $(UV) run mypy --show-error-codes $(SRC_ROOT)/tapen; \
       $(UV) run mypy --show-error-codes $(SRC_ROOT)/ptouch_py; \
       \
       echo "DONE: MyPy"; \
    )

format: ruff-import-sort ruff-format
check-format: ruff-import-sort-check ruff-format-check

.PHONY: lint
lint: check-format ruff-lint mypy

build: copyright format lint clean
	@( \
	   set -e; \
       echo "Building wheel package..."; \
       $(UV) build; \
       echo "DONE: wheel package"; \
    )

package:
	@( \
		echo "Building packages"; \
		set -e; \
		$(UV) build; \
		echo "DONE: Building packages"; \
	)

single-binary:
	@( \
	   set -e; \
       echo "Building single binary"; \
	       $(UV) run pyinstaller tapen.spec; \
       echo "DONE: wheel package"; \
    )

clean:
	@(rm -rf src/build dist/* *.egg-info src/*.egg-info .pytest_cache)

publish:
	@( \
       set -e; \
       if [ ! -z $(PYPI_API_KEY) ]; then export TWINE_USERNAME="__token__"; export TWINE_PASSWORD="$(PYPI_API_KEY)"; fi; \
       if [ ! -z $(PYPI_REPOSITORY_URL) ]; then  export TWINE_REPOSITORY_URL="$(PYPI_REPOSITORY_URL)"; fi; \
       echo "Uploading to PyPi"; \
	       $(UV) run twine upload -r pypi dist/*; \
       echo "DONE: Publish"; \
    )

set-version:
	@( \
		if [ -z $(VERSION) ]; then echo "Missing VERSION argument"; exit 1; fi; \
		echo '__version__ = "$(VERSION)"' > $(SRC_ROOT)/__version__.py; \
		echo "Version updated: $(VERSION)"; \
	)

deps: venv
	@( \
		set -e; \
		$(UV) sync --all-groups; \
	)

# Synchronize installed dependencies to match the lock file
.PHONY: deps-sync
deps-sync:
	@( \
		set -e; \
		echo "Syncing dependencies..."; \
		$(UV) sync --all-groups; \
		echo "DONE: all dependencies are synchronized"; \
	)

deps-update:
	@( \
		$(UV) lock --upgrade; \
	)

deps-lock:
	@( \
		$(UV) lock; \
	)

deps-tree:
	@( \
		$(UV) tree; \
	)

.PHONY: venv
venv:
	@( \
		test -x $(VIRTUAL_ENV_PATH)/bin/python || $(UV) venv --python $(PYTHON) $(VIRTUAL_ENV_PATH); \
	)

.PHONY: ruff-fix-pyupgrade
ruff-fix-pyupgrade:
	@( \
       echo "Applying pyupgrade..."; \
       $(UV) run ruff check --select UP --fix; \
       echo "DONE: pyupgrade"; \
    )

.PHONY: ruff-fix-pyupgrade-unsafe
ruff-fix-pyupgrade-unsafe:
	@( \
	   echo "Applying pyupgrade..."; \
	   $(UV) run ruff check --select UP --fix --unsafe-fixes; \
	   echo "DONE: pyupgrade"; \
	)

ruff-format:
	@( \
	   echo "Running Ruff code formatter..."; \
	   $(UV) run ruff format $(FORMAT_PATH); \
	   echo "DONE: Ruff"; \
	)

ruff-format-check:
	@( \
	   echo "Running Ruff format check..."; \
	   $(UV) run ruff format --diff $(FORMAT_PATH) || exit 1; \
	   echo "DONE: Ruff"; \
	)

ruff-import-sort:
	@( \
	   echo "Running Ruff import sort..."; \
	   $(UV) run ruff check --select I --fix; \
	   echo "DONE: Ruff"; \
	)

ruff-import-sort-check:
	@( \
	   echo "Running Ruff import sort..."; \
	   $(UV) run ruff check --select I || exit 1; \
	   echo "DONE: Ruff"; \
	)

ruff-lint:
	@( \
	   echo "Running Ruff lint..."; \
	   $(UV) run ruff check $(LINT_PATH) || exit 1; \
	   echo "DONE: Ruff"; \
	)

changelog:
	@( \
		echo "Generating changelog"; \
		set -e; \
		$(UV) run cz changelog --incremental; \
		echo "DONE: Changelog"; \
	)

print-changelog:
	@( \
		$(UV) run cz changelog --dry-run --incremental; \
	)

release:
	@( \
		echo "Preparing release"; \
		set -e; \
		$(UV) run cz bump --changelog; \
		echo "DONE: Preparing release"; \
	)

print-version:
	@( \
		$(UV) run cz version --project; \
	)
