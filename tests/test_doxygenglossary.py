# SPDX-License-Identifier: BSD-2-Clause
""" Tests for the doxygenglossary module. """

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

# REUSE-IgnoreStart

from pathlib import Path

from specware import (DoxygenGlossaryConfig, generate_doxygen_glossary,
                      is_doxygen_glossary_affected)

from .conftest import code_context
from .util import create_item_cache

_BSD_2_CLAUSE = """ * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 * 1. Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
 * LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
 * CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
 * SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
 * INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
 * CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 * POSSIBILITY OF SUCH DAMAGE."""


def test_doxygen_glossary(tmpdir):
    item_cache = create_item_cache(tmpdir, "spec-doxygen-glossary")
    target = Path(tmpdir) / "glossary.h"
    config = DoxygenGlossaryConfig(target=str(target),
                                   page_name="Glossary",
                                   page_title="Terms",
                                   groups=["/glossary/general"],
                                   file_ingroups=["A", "B"])
    generate_doxygen_glossary(config, item_cache, code_context())
    assert target.read_text(
        encoding="utf-8") == f"""/* SPDX-License-Identifier: BSD-2-Clause */

/**
 * @file
 *
 * @ingroup A
 * @ingroup B
 *
 * @brief This header file provides the glossary page.
 */

/*
 * Copyright (C) 2026 embedded brains GmbH & Co. KG
 *
{_BSD_2_CLAUSE}
 */

/*
 * This file was automatically generated.  Do not edit it.
 */

/**
 * @page Glossary Terms
 *
 * <dl>
 *
 * <dt>@anchor GlossaryAPI API</dt>
 * <dd>
 * This term is an acronym for Application Programming Interface, see [*The
 * Document 2026*].
 * </dd>
 *
 * <dt>@anchor GlossarySubBody Sub - body</dt>
 * <dd>
 * The body uses an @ref GlossaryAPI "API", two @ref GlossaryAPI "APIs", an
 * outside and two outsides.
 *
 * The standard *The Document 2026*.
 * </dd>
 *
 * </dl>
 */
"""

    # The file block names no group without the optional attribute.
    config.file_ingroups = []
    generate_doxygen_glossary(config, item_cache, code_context())
    assert "@ingroup" not in target.read_text(encoding="utf-8")


def test_doxygen_glossary_affected(tmpdir):
    item_cache = create_item_cache(tmpdir, "spec-doxygen-glossary")
    config = DoxygenGlossaryConfig(groups=["/glossary/general"])
    assert is_doxygen_glossary_affected(config, item_cache, {"/glossary/body"})
    assert not is_doxygen_glossary_affected(config, item_cache,
                                            {"/glossary/outside"})
    assert not is_doxygen_glossary_affected(config, item_cache, set())
