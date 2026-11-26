# SPDX-License-Identifier: BSD-2-Clause
""" Provides a generator of a glossary page for Doxygen. """

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

import dataclasses
from typing import Optional

from specitems import (ClangFormatter, ContentContext, Item, ItemCache,
                       ItemGetValueContext, ItemMapper, augment_glossary_terms,
                       get_value_plural, to_camel_case)

from .applconfig import add_doxygen_get_values
from .contentc import CContent


@dataclasses.dataclass
class DoxygenGlossaryConfig:
    """ Represents a Doxygen glossary configuration. """
    target: str = "glossary.h"
    page_name: str = "Glossary"
    page_title: str = "Glossary"
    groups: list[str] = dataclasses.field(default_factory=list)
    file_ingroups: list[str] = dataclasses.field(default_factory=list)


def _gather_terms(item: Item, terms: dict[str, Item]) -> None:
    for child in item.children("requirement-refinement"):
        _gather_terms(child, terms)
    for child in item.children("glossary-member"):
        terms[child.uid] = child


def _get_terms(config: DoxygenGlossaryConfig,
               item_cache: ItemCache) -> dict[str, Item]:
    terms: dict[str, Item] = {}
    for uid in config.groups:
        group = item_cache[uid]
        assert group.type == "glossary/group"
        augment_glossary_terms(group, [])
        _gather_terms(group, terms)
    return terms


def is_doxygen_glossary_affected(config: DoxygenGlossaryConfig,
                                 item_cache: ItemCache,
                                 uids: set[str]) -> bool:
    """
    Return true, if the page of the Doxygen glossary task defines a term
    specified by the UIDs, otherwise false.

    Args:
        config: The Doxygen glossary configuration.
        item_cache: The item cache containing the glossary groups and terms.
        uids: The UIDs of the items which changed.
    """
    return not uids.isdisjoint(_get_terms(config, item_cache))


def _get_cite_long(ctx: ItemGetValueContext) -> str:
    return f"*{ctx.mapper.substitute(ctx.item['title'], ctx.item)}*"


def _get_cite(ctx: ItemGetValueContext) -> str:
    return f"[{_get_cite_long(ctx)}]"


class _GlossaryMapper(ItemMapper):
    """
    Maps a glossary term of the page to a reference to its anchor.

    A term outside the page maps to its plain text.
    """

    def __init__(self, item: Item, page_name: str, terms: dict[str, Item]):
        super().__init__(item)
        self._page_name = page_name
        self._terms = terms
        add_doxygen_get_values(self)
        self.add_get_value("glossary/term:/term", self._get_term)
        self.add_get_value("glossary/term:/plural", self._get_plural)
        self.add_get_value("reference:/cite", _get_cite)
        self.add_get_value("reference:/cite-long", _get_cite_long)

    def get_anchor(self, term: Item) -> str:
        """ Get the anchor of the term. """
        return f"{self._page_name}{to_camel_case(term.view['term'])}"

    def _reference(self, ctx: ItemGetValueContext, text: str) -> str:
        if ctx.item.uid not in self._terms:
            return text
        return f"@ref {self.get_anchor(ctx.item)} \"{text}\""

    def _get_term(self, ctx: ItemGetValueContext) -> str:
        return self._reference(ctx, ctx.item.view["term"])

    def _get_plural(self, ctx: ItemGetValueContext) -> str:
        return self._reference(ctx, get_value_plural(ctx))


def generate_doxygen_glossary(
        config: DoxygenGlossaryConfig,
        item_cache: ItemCache,
        context: ContentContext,
        formatter: Optional[ClangFormatter] = None) -> None:
    """
    Generate a Doxygen source with a page which defines the glossary terms.

    The page holds a definition list of the terms of the glossary groups.  The
    list is sorted by the term without regard to case.  Each term has an
    anchor, and a substituted term of the page refers to it.

    Args:
        config: The Doxygen glossary configuration.
        item_cache: The item cache containing the glossary groups and terms.
        context: The content context of the Doxygen source.
        formatter: The optional formatter of the Doxygen source.
    """
    terms = _get_terms(config, item_cache)
    page_name = config.page_name
    mapper = _GlossaryMapper(next(iter(item_cache.values())), page_name, terms)
    content = CContent(context)
    content.add_automatically_generated_warning()
    with content.doxygen_block():
        content.add(f"@page {page_name} {config.page_title}")
        content.add("<dl>")
        for term in sorted(terms.values(),
                           key=lambda item: item.view["term"].lower()):
            content.register_license_and_copyrights_of_item(term)
            content.add(f"<dt>@anchor {mapper.get_anchor(term)} "
                        f"{term.view['term']}</dt>")
            content.append("<dd>")
            content.gap = False
            content.wrap(mapper.substitute(term["text"], term))
            content.append("</dd>")
        content.add("</dl>")
    content.prepend_copyrights_and_licenses()
    file_block = ["/**", " * @file", " *"]
    file_block.extend(f" * @ingroup {group}" for group in config.file_ingroups)
    file_block.extend([
        " *", " * @brief This header file provides the glossary page.", " */",
        ""
    ])
    content.prepend(file_block)
    content.prepend_spdx_license_identifier()
    content.write(config.target, beautify=True, formatter=formatter)
