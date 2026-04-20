# SPDX-License-Identifier: BSD-2-Clause
""" Provides methods to generate the interface documentation. """

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

import functools
import os
from typing import Any, Callable, Optional

from specitems import (EnabledSet, Item, ItemCache, ItemGetValueContext,
                       ItemMapper, make_label, TextContent)

from .contentc import (CContent, get_value_compound,
                       get_value_forward_declaration,
                       get_value_unspecified_type)
from .interfacemapper import sanitize_name


def _get_code_param(ctx: ItemGetValueContext) -> Any:
    return sanitize_name(ctx.value[ctx.key])


class CodeMapper(ItemMapper):
    """ Item mapper for code blocks. """

    def __init__(self, item: Item):
        super().__init__(item)
        self.add_get_value("interface/forward-declaration:/name",
                           get_value_forward_declaration)
        self.add_get_value("interface/struct:/name", get_value_compound)
        self.add_get_value("interface/union:/name", get_value_compound)
        self.add_get_value("interface/macro:/params/name", _get_code_param)
        self.add_get_value("interface/unspecified-struct:/name",
                           get_value_unspecified_type)
        self.add_get_value("interface/unspecified-union:/name",
                           get_value_unspecified_type)


def _generate_introduction(content: TextContent, mapper: ItemMapper,
                           target: str, group: Item,
                           items: list[Item]) -> None:
    content.register_license_and_copyrights_of_item(group)
    content.add_automatically_generated_warning()
    with content.comment_block():
        content.add(f"Generated from spec:{group.uid}")
    group_name = group["name"]
    content.push_label(make_label(group_name))
    with content.section("Introduction"):
        # This needs to be in front of the list since comment blocks have an
        # effect on the list layout in the HTML output
        with content.comment_block():
            content.add("The following list was generated from:")
            for item in items:
                content.append(f"spec:{item.uid}")

        content.append("")
        content.gap = False
        content.wrap(mapper.substitute(group["brief"], group))
        content.wrap(mapper.substitute(group["description"], group))
        content.paste(f"The directives provided by the {group_name} are:")

        for item in items:
            content.register_license_and_copyrights_of_item(item)
            name = item["name"]
            brief = mapper.substitute(item["brief"], item)
            if brief:
                brief = f" - {brief}"
            else:
                brief = ""
            ref = content.reference(make_label(f"Interface {name}"))
            content.add_list_item(f"{ref}{brief}")
    content.add_licence_and_copyrights()
    content.write(target, beautify=True)


def _add_function_definition(content: CContent, mapper: ItemMapper, item: Item,
                             prefix: str, value: dict[str, Any]) -> None:
    ret = mapper.substitute(value["return"], item)
    name = item["name"]
    params = [
        mapper.substitute(param, item, prefix) for param in value["params"]
    ]
    content.declare_function(ret, name, params)


_ADD_DEFINITION = {
    "interface/function": _add_function_definition,
    "interface/macro": _add_function_definition,
}


def _add_definition(content: CContent, mapper: ItemMapper, item: Item,
                    prefix: str, value: dict[str, dict]) -> None:
    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-positional-arguments
    add_definition = _ADD_DEFINITION[item.type]
    key = "default"
    definition = value[key]
    if not definition:
        # Assume that all definitions have the same interface
        key = "variants[0]/definition"
        definition = value["variants"][0]["definition"]
    add_definition(content, mapper, item, os.path.join(prefix, key),
                   definition)


def _add_text(content: TextContent, mapper: ItemMapper, item: Item,
              key: str) -> None:
    text = item[key]
    if text:
        content.add_rubric(f"{key.upper()}:")
        content.wrap(mapper.substitute(text, item))


def _add_params(content: TextContent, mapper: ItemMapper, item: Item,
                params: dict) -> None:
    if params:
        content.add_rubric("PARAMETERS:")
        for param in params:
            description = param["description"]
            if description:
                content.add_definition_item(
                    content.code(sanitize_name(param["name"])),
                    mapper.substitute(f"This parameter {description}", item))


