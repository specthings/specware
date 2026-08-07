# SPDX-License-Identifier: BSD-2-Clause
""" Tests for the command line interfaces. """

# Copyright (C) 2025 embedded brains GmbH & Co. KG
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import contextlib
import os
from pathlib import Path

from specware.cliexport import cliexport
from specware.cliexportheader import cliexportheader
from specware.clifind import clifind
from specware.cliview import cliview

from .util import get_and_clear_log

_FILES = Path(__file__).parent.absolute() / "files"
_FAKE_CLANG_FORMAT = _FILES / "clang-format"
_FAKE_CLANG_FORMAT_FAIL = _FILES / "clang-format-fail"
_FAKE_CLANG_FORMAT_UNAVAILABLE = _FILES / "clang-format-unavailable"


def _create_specview_yml(tmpdir):
    base = Path(__file__).parent.absolute()
    spec_build = base / "spec-build"
    spec_rtems = base / "spec-rtems"
    config_file = Path(tmpdir) / "specware.yml"
    with open(config_file, "w", encoding="utf-8") as out:
        out.write(f"""spec:
  cache-directory: cache
  paths:
  - {spec_build}
  - {spec_rtems}
  resolve-proxies: true
appl-config:
  doxygen-target: appl-config.h
  enabled-source: []
  enabled-documentation: []
  groups:
  - uid: /if/group-general
    target: acfg.rst
build:
  arch: foo
  bsp: bar
  enabled-set:
  - A
  build-uids:
  - /g
  base-directory-map:
  - source: {spec_build}
    target: {tmpdir}
  - source: {spec_rtems}
    target: {tmpdir}
glossary:
  project-groups:
  - /glossary-general
  project-header: Glossary
  project-target: project-glossary.md
  documents:
  - header: Glossary
    md-source-paths: []
    rest-source-paths: []
    target: glossary.md
interface:
  enabled: []
  item-level-interfaces: []
  domains: {{}}
interface-documentation:
  enabled: []
  groups:
  - directives-target: directives.rst
    group: /if/group
    introduction-target: introduction.rst
  types:
    domains: []
    groups: []
    target: types.rst
validation:
  base-directory-map:
  - source: {spec_build}
    target: {tmpdir}
  - source: {spec_rtems}
    target: {tmpdir}
spec-documentation:
  target: items.rst
  hierarchy-subsection-name: Specification Item Hierarchy
  hierarchy-text: |
    The specification item types have the following hierarchy:
  ignore: '^$'
  item-types-subsection-name: Specification Item Types
  label-prefix: SpecType
  root-type-uid: /spec/root
  section-label-prefix: ReqEng
  section-name: Specification Items
  value-types-subsection-name: Specification Attribute Sets and Value Types
""")
    return str(config_file)


def test_cliexport(tmpdir):
    config_file = _create_specview_yml(tmpdir)
    exit_code = cliexport(["command", "--config-file", config_file])
    assert exit_code == 0
    exit_code = cliexport(["command", "--config-file", config_file, "tc.c"])
    assert exit_code == 0
    exit_code = cliexport([
        "command", "--config-file", config_file, "--no-code",
        "--no-documentation", "--format=myst"
    ])
    assert exit_code == 0
    exit_code = cliexport([
        "command", "--config-file", config_file,
        "--no-application-configuration-code", "--no-interface-code",
        "--no-validation-code", "--format=rest"
    ])
    assert exit_code == 0


def test_cliexport_format_code(tmpdir, caplog):
    config_file = _create_specview_yml(tmpdir)
    exit_code = cliexport([
        "command", "--config-file", config_file, "--format-code",
        f"--clang-format-path={_FAKE_CLANG_FORMAT}",
        "--clang-format-style=llvm"
    ])
    assert exit_code == 0

    # The C language files are formatted and the assumed file name is the
    # target file path
    for name in ["tc.c", "ts.c", "th"]:
        target = Path(tmpdir) / name
        assert target.read_text(encoding="utf-8").splitlines()[0] == (
            f"/* fake clang-format: style=llvm filename={target} */")
    appl_config = Path(tmpdir) / "appl-config.h"
    assert appl_config.read_text(encoding="utf-8").splitlines()[0] == (
        "/* fake clang-format: style=llvm filename=appl-config.h */")

    # The documentation files are not formatted
    for name in ["directives.rst", "acfg.rst", "glossary.md"]:
        target = Path(tmpdir) / name
        assert "fake clang-format" not in target.read_text(encoding="utf-8")

    exit_code = cliexport([
        "command", "--config-file", config_file, "--format-code",
        f"--clang-format-path={_FAKE_CLANG_FORMAT_FAIL}"
    ])
    assert exit_code == 1
    assert "the clang-format tool failed with exit status 1: " \
        "fake clang-format cannot format this" in get_and_clear_log(caplog)

    exit_code = cliexport([
        "command", "--config-file", config_file, "--format-code",
        f"--clang-format-path={_FAKE_CLANG_FORMAT_UNAVAILABLE}"
    ])
    assert exit_code == 1
    assert (f"cannot run the clang-format tool "
            f"'{_FAKE_CLANG_FORMAT_UNAVAILABLE}': it failed with exit "
            f"status 1: fake clang-format is unavailable"
            in get_and_clear_log(caplog))

    exit_code = cliexport([
        "command", "--config-file", config_file, "--format-code",
        "--clang-format-path=there-is-no-such-clang-format"
    ])
    assert exit_code == 1
    assert ("cannot run the clang-format tool "
            "'there-is-no-such-clang-format': [Errno 2] "
            "No such file or directory" in get_and_clear_log(caplog))


