# SPDX-License-Identifier: BSD-2-Clause
""" Tests for the interfacedoc module. """

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

import os
import pytest

from specitems import (augment_glossary_terms, EmptyItem, ItemMapper,
                       MarkdownContent, SphinxContent)

from specware import (document_directive, generate_interface_documentation,
                      MarkdownInterfaceMapper, SphinxInterfaceMapper)

from .util import create_item_cache


def test_interfacedoc(tmpdir):
    item_cache = create_item_cache(tmpdir, "spec-interface")

    directive_item = item_cache["/func3"]
    directive_content = SphinxContent()
    document_directive(directive_content, ItemMapper(EmptyItem()),
                       directive_item, [])
    assert str(directive_content) == """.. rubric:: CALLING SEQUENCE:

.. code-block:: c

    void VoidFunction( void );
"""

    augment_glossary_terms(item_cache["/glossary"], [])

    doc_config = {}
    doc_config["group"] = "/gb"

    doc_config_2 = {}
    doc_config_2["group"] = "/ga"

    types_config = {"domains": ["/domain-abc"], "groups": []}

    config = {
        "enabled": [],
        "groups": [doc_config, doc_config_2],
        "types": types_config
    }

    introduction_rst = os.path.join(tmpdir, "introduction.rst")
    doc_config["introduction-target"] = introduction_rst
    directives_rst = os.path.join(tmpdir, "directives.rst")
    doc_config["directives-target"] = directives_rst
    introduction_2_rst = os.path.join(tmpdir, "introduction-2.rst")
    doc_config_2["introduction-target"] = introduction_2_rst
    directives_2_rst = os.path.join(tmpdir, "directives-2.rst")
    doc_config_2["directives-target"] = directives_2_rst
    types_rst = os.path.join(tmpdir, "types.rst")
    types_config["target"] = types_rst
    generate_interface_documentation(config, item_cache, SphinxInterfaceMapper,
                                     SphinxContent)

    introduction_md = os.path.join(tmpdir, "introduction.md")
    doc_config["introduction-target"] = introduction_md
    directives_md = os.path.join(tmpdir, "directives.md")
    doc_config["directives-target"] = directives_md
    introduction_2_md = os.path.join(tmpdir, "introduction-2.md")
    doc_config_2["introduction-target"] = introduction_2_md
    directives_2_md = os.path.join(tmpdir, "directives-2.md")
    doc_config_2["directives-target"] = directives_2_md
    types_md = os.path.join(tmpdir, "types.md")
    types_config["target"] = types_md
    generate_interface_documentation(config, item_cache,
                                     MarkdownInterfaceMapper, MarkdownContent)

    with open(introduction_rst, "r") as src:
        content = """.. SPDX-License-Identifier: CC-BY-SA-4.0

.. Copyright (C) 2020 embedded brains GmbH & Co. KG

.. This file was automatically generated.  Do not edit it.

.. Generated from spec:/gb

.. _GroupBIntroduction:

Introduction
############

.. The following list was generated from:
.. spec:/func4
.. spec:/func2
.. spec:/func3
.. spec:/macro
.. spec:/macro2
.. spec:/macro3

The directives provided by the Group B are:

- :ref:`InterfaceVeryLongTypeFunction` - Function brief description with very
  long return type.

- :ref:`InterfaceVeryLongFunction` - Very long function brief description.

- :ref:`InterfaceVoidFunction`

- :ref:`InterfaceVERYLONGMACRO` - Very long macro brief description.

- :ref:`InterfaceMACRO` - Short macro brief description.

- :ref:`InterfaceMACRO` - Macro without parameters.
"""
        assert content == src.read()

    with open(directives_rst, "r") as src:
        content = """.. SPDX-License-Identifier: CC-BY-SA-4.0

.. Copyright (C) 2020 embedded brains GmbH & Co. KG

.. This file was automatically generated.  Do not edit it.

.. _GroupBDirectives:

Directives
##########

This section details the directives of the Group B. A subsection is dedicated
to each of this manager's directives and lists the calling sequence,
parameters, description, return values, and notes of the directive.

.. Generated from spec:/func4

.. raw:: latex

    \\clearpage

.. index:: VeryLongTypeFunction()

.. _InterfaceVeryLongTypeFunction:

VeryLongTypeFunction()
**********************

Function brief description with very long return type.

.. rubric:: CALLING SEQUENCE:

.. code-block:: c

    VeryLongLongLongLongLongLongLongLongLongLongLongLongLongLongLongType
    VeryLongTypeFunction( void );

.. rubric:: DESCRIPTION:

I am defined in ``<h4.h>``.

.. rubric:: RETURN VALUES:

This function returns an object with a very long type.

.. rubric:: NOTES:

See also :c:func:`Func5`.

.. Generated from spec:/func2

.. raw:: latex

    \\clearpage

.. index:: VeryLongFunction()

.. _InterfaceVeryLongFunction:

VeryLongFunction()
******************

Very long function brief description.

.. rubric:: CALLING SEQUENCE:

.. code-block:: c

    int VeryLongFunction(
      int                  VeryLongParam0,
      const struct Struct *VeryLongParam1,
      Union            *( *VeryLongParam2 )( void ),
      struct Struct       *VeryLongParam3
    );

.. rubric:: PARAMETERS:

``VeryLongParam0``
    This parameter is very long parameter 0 with some super important and extra
    very long description which makes a lot of sense.

``VeryLongParam1``
    This parameter is very long parameter 1.

``VeryLongParam2``
    This parameter is very long parameter 2.

``VeryLongParam3``
    This parameter is very long parameter 3.

.. rubric:: DESCRIPTION:

VeryLongFunction description.

.. rubric:: RETURN VALUES:

``1``
    is returned, in case A.

``2``
    is returned, in case B.

:ref:`InterfaceEnum`
    is returned, in case C.

Sometimes some value.  See :ref:`InterfaceFunction`.

.. rubric:: NOTES:

VeryLongFunction notes.

.. Generated from spec:/func3

.. raw:: latex

    \\clearpage

.. index:: VoidFunction()

.. _InterfaceVoidFunction:

VoidFunction()
**************

.. rubric:: CALLING SEQUENCE:

.. code-block:: c

    void VoidFunction( void );

.. Generated from spec:/macro

.. raw:: latex

    \\clearpage

.. index:: VERY_LONG_MACRO()

.. _InterfaceVERYLONGMACRO:

VERY_LONG_MACRO()
*****************

Very long macro brief description.

.. rubric:: CALLING SEQUENCE:

.. code-block:: c

    VERY_LONG_MACRO(
      VeryLongParam0,
      VeryLongParam1,
      VeryLongParam2,
      VeryLongParam3
    );

.. rubric:: PARAMETERS:

``VeryLongParam0``
    This parameter is very long parameter 0 with some super important and extra
    very long description which makes a lot of sense.

``VeryLongParam1``
    This parameter is very long parameter 1.

``VeryLongParam2``
    This parameter is very long parameter 2.

``VeryLongParam3``
    This parameter is very long parameter 3.

.. rubric:: RETURN VALUES:

``1``
    is returned, in case A.

``2``
    is returned, in case B.

Sometimes some value.

.. Generated from spec:/macro2

.. raw:: latex

    \\clearpage

.. index:: MACRO()

.. _InterfaceMACRO:

MACRO()
*******

Short macro brief description.

.. rubric:: CALLING SEQUENCE:

.. code-block:: c

    MACRO( Param0 );

.. rubric:: PARAMETERS:

``Param0``
    This parameter is parameter 0.

.. rubric:: RETURN VALUES:

Sometimes some value.

.. Generated from spec:/macro3

.. raw:: latex

    \\clearpage

.. index:: MACRO()

.. _InterfaceMACRO:

MACRO()
*******

Macro without parameters.

.. rubric:: CALLING SEQUENCE:

.. code-block:: c

    MACRO( void );
"""
        assert content == src.read()

    with open(introduction_2_rst, "r") as src:
        content = """.. SPDX-License-Identifier: CC-BY-SA-4.0

.. Copyright (C) 2020 embedded brains GmbH & Co. KG

.. This file was automatically generated.  Do not edit it.

.. Generated from spec:/ga

.. _GroupAIntroduction:

Introduction
############

.. The following list was generated from:
.. spec:/func

Group A brief description.

Group A description. The directives provided by the Group A are:

- :ref:`InterfaceFunction` - Function brief description.
"""
        assert content == src.read()

    with open(directives_2_rst, "r") as src:
        content = """.. SPDX-License-Identifier: CC-BY-SA-4.0

.. Copyright (C) 2020 embedded brains GmbH & Co. KG

.. This file was automatically generated.  Do not edit it.

.. _GroupADirectives:

Directives
==========

This section details the directives of the Group A. A subsection is dedicated
to each of this manager's directives and lists the calling sequence,
parameters, description, return values, and notes of the directive.

.. Generated from spec:/func

.. raw:: latex

    \\clearpage

.. index:: Function()

.. _InterfaceFunction:

Function()
**********

Function brief description.

.. rubric:: CALLING SEQUENCE:

.. code-block:: c

    void Function(
      int        Param0,
      const int *Param1,
      int       *Param2,
      int       *Param3,
      int       *Param4
    );

.. rubric:: PARAMETERS:

``Param0``
    This parameter is parameter 0.

``Param1``
    This parameter is parameter 1.

``Param2``
    This parameter is parameter 2.

``Param3``
    This parameter is parameter 3.

.. rubric:: DESCRIPTION:

Function description.  References to :term:`xs <x>`,
:ref:`InterfaceVeryLongFunction`, :ref:`InterfaceInteger`,
:ref:`InterfaceEnum`, :c:macro:`DEFINE`, :ref:`InterfaceVERYLONGMACRO`,
Variable, :c:macro:`ENUMERATOR_0`, ``struct Struct``, :ref:`a`, interface,
:ref:`GroupA`, and Group F.  Second parameter is ``Param1``. Mention ``struct
US``.

.. code-block:: foobar

    these two lines
    are not wrapped

.. rubric:: CONSTRAINTS:

The following constraints apply to this directive:

- Constraint A for :ref:`InterfaceFunction`.
"""

    with open(types_rst, "r") as src:
        content = """.. SPDX-License-Identifier: CC-BY-SA-4.0

.. Copyright (C) 2020, 2023 embedded brains GmbH & Co. KG

.. This file was automatically generated.  Do not edit it.

.. index:: RTEMS Data Types
.. index:: data types

.. _RTEMSDataTypes:

RTEMS Data Types
################

.. _RTEMSDataTypesIntroduction:

Introduction
************

This chapter contains a complete list of the RTEMS primitive data types in
alphabetical order.  This is intended to be an overview and the user is
encouraged to look at the appropriate chapters in the manual for more
information about the usage of the various data types.

.. _RTEMSDataTypesListOfDataTypes:

List of Data Types
******************

The following is a complete list of the RTEMS primitive data types in
alphabetical order:

.. Generated from spec:/enum

.. index:: Enum

.. _InterfaceEnum:

Enum
====

Enum brief description.

.. rubric:: ENUMERATORS:

ENUMERATOR_0
    Enumerator 0 brief description.

ENUMERATOR_1
    Enumerator 1 brief description.

ENUMERATOR_2
    Enumerator 2 brief description.

.. rubric:: DESCRIPTION:

Enum description.

.. Generated from spec:/enum2

.. index:: EnumA

.. _InterfaceEnumA:

EnumA
=====

Enum A brief description.

.. rubric:: ENUMERATORS:

ENUMERATOR_A
    Enumerator A brief description.

.. Generated from spec:/enum3

.. index:: EnumB

.. _InterfaceEnumB:

EnumB
=====

Enum B brief description.

.. rubric:: ENUMERATORS:

ENUMERATOR_B
    Enumerator B brief description.

.. Generated from spec:/enum4

.. index:: EnumC

.. _InterfaceEnumC:

EnumC
=====

Enum C brief description.

.. rubric:: ENUMERATORS:

.. Generated from spec:/td

.. index:: Integer

.. _InterfaceInteger:

Integer
=======

Typedef Integer brief description.

.. rubric:: DESCRIPTION:

Typedef Integer description.

.. Generated from spec:/td3

.. index:: Integer3

.. _InterfaceInteger3:

Integer3
========

Interface3 brief.

.. Generated from spec:/s

.. index:: Struct

.. _InterfaceStruct:

Struct
======

.. rubric:: MEMBERS:

some_union
    Brief union description. Union description.

some_member_4
    Brief member 4 description. Member 4 description.

.. Generated from spec:/s2

.. index:: Struct2

.. _InterfaceStruct2:

Struct2
=======

.. rubric:: MEMBERS:

Members of the type shall not be accessed directly by the application.

.. rubric:: DESCRIPTION:

References: :ref:`InterfaceStruct2`

.. rubric:: NOTES:

See also ``struct Struct`` and :c:func:`unspec_func`.

.. Generated from spec:/u

.. index:: Union

.. _InterfaceUnion:

Union
=====

.. rubric:: MEMBERS:

m_0
    Brief member 0 description.

m_1
    Brief member 1 description.
"""
        assert content == src.read()

    with open(introduction_md, "r") as src:
        content = """% SPDX-License-Identifier: CC-BY-SA-4.0

% Copyright (C) 2020 embedded brains GmbH & Co. KG

% This file was automatically generated.  Do not edit it.

% Generated from spec:/gb

(GroupBIntroduction)=

# Introduction

% The following list was generated from:
% spec:/func4
% spec:/func2
% spec:/func3
% spec:/macro
% spec:/macro2
% spec:/macro3

The directives provided by the Group B are:

- {ref}`InterfaceVeryLongTypeFunction` - Function brief description with very
  long return type.

- {ref}`InterfaceVeryLongFunction` - Very long function brief description.

- {ref}`InterfaceVoidFunction`

- {ref}`InterfaceVERYLONGMACRO` - Very long macro brief description.

- {ref}`InterfaceMACRO` - Short macro brief description.

- {ref}`InterfaceMACRO` - Macro without parameters.
"""
        assert content == src.read()

    with open(directives_md, "r") as src:
        content = """% SPDX-License-Identifier: CC-BY-SA-4.0

% Copyright (C) 2020 embedded brains GmbH & Co. KG

% This file was automatically generated.  Do not edit it.

(GroupBDirectives)=

# Directives

This section details the directives of the Group B. A subsection is dedicated
to each of this manager's directives and lists the calling sequence,
parameters, description, return values, and notes of the directive.

% Generated from spec:/func4

```{raw} latex
\\clearpage
```

```{index} VeryLongTypeFunction()
```

(InterfaceVeryLongTypeFunction)=

## VeryLongTypeFunction()

Function brief description with very long return type.

```{eval-rst}
.. rubric:: CALLING SEQUENCE:
```

```{code-block} c
VeryLongLongLongLongLongLongLongLongLongLongLongLongLongLongLongType
VeryLongTypeFunction( void );
```

```{eval-rst}
.. rubric:: DESCRIPTION:
```

I am defined in `<h4.h>`.

```{eval-rst}
.. rubric:: RETURN VALUES:
```

This function returns an object with a very long type.

```{eval-rst}
.. rubric:: NOTES:
```

See also {c:func}`Func5`.

% Generated from spec:/func2

```{raw} latex
\\clearpage
```

```{index} VeryLongFunction()
```

(InterfaceVeryLongFunction)=

## VeryLongFunction()

Very long function brief description.

```{eval-rst}
.. rubric:: CALLING SEQUENCE:
```

```{code-block} c
int VeryLongFunction(
  int                  VeryLongParam0,
  const struct Struct *VeryLongParam1,
  Union            *( *VeryLongParam2 )( void ),
  struct Struct       *VeryLongParam3
);
```

```{eval-rst}
.. rubric:: PARAMETERS:
```

`VeryLongParam0`
: This parameter is very long parameter 0 with some super important and extra
  very long description which makes a lot of sense.

`VeryLongParam1`
: This parameter is very long parameter 1.

`VeryLongParam2`
: This parameter is very long parameter 2.

`VeryLongParam3`
: This parameter is very long parameter 3.

```{eval-rst}
.. rubric:: DESCRIPTION:
```

VeryLongFunction description.

```{eval-rst}
.. rubric:: RETURN VALUES:
```

`1`
: is returned, in case A.

`2`
: is returned, in case B.

{ref}`InterfaceEnum`
: is returned, in case C.

Sometimes some value. See {ref}`InterfaceFunction`.

```{eval-rst}
.. rubric:: NOTES:
```

VeryLongFunction notes.

% Generated from spec:/func3

```{raw} latex
\\clearpage
```

```{index} VoidFunction()
```

(InterfaceVoidFunction)=

## VoidFunction()

```{eval-rst}
.. rubric:: CALLING SEQUENCE:
```

```{code-block} c
void VoidFunction( void );
```

% Generated from spec:/macro

```{raw} latex
\\clearpage
```

```{index} VERY_LONG_MACRO()
```

(InterfaceVERYLONGMACRO)=

## VERY_LONG_MACRO()

Very long macro brief description.

```{eval-rst}
.. rubric:: CALLING SEQUENCE:
```

```{code-block} c
VERY_LONG_MACRO(
  VeryLongParam0,
  VeryLongParam1,
  VeryLongParam2,
  VeryLongParam3
);
```

```{eval-rst}
.. rubric:: PARAMETERS:
```

`VeryLongParam0`
: This parameter is very long parameter 0 with some super important and extra
  very long description which makes a lot of sense.

`VeryLongParam1`
: This parameter is very long parameter 1.

`VeryLongParam2`
: This parameter is very long parameter 2.

`VeryLongParam3`
: This parameter is very long parameter 3.

```{eval-rst}
.. rubric:: RETURN VALUES:
```

`1`
: is returned, in case A.

`2`
: is returned, in case B.

Sometimes some value.

% Generated from spec:/macro2

```{raw} latex
\\clearpage
```

```{index} MACRO()
```

(InterfaceMACRO)=

## MACRO()

Short macro brief description.

```{eval-rst}
.. rubric:: CALLING SEQUENCE:
```

```{code-block} c
MACRO( Param0 );
```

```{eval-rst}
.. rubric:: PARAMETERS:
```

`Param0`
: This parameter is parameter 0.

```{eval-rst}
.. rubric:: RETURN VALUES:
```

Sometimes some value.

% Generated from spec:/macro3

```{raw} latex
\\clearpage
```

```{index} MACRO()
```

(InterfaceMACRO)=

## MACRO()

Macro without parameters.

```{eval-rst}
.. rubric:: CALLING SEQUENCE:
```

```{code-block} c
MACRO( void );
```
"""
        assert content == src.read()

    with open(introduction_2_md, "r") as src:
        content = """% SPDX-License-Identifier: CC-BY-SA-4.0

% Copyright (C) 2020 embedded brains GmbH & Co. KG

% This file was automatically generated.  Do not edit it.

% Generated from spec:/ga

(GroupAIntroduction)=

# Introduction

% The following list was generated from:
% spec:/func

Group A brief description.

Group A description. The directives provided by the Group A are:

- {ref}`InterfaceFunction` - Function brief description.
"""
        assert content == src.read()

    with open(directives_2_md, "r") as src:
        content = """% SPDX-License-Identifier: CC-BY-SA-4.0

% Copyright (C) 2020 embedded brains GmbH & Co. KG

% This file was automatically generated.  Do not edit it.

(GroupADirectives)=

# Directives

This section details the directives of the Group A. A subsection is dedicated
to each of this manager's directives and lists the calling sequence,
parameters, description, return values, and notes of the directive.

% Generated from spec:/func

```{raw} latex
\\clearpage
```

```{index} Function()
```

(InterfaceFunction)=

## Function()

Function brief description.

```{eval-rst}
.. rubric:: CALLING SEQUENCE:
```

```{code-block} c
void Function(
  int        Param0,
  const int *Param1,
  int       *Param2,
  int       *Param3,
  int       *Param4
);
```

```{eval-rst}
.. rubric:: PARAMETERS:
```

`Param0`
: This parameter is parameter 0.

`Param1`
: This parameter is parameter 1.

`Param2`
: This parameter is parameter 2.

`Param3`
: This parameter is parameter 3.

```{eval-rst}
.. rubric:: DESCRIPTION:
```

Function description. References to {term}`xs <x>`,
{ref}`InterfaceVeryLongFunction`, {ref}`InterfaceInteger`,
{ref}`InterfaceEnum`, {c:macro}`DEFINE`, {ref}`InterfaceVERYLONGMACRO`,
Variable, {c:macro}`ENUMERATOR_0`, `struct Struct`, {ref}`a`, interface,
{ref}`GroupA`, and Group F. Second parameter is `Param1`. Mention
{c:type}`struct US`.

```foobar
these two lines
are not wrapped
```

```{eval-rst}
.. rubric:: CONSTRAINTS:
```

The following constraints apply to this directive:

- Constraint A for {ref}`InterfaceFunction`.
"""
        assert content == src.read()

    with open(types_md, "r") as src:
        content = """% SPDX-License-Identifier: CC-BY-SA-4.0

% Copyright (C) 2020, 2023 embedded brains GmbH & Co. KG

% This file was automatically generated.  Do not edit it.

```{index} RTEMS Data Types
```

```{index} data types
```

(RTEMSDataTypes)=

# RTEMS Data Types

(RTEMSDataTypesIntroduction)=

## Introduction

This chapter contains a complete list of the RTEMS primitive data types in
alphabetical order. This is intended to be an overview and the user is
encouraged to look at the appropriate chapters in the manual for more
information about the usage of the various data types.

(RTEMSDataTypesListOfDataTypes)=

## List of Data Types

The following is a complete list of the RTEMS primitive data types in
alphabetical order:

% Generated from spec:/enum

```{index} Enum
```

(InterfaceEnum)=

### Enum

Enum brief description.

```{eval-rst}
.. rubric:: ENUMERATORS:
```

ENUMERATOR_0
: Enumerator 0 brief description.

ENUMERATOR_1
: Enumerator 1 brief description.

ENUMERATOR_2
: Enumerator 2 brief description.

```{eval-rst}
.. rubric:: DESCRIPTION:
```

Enum description.

% Generated from spec:/enum2

```{index} EnumA
```

(InterfaceEnumA)=

### EnumA

Enum A brief description.

```{eval-rst}
.. rubric:: ENUMERATORS:
```

ENUMERATOR_A
: Enumerator A brief description.

% Generated from spec:/enum3

```{index} EnumB
```

(InterfaceEnumB)=

### EnumB

Enum B brief description.

```{eval-rst}
.. rubric:: ENUMERATORS:
```

ENUMERATOR_B
: Enumerator B brief description.

% Generated from spec:/enum4

```{index} EnumC
```

(InterfaceEnumC)=

### EnumC

Enum C brief description.

```{eval-rst}
.. rubric:: ENUMERATORS:
```

% Generated from spec:/td

```{index} Integer
```

(InterfaceInteger)=

### Integer

Typedef Integer brief description.

```{eval-rst}
.. rubric:: DESCRIPTION:
```

Typedef Integer description.

% Generated from spec:/td3

```{index} Integer3
```

(InterfaceInteger3)=

### Integer3

Interface3 brief.

% Generated from spec:/s

```{index} Struct
```

(InterfaceStruct)=

### Struct

```{eval-rst}
.. rubric:: MEMBERS:
```

some_union
: Brief union description. Union description.

some_member_4
: Brief member 4 description. Member 4 description.

% Generated from spec:/s2

```{index} Struct2
```

(InterfaceStruct2)=

### Struct2

```{eval-rst}
.. rubric:: MEMBERS:
```

Members of the type shall not be accessed directly by the application.

```{eval-rst}
.. rubric:: DESCRIPTION:
```

References: {ref}`InterfaceStruct2`

```{eval-rst}
.. rubric:: NOTES:
```

See also `struct Struct` and {c:func}`unspec_func`.

% Generated from spec:/u

```{index} Union
```

(InterfaceUnion)=

### Union

```{eval-rst}
.. rubric:: MEMBERS:
```

m_0
: Brief member 0 description.

m_1
: Brief member 1 description.
"""
        assert content == src.read()