def _add_return(content: TextContent, mapper: ItemMapper, item: Item,
                ret: dict) -> None:
    if ret:
        content.add_rubric("RETURN VALUES:")
        for retval in ret["return-values"]:
            if isinstance(retval["value"], str):
                value = mapper.substitute(retval["value"], item)
            else:
                value = content.code(str(retval["value"]))
            content.add_definition_item(
                value, mapper.substitute(retval["description"], item))
        content.wrap(mapper.substitute(ret["return"], item))


def _document_directive(content: TextContent, mapper: ItemMapper,
                        code_mapper: CodeMapper, item: Item,
                        enable_set: EnabledSet) -> None:
    content.wrap(mapper.substitute(item["brief"], item))
    content.add_rubric("CALLING SEQUENCE:")
    with content.directive("code-block", "c"):
        code = CContent()
        _add_definition(code, code_mapper, item, "definition",
                        item["definition"])
        content.add(code)
    _add_params(content, mapper, item, item["params"])
    _add_text(content, mapper, item, "description")
    _add_return(content, mapper, item, item["return"])
    _add_text(content, mapper, item, "notes")
    constraints = [
        mapper.substitute(parent["text"], parent)
        for parent in item.parents("constraint")
        if parent.is_enabled(enable_set)
    ]
    if constraints:
        content.add_rubric("CONSTRAINTS:")
        content.add_list(constraints,
                         "The following constraints apply to this directive:")


def document_directive(content: TextContent, mapper: ItemMapper, item: Item,
                       enable_set: EnabledSet) -> None:
    """
    Document the directive specified by the item using the item mapper and
    enabled set.
    """
    _document_directive(content, mapper, CodeMapper(item), item, enable_set)


def _generate_directives(content: TextContent, mapper: ItemMapper, target: str,
                         group: Item, items: list[Item],
                         enable_set: EnabledSet) -> None:
    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-positional-arguments
    content.register_license_and_copyrights_of_item(group)
    content.add_automatically_generated_warning()
    group_name = group["name"]
    content.push_label(make_label(group_name))
    with content.section("Directives"):
        content.wrap([
            f"This section details the directives of the {group_name}.",
            "A subsection is dedicated to each of this manager's directives",
            "and lists the calling sequence, parameters, description,",
            "return values, and notes of the directive."
        ])
        for item in items:
            content.register_license_and_copyrights_of_item(item)
            name = item["name"]
            code_mapper = CodeMapper(item)
            with content.comment_block():
                content.add(f"Generated from spec:{item.uid}")
            with content.directive("raw", "latex"):
                content.add("\\clearpage")
            directive = f"{name}()"
            content.add_index_entries([directive] + item["index-entries"])
            with content.section(directive,
                                 label=make_label(f"Interface {directive}")):
                _document_directive(content, mapper, code_mapper, item,
                                    enable_set)
    content.add_licence_and_copyrights()
    content.write(target, beautify=True)


def _directive_key(order: list[Item], item: Item) -> tuple[int, str]:
    try:
        index = order.index(item) - len(order)
    except ValueError:
        index = 1
    return (index, item.uid)


def _add_type_definition(content: TextContent, mapper: ItemMapper, item: Item,
                         definition: dict | Item) -> None:
    text = definition["brief"].strip()
    if definition["description"]:
        text += "\n" + definition["description"].strip()
    content.add_definition_item(definition["name"],
                                mapper.substitute(text, item))


def _type_compound(content: TextContent, mapper: ItemMapper,
                   item: Item) -> None:
    content.add_rubric("MEMBERS:")
    for member in item["definition"]:
        _add_type_definition(content, mapper, item, member["default"])
    _add_text(content, mapper, item, "description")


def _type_enum(content: TextContent, mapper: ItemMapper, item: Item) -> None:
    content.add_rubric("ENUMERATORS:")
    for enumerator in item.parents("interface-enumerator"):
        _add_type_definition(content, mapper, item, enumerator)
    _add_text(content, mapper, item, "description")


