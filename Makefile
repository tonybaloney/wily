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
	ruff .
	@# TODO(skarzi): fix type hints and require `mypy` to pass
	mypy --install-types --non-interactive src || true

.PHONY: lint_formatting
lint_formatting:
	black --check .

.PHONY: lint_spelling
lint_spelling:
	codespell

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
