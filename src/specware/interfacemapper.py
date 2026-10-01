# SPDX-License-Identifier: BSD-2-Clause
""" Provides methods to generate the interface documentation. """

# Copyright (C) 2020, 2026 embedded brains GmbH & Co. KG
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

from typing import Callable, Optional

from specitems import (BibTeXCitationProvider, ContentContext, Item,
                       ItemGetValue, ItemGetValueContext, ItemMapper,
                       MarkdownMapper, ReferenceTarget, SphinxMapper,
                       get_reference, get_reference_target, make_label)

from .contentc import get_value_header_file


def sanitize_name(name: str) -> str:
    """ Remove leading underscores from the name. """
    return name.lstrip("_")


def get_interface_reference(item: Item) -> Optional[ReferenceTarget]:
    """
    Get the target of the reference link of the interface.

    Return None, if the interface has no reference link.

    Raises:
        ValueError: The interface has more than one reference link.
    """
    links = list(item.links_to_parents("reference"))
    if not links:
        return None
    if len(links) > 1:
        raise ValueError(f"{item.uid}: an interface shall have at most one "
                         "reference link")
    return get_reference_target(links[0].item, links[0])


def get_reference_url(mapper: ItemMapper,
                      target: ReferenceTarget) -> Optional[str]:
    """
    Get the URL of the reference target substituted in the context of the
    referenced work.
    """
    if target.url is None:
        return None
    return mapper.substitute(target.url, target.work)


def _relpath(_ctx: ItemGetValueContext, value: str) -> str:
    return value


def add_reference_transformers(mapper: ItemMapper) -> None:
    """
    Add the value transformers which the URLs of references may use.

    Outside a package build, the relpath transformer returns the path
    unchanged.
    """
    mapper.add_value_transformer("relpath", _relpath)


#: Formats a reference to a label with an optional name.
FormatLabel = Callable[[Optional[str], str], str]

#: Formats a hyperlink with a name to an URL.
FormatLink = Callable[[str, str], str]


def _format_reference(ctx: ItemGetValueContext,
                      target: Optional[ReferenceTarget], name: Optional[str],
                      fallback: str) -> str:
    """
    Format a reference to the target.

    Inside the target document, a target with a label yields a reference to
    the label.  Elsewhere, a target with an URL yields a hyperlink.  A name of
    None makes the reference to the label take the title of the label target.
    """
    if target is None:
        return fallback
    mapper = ctx.mapper
    assert isinstance(mapper, (SphinxInterfaceMapper, MarkdownInterfaceMapper))
    if (target.label is not None
            and mapper.target_document_uid == target.work.uid):
        return mapper.format_reference_label(name, target.label)
    url = get_reference_url(mapper, target)
    if url is None:
        return fallback
    return mapper.format_reference_link(fallback if name is None else name,
                                        url)


def _get_value_ref(ctx: ItemGetValueContext,
                   get_value: ItemGetValue,
                   postfix: str = "",
                   prefix: str = "") -> str:
    return _format_reference(ctx, get_interface_reference(ctx.item),
                             f"{prefix}{ctx.value[ctx.key]}{postfix}",
                             get_value(ctx))


def _get_value_unspecified_group(ctx: ItemGetValueContext) -> str:
    return _format_reference(ctx, get_interface_reference(ctx.item), None,
                             ctx.value[ctx.key])


def _get_value_reference_location(ctx: ItemGetValueContext) -> str:
    return _format_reference(ctx, get_reference_target(ctx.item), None,
                             ctx.value[ctx.key])


def _format_sphinx_label(name: Optional[str], label: str) -> str:
    if name is None:
        return f":ref:`{label}`"
    return f":ref:`{name} <{label}>`"


def _format_sphinx_link(name: str, url: str) -> str:
    return f"`{name} <{url}>`_"


def _format_markdown_label(name: Optional[str], label: str) -> str:
    if name is None:
        return f"{{ref}}`{label}`"
    return f"{{ref}}`{name} <{label}>`"


def _format_markdown_link(name: str, url: str) -> str:
    return f"[{name}]({url})"


