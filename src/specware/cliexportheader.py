# SPDX-License-Identifier: BSD-2-Clause
"""
Provides a command line interface to exports the specified header to a header
file.
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
import sys
import logging
from typing import Optional

from specitems import (ClangFormatter, Item, LicenseProvider,
                       check_license_items, create_content_context,
                       item_is_enabled, yield_tasks)

from specware import (add_clang_format_arguments, generate_header_file,
                      open_tree, run_with_clang_formatter)


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=cliexportheader.__doc__)
    parser.add_argument("--config-file",
                        type=str,
                        default=None,
                        help="use this configuration file")
    parser.add_argument("--style",
                        type=str,
                        default="default",
                        help="use this coding style")
    add_clang_format_arguments(parser)
    parser.add_argument("uid",
                        metavar="UID",
                        nargs=1,
                        help="the header file item UID")
    parser.add_argument("file",
                        metavar="FILE",
                        nargs=1,
                        help="the header file path")
    return parser.parse_args(argv[1:])


def _get_interface_task(config: Item, header_file: Item) -> Optional[dict]:
    domain = header_file.parent("interface-placement")
    tasks = [
        task for task in yield_tasks(config, "interface")
        if domain.uid in task["domains"]
    ]
    if len(tasks) == 1:
        return tasks[0]
    if tasks:
        names = ", ".join(task["task-name"] for task in tasks)
        logging.error("the interface tasks %s map the domain %s of %s", names,
                      domain.uid, header_file.uid)
    else:
        logging.error("no interface task maps the domain %s of %s", domain.uid,
                      header_file.uid)
    return None


def _export_header(args: argparse.Namespace,
                   formatter: Optional[ClangFormatter]) -> None:
    with open_tree(args.config_file,
                   item_is_enabled) as (config, item_cache, _):
        provider = LicenseProvider(item_cache.values())
        check_license_items(config, provider)
        header_file = item_cache[args.uid[0]]
        task = _get_interface_task(config, header_file)
        if task is None:
            return
        task["enabled"] = []
        task["style"] = args.style
        generate_header_file(task, header_file,
                             create_content_context(task, provider),
                             args.file[0], formatter)


def cliexportheader(argv: list[str] = sys.argv):
    """ Export the specified header to its target file. """
    args = _parse_args(argv)
    return run_with_clang_formatter(
        args, lambda formatter: _export_header(args, formatter))
