VIRTUAL_ENV_PATH=venv
SKIP_VENV="${NO_VENV}"

SHELL := /bin/bash
PYTHON := python3.14
POETRY := poetry

PYPI_API_KEY :=
PYPI_REPOSITORY_URL :=
ALPHA_VERSION :=
SRC_ROOT := ./src
ROOT_PACKAGE := tapen
FORMAT_PATH := $(SRC_ROOT)

POETRY_GROUPS := dev

.DEFAULT_GOAL := pre_commit

pre_commit: pre_commit_hook lint

UNAME_S := $(shell uname -s)

ifeq ($(UNAME_S),Darwin)
    SED_COMMAND := gsed
else
    SED_COMMAND := sed
endif

define activate_venv
  if [ -z $(SKIP_VENV) ]; then source $(VIRTUAL_ENV_PATH)/bin/activate; fi;
endef

pre_commit_hook:
	@( \
		$(call activate_venv) \
		pre-commit run --all --hook-stage=commit; \
	)

verify-prerequisites:
	@(development/ensure-dependencies.sh)

setup: verify-prerequisites venv deps
	@( \
		$(call activate_venv) \
		pre-commit install; \
		echo "Pre-commit hooks installed"; \
		./development/install-cli-commands.sh "$(VIRTUAL_ENV_PATH)" "$(SRC_ROOT)"; \
		echo "DONE: setup"; \
	)

copyright:
	@( \
       $(call activate_venv) \
       echo "Applying copyright..."; \
       for p in $(FORMAT_PATH); do \
       	 licenseheaders -t ./development/copyright.tmpl -E ".py" -cy -d $$p; \
       done; \
       echo "DONE: copyright"; \
    )

mypy:
	@( \
       set -e; \
       $(call activate_venv) \
       echo "Running MyPy checks..."; \
       mypy --show-error-codes $(SRC_ROOT)/tapen; \
       mypy --show-error-codes $(SRC_ROOT)/ptouch_py; \
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
       $(call activate_venv) \
       echo "Building wheel package..."; \
       poetry build; \
       echo "DONE: wheel package"; \
    )

package:
	@( \
		echo "Building packages"; \
		set -e; \
		$(call activate_venv) \
		poetry build; \
		echo "DONE: Building packages"; \
	)

single-binary:
	@( \
	   set -e; \
       $(call activate_venv) \
       echo "Building single binary"; \
       bash -c "pyinstaller tapen.spec"; \
       echo "DONE: wheel package"; \
    )

clean:
	@(rm -rf src/build dist/* *.egg-info src/*.egg-info .pytest_cache)

publish:
	@( \
       set -e; \
       $(call activate_venv) \
       if [ ! -z $(PYPI_API_KEY) ]; then export TWINE_USERNAME="__token__"; export TWINE_PASSWORD="$(PYPI_API_KEY)"; fi; \
       if [ ! -z $(PYPI_REPOSITORY_URL) ]; then  export TWINE_REPOSITORY_URL="$(PYPI_REPOSITORY_URL)"; fi; \
       echo "Uploading to PyPi"; \
       twine upload -r pypi dist/*; \
       echo "DONE: Publish"; \
    )

set-version:
	@( \
		if [ -z $(VERSION) ]; then echo "Missing VERSION argument"; exit 1; fi; \
		echo '__version__ = "$(VERSION)"' > $(SRC_ROOT)/__version__.py; \
		echo "Version updated: $(VERSION)"; \
	)

deps:
	@( \
		set -e; \
		$(call activate_venv) \
		$(POETRY) install --all-extras --no-root --with "$(POETRY_GROUPS)";; \
	)

# Synchronize installed dependencies to match the lock file
.PHONY: deps-sync
deps-sync:
	@( \
		$(call activate_venv) \
		set -e; \
		echo "Syncing dependencies..."; \
		$(POETRY) sync --all-extras --no-root --with "$(POETRY_GROUPS)"; \
		echo "DONE: all dependencies are synchronized"; \
	)

deps-update:
	@( \
		$(call activate_venv) \
		$(POETRY) update; \
	)

deps-lock:
	@( \
		$(call activate_venv) \
		$(POETRY) lock \
	)

deps-tree:
	@( \
		$(call activate_venv) \
		$(POETRY) show --tree; \
	)

.PHONY: venv
venv:
	@( \
		python3 -m venv $(VIRTUAL_ENV_PATH); \
		source $(VIRTUAL_ENV_PATH)/bin/activate; \
	)

.PHONY: ruff-fix-pyupgrade
ruff-fix-pyupgrade:
	@( \
	   $(call activate_venv) \
       echo "Applying pyupgrade..."; \
       ruff check --select UP --fix; \
       echo "DONE: pyupgrade"; \
    )

.PHONY: ruff-fix-pyupgrade-unsafe
ruff-fix-pyupgrade-unsafe:
	@( \
	   $(call activate_venv) \
	   echo "Applying pyupgrade..."; \
	   ruff check --select UP --fix --unsafe-fixes; \
	   echo "DONE: pyupgrade"; \
	)

ruff-format:
	@( \
	   $(call activate_venv) \
	   echo "Running Ruff code formatter..."; \
	   ruff format $(FORMAT_PATH); \
	   echo "DONE: Ruff"; \
	)

ruff-format-check:
	@( \
	   $(call activate_venv) \
	   echo "Running Ruff format check..."; \
	   ruff format --diff $(FORMAT_PATH) || exit 1; \
	   echo "DONE: Ruff"; \
	)

ruff-import-sort:
	@( \
	   $(call activate_venv) \
	   echo "Running Ruff import sort..."; \
	   ruff check --select I --fix; \
	   echo "DONE: Ruff"; \
	)

ruff-import-sort-check:
	@( \
	   $(call activate_venv) \
	   echo "Running Ruff import sort..."; \
	   ruff check --select I || exit 1; \
	   echo "DONE: Ruff"; \
	)

ruff-lint:
	@( \
	   $(call activate_venv) \
	   echo "Running Ruff link..."; \
	   ruff check $(LINT_PATH) || exit 1; \
	   echo "DONE: Ruff"; \
	)

changelog:
	@( \
		echo "Generating changelog"; \
		set -e; \
		$(call activate_venv) \
		cz changelog --incremental; \
		echo "DONE: Changelog"; \
	)

print-changelog:
	@( \
		$(call activate_venv) \
		cz changelog --dry-run --incremental; \
	)

release:
	@( \
		echo "Preparing release"; \
		set -e; \
		$(call activate_venv) \
		cz bump --changelog; \
		echo "DONE: Preparing release"; \
	)

print-version:
	@( \
		$(call activate_venv) \
		cz version --project; \
	)