def test_cliexportheader(tmpdir):
    config_file = _create_specview_yml(tmpdir)
    exit_code = cliexportheader([
        "command", "--config-file", config_file, "/if/header-empty", "header.h"
    ])
    assert exit_code == 0


def test_cliexportheader_format_code(tmpdir, caplog):
    config_file = _create_specview_yml(tmpdir)
    header = Path(tmpdir) / "header.h"
    exit_code = cliexportheader([
        "command", "--config-file", config_file, "--format-code",
        f"--clang-format-path={_FAKE_CLANG_FORMAT}", "/if/header-empty",
        str(header)
    ])
    assert exit_code == 0
    assert header.read_text(encoding="utf-8").splitlines()[0] == (
        f"/* fake clang-format: style=file filename={header} */")

    exit_code = cliexportheader([
        "command", "--config-file", config_file, "--format-code",
        f"--clang-format-path={_FAKE_CLANG_FORMAT_FAIL}", "/if/header-empty",
        str(header)
    ])
    assert exit_code == 1
    assert "the clang-format tool failed" in get_and_clear_log(caplog)

    exit_code = cliexportheader([
        "command", "--config-file", config_file, "--format-code",
        "--clang-format-path=there-is-no-such-clang-format",
        "/if/header-empty",
        str(header)
    ])
    assert exit_code == 1
    assert "cannot run the clang-format tool" in get_and_clear_log(caplog)


def test_clifind(tmpdir):
    config_file = _create_specview_yml(tmpdir)
    clifind(["command", "--config-file", config_file, "th"])


def test_cliview(tmpdir):
    config_file = _create_specview_yml(tmpdir)
    cliview(["command", "--config-file", config_file])
    cliview(["command", "--config-file", config_file, "--validated=no"])
    cliview(["command", "--config-file", config_file, "--validated=yes"])
    cliview([
        "command", "--config-file", config_file, "--filter=action-table",
        "/req/clock-gettime"
    ])
    cliview([
        "command", "--config-file", config_file, "--filter=action-list",
        "/req/clock-gettime"
    ])
    cliview([
        "command", "--config-file", config_file, "--filter=action-table",
        "/req/clock-nanosleep"
    ])
    cliview([
        "command", "--config-file", config_file, "--filter=action-table",
        "--format=commonmark", "/req/clock-nanosleep"
    ])
    cliview([
        "command", "--config-file", config_file,
        "--filter=action-compact-table", "/req/clock-nanosleep"
    ])
    cliview([
        "command", "--config-file", config_file,
        "--filter=action-compact-table", "--format=commonmark",
        "/req/clock-nanosleep"
    ])
    cliview([
        "command", "--config-file", config_file,
        "--filter=action-compact-table", "--format=myst",
        "/req/clock-nanosleep"
    ])
    cliview([
        "command", "--config-file", config_file, "--filter=action-list",
        "/req/clock-nanosleep"
    ])
    cliview(["command", "--config-file", config_file, "--filter=action-stats"])
    cliview([
        "command", "--config-file", config_file,
        "--filter=action-table-show-skip", "/req/clock-nanosleep"
    ])
    cliview([
        "command", "--config-file", config_file,
        "--filter=action-table-show-skip", "--format=myst",
        "/req/clock-nanosleep"
    ])
    cliview(["command", "--config-file", config_file, "--filter=orphan"])
    cliview(
        ["command", "--config-file", config_file, "--filter=no-validation"])
    cliview(["command", "--config-file", config_file, "--filter=api"])
    cliview(["command", "--config-file", config_file, "--filter=design"])
    cliview(["command", "--config-file", config_file, "--filter=types"])
    cliview(["command", "--config-file", config_file, "--filter=build"])


