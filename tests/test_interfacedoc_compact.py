# SPDX-License-Identifier: BSD-2-Clause
""" Tests for the interfacedoc module with the compact layout. """

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

from specitems import augment_glossary_terms, SphinxContent

from specware import document_directive, SphinxInterfaceMapper

from .util import create_item_cache


def test_interfacedoc_compact(tmpdir):
    item_cache = create_item_cache(tmpdir, "spec-interface")
    augment_glossary_terms(item_cache["/glossary"], [])

    item = item_cache["/func"]
    content = SphinxContent(topic_as_definition=True)
    document_directive(content, SphinxInterfaceMapper(item, []), item, [])
    assert str(content) == """Calling sequence
    .. code-block:: c

        void Function(
          int        Param0,
          const int *Param1,
          int       *Param2,
          int       *Param3,
          int       *Param4
        );

Parameters
    ``Param0``
        This parameter is parameter 0.

    ``Param1``
        This parameter is parameter 1.

    ``Param2``
        This parameter is parameter 2.

    ``Param3``
        This parameter is parameter 3.

Description
    Function description.  References to :term:`xs <x>`,
    :c:func:`VeryLongFunction`, :c:type:`Integer`, :c:type:`Enum`,
    :c:macro:`DEFINE`, :c:func:`VERY_LONG_MACRO`, Variable,
    :c:macro:`ENUMERATOR_0`, ``struct Struct``, :ref:`a`, interface, Group A,
    and Group F.  Second parameter is ``Param1``. Mention ``struct US``.  Cite
    :cite:`RefMisc`.

    .. code-block:: foobar

        these two lines
        are not wrapped

Errors
    :c:macro:`DEFINE`
        The errno description.

Constraints
    The following constraints apply to this directive:

    - Constraint A for :c:func:`Function`.
"""

    item = item_cache["/func2"]
    content = SphinxContent(topic_as_definition=True)
    document_directive(content, SphinxInterfaceMapper(item, []), item, [])
    assert str(content) == """Calling sequence
    .. code-block:: c

        int VeryLongFunction(
          int                  VeryLongParam0,
          const struct Struct *VeryLongParam1,
          Union            *( *VeryLongParam2 )( void ),
          struct Struct       *VeryLongParam3
        );

Parameters
    ``VeryLongParam0``
        This parameter is very long parameter 0 with some super important and
        extra very long description which makes a lot of sense.

    ``VeryLongParam1``
        This parameter is very long parameter 1.

    ``VeryLongParam2``
        This parameter is very long parameter 2.

    ``VeryLongParam3``
        This parameter is very long parameter 3.

Description
    VeryLongFunction description.

Return values
    ``1``
        is returned, in case A.

    ``2``
        is returned, in case B.

    :c:type:`Enum`
        is returned, in case C.

    Sometimes some value.  See :c:func:`Function`.

Notes
    VeryLongFunction notes.
"""
