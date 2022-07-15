SHELL:=/usr/bin/env bash


build:
	flit build

install:
	flit install

extract_messages:
	find src/wily -iname "*.py" | xargs xgettext -o src/wily/locales/messages.pot
	find src/wily/locales -name \*.po -execdir msgmerge {} -U ../../../../../src/wily/locales/messages.pot \;

compile_messages:
	find src/wily/locales -name \*.po -execdir msgfmt {} -o messages.mo \;

.PHONY: lint_python
lint_python:
	flake8 .
	@# TODO(skarzi): fix type hitings and require `mypy` to pass
	mypy . || true
	bandit --configfile pyproject.toml --recursive .
	pydocstyle src/wily
	find . -type f -name '*.py' | xargs pyupgrade --py37-plus

.PHONY: lint_formatting
lint_formatting:
	@# TODO(skarzi): apply `black` on codebase and require it to pass
	black --check . || true
	@# TODO(skarzi): apply `isort` on codebase and require it to pass
	isort --check-only . || true

.PHONY: lint_spelling
lint_spelling:
	codespell || true

.PHONY: lint_deps
lint_deps:
	pip check
	safety check --full-report

.PHONY: lint
lint: lint_python lint_formatting lint_spelling lint_deps

.PHONY: test
test:
	pytest

.PHONY: ci
ci: lint test
