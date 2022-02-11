VIRTUAL_ENV_PATH=venv
SKIP_VENV="${NO_VENV}"

SHELL := /bin/bash

PYPI_API_KEY :=
PYPI_REPOSITORY_URL :=
ALPHA_VERSION :=
SRC_ROOT := ./src

.DEFAULT_GOAL := pre_commit

pre_commit: copyright format lint
setup: venv deps

copyright:
	@( \
       if [ -z $(SKIP_VENV) ]; then source $(VIRTUAL_ENV_PATH)/bin/activate; fi; \
       echo "Applying copyright..."; \
       ./development/copyright-update; \
       echo "DONE: copyright"; \
    )

flake8:
	@( \
       set -e; \
       if [ -z $(SKIP_VENV) ]; then source $(VIRTUAL_ENV_PATH)/bin/activate; fi; \
       echo "Running Flake8 checks..."; \
       flake8 $(SRC_ROOT) --count --statistics; \
       \
       echo "DONE: Flake8"; \
    )

mypy:
	@( \
       set -e; \
       if [ -z $(SKIP_VENV) ]; then source $(VIRTUAL_ENV_PATH)/bin/activate; fi; \
       echo "Running MyPy checks..."; \
       mypy --show-error-codes $(SRC_ROOT)/tapen; \
       mypy --show-error-codes $(SRC_ROOT)/ptouch_py; \
       \
       echo "DONE: MyPy"; \
    )

format:
	@( \
       if [ -z $(SKIP_VENV) ]; then source $(VIRTUAL_ENV_PATH)/bin/activate; fi; \
       echo "Running Black code formatter..."; \
       black $(SRC_ROOT)/tapen $(SRC_ROOT)/ptouch_py; \
       \
       echo "DONE: Black"; \
    )

check-format:
	@( \
       if [ -z $(SKIP_VENV) ]; then source $(VIRTUAL_ENV_PATH)/bin/activate; fi; \
       echo "Running Black format check..."; \
       black --check $(SRC_ROOT)/tapen $(SRC_ROOT)/ptouch_py; \
       \
       echo "DONE: Black format check"; \
    )
	

lint: flake8 mypy check-format

build: copyright format lint clean
	@( \
	   set -e; \
       if [ -z $(SKIP_VENV) ]; then source $(VIRTUAL_ENV_PATH)/bin/activate; fi; \
       echo "Building wheel package..."; \
       bash -c "cd src && VERSION_OVERRIDE="$(ALPHA_VERSION)" python ./setup.py bdist_wheel --dist-dir=../dist --bdist-dir=../build"; \
       echo "DONE: wheel package"; \
    )
	@( \
	   set -e; \
       if [ -z $(SKIP_VENV) ]; then source $(VIRTUAL_ENV_PATH)/bin/activate; fi; \
       echo "Building source distribution..."; \
       bash -c "cd src && VERSION_OVERRIDE="$(ALPHA_VERSION)" python ./setup.py sdist --dist-dir=../dist"; \
       echo "DONE: source distribution"; \
    )

clean:
	@(rm -rf src/build dist/* *.egg-info src/*.egg-info .pytest_cache)

publish:
	@( \
       set -e; \
       if [ -z $(SKIP_VENV) ]; then source $(VIRTUAL_ENV_PATH)/bin/activate; fi; \
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
		source ./venv/bin/activate; \
		pip install -r ./requirements-dev.txt; \
	)

venv:
	@( \
		virtualenv $(VIRTUAL_ENV_PATH); \
		source ./venv/bin/activate; \
	)
