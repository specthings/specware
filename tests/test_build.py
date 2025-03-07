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

from pathlib import Path

from specitems import ItemCache, item_is_enabled
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
        "stu", "jkl", "a/b/c/d.h", "mno", "o2i", "o2s", "abc", "def", "a", "b",
        "ghi", "th"
    ]
    files = gather_build_files(build_config, item_cache, test_header=False)
    assert files == [
        "stu", "jkl", "a/b/c/d.h", "mno", "o2i", "o2s", "abc", "def", "a", "b",
        "ghi"
    ]
    build_config["arch"] = None
    build_config["bsp"] = None
    files = gather_build_files(build_config, item_cache, test_header=False)
    assert files == ["a", "b", "ghi"]
