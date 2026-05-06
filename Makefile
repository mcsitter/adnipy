.PHONY: help init check lint test test-all coverage docs servedocs clean clean-build clean-pyc clean-test clean-docs dist install release check-deps
.DEFAULT_GOAL := help

VENV_DIR := .venv
PYTHON := $(VENV_DIR)/bin/python
PIP := $(VENV_DIR)/bin/pip
SYSTEM_PYTHON := python3

BROWSER := $(PYTHON) -c

define BROWSER_PYSCRIPT
import os, webbrowser, sys
from urllib.request import pathname2url
webbrowser.open("file://" + pathname2url(os.path.abspath(sys.argv[1])))
endef
export BROWSER_PYSCRIPT

define PRINT_HELP_PYSCRIPT
import re, sys
for line in sys.stdin:
    match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
    if match:
        print("%-20s %s" % match.groups())
endef
export PRINT_HELP_PYSCRIPT

help:
	@$(SYSTEM_PYTHON) -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

$(VENV_DIR):
	$(SYSTEM_PYTHON) -m venv $(VENV_DIR)
	$(PIP) install --upgrade pip

init: $(VENV_DIR) ## initialize environment
	$(PIP) install -r requirements_dev.txt
	$(PYTHON) -m pre_commit install

check: $(VENV_DIR) ## run pre-commit checks
	$(PYTHON) -m pre_commit run --all-files

lint: $(VENV_DIR) ## lint code
	$(PYTHON) -m flake8 adnipy tests

test: $(VENV_DIR) ## run tests
	$(PYTHON) -m pytest

test-all: $(VENV_DIR) ## run tox
	$(PYTHON) -m tox

coverage: $(VENV_DIR) ## coverage report
	$(PYTHON) -m coverage run --source adnipy -m pytest
	$(PYTHON) -m coverage report -m
	$(PYTHON) -m coverage html
	$(PYTHON) -c "$$BROWSER_PYSCRIPT" htmlcov/index.html

docs: ## build docs
	sphinx-apidoc -o docs adnipy
	$(MAKE) -C docs clean
	$(MAKE) -C docs html
	$(PYTHON) -c "$$BROWSER_PYSCRIPT" docs/_build/html/index.html

servedocs: docs ## live docs
	watchmedo shell-command -p '*.rst' -c '$(MAKE) -C docs html' -R -D .

clean: clean-build clean-pyc clean-test clean-docs ## full clean

clean-build:
	rm -rf build dist .eggs *.egg-info

clean-pyc:
	find . -name '*.pyc' -delete
	find . -name '__pycache__' -delete

clean-test:
	rm -rf .tox .pytest_cache .coverage htmlcov

clean-docs:
	rm -f docs/adnipy.rst docs/modules.rst

dist: $(VENV_DIR) clean ## build package
	$(PYTHON) -m build

install: $(VENV_DIR) ## install package locally
	$(PIP) install .

release: dist ## upload package
	twine upload dist/*

check-deps: $(VENV_DIR) ## SPEC0 dependency check
	$(PYTHON) scripts/check_spec0.py
