<!--
SPDX-License-Identifier: CC-BY-SA-4.0

Copyright (C) 2026 embedded brains GmbH & Co. KG
-->
# AGENTS.md

## Build and test

Run `make` before a commit. It regenerates `src/specware/spec.pickle`, formats,
analyses `src/` and runs the tests. CI runs `make` and fails on any diff which
it leaves in the tree.

`pyproject.toml` makes `pytest` fail below 100 % line and branch coverage. Run
a single test with `--no-cov`:

```
uv run pytest --no-cov tests/test_interface.py::test_interface_item_marker
```

Git tracks `src/specware/spec.pickle`. Regenerate it with `make` after each
edit of `spec-types/spec/`.

`make analyse` runs `reuse lint`. A new file needs an SPDX header or an entry
in `REUSE.toml`. Enclose license identifiers which a file holds as data in
`REUSE-IgnoreStart` and `REUSE-IgnoreEnd` comments.

## Architecture

specware builds on the item model of
[specitems](https://github.com/specthings/specitems). It adds the types of a
software specification and generates C code and documentation from the items.

- `spec.pickle` holds the types of `spec-types/spec/`. The entry point
  `specitems_type_provider.plugins` hands them to specitems.
  `SpecWareTypeProvider` in `util.py` adds them to an item cache.
- `specwareexport` runs the tasks of a configuration item such as
  `tests/specitems.yml`. The `task-type` selects the generator.

| Task type | Generator |
| --------- | --------- |
| `interface` | `interface.py`, C headers in the RTEMS or the Zephyr style |
| `interface-documentation` | `interfacedoc.py` |
| `appl-config` | `applconfig.py` |
| `doxygen-glossary` | `doxygenglossary.py`, a Doxygen page of the glossary terms |
| `validation` | `validation.py`, C test code, with `transitionmap.py` for action requirements |

`contentc.py` holds `CContent`, the C variant of the specitems `Content`.
`rtems.py` holds the rules which only the RTEMS specification needs.

## Tests

`create_item_cache()` in `tests/util.py` loads the fixture trees in
`tests/spec-*/` in place. It writes the cache into `tmpdir`. A test of a
generator compares the generated file with the expected text inline in
the test. `tests/files/clang-format` is a fake formatter which marks the text
which it formats.

## Commits

A commit message follows Conventional Commits with a sentence-case subject. The
scope is the module name, or `spec` for `spec-types/`. Add the `Assisted-by:`
and `Signed-off-by:` trailers as `CONTRIBUTING.md` prescribes. Run
`make commitlint` before a push. Only a maintainer runs `make publish` or
`make devel-publish`.
