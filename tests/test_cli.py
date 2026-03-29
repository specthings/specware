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
from pathlib import Path

from specware.cliexport import cliexport
from specware.cliexportheader import cliexportheader
from specware.cliverify import cliverify
from specware.cliview import cliview

from .util import get_and_clear_log


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
    cliexport(["command", "--config-file", config_file])
    cliexport(["command", "--config-file", config_file, "tc.c"])


def test_cliexportheader(tmpdir):
    config_file = _create_specview_yml(tmpdir)
    cliexportheader([
        "command", "--config-file", config_file, "/if/header-empty", "header.h"
    ])


def test_cliverify(tmpdir, caplog):
    spec_dir = Path(__file__).parent / "spec-types"
    with contextlib.chdir(tmpdir):
        cliverify(["command", "--log-level=ERROR", str(spec_dir)])
    assert get_and_clear_log(caplog) == ""


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
        "command", "--config-file", config_file,
        "--filter=action-compact-table", "/req/clock-nanosleep"
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
    cliview(["command", "--config-file", config_file, "--filter=orphan"])
    cliview(
        ["command", "--config-file", config_file, "--filter=no-validation"])
    cliview(["command", "--config-file", config_file, "--filter=api"])
    cliview(["command", "--config-file", config_file, "--filter=design"])
    cliview(["command", "--config-file", config_file, "--filter=types"])
    cliview(["command", "--config-file", config_file, "--filter=build"])
