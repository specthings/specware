# SPDX-License-Identifier: BSD-2-Clause
""" Tests for the build module. """

# Copyright (C) 2020 embedded brains GmbH & Co. KG
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

import shutil
from pathlib import Path

from specitems import (ItemCache, SpecYAMLFormatter, item_is_enabled,
                       verify_specification_format)
from specware import gather_build_files

from .util import create_item_cache


def test_build(tmpdir):
    item_cache = create_item_cache(tmpdir, "spec-build")

    build_config = {}
    build_config["arch"] = "foo"
    build_config["bsp"] = "bar"
    build_config["enabled-set"] = ["A"]

    base = Path(__file__).parent.absolute()
    build_config["base-directory-map"] = [{
        "source": str(base / "spec-build"),
        "target": str(base / "files")
    }]
    build_config["build-uids"] = ["/g"]
    files = gather_build_files(build_config, item_cache)
    assert files == [
        "stu", "jkl", "a/b/c/d.h", "mno", "o2i", "o2s", "abc", "def", "ts.c",
        "tc.c", "tc-b.c", "tc-clock-gettime.c", "tc-clock-nanosleep.c",
        "tc-barrier-performance.c", "a", "b", "ghi", "th"
    ]
    files = gather_build_files(build_config, item_cache, test_header=False)
    assert files == [
        "stu", "jkl", "a/b/c/d.h", "mno", "o2i", "o2s", "abc", "def", "ts.c",
        "tc.c", "tc-b.c", "tc-clock-gettime.c", "tc-clock-nanosleep.c",
        "tc-barrier-performance.c", "a", "b", "ghi"
    ]
    build_config["arch"] = None
    build_config["bsp"] = None
    files = gather_build_files(build_config, item_cache, test_header=False)
    assert files == [
        "ts.c", "tc.c", "tc-b.c", "tc-clock-gettime.c", "tc-clock-nanosleep.c",
        "tc-barrier-performance.c", "a", "b", "ghi"
    ]


def test_build_action_format(tmpdir):
    spec_dir = Path(tmpdir) / "spec"
    shutil.copytree(Path(__file__).parent / "spec-build-format", spec_dir)
    item_cache = create_item_cache(tmpdir, str(spec_dir))
    formatter = SpecYAMLFormatter(clang_format_path="clang-format",
                                  clang_format_style={},
                                  indent_lists=False)
    status = verify_specification_format(item_cache, formatter=formatter)
    assert status.critical == 0
    assert status.error == 0
    hex_actions = (spec_dir / "hex.yml").read_text(encoding="utf-8")
    assert """actions:
- get-integer: null
- assert-aligned: 0x00001000
- assert-eq: 0x00004000
- assert-ge: 0x00001000
- assert-gt: 0x00000000
- assert-in-set:
  - 0x00001000
  - 0x00002000
- assert-le: 0x00010000
- assert-lt: 0x00020000
- assert-ne: 0x00003000
- format-and-define: null
""" in hex_actions
    assert "  value: 0x00004000\n" in hex_actions
    dec_actions = (spec_dir / "dec.yml").read_text(encoding="utf-8")
    assert """actions:
- get-integer: null
- assert-aligned: 16
- assert-eq: true
- assert-ge: 1
- assert-in-set:
  - 16
  - abc
- assert-le: ABC
- format-and-define: null
""" in dec_actions
    assert "  value: 32\n" in dec_actions
