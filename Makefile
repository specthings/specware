# SPDX-License-Identifier: BSD-2-Clause

# Copyright (C) 2026 embedded brains GmbH & Co. KG

PACKAGE = specware

VENV ?= .venv

EXCLUDED_FILES =

PY_SRC_FILES = $(filter-out $(EXCLUDED_FILES), $(wildcard src/$(PACKAGE)/*.py))

PY_ALL_FILES = $(filter-out $(EXCLUDED_FILES), $(PY_SRC_FILES) $(wildcard tests/*.py))

all: src/$(PACKAGE)/spec.pickle format analyse check

format: $(PY_ALL_FILES) | prepare
	uv run yapf -i --parallel $^

analyse: $(PY_SRC_FILES) | prepare
	uv run flake8 $^
	uv run mypy $^
	uv run pylint --disable=duplicate-code $^

check: src/$(PACKAGE)/spec.pickle | prepare
	uv run pytest -vv

dist: all
	uv build

devel-publish: all
	test -z "`git status --short`"
	uv version --bump=dev
	uv sync
	git ci -m "feat: Development release `uv version --short`" pyproject.toml uv.lock
	git tag "devel/`uv version --short`"
	git push upstream
	git push upstream --tags

publish: all
	test -z "`git status --short`"
	uv version --bump=stable
	uv sync
	git ci -m "feat: Stable release `uv version --short`" pyproject.toml uv.lock
	git tag "release/`uv version --short`"
	uv version --bump=patch --bump=dev
	uv sync
	git ci -m "feat: Start development `uv version --short`" pyproject.toml uv.lock
	git push upstream
	git push upstream --tags

src/$(PACKAGE)/spec.pickle: spec-types/spec/* | prepare
	uv run specpickle spec-types src/$(PACKAGE)/spec.pickle

VENV_MARKER = $(VENV)/uv-sync-marker

prepare: $(VENV_MARKER)

$(VENV_MARKER): uv.lock
	uv sync --all-groups
	touch $@

ifndef CI
uv.lock: pyproject.toml
	uv lock
	touch $@
endif

docs/source/items.rst: src/$(PACKAGE)/spec.pickle
	uv run specdocitems --format=rest docs/source/items.rst

.PHONY: docs
docs: | docs/source/items.rst
	uv run make -C docs html