def _compound_kind(ctx: ItemGetValueContext) -> str:
    type_name = ctx.item.type
    return f"{type_name[type_name.rfind('-') + 1:]} "


def _get_value_sphinx_appl_config_option(ctx: ItemGetValueContext) -> str:
    return f":ref:`{ctx.value[ctx.key]}`"


def _get_value_sphinx_macro(ctx: ItemGetValueContext) -> str:
    return f":c:macro:`{ctx.value[ctx.key]}`"


def _get_value_sphinx_function(ctx: ItemGetValueContext) -> str:
    return f":c:func:`{ctx.value[ctx.key]}`"


def _get_value_sphinx_type(ctx: ItemGetValueContext) -> str:
    return f":c:type:`{ctx.value[ctx.key]}`"


def _get_value_sphinx_compound(ctx: ItemGetValueContext) -> str:
    return f"``{_compound_kind(ctx)}{ctx.value[ctx.key]}``"


def _get_value_sphinx_unspecified_define(ctx: ItemGetValueContext) -> str:
    return _get_value_ref(ctx, _get_value_sphinx_macro)


def _get_value_sphinx_unspecified_function(ctx: ItemGetValueContext) -> str:
    return _get_value_ref(ctx, _get_value_sphinx_function, "()")


def _get_value_sphinx_unspecified_type(ctx: ItemGetValueContext) -> str:
    return _get_value_ref(ctx, _get_value_sphinx_type)


def _get_value_sphinx_unspecified_compound(ctx: ItemGetValueContext) -> str:
    return _get_value_ref(ctx,
                          _get_value_sphinx_compound,
                          prefix=_compound_kind(ctx))


def get_value_sphinx_param(ctx: ItemGetValueContext) -> str:
    """ Gets a function or macro parameter. """
    return f"``{sanitize_name(ctx.value[ctx.key])}``"


def get_value_sphinx_header_file(ctx: ItemGetValueContext) -> str:
    """ Gets a header file. """
    return f"``<{ctx.value[ctx.key]}>``"


