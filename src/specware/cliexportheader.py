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
import contextlib
import sys

from specitems import (ItemCache, ItemCacheConfig, create_config,
                       item_is_enabled)

from specware import (SpecWareTypeProvider, generate_header_file,
                      load_specware_config)


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config-file",
                        type=str,
                        default=None,
                        help="use this configuration file")
    parser.add_argument("--style",
                        type=str,
                        default="default",
                        help="use this coding style")
    parser.add_argument("uid",
                        metavar="UID",
                        nargs=1,
                        help="the header file item UID")
    parser.add_argument("file",
                        metavar="FILE",
                        nargs=1,
                        help="the header file path")
    return parser.parse_args(argv[1:])


def cliexportheader(argv: list[str] = sys.argv):
    """ Export the specified header to a header file. """
    args = _parse_args(argv)
    config, working_directory = load_specware_config(args.config_file)
    with contextlib.chdir(working_directory):
        config["enabled"] = []
        config["interface"]["style"] = args.style
        item_cache = ItemCache(create_config(config["spec"], ItemCacheConfig),
                               type_provider=SpecWareTypeProvider({}),
                               is_item_enabled=item_is_enabled)
        generate_header_file(config["interface"], item_cache[args.uid[0]],
                             args.file[0])