def _spec_rtems(*names):
    base = Path(__file__).parent.absolute() / "spec-rtems"
    return [str(base.joinpath(*name.split("/"))) for name in names]


def test_cliexport_items(tmpdir):
    config_file = _create_specview_yml(tmpdir)

    # A test case is associated with its test source file only.
    exit_code = cliexport(["command", "--config-file", config_file] +
                          _spec_rtems("val/tc.yml"))
    assert exit_code == 0
    assert os.path.exists(os.path.join(tmpdir, "tc.c"))
    assert not os.path.exists(os.path.join(tmpdir, "ts.c"))
    assert not os.path.exists(os.path.join(tmpdir, "appl-config.h"))

    # Documentation is not exported if a target is present.
    assert not os.path.exists(os.path.join(tmpdir, "items.rst"))

    # A target file and a specification item file combine.
    exit_code = cliexport(["command", "--config-file", config_file, "ts.c"] +
                          _spec_rtems("val/tc.yml"))
    assert exit_code == 0
    assert os.path.exists(os.path.join(tmpdir, "ts.c"))

    # An interface item selects its header file.  The interface domain is
    # not configured in this test, so no header file is written.
    exit_code = cliexport(["command", "--config-file", config_file] +
                          _spec_rtems("if/errno.yml"))
    assert exit_code == 0

    # An application configuration option regenerates the Doxygen header file.
    exit_code = cliexport(["command", "--config-file", config_file] +
                          _spec_rtems("if/disable-newlib-reentrancy.yml"))
    assert exit_code == 0
    assert os.path.exists(os.path.join(tmpdir, "appl-config.h"))
    assert not os.path.exists(os.path.join(tmpdir, "acfg.rst"))


def test_cliexport_items_without_association(tmpdir):
    config_file = _create_specview_yml(tmpdir)

    # A glossary term is associated with no source file at all.
    exit_code = cliexport(["command", "--config-file", config_file] +
                          _spec_rtems("glossary-empty.yml"))
    assert exit_code == 0
    assert not os.path.exists(os.path.join(tmpdir, "tc.c"))
    assert not os.path.exists(os.path.join(tmpdir, "appl-config.h"))

    # The code generation is disabled.
    exit_code = cliexport(
        ["command", "--config-file", config_file, "--no-code"] +
        _spec_rtems("val/tc.yml"))
    assert exit_code == 0
    assert not os.path.exists(os.path.join(tmpdir, "tc.c"))

    # The interface and application configuration code generation is disabled.
    exit_code = cliexport([
        "command", "--config-file", config_file, "--no-interface-code",
        "--no-application-configuration-code"
    ] + _spec_rtems("if/disable-newlib-reentrancy.yml"))
    assert exit_code == 0
    assert not os.path.exists(os.path.join(tmpdir, "appl-config.h"))


def test_cliexport_unknown_item(tmpdir, caplog):
    config_file = _create_specview_yml(tmpdir)
    unknown = os.path.join(tmpdir, "unknown.yml")

    exit_code = cliexport(["command", "--config-file", config_file, unknown])
    assert exit_code == 1
    assert get_and_clear_log(caplog) == (
        "ERROR no specification item is associated with the file "
        f"'{os.path.realpath(unknown)}'")
    assert not os.path.exists(os.path.join(tmpdir, "tc.c"))


def test_cliexport_item_via_symlink(tmpdir):
    config_file = _create_specview_yml(tmpdir)
    link = Path(tmpdir) / "tc-link.yml"
    link.symlink_to(_spec_rtems("val/tc.yml")[0])

    exit_code = cliexport(["command", "--config-file", config_file, str(link)])
    assert exit_code == 0
    assert os.path.exists(os.path.join(tmpdir, "tc.c"))


def test_cliexport_item_via_two_paths(tmpdir):
    config_file = _create_specview_yml(tmpdir)
    real = _spec_rtems("val/tc.yml")[0]
    link = Path(tmpdir) / "tc-link.yml"
    link.symlink_to(real)

    # The same item reached through its real path and through a symbolic link
    # resolves to one UID.
    exit_code = cliexport(
        ["command", "--config-file", config_file, real,
         str(link)])
    assert exit_code == 0
    assert os.path.exists(os.path.join(tmpdir, "tc.c"))
