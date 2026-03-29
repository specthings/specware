# SPDX-License-Identifier: BSD-2-Clause
""" Provides methods used by tests. """

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

import os

from specitems import ItemCache, ItemCacheConfig, item_is_enabled, load_data

from specware import SpecWareTypeProvider


def create_item_cache(tmp_dir: str, spec_dir: str | list[str]) -> ItemCache:
    """
    Create an item cache configuration and copies a specification
    directory to the temporary tests directory.
    """
    if isinstance(spec_dir, str):
        spec_dir = [spec_dir]
    base = os.path.dirname(__file__)
    config = ItemCacheConfig(paths=[
        os.path.normpath(os.path.join(base, path)) for path in spec_dir
    ],
                             cache_directory=os.path.normpath(
                                 os.path.join(tmp_dir, "cache")))
    uid = "/spec/other"
    other_types = {uid: load_data(os.path.join(base, f"spec-types/{uid}.yml"))}
    return ItemCache(config,
                     type_provider=SpecWareTypeProvider(other_types),
                     is_item_enabled=item_is_enabled)


def get_and_clear_log(the_caplog) -> str:
    log = "\n".join(f"{rec.levelname} {rec.message}"
                    for rec in the_caplog.records)
    the_caplog.clear()
    return log
