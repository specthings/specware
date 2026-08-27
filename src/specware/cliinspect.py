# SPDX-License-Identifier: BSD-2-Clause
""" Provides a command line interface to check the inspection items. """

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

from specitems import (ItemCache, ItemCacheConfig, create_config, save_data)

from .inspection import State, check, renew
from .util import SpecWareTypeProvider, load_specware_config

#: The states which are reported by default.  A valid scope is not news.
_DEFAULT_STATES = tuple(state.value for state in State
                        if state is not State.VALID)


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=cliinspect.__doc__)
    parser.add_argument("--config-file",
                        type=str,
                        default=None,
                        help="use this configuration file")
    parser.add_argument("--state",
                        action="append",
                        choices=[state.value for state in State],
                        default=None,
                        help="report only scopes in this state")
    parser.add_argument("--renew",
                        type=str,
                        default=None,
                        help=("write a new inspection round which supersedes "
                              "this inspection item"))
    parser.add_argument("--output",
                        type=str,
                        default=None,
                        help="write the new inspection round to this file")
    return parser.parse_args(argv[1:])


def _renew(item_cache: ItemCache, uid: str, output: str | None) -> int:
    if output is None:
        print("--renew needs an --output file", file=sys.stderr)
        return 1
    try:
        item = item_cache[uid]
    except KeyError:
        print(f"there is no item {uid}", file=sys.stderr)
        return 1
    save_data(output, renew(item))
    print(f"wrote {output}")
    return 0


def cliinspect(argv: list[str] = sys.argv) -> int:
    """ Check the inspection items. """
    args = _parse_args(argv)
    config, working_directory = load_specware_config(args.config_file)
    with contextlib.chdir(working_directory):
        # The inspected trees and analyses are package items whose types
        # belong to the build tool, which specware must not depend on.  An
        # unknown type is therefore expected here and must not be fatal.  The
        # cache honours this setting only for a provider it creates itself,
        # so set it on the provider.
        type_provider = SpecWareTypeProvider({})
        type_provider.permissive_type_errors = True
        item_cache = ItemCache(create_config(config["spec"], ItemCacheConfig),
                               type_provider=type_provider)
        if args.renew is not None:
            return _renew(item_cache, args.renew, args.output)
        states = tuple(args.state) if args.state else _DEFAULT_STATES
        status = 0
        for result in check(item_cache.values()):
            if result.state.fails:
                status = 1
            if result.state.value in states:
                print(result)
        return status