class SphinxInterfaceMapper(SphinxMapper):
    """ Sphinx item mapper for the interface documentation. """

    def __init__(self,
                 item: Item,
                 group_uids: list[str],
                 context: str | ContentContext,
                 target_document_uid: Optional[str] = None):
        super().__init__(item, context)
        self._group_uids = set(group_uids)

        #: The UID of the target document of the mapper.
        self.target_document_uid = target_document_uid

        self.format_reference_label: FormatLabel = _format_sphinx_label
        self.format_reference_link: FormatLink = _format_sphinx_link
        BibTeXCitationProvider(self)
        add_reference_transformers(self)
        self.add_get_value("reference-location:/name",
                           _get_value_reference_location)
        self.add_get_value("interface/appl-config-option/feature-enable:/name",
                           _get_value_sphinx_appl_config_option)
        self.add_get_value("interface/appl-config-option/feature:/name",
                           _get_value_sphinx_appl_config_option)
        self.add_get_value("interface/appl-config-option/initializer:/name",
                           _get_value_sphinx_appl_config_option)
        self.add_get_value("interface/appl-config-option/integer:/name",
                           _get_value_sphinx_appl_config_option)
        self.add_get_value("interface/define:/name", _get_value_sphinx_macro)
        self.add_get_value("interface/enum:/name", self._get_type)
        self.add_get_value("interface/enumerator:/name",
                           _get_value_sphinx_macro)
        self.add_get_value("interface/function:/name", self._get_function)
        self.add_get_value("interface/function:/params/name",
                           get_value_sphinx_param)
        self.add_get_value("interface/group:/name", self._get_group)
        self.add_get_value("interface/header-file:/path",
                           get_value_sphinx_header_file)
        self.add_get_value("interface/macro:/name", self._get_function)
        self.add_get_value("interface/macro:/params/name",
                           get_value_sphinx_param)
        self.add_get_value("interface/struct:/name", self._get_compound)
        self.add_get_value("interface/typedef:/name", self._get_type)
        self.add_get_value("interface/typedef:/params/name",
                           get_value_sphinx_param)
        self.add_get_value("interface/union:/name", self._get_compound)
        self.add_get_value("interface/unspecified-define:/name",
                           _get_value_sphinx_unspecified_define)
        self.add_get_value("interface/unspecified-enumerator:/name",
                           _get_value_sphinx_unspecified_define)
        self.add_get_value("interface/unspecified-function:/name",
                           _get_value_sphinx_unspecified_function)
        self.add_get_value("interface/unspecified-group:/name",
                           _get_value_unspecified_group)
        self.add_get_value("interface/unspecified-enum:/name",
                           _get_value_sphinx_unspecified_type)
        self.add_get_value("interface/unspecified-struct:/name",
                           _get_value_sphinx_unspecified_compound)
        self.add_get_value("interface/unspecified-typedef:/name",
                           _get_value_sphinx_unspecified_type)
        self.add_get_value("interface/unspecified-union:/name",
                           _get_value_sphinx_unspecified_compound)

    def _get_reference(self, ctx: ItemGetValueContext, name: str,
                       fallback: str) -> str:
        for group in ctx.item.parents("interface-ingroup"):
            if group.uid in self._group_uids:
                return get_reference(make_label(f"Interface {name}"))
        return fallback

    def _get_compound(self, ctx: ItemGetValueContext) -> str:
        if ctx.item["definition-kind"] in ["struct-only", "union-only"]:
            prefix = f"{ctx.item['interface-type']} "
        else:
            prefix = ""
        name = ctx.value[ctx.key]
        return self._get_reference(ctx, name, f"``{prefix}{name}``")

    def _get_function(self, ctx: ItemGetValueContext) -> str:
        name = ctx.value[ctx.key]
        return self._get_reference(ctx, name, f":c:func:`{name}`")

    def _get_type(self, ctx: ItemGetValueContext) -> str:
        name = ctx.value[ctx.key]
        return self._get_reference(ctx, name, f":c:type:`{name}`")

    def _get_group(self, ctx: ItemGetValueContext) -> str:
        if ctx.item.uid in self._group_uids:
            return get_reference(ctx.value["identifier"])
        return ctx.value[ctx.key]


def _get_value_markdown_appl_config_option(ctx: ItemGetValueContext) -> str:
    return f"{{ref}}`{ctx.value[ctx.key]}`"


def _get_value_markdown_macro(ctx: ItemGetValueContext) -> str:
    return f"{{c:macro}}`{ctx.value[ctx.key]}`"


def _get_value_markdown_function(ctx: ItemGetValueContext) -> str:
    return f"{{c:func}}`{ctx.value[ctx.key]}`"


def _get_value_markdown_type(ctx: ItemGetValueContext) -> str:
    return f"{{c:type}}`{ctx.value[ctx.key]}`"


def _get_value_markdown_compound(ctx: ItemGetValueContext) -> str:
    return f"{{c:type}}`{_compound_kind(ctx)}{ctx.value[ctx.key]}`"


def _get_value_markdown_unspecified_define(ctx: ItemGetValueContext) -> str:
    return _get_value_ref(ctx, _get_value_markdown_macro)


def _get_value_markdown_unspecified_function(ctx: ItemGetValueContext) -> str:
    return _get_value_ref(ctx, _get_value_markdown_function, "()")


def _get_value_markdown_unspecified_type(ctx: ItemGetValueContext) -> str:
    return _get_value_ref(ctx, _get_value_markdown_type)


def _get_value_markdown_unspecified_compound(ctx: ItemGetValueContext) -> str:
    return _get_value_ref(ctx,
                          _get_value_markdown_compound,
                          prefix=_compound_kind(ctx))


def get_value_markdown_param(ctx: ItemGetValueContext) -> str:
    """ Gets a function or macro parameter. """
    return f"`{sanitize_name(ctx.value[ctx.key])}`"


