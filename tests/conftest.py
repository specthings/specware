# SPDX-License-Identifier: BSD-2-Clause
""" Test fixtures. """

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

import functools
from pathlib import Path

from specitems import (ContentContext, EmptyItemCache, LicenseAggregate,
                       LicenseProvider)

#: The license of the generated C files of the test fixtures.
CODE_LICENSE = "BSD-2-Clause"

#: The license of the generated documentation of the test fixtures.
DOC_LICENSE = "CC-BY-SA-4.0"


@functools.lru_cache(maxsize=1)
def license_provider() -> LicenseProvider:
    """ Provide the licenses which the test fixtures carry. """
    item_cache = EmptyItemCache()
    directory = Path(__file__).parent / "spec-rtems" / "license"
    for path in sorted(directory.glob("*.yml")):
        item = item_cache.add_item_from_file(f"/license/{path.stem}",
                                             str(path),
                                             initialize_links=False)
        item.type = "license"
    return LicenseProvider(item_cache.values())


def code_context(name: str = "code") -> ContentContext:
    """ Create the content context of a generated C file. """
    return ContentContext(
        LicenseAggregate(CODE_LICENSE, ["CC-BY-SA-4.0"], name), None,
        license_provider())


def zephyr_context(name: str = "zephyr") -> ContentContext:
    """ Create the content context of a generated Zephyr file. """
    return ContentContext(
        LicenseAggregate("Apache-2.0", ["BSD-2-Clause", "CC-BY-SA-4.0"], name),
        None, license_provider())


def doc_context(name: str = "doc") -> ContentContext:
    """ Create the content context of a generated documentation file. """
    return ContentContext(
        LicenseAggregate(DOC_LICENSE, ["BSD-2-Clause"], name), None,
        license_provider())