def _type_typedef(content: TextContent, mapper: ItemMapper,
                  item: Item) -> None:
    _add_params(content, mapper, item, item["params"])
    _add_text(content, mapper, item, "description")
    _add_return(content, mapper, item, item["return"])


_TYPE_GENERATORS = {
    "interface/enum": _type_enum,
    "interface/struct": _type_compound,
    "interface/typedef": _type_typedef,
    "interface/union": _type_compound
}


def _gather_types(item: Item, types: list[Item]) -> None:
    for child in item.children("interface-placement"):
        if child.type in _TYPE_GENERATORS:
            types.append(child)
        _gather_types(child, types)


def _is_opaque_type(item: Item) -> Optional[Item]:
    for constraint in item.parents("constraint"):
        if constraint.uid == "/constraint/type-opaque":
            return constraint
    return None


def _generate_types(content: TextContent, mapper: ItemMapper, config: dict,
                    item_cache: ItemCache) -> None:
    types: list[Item] = []
    for domain in config["domains"]:
        _gather_types(item_cache[domain], types)
    content.add_automatically_generated_warning()
    content.add_index_entries(["RTEMS Data Types", "data types"])
    with content.section("RTEMS Data Types"):
        with content.section("Introduction"):
            content.wrap("""This chapter contains a complete list of the RTEMS
primitive data types in alphabetical order.  This is intended to be an overview
and the user is encouraged to look at the appropriate chapters in the manual
for more information about the usage of the various data types.""")

        with content.section("List of Data Types"):
            content.wrap(
                "The following is a complete list of the RTEMS primitive data "
                "types in alphabetical order:")
            for item in sorted(types, key=lambda x: x["name"]):
                content.register_license_and_copyrights_of_item(item)
                with content.comment_block():
                    content.add(f"Generated from spec:{item.uid}")
                name = item["name"]
                content.add_index_entries([name] + item["index-entries"])
                with content.section(name,
                                     label=make_label(f"Interface {name}")):
                    content.wrap(mapper.substitute(item["brief"], item))
                    constraint = _is_opaque_type(item)
                    if constraint is None:
                        _TYPE_GENERATORS[item.type](content, mapper, item)
                    else:
                        content.add_rubric("MEMBERS:")
                        content.wrap(
                            mapper.substitute(constraint["text"], item))
                        _add_text(content, mapper, item, "description")
                    _add_text(content, mapper, item, "notes")
    content.add_licence_and_copyrights()
    content.write(config["target"], beautify=True)


def generate_interface_documentation(
        config: dict, item_cache: ItemCache,
        create_mapper: Callable[[Item, list[str]], ItemMapper],
        create_content: Callable[[], TextContent]) -> None:
    """
    Generate interface documentation according to the configuration.

    Args:
        config: The interface generation configuration.
        item_cache: The item cache containing the interfaces.
        create_mapper: The item mapper constructor to create mappers used for
            content substitutions.
        create_content: The content builder constructor.
    """
    groups = config["groups"]
    enable_set = config["enabled"]
    group_uids = [doc_config["group"] for doc_config in groups]
    group_uids.extend(uid for uid in config["types"]["groups"])
    some_item = next(iter(item_cache.values()))
    mapper = create_mapper(some_item, group_uids)
    for doc_config in groups:
        items: list[Item] = []
        group = item_cache[doc_config["group"]]
        assert group.type == "interface/group"
        for child in group.children("interface-ingroup"):
            if child.type in ["interface/function", "interface/macro"]:
                items.append(child)
        items.sort(key=functools.partial(
            _directive_key, list(group.parents("placement-order"))))
        _generate_introduction(create_content(), mapper,
                               doc_config["introduction-target"], group, items)
        _generate_directives(create_content(), mapper,
                             doc_config["directives-target"], group, items,
                             enable_set)
    _generate_types(create_content(), mapper, config["types"], item_cache)
