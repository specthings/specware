# SPDX-License-Identifier: BSD-2-Clause
"""
Provides a command line interface to verify the specification item format.
"""

# Copyright (C) 2020, 2025 embedded brains GmbH & Co. KG
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

import sys

from specitems import (ItemCache, ItemCacheConfig, create_argument_parser,
                       init_logging, verify_specification_format)

from specware import SpecWareTypeProvider


def cliverify(argv: list[str] = sys.argv):
    """ Verify the specification item format. """
    parser = create_argument_parser()
    parser.add_argument("spec_directories",
                        nargs="+",
                        metavar="SPEC_DIRECTORIES")
    args = parser.parse_args(argv[1:])
    init_logging(args)
    config = ItemCacheConfig(paths=args.spec_directories,
                             cache_directory="cache-specware")
    type_provider = SpecWareTypeProvider({})
    item_cache = ItemCache(config, type_provider=type_provider)
    verify_specification_format(item_cache)
