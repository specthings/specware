# SPDX-License-Identifier: BSD-2-Clause
"""
Provides a command line interface to find the items related to generated files.
"""

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

import argparse
import contextlib
import itertools
import os
import sys

from specitems import Item, ItemCache, ItemCacheConfig, create_config
from specware import (SpecWareTypeProvider, get_items_by_type_map,
                      get_benchmark_and_test_suite_items,
                      get_interface_and_requirement_items,
                      get_validation_items, load_specware_config)


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=clifind.__doc__)
    parser.add_argument("--config-file",
                        type=str,
                        default=None,
                        help="use this configuration file")
    parser.add_argument("files",
                        metavar="FILE",
                        nargs="*",
                        help="find and list the related items of this file")
    return parser.parse_args(argv[1:])


def _process_item_data(cwd: str, file_to_item: dict[str, list[str]],
                       item: Item, data: dict) -> None:
    for name in ("target", "test-target"):
        target = data.get(name)
        if isinstance(target, str):
            file_to_item.setdefault(target, []).append(
                os.path.normpath(os.path.relpath(item.file, cwd)))


def clifind(argv: list[str] = sys.argv) -> None:
    """ Find the items related to generated files. """
    cwd = os.getcwd()
    args = _parse_args(argv)
    config, working_directory = load_specware_config(args.config_file)
    with contextlib.chdir(working_directory):
        item_cache = ItemCache(create_config(config["spec"], ItemCacheConfig),
                               type_provider=SpecWareTypeProvider({}))
        file_to_item: dict[str, list[str]] = {}
        items_by_type = get_items_by_type_map(item_cache.values())
        for item in itertools.chain(
                get_interface_and_requirement_items(items_by_type),
                get_validation_items(items_by_type),
                get_benchmark_and_test_suite_items(items_by_type)):
            _process_item_data(cwd, file_to_item, item, item.data)
            data = item.get("test-header")
            if data is not None:
                _process_item_data(cwd, file_to_item, item, data)
        items: set[str] = set()
        for file in args.files:
            file = os.path.normpath(file)
            items.update(file_to_item.get(file, tuple()))
        print("\n".join(sorted(items)))
