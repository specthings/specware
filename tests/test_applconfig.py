# SPDX-License-Identifier: BSD-2-Clause
""" Tests for the applconfig module. """

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

from specitems import ItemMapper, MarkdownContent, SphinxContent

from specware import (document_option, generate_application_configuration,
                      MarkdownInterfaceMapper, SphinxInterfaceMapper)

from .util import create_item_cache


def test_applconfig(tmpdir):
    item_cache = create_item_cache(tmpdir, "spec-applconfig")

    applconfig_config = {}
    applconfig_config["enabled-source"] = ["X"]
    applconfig_config["enabled-documentation"] = ["X"]
    doxygen_h = os.path.join(tmpdir, "doxygen.h")
    applconfig_config["doxygen-target"] = doxygen_h

    g_rst = os.path.join(tmpdir, "g.rst")
    applconfig_config["groups"] = [{"uid": "/g", "target": g_rst}]
    generate_application_configuration(applconfig_config, [], item_cache,
                                       SphinxInterfaceMapper, SphinxContent)

    g_md = os.path.join(tmpdir, "g.md")
    applconfig_config["groups"] = [{"uid": "/g", "target": g_md}]
    generate_application_configuration(applconfig_config, [], item_cache,
                                       MarkdownInterfaceMapper,
                                       MarkdownContent)

    with open(g_rst, "r") as src:
        content = """.. SPDX-License-Identifier: CC-BY-SA-4.0

.. Copyright (C) 2020, 2021 embedded brains GmbH & Co. KG

.. This file was automatically generated.  Do not edit it.

.. Generated from spec:/g

group name
##########

description

.. Generated from spec:/a

.. raw:: latex

    \\clearpage

.. index:: a
.. index:: index a

.. _a:

a
*

.. rubric:: CONSTANT:

``a``

.. rubric:: OPTION TYPE:

This configuration option is a boolean feature define.

.. rubric:: DEFAULT CONFIGURATION:

default a

.. rubric:: DESCRIPTION:

description a

.. rubric:: NOTES:

notes a

references:

* :ref:`b`

* :ref:`SphinxRefUnspecGroup`

* Unspec Group 2

* `Unspec Group 3 <unspec-group-3.html>`_

* :ref:`unspec_func() <SphinxRefUnspecFunc>`

* :c:func:`unspec_func_no_ref`

* :c:func:`func`

* :c:type:`td`

* :c:macro:`DEFINE`

* :ref:`UNSPEC_DEFINE <SphinxRefTarget>`

* `UNSPEC_DEFINE_2 <https://foo>`_

* :c:type:`unspec_type`

* `unspec_type_2 <https://bar>`_

.. Generated from spec:/b

.. raw:: latex

    \\clearpage

.. index:: b

.. _b:

b
*

.. rubric:: CONSTANT:

``b``

.. rubric:: OPTION TYPE:

This configuration option is a boolean feature define.

.. rubric:: DEFAULT CONFIGURATION:

If this configuration option is undefined, then the described feature is not
enabled.

.. rubric:: DESCRIPTION:

description b

.. Generated from spec:/c

.. raw:: latex

    \\clearpage

.. index:: c

.. _c:

c
*

.. rubric:: CONSTANT:

``c``

.. rubric:: OPTION TYPE:

This configuration option is an integer define.

.. rubric:: DEFAULT VALUE:

The default value is 13.

.. rubric:: DESCRIPTION:

description c

.. rubric:: NOTES:

notes c

.. rubric:: CONSTRAINTS:

constraint d

.. Generated from spec:/e

.. raw:: latex

    \\clearpage

.. index:: e

.. _e:

e
*

.. rubric:: CONSTANT:

``e``

.. rubric:: OPTION TYPE:

This configuration option is an integer define.

.. rubric:: DEFAULT VALUE:

The default value is 7.

.. rubric:: DESCRIPTION:

description e

.. Generated from spec:/f

.. raw:: latex

    \\clearpage

.. index:: f

.. _f:

f
*

.. rubric:: CONSTANT:

``f``

.. rubric:: OPTION TYPE:

This configuration option is an integer define.

.. rubric:: DEFAULT VALUE:

The default value is 1.

.. rubric:: DESCRIPTION:

description f

.. Generated from spec:/h

.. raw:: latex

    \\clearpage

.. index:: h

.. _h:

h
*

.. rubric:: CONSTANT:

``h``

.. rubric:: OPTION TYPE:

This configuration option is an integer define.

.. rubric:: DEFAULT VALUE:

The default value is 1.

.. rubric:: DESCRIPTION:

description h

.. Generated from spec:/i

.. raw:: latex

    \\clearpage

.. index:: i

.. _i:

i
*

.. rubric:: CONSTANT:

``i``

.. rubric:: OPTION TYPE:

This configuration option is an integer define.

.. rubric:: DEFAULT VALUE:

The default value is 1.

.. rubric:: DESCRIPTION:

description i

.. Generated from spec:/j

.. raw:: latex

    \\clearpage

.. index:: j

.. _j:

j
*

.. rubric:: CONSTANT:

``j``

.. rubric:: OPTION TYPE:

This configuration option is an integer define.

.. rubric:: DEFAULT VALUE:

Foo bar.

.. rubric:: DESCRIPTION:

description j

.. rubric:: CONSTRAINTS:

constraint d

.. Generated from spec:/k

.. raw:: latex

    \\clearpage

.. index:: k

.. _k:

k
*

.. rubric:: CONSTANT:

``k``

.. rubric:: OPTION TYPE:

This configuration option is an integer define.

.. rubric:: DEFAULT VALUE:

The default value is 1.

.. rubric:: DESCRIPTION:

description k

.. Generated from spec:/l

.. raw:: latex

    \\clearpage

.. index:: l

.. _l:

l
*

.. rubric:: CONSTANT:

``l``

.. rubric:: OPTION TYPE:

This configuration option is an initializer define.

.. rubric:: DEFAULT VALUE:

The default value is 1.

.. rubric:: DESCRIPTION:

description l

.. rubric:: CONSTRAINTS:

The following constraints apply to this configuration option:

- The value of the configuration option shall be greater than or equal to zero.

- The value of the configuration option shall be

- - less than, or

- - equal to two.

.. Generated from spec:/m

.. raw:: latex

    \\clearpage

.. index:: m

.. _m:

m
*

.. rubric:: CONSTANT:

``m``

.. rubric:: OPTION TYPE:

This configuration option is an initializer define.

.. rubric:: DEFAULT VALUE:

The default value is 1.

.. rubric:: DESCRIPTION:

description m
"""
        assert content == src.read()
    with open(g_md, "r") as src:
        content = """% SPDX-License-Identifier: CC-BY-SA-4.0

% Copyright (C) 2020, 2021 embedded brains GmbH & Co. KG

% This file was automatically generated.  Do not edit it.

% Generated from spec:/g

# group name

description

% Generated from spec:/a

```{raw} latex
\\clearpage
```

```{index} a
```

```{index} index a
```

(a)=

## a

```{eval-rst}
.. rubric:: CONSTANT:
```

`a`

```{eval-rst}
.. rubric:: OPTION TYPE:
```

This configuration option is a boolean feature define.

```{eval-rst}
.. rubric:: DEFAULT CONFIGURATION:
```

default a

```{eval-rst}
.. rubric:: DESCRIPTION:
```

description a

```{eval-rst}
.. rubric:: NOTES:
```

notes a

references:

- {ref}`b`

- {ref}`SphinxRefUnspecGroup`

- Unspec Group 2

- [Unspec Group 3](unspec-group-3.html)

- {ref}`unspec_func() <SphinxRefUnspecFunc>`

- {c:func}`unspec_func_no_ref`

- {c:func}`func`

- {c:type}`td`

- {c:macro}`DEFINE`

- {ref}`UNSPEC_DEFINE <SphinxRefTarget>`

- [UNSPEC_DEFINE_2](https://foo)

- {c:type}`unspec_type`

- [unspec_type_2](https://bar)

% Generated from spec:/b

```{raw} latex
\\clearpage
```

```{index} b
```

(b)=

## b

```{eval-rst}
.. rubric:: CONSTANT:
```

`b`

```{eval-rst}
.. rubric:: OPTION TYPE:
```

This configuration option is a boolean feature define.

```{eval-rst}
.. rubric:: DEFAULT CONFIGURATION:
```

If this configuration option is undefined, then the described feature is not
enabled.

```{eval-rst}
.. rubric:: DESCRIPTION:
```

description b

% Generated from spec:/c

```{raw} latex
\\clearpage
```

```{index} c
```

(c)=

## c

```{eval-rst}
.. rubric:: CONSTANT:
```

`c`

```{eval-rst}
.. rubric:: OPTION TYPE:
```

This configuration option is an integer define.

```{eval-rst}
.. rubric:: DEFAULT VALUE:
```

The default value is 13.

```{eval-rst}
.. rubric:: DESCRIPTION:
```

description c

```{eval-rst}
.. rubric:: NOTES:
```

notes c

```{eval-rst}
.. rubric:: CONSTRAINTS:
```

constraint d

% Generated from spec:/e

```{raw} latex
\\clearpage
```

```{index} e
```

(e)=

## e

```{eval-rst}
.. rubric:: CONSTANT:
```

`e`

```{eval-rst}
.. rubric:: OPTION TYPE:
```

This configuration option is an integer define.

```{eval-rst}
.. rubric:: DEFAULT VALUE:
```

The default value is 7.

```{eval-rst}
.. rubric:: DESCRIPTION:
```

description e

% Generated from spec:/f

```{raw} latex
\\clearpage
```

```{index} f
```

(f)=

## f

```{eval-rst}
.. rubric:: CONSTANT:
```

`f`

```{eval-rst}
.. rubric:: OPTION TYPE:
```

This configuration option is an integer define.

```{eval-rst}
.. rubric:: DEFAULT VALUE:
```

The default value is 1.

```{eval-rst}
.. rubric:: DESCRIPTION:
```

description f

% Generated from spec:/h

```{raw} latex
\\clearpage
```

```{index} h
```

(h)=

## h

```{eval-rst}
.. rubric:: CONSTANT:
```

`h`

```{eval-rst}
.. rubric:: OPTION TYPE:
```

This configuration option is an integer define.

```{eval-rst}
.. rubric:: DEFAULT VALUE:
```

The default value is 1.

```{eval-rst}
.. rubric:: DESCRIPTION:
```

description h

% Generated from spec:/i

```{raw} latex
\\clearpage
```

```{index} i
```

(i)=

## i

```{eval-rst}
.. rubric:: CONSTANT:
```

`i`

```{eval-rst}
.. rubric:: OPTION TYPE:
```

This configuration option is an integer define.

```{eval-rst}
.. rubric:: DEFAULT VALUE:
```

The default value is 1.

```{eval-rst}
.. rubric:: DESCRIPTION:
```

description i

% Generated from spec:/j

```{raw} latex
\\clearpage
```

```{index} j
```

(j)=

## j

```{eval-rst}
.. rubric:: CONSTANT:
```

`j`

```{eval-rst}
.. rubric:: OPTION TYPE:
```

This configuration option is an integer define.

```{eval-rst}
.. rubric:: DEFAULT VALUE:
```

Foo bar.

```{eval-rst}
.. rubric:: DESCRIPTION:
```

description j

```{eval-rst}
.. rubric:: CONSTRAINTS:
```

constraint d

% Generated from spec:/k

```{raw} latex
\\clearpage
```

```{index} k
```

(k)=

## k

```{eval-rst}
.. rubric:: CONSTANT:
```

`k`

```{eval-rst}
.. rubric:: OPTION TYPE:
```

This configuration option is an integer define.

```{eval-rst}
.. rubric:: DEFAULT VALUE:
```

The default value is 1.

```{eval-rst}
.. rubric:: DESCRIPTION:
```

description k

% Generated from spec:/l

```{raw} latex
\\clearpage
```

```{index} l
```

(l)=

## l

```{eval-rst}
.. rubric:: CONSTANT:
```

`l`

```{eval-rst}
.. rubric:: OPTION TYPE:
```

This configuration option is an initializer define.

```{eval-rst}
.. rubric:: DEFAULT VALUE:
```

The default value is 1.

```{eval-rst}
.. rubric:: DESCRIPTION:
```

description l

```{eval-rst}
.. rubric:: CONSTRAINTS:
```

The following constraints apply to this configuration option:

- The value of the configuration option shall be greater than or equal to zero.

- The value of the configuration option shall be

- - less than, or

- - equal to two.

% Generated from spec:/m

```{raw} latex
\\clearpage
```

```{index} m
```

(m)=

## m

```{eval-rst}
.. rubric:: CONSTANT:
```

`m`

```{eval-rst}
.. rubric:: OPTION TYPE:
```

This configuration option is an initializer define.

```{eval-rst}
.. rubric:: DEFAULT VALUE:
```

The default value is 1.

```{eval-rst}
.. rubric:: DESCRIPTION:
```

description m
"""
        assert content == src.read()
    with open(doxygen_h, "r") as src:
        content = """/* SPDX-License-Identifier: BSD-2-Clause */

/**
 * @file
 *
 * @ingroup RTEMSImplDoxygen
 *
 * @brief This header file documents the application configuration options.
 */

/*
 * Copyright (C) 2020, 2021 embedded brains GmbH & Co. KG
 *
 * Redistribution and use in source and binary forms, with or without
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
 * POSSIBILITY OF SUCH DAMAGE.
 */

/*
 * This file was automatically generated.  Do not edit it.
 */

/**
 * @defgroup RTEMSApplConfig Application Configuration Options
 *
 * @ingroup RTEMSAPI
 */

/* Generated from spec:/g */

/**
 * @defgroup RTEMSApplConfiggroupname group name
 *
 * @ingroup RTEMSApplConfig
 *
 * description
 *
 * @{
 */

/* Generated from spec:/a */

/**
 * @brief This configuration option is a boolean feature define.
 *
 * @anchor a
 *
 * description a
 *
 * @par Default Configuration
 * default a
 *
 * @par Notes
 * @parblock
 * notes a
 *
 * references:
 *
 * * @ref b
 *
 * * <a href="unspec-group.html">Unspec Group</a>
 *
 * * Unspec Group 2
 *
 * * <a href="unspec-group-3.html">Unspec Group 3</a>
 *
 * * <a href="unspec-func.html">unspec_func()</a>
 *
 * * unspec_func_no_ref()
 *
 * * func()
 *
 * * ::td
 *
 * * #DEFINE
 *
 * * #UNSPEC_DEFINE
 *
 * * <a href="https://foo">UNSPEC_DEFINE_2</a>
 *
 * * ::unspec_type
 *
 * * <a href="https://bar">unspec_type_2</a>
 * @endparblock
 */
#define a

/* Generated from spec:/b */

/**
 * @brief This configuration option is a boolean feature define.
 *
 * @anchor b
 *
 * description b
 *
 * @par Default Configuration
 * If this configuration option is undefined, then the described feature is not
 * enabled.
 */
#define b

/* Generated from spec:/c */

/**
 * @brief This configuration option is an integer define.
 *
 * @anchor c
 *
 * description c
 *
 * @par Default Value
 * The default value is 13.
 *
 * @par Constraints
 * constraint d
 *
 * @par Notes
 * notes c
 */
#define c

/* Generated from spec:/e */

/**
 * @brief This configuration option is an integer define.
 *
 * @anchor e
 *
 * description e
 *
 * @par Default Value
 * The default value is 7.
 */
#define e

/* Generated from spec:/f */

/**
 * @brief This configuration option is an integer define.
 *
 * @anchor f
 *
 * description f
 *
 * @par Default Value
 * The default value is 1.
 */
#define f

/* Generated from spec:/h */

/**
 * @brief This configuration option is an integer define.
 *
 * @anchor h
 *
 * description h
 *
 * @par Default Value
 * The default value is 1.
 */
#define h

/* Generated from spec:/i */

/**
 * @brief This configuration option is an integer define.
 *
 * @anchor i
 *
 * description i
 *
 * @par Default Value
 * The default value is 1.
 */
#define i

/* Generated from spec:/j */

/**
 * @brief This configuration option is an integer define.
 *
 * @anchor j
 *
 * description j
 *
 * @par Default Value
 * Foo bar.
 *
 * @par Constraints
 * constraint d
 */
#define j

/* Generated from spec:/k */

/**
 * @brief This configuration option is an integer define.
 *
 * @anchor k
 *
 * description k
 *
 * @par Default Value
 * The default value is 1.
 */
#define k

/* Generated from spec:/l */

/**
 * @brief This configuration option is an initializer define.
 *
 * @anchor l
 *
 * description l
 *
 * @par Default Value
 * The default value is 1.
 *
 * @par Constraints
 * @parblock
 * The following constraints apply to this configuration option:
 *
 * - The value of the configuration option shall be greater than or equal to
 *   zero.
 *
 * - The value of the configuration option shall be
 *
 * - - less than, or
 *
 * - - equal to two.
 * @endparblock
 */
#define l

/* Generated from spec:/m */

/**
 * @brief This configuration option is an initializer define.
 *
 * @anchor m
 *
 * description m
 *
 * @par Default Value
 * The default value is 1.
 */
#define m

/** @} */
"""
        assert content == src.read()
        option_item = item_cache["/k"]
        option_content = SphinxContent()
        document_option(option_content, ItemMapper(option_item), option_item,
                        [])
        assert str(option_content) == """.. rubric:: OPTION TYPE:

This configuration option is an integer define.

.. rubric:: DEFAULT VALUE:

The default value is 1.

.. rubric:: DESCRIPTION:

description k
"""
