default:
	@echo "an explicit target is required"

SHELL=/usr/bin/env bash

PYTHON_FILES=gitmine/*.py gitmine/commands/*.py

install:
	pip install -r requirements.txt

lint:
	pylint $(PYTHON_FILES)

docstyle:
	pydocstyle --convention=google $(PYTHON_FILES)

mypy:
	mypy $(PYTHON_FILES)

flake8:
	flake8 $(PYTHON_FILES)

SORT=LC_ALL=C sort --key=1,1 --key=3V --field-separator="="

reqs-fix:
	$(SORT) --output=requirements.txt requirements.txt
	$(SORT) --output=requirements-dev.txt requirements-dev.txt

reqs-check:
	$(SORT) --check requirements.txt
	$(SORT) --check requirements-dev.txt

black-fix:
	isort $(PYTHON_FILES)
	black --config pyproject.toml $(PYTHON_FILES)

black-check:
	isort --check $(PYTHON_FILES)
	black --config pyproject.toml --check $(PYTHON_FILES)

check: reqs-check black-check flake8 mypy lint docstyle