class MarkdownInterfaceMapper(MarkdownMapper):
    """ Markdown item mapper for the interface documentation. """

    def __init__(self,
                 item: Item,
                 group_uids: list[str],
                 context: str | ContentContext,
                 target_document_uid: Optional[str] = None):
        super().__init__(item, context)
        self._group_uids = set(group_uids)

        #: The UID of the target document of the mapper.
        self.target_document_uid = target_document_uid

        self.format_reference_label: FormatLabel = _format_markdown_label
        self.format_reference_link: FormatLink = _format_markdown_link
        BibTeXCitationProvider(self)
        add_reference_transformers(self)
        self.add_get_value("reference-location:/name",
                           _get_value_reference_location)
        self.add_get_value("interface/appl-config-option/feature-enable:/name",
                           _get_value_markdown_appl_config_option)
        self.add_get_value("interface/appl-config-option/feature:/name",
                           _get_value_markdown_appl_config_option)
        self.add_get_value("interface/appl-config-option/initializer:/name",
                           _get_value_markdown_appl_config_option)
        self.add_get_value("interface/appl-config-option/integer:/name",
                           _get_value_markdown_appl_config_option)
        self.add_get_value("interface/define:/name", _get_value_markdown_macro)
        self.add_get_value("interface/enum:/name", self._get_type)
        self.add_get_value("interface/enumerator:/name",
                           _get_value_markdown_macro)
        self.add_get_value("interface/function:/name", self._get_function)
        self.add_get_value("interface/function:/params/name",
                           get_value_markdown_param)
        self.add_get_value("interface/group:/name", self._get_group)
        self.add_get_value("interface/header-file:/path",
                           get_value_header_file)
        self.add_get_value("interface/macro:/name", self._get_function)
        self.add_get_value("interface/macro:/params/name",
                           get_value_markdown_param)
        self.add_get_value("interface/struct:/name", self._get_compound)
        self.add_get_value("interface/typedef:/name", self._get_type)
        self.add_get_value("interface/typedef:/params/name",
                           get_value_markdown_param)
        self.add_get_value("interface/union:/name", self._get_compound)
        self.add_get_value("interface/unspecified-define:/name",
                           _get_value_markdown_unspecified_define)
        self.add_get_value("interface/unspecified-enumerator:/name",
                           _get_value_markdown_unspecified_define)
        self.add_get_value("interface/unspecified-function:/name",
                           _get_value_markdown_unspecified_function)
        self.add_get_value("interface/unspecified-group:/name",
                           _get_value_unspecified_group)
        self.add_get_value("interface/unspecified-enum:/name",
                           _get_value_markdown_unspecified_type)
        self.add_get_value("interface/unspecified-struct:/name",
                           _get_value_markdown_unspecified_compound)
        self.add_get_value("interface/unspecified-typedef:/name",
                           _get_value_markdown_unspecified_type)
        self.add_get_value("interface/unspecified-union:/name",
                           _get_value_markdown_unspecified_compound)

    def _get_reference(self, ctx: ItemGetValueContext, name: str,
                       fallback: str) -> str:
        for group in ctx.item.parents("interface-ingroup"):
            if group.uid in self._group_uids:
                label = make_label(f"Interface {name}")
                return f"{{ref}}`{label}`"
        return fallback

    def _get_compound(self, ctx: ItemGetValueContext) -> str:
        if ctx.item["definition-kind"] in ["struct-only", "union-only"]:
            prefix = f"{ctx.item['interface-type']} "
        else:
            prefix = ""
        name = ctx.value[ctx.key]
        return self._get_reference(ctx, name, f"`{prefix}{name}`")

    def _get_function(self, ctx: ItemGetValueContext) -> str:
        name = ctx.value[ctx.key]
        return self._get_reference(ctx, name, f"{{c:func}}`{name}`")

    def _get_type(self, ctx: ItemGetValueContext) -> str:
        name = ctx.value[ctx.key]
        return self._get_reference(ctx, name, f"{{c:type}}`{name}`")

    def _get_group(self, ctx: ItemGetValueContext) -> str:
        if ctx.item.uid in self._group_uids:
            return f"{{ref}}`{ctx.value['identifier']}`"
        return ctx.value[ctx.key]
