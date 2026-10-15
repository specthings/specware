# SPDX-License-Identifier: BSD-2-Clause
""" Tests for the quality model item type. """

# Copyright (C) 2026 embedded brains GmbH & Co. KG
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

import logging
from pathlib import Path
import shutil

from specitems import load_data, save_data, verify_specification_format

from .util import create_item_cache


def test_quality_model(caplog, tmpdir):
    item_cache = create_item_cache(tmpdir, "spec-quality-model")
    item = item_cache["/defs/quality-model"]
    assert item.type == "quality-model"
    assert item["thresholds"]["lines-of-code"] == 500
    assert item["thresholds"]["rid-action-status"] is None
    status = verify_specification_format(item_cache)
    assert status.critical == 0
    assert status.error == 0

    spec_dir = Path(tmpdir) / "spec"
    shutil.copytree(Path(__file__).parent / "spec-quality-model", spec_dir)
    item_file = spec_dir / "defs" / "quality-model.yml"
    data = load_data(str(item_file))
    data.pop("_file", None)
    del data["thresholds"]["lines-of-code"]
    save_data(str(item_file), data)
    item_cache = create_item_cache(tmpdir, str(spec_dir))
    caplog.set_level(logging.WARNING)
    status = verify_specification_format(item_cache)
    assert status.error == 1
    assert ("/defs/quality-model:/thresholds: missing mandatory keys "
            "for type 'quality-model-thresholds': ['lines-of-code']"
            ) in caplog.text
