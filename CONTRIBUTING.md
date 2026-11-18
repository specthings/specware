<!--
SPDX-License-Identifier: CC-BY-SA-4.0

Copyright (C) 2026 embedded brains GmbH & Co. KG
-->
## Submitting issues

Please submit issues related to the *specware* project through
[Github specware issues](https://github.com/specthings/specware/issues).

## Contributing to the project

### Python development guidelines

The project tries to follow the
[PEP 8 - Style Guide for Python Code](https://www.python.org/dev/peps/pep-0008/)
and the
[Google Python Style Guide](https://google.github.io/styleguide/pyguide.html).
If the Google and PEP 8 guidelines disagree with each other, the PEP 8
guidelines have precedence.

For documenting Python code, use the
[Google Python documentation style](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)
in the imperative form.

The [yapf](https://github.com/google/yapf>) Python code formatter with
default settings (PEP 8 formatting) is used by the project.

The `flake8` and `pylint` static analysis tools for Python with default
settings are used by the project.

Use type annotations for contributions.  The `mypy` static type checker is used
by the project.

Type annotations and the use of analysis tools is not required for test code.

### Tests

Use `pytest` for tests.  Run `make check` to run the tests.  Make sure the code
and branch coverage stays at 100% when you make a contribution.

### Conventional commits

Use [Conventional Commits](https://www.conventionalcommits.org) for your commit
messages.
```
feat(items): Add foobar support
```

The CI checks each commit message against `commitlint.yml`.  To run the same
check before a push, run `make commitlint`.  It checks the commits since `main`
and needs `npm`.  Set `COMMIT_BASE` to check against another branch.  To check
each message at commit time, run `make hooks` once.  It installs a `commit-msg`
hook.

### Sign your work

We use the
[Developer Certificate of Origin (DCO)](https://github.com/specthings/specware/blob/main/DCO.txt)
which is included in the repository.  Please read this text.  If you can
certify it, then add a line like this to every Git commit message of your
contributions:

```
Signed-off-by: Erika Mustermann <erika.mustermann@example.com>
```

Use your real name for contributions to this project.

### Disclose assistance

A commit which a coding assistant helped to write carries an `Assisted-by:`
line immediately before `Signed-off-by:`.  Use the form
`AGENT_NAME:MODEL_VERSION [TOOL1] [TOOL2]` of the Linux kernel document
[Documentation/process/coding-assistants.rst](https://docs.kernel.org/process/coding-assistants.html):

```
Assisted-by: Claude:claude-opus-5-5 claude-code
Signed-off-by: Erika Mustermann <erika.mustermann@example.com>
```

Take the model version from the assistant session.  Drop a deployment suffix
such as `[1m]`.  List only coding assistants and specialised analysis tools.
Git, the compiler and the editor are not tools in this sense.

The person who certifies the DCO signs off.  An assistant never signs off and
never appears in a `Co-authored-by:` line.
