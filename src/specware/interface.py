# SPDX-License-Identifier: BSD-2-Clause
""" Provides methods to generate C language interfaces. """

# Copyright (C) 2020, 2021 embedded brains GmbH & Co. KG
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

# pylint: disable=too-many-lines

import collections
from contextlib import contextmanager
import functools
import itertools
import os
from typing import Any, Callable, Iterator, NamedTuple, Optional, Union

from specitems import (Item, ItemCache, ItemGetValueContext, ItemGetValueMap,
                       ItemMapper, get_value_default, get_value_plural, Link,
                       to_camel_case)

from .contentc import (CContent, CInclude, enabled_by_to_exp, ExpressionMapper,
                       forward_declaration, get_value_compound,
                       get_value_double_colon, get_value_doxygen_function,
                       get_value_doxygen_group, get_value_doxygen_ref,
                       get_value_forward_declaration, get_value_hash,
                       get_value_header_file, get_value_params,
                       get_value_unspecified_type)

_ItemMap = dict[str, Item]
_Lines = Union[str, list[str]]
_GetLines = Callable[["_Node", Item, str, Any], _Lines]


def _get_ingroups(item: Item) -> _ItemMap:
    ingroups: _ItemMap = {}
    for group in item.parents("interface-ingroup"):
        ingroups[group.uid] = group
    return ingroups


def _get_group_identifiers(groups: _ItemMap) -> list[str]:
    return [item["identifier"] for item in groups.values()]


class _InterfaceMapper(ItemMapper):

    def __init__(self, node: "_Node"):
        super().__init__(node.item)
        self._node = node
        self._is_doc = True
        self.add_get_value("glossary/term:/plural", get_value_plural)
        self.add_get_value("interface/appl-config-option:/name",
                           get_value_doxygen_ref)
        self.add_get_value("interface/define:/name", self._get_value_hash)
        self.add_get_value("interface/enum:/name", self._get_value_hash)
        self.add_get_value("interface/enumerator:/name",
                           self._get_value_double_colon)
        self.add_get_value("interface/forward-declaration:/name",
                           get_value_forward_declaration)
        self.add_get_value("interface/function:/name",
                           self._get_value_doxygen_function)
        self.add_get_value("interface/function:/params/name",
                           self._get_value_params)
        self.add_get_value("interface/group:/name", get_value_doxygen_group)
        self.add_get_value("interface/header-file:/path",
                           get_value_header_file)
        self.add_get_value("interface/macro:/name",
                           self._get_value_doxygen_function)
        self.add_get_value("interface/macro:/params/name",
                           self._get_value_params)
        self.add_get_value("interface/struct:/name", self._get_value_compound)
        self.add_get_value("interface/typedef:/name",
                           self._get_value_double_colon)
        self.add_get_value("interface/typedef:/params/name",
                           self._get_value_params)
        self.add_get_value("interface/union:/name", self._get_value_compound)
        self.add_get_value("interface/unspecified-function:/name",
                           self._get_value_doxygen_function)
        self.add_get_value("interface/unspecified-struct:/name",
                           get_value_unspecified_type)
        self.add_get_value("interface/unspecified-union:/name",
                           get_value_unspecified_type)
        self.add_get_value("interface/variable:/name", self._get_value_hash)

    @contextmanager
    def code(self) -> Iterator[None]:
        """ Enables code mapping. """
        is_doc = self._is_doc
        self._is_doc = False
        yield
        self._is_doc = is_doc

    def get_value_map(self, item: Item) -> ItemGetValueMap:
        if not self._is_doc and item["type"] == "interface":
            node = self._node
            header_file = node.header_file
            if item["interface-type"] == "enumerator":
                for child in item.children("interface-enumerator"):
                    header_file.add_includes(child)
            else:
                header_file.add_includes(item)
            header_file.add_dependency(node, item)
        return self._get_value_map.get(item.type, {})

    def enabled_by_to_defined(self, enabled_by: str) -> str:
        """
        Map an item-level enabled-by attribute value to the corresponding
        defined expression.
        """
        return self._node.header_file.options[enabled_by]

    def _get_value_compound(self, ctx: ItemGetValueContext) -> str:
        if not self._is_doc:
            return get_value_compound(ctx)
        return get_value_default(ctx)

    def _get_value_double_colon(self, ctx: ItemGetValueContext) -> str:
        if self._is_doc:
            return get_value_double_colon(ctx)
        return get_value_default(ctx)

    def _get_value_doxygen_function(self, ctx: ItemGetValueContext) -> str:
        if self._is_doc:
            return get_value_doxygen_function(ctx)
        return get_value_default(ctx)

    def _get_value_hash(self, ctx: ItemGetValueContext) -> str:
        if self._is_doc:
            return get_value_hash(ctx)
        return get_value_default(ctx)

    def _get_value_params(self, ctx: ItemGetValueContext) -> str:
        if self._is_doc:
            return get_value_params(ctx)
        return get_value_default(ctx)


class _InterfaceExpressionMapper(ExpressionMapper):

    def __init__(self, mapper: _InterfaceMapper, prefix: str):
        super().__init__()
        self._mapper = mapper
        self._prefix = prefix

    def map_symbol(self, symbol: str) -> str:
        with self._mapper.code():
            return self._mapper.substitute(symbol, prefix=self._prefix)


def _filter_op_binary(op_name: str, options: dict[str, str],
                      enabled_by: Any) -> Any:
    new_enabled_by = []
    for next_enabled_by in enabled_by:
        exp = _discard_non_options(options, next_enabled_by)
        if exp is not None:
            new_enabled_by.append(exp)
    if len(new_enabled_by) == 0:
        return None
    if len(new_enabled_by) == 1:
        return new_enabled_by[0]
    return {op_name: new_enabled_by}


def _filter_op_not(options: dict[str, str], enabled_by: Any) -> Any:
    exp = _discard_non_options(options, enabled_by)
    if exp is None:
        return None
    return {"not": exp}


_FILTER_OP = {
    "and": functools.partial(_filter_op_binary, "and"),
    "not": _filter_op_not,
    "or": functools.partial(_filter_op_binary, "or")
}


def _discard_non_options(options: dict[str, str], enabled_by: Any) -> Any:
    if isinstance(enabled_by, bool):
        return enabled_by
    if isinstance(enabled_by, list):
        return _filter_op_binary("or", options, enabled_by)
    if isinstance(enabled_by, dict):
        key, value = next(iter(enabled_by.items()))
        return _FILTER_OP[key](options, value)  # type: ignore
    if enabled_by in options:
        return enabled_by
    return None


class _ItemLevelExpressionMapper(ExpressionMapper):

    def __init__(self, mapper: _InterfaceMapper):
        super().__init__()
        self._mapper = mapper

    def map_symbol(self, symbol: str) -> str:
        with self._mapper.code():
            return self._mapper.substitute(
                self._mapper.enabled_by_to_defined(symbol))


class _HeaderExpressionMapper(ExpressionMapper):

    def __init__(self, item: Item, options: dict[str, str]):
        super().__init__()
        self._mapper = ItemMapper(item)
        self._options = options

    def map_symbol(self, symbol: str) -> str:
        return self._mapper.substitute(self._options[symbol])


def _add_definition(node: "_Node", item: Item, prefix: str,
                    value: dict[str, Any], get_lines: _GetLines) -> CContent:
    content = CContent()
    default = value["default"]
    variants = value["variants"]
    if variants:
        ifelse = "#if "
        for index, variant in enumerate(variants):
            prefix_2 = os.path.join(prefix, f"variants[{index}]")
            enabled_by = enabled_by_to_exp(
                variant["enabled-by"],
                _InterfaceExpressionMapper(node.mapper, prefix_2))
            content.append(f"{ifelse}{enabled_by}")
            with content.indent():
                content.append(
                    get_lines(node, item, os.path.join(prefix_2, "definition"),
                              variant["definition"]))
            ifelse = "#elif "
        if default is not None:
            content.append("#else")
            with content.indent():
                content.append(
                    get_lines(node, item, os.path.join(prefix, "default"),
                              default))
        content.append("#endif")
    else:
        content.append(
            get_lines(node, item, os.path.join(prefix, "default"), default))
    return content


class _RegisterMemberContext(NamedTuple):
    sizes: dict[int, int]
    regs: dict[str, Any]
    reg_counts: dict[str, int]
    reg_indices: dict[str, int]


def _add_register_padding(content: CContent, new_offset: int, old_offset: int,
                          default_padding: int) -> None:
    delta = new_offset - old_offset
    if delta > 0:
        padding = default_padding
        while delta % padding != 0:
            padding //= 2
        count = delta // padding
        array = f"[ {count} ]" if count > 1 else ""
        content.add(f"uint{padding * 8}_t "
                    f"reserved_{old_offset:x}_{new_offset:x}{array};")


def _get_register_name(definition: dict[str, Any]) -> tuple[str, str]:
    name = definition["name"]
    try:
        name, alias = name.split(":")
    except ValueError:
        alias = name
    return name, alias


_CONSTRAINT_TARGET = {
    "interface/define": "this constant",
    "interface/function": "this directive",
    "interface/macro": "this directive",
    "interface/struct": "this structure",
    "interface/typedef": "functions of this type",
    "interface/union": "this union",
    "interface/variable": "this object",
}


class _Node:
    """ Nodes of a header file. """

    # pylint: disable=too-many-instance-attributes
    def __init__(self, header_file: "_HeaderFile", item: Item):
        self.header_file = header_file
        self.item = item
        self.ingroups = _get_ingroups(item)
        self.dependents: set[_Node] = set()
        self.depends_on: set[_Node] = set()
        self.content = CContent()
        self.mapper = _InterfaceMapper(self)
        try:
            group = item.child("placement-order")
        except IndexError:
            self.index = None
        else:
            self.index = (group.uid,
                          list(group.parents("placement-order")).index(item))

    def __lt__(self, other: "_Node") -> bool:
        return self.item.uid < other.item.uid

    @contextmanager
    def _enum_struct_or_union(self) -> Iterator[None]:
        self.content.add(self._get_description(self.item, self.ingroups))
        name = self.item["name"]
        typename = self.item["interface-type"]
        kind = self.item["definition-kind"]
        if kind == f"{typename}-only":
            self.content.append(f"{typename} {name} {{")
        elif kind == "typedef-only":
            self.content.append(f"typedef {typename} {{")
        else:
            self.content.append(f"typedef {typename} {name} {{")
        self.content.push_indent()
        yield
        self.content.pop_indent()
        if kind == f"{typename}-only":
            self.content.append("};")
        else:
            self.content.append(f"}} {name};")

    def generate_directly(self) -> None:
        """ Directly generate the node content. """
        self.content.add(f"/* Generated from spec:{self.item.uid} */")
        _NODE_GENERATORS[self.item["interface-type"]](self)

    def generate(self) -> None:
        """
        Generate the node content taking item-level enabled-by expressions
        into account.
        """
        enabled_by = _discard_non_options(self.header_file.options,
                                          self.item["enabled-by"])
        if enabled_by is not None and (not isinstance(enabled_by, bool)
                                       or not enabled_by):
            mapper = _ItemLevelExpressionMapper(self.mapper)
            self.content.add(f"#if {enabled_by_to_exp(enabled_by, mapper)}")
            with self.content.indent():
                self.generate_directly()
            self.content.add("#endif")
        else:
            self.generate_directly()

    def generate_compound(self) -> None:
        """ Generate a compound (struct or union). """
        with self._enum_struct_or_union():
            for index, definition in enumerate(self.item["definition"]):
                self.content.add(
                    _add_definition(self, self.item, f"definition[{index}]",
                                    definition,
                                    _Node._get_compound_definition))

    def generate_enum(self) -> None:
        """ Generate an enum. """
        with self._enum_struct_or_union():
            enumerators: list[CContent] = []
            for parent in self.item.parents("interface-enumerator"):
                enumerator = self._get_description(parent, {})
                enumerator.append(
                    _add_definition(self, parent, "definition",
                                    parent["definition"],
                                    _Node._get_enumerator_definition))
                enumerators.append(enumerator)
            for enumerator in enumerators[0:-1]:
                enumerator.lines[-1] += ","
                enumerator.append("")
                self.content.append(enumerator)
            try:
                self.content.append(enumerators[-1])
            except IndexError:
                pass

    def generate_define(self) -> None:
        """ Generate a define. """
        self._add_generic_definition(_Node._get_define_definition)

    def generate_forward_declaration(self) -> None:
        """ Generate a forward declaration. """
        self.content.append([
            "", "/* Forward declaration */",
            forward_declaration(self.item) + ";"
        ])

    def generate_function(self) -> None:
        """ Generate a function. """
        self._add_generic_definition(_Node._get_function_definition)

    def generate_group(self) -> None:
        """ Generate a group. """
        self.content.add_group(self.item["identifier"], self.item["name"],
                               _get_group_identifiers(self.ingroups),
                               self.substitute_text(self.item["brief"]),
                               self.substitute_text(self.item["description"]))

    def generate_macro(self) -> None:
        """ Generate a macro. """
        self._add_generic_definition(_Node._get_macro_definition)

    def _add_register_bits(self, group: str) -> _RegisterMemberContext:
        ctx = _RegisterMemberContext({}, {}, collections.defaultdict(int),
                                     collections.defaultdict(int))
        for index, register in enumerate(self.item["registers"]):
            name = register["name"]
            group_ident = group + to_camel_case(name)
            width = register["width"]
            assert width in [8, 16, 32, 64]
            ctx.regs[name] = {
                "size": width // 8,
                "type": f"uint{width}_t",
                "group": group_ident
            }
            brief = self.substitute_text(register["brief"])
            with self.content.defgroup_block(group_ident, f"{brief} ({name})"):
                self.content.add_brief_description(
                    "This group contains register bit definitions.")
                self.content.wrap(self.substitute_text(
                    register["description"]))
                self.content.add("@{")
            for index_2, bits in enumerate(register["bits"]):
                self.content.add(
                    _add_definition(
                        self, self.item, f"registers[{index}]/bits[{index_2}]",
                        bits,
                        functools.partial(_Node._get_register_bits_definition,
                                          reg_name=name)))
            self.content.add_close_group()
        return ctx

    def _add_register_block_includes(self,
                                     ctx: _RegisterMemberContext) -> None:
        for link in self.item.links_to_parents("register-block-include"):
            name = link["name"]
            ctx.regs[name] = {}
            ctx.regs[name]["size"] = link.item["register-block-size"]
            ctx.regs[name]["type"] = link.item["name"]
            ctx.regs[name]["group"] = link.item["identifier"]

    def _get_register_member_info(self, ctx: _RegisterMemberContext) -> None:
        offset = -1
        for index, member in enumerate(self.item["definition"]):
            assert member["offset"] > offset
            offset = member["offset"]
            default = [member["default"]] if member["default"] else []
            for index_2, definition in enumerate(
                    itertools.chain(default,
                                    (variant["definition"]
                                     for variant in member["variants"]))):
                name, alias = _get_register_name(definition)
                assert name.lower() != "reserved"
                count = definition["count"]
                if index_2 == 0:
                    ctx.sizes[index] = ctx.regs[name]["size"] * count
                else:
                    assert ctx.sizes[index] == ctx.regs[name]["size"] * count
                ctx.reg_counts[alias] += 1

    def _add_register_defines(self, ctx: _RegisterMemberContext) -> None:
        with self.content.doxygen_block():
            self.content.add("@name Registers")
            self.content.add_brief_description(
                self.substitute_text(self.item["brief"]))
            self.content.wrap(self.substitute_text(self.item["description"]))
            self.content.add("@{")
        for index, member in enumerate(self.item["definition"]):
            self.content.add(
                _add_definition(
                    self, self.item, f"definition[{index}]", member,
                    functools.partial(_Node._get_register_define_definition,
                                      ctx=ctx,
                                      offset=member["offset"])))
        self.content.add_close_group()

    def _add_register_struct(self, ctx: _RegisterMemberContext,
                             size: int) -> None:
        with self.content.doxygen_block():
            self.content.add_brief_description(
                self.substitute_text(self.item["brief"]))
            self.content.wrap(self.substitute_text(self.item["description"]))
        self.content.append(f"typedef struct {self.item['name']} {{")
        default_padding = min(*ctx.sizes.values(), 8)
        offset = 0
        with self.content.indent():
            for index, member in enumerate(self.item["definition"]):
                member_offset = member["offset"]
                _add_register_padding(self.content, member_offset, offset,
                                      default_padding)
                self.content.add(
                    _add_definition(
                        self, self.item, f"definition[{index}]", member,
                        functools.partial(
                            _Node._get_register_member_definition, ctx=ctx)))
                offset = member_offset + ctx.sizes[index]
            assert offset <= size
            _add_register_padding(self.content, size, offset, default_padding)
        self.content.add(f"}} {self.item['name']};")

    def _add_register_members(self, ctx: _RegisterMemberContext) -> None:
        size = self.item["register-block-size"]
        if size is None:
            self._add_register_defines(ctx)
        else:
            self._add_register_struct(ctx, size)

    def generate_register_block(self) -> None:
        """ Generate a register block. """
        self.header_file.add_includes(self.item.map("/c/if/uint32_t"))
        for parent in self.item.parents("register-block-include"):
            self.header_file.add_includes(parent)
            self.header_file.add_dependency(self, parent)
        group = self.item["identifier"]
        name = self.item["register-block-group"]
        with self.content.defgroup_block(group, name):
            self.content.add_ingroup(_get_group_identifiers(self.ingroups))
            self.content.add_brief_description(
                f"This group contains the {name} interfaces.")
            self.content.add("@{")
        ctx = self._add_register_bits(group)
        self._add_register_block_includes(ctx)
        self._get_register_member_info(ctx)
        self._add_register_members(ctx)
        self.content.add_close_group()

    def generate_typedef(self) -> None:
        """ Generate a typedef. """
        self._add_generic_definition(_Node._get_typedef_definition)

    def generate_variable(self) -> None:
        """ Generate a variable. """
        self._add_generic_definition(_Node._get_variable_definition)

    def substitute_code(self, text: str, prefix: str) -> str:
        """
        Perform a variable substitution on code using the item mapper of the
        node.
        """
        if text:
            with self.mapper.code():
                return self.mapper.substitute(text.strip("\n"), prefix=prefix)
        return text

    def substitute_text(self,
                        text: Optional[str],
                        item: Optional[Item] = None,
                        prefix: str = "") -> str:
        """
        Perform a variable substitution on a description using the item mapper
        of the node.
        """
        if text:
            return self.mapper.substitute(text.strip("\n"), item, prefix)
        return ""

    def _get_compound_definition(self, item: Item, prefix: str,
                                 definition: Any) -> _Lines:
        content = CContent()
        content.add_description_block(
            self.substitute_text(definition["brief"], prefix=prefix),
            self.substitute_text(definition["description"], prefix=prefix))
        kind = definition["kind"]
        if kind == "member":
            member = self.substitute_code(definition["definition"],
                                          prefix) + ";"
            content.append(member.split("\n"))
        else:
            content.append(f"{kind} {{")
            content.gap = False
            with content.indent():
                for index, compound_member in enumerate(
                        definition["definition"]):
                    content.add(
                        _add_definition(
                            self, item,
                            os.path.join(prefix, f"definition[{index}]"),
                            compound_member, _Node._get_compound_definition))
            name = definition["name"]
            content.append(f"}} {name};")
        return content.lines

    def _get_enumerator_definition(self, item: Item, prefix: str,
                                   definition: Any) -> _Lines:
        name = item["name"]
        if definition:
            return f"{name} = {self.substitute_code(definition, prefix)}"
        return f"{name}"

    def _get_define_definition(self, item: Item, prefix: str,
                               definition: Any) -> _Lines:
        name = item["name"]
        value = self.substitute_code(definition, prefix)
        if value:
            return f"#define {name} {value}".split("\n")
        return f"#define {name}"

    def _get_function_definition(self, item: Item, prefix: str,
                                 definition: Any) -> _Lines:
        content = CContent()
        name = item["name"]
        attrs = self.substitute_code(definition["attributes"], prefix)
        attrs = f"{attrs} " if attrs else ""
        ret = self.substitute_code(definition["return"], prefix)
        params = [
            self.substitute_code(param, prefix)
            for param in definition["params"]
        ]
        body = definition["body"]
        if body:
            with content.function(f"{attrs}static inline {ret}", name, params):
                content.add(self.substitute_code(body, prefix))
        else:
            content.declare_function(f"{attrs}{ret}", name, params)
        return content.lines

    def _get_macro_definition(self, item: Item, prefix: str,
                              definition: Any) -> _Lines:
        name = item["name"]
        params = [param["name"] for param in item["params"]]
        if params:
            param_line = " " + ", ".join(params) + " "
        else:
            param_line = ""
        line = f"#define {name}({param_line})"
        if len(line) > 79:
            param_block = ", \\\n  ".join(params)
            line = f"#define {name}( \\\n  {param_block} \\\n)"
        body = definition["body"]
        if not body:
            return line
        body_lines = self.substitute_code(body, prefix).split("\n")
        if len(body_lines) == 1 and len(line + body_lines[0]) <= 79:
            body = " "
        else:
            body = " \\\n  "
        body += " \\\n  ".join(body_lines)
        return line + body

    def _get_register_bits_definition(self, _item: Item, _prefix: str,
                                      definition: Any,
                                      reg_name: str) -> _Lines:
        lines = []  # list[str]
        prefix = self.item["register-prefix"]
        if prefix is None:
            prefix = self.item["name"]
        prefix = f"{prefix}_{reg_name}_" if prefix else f"{reg_name}_"
        for index, bit in enumerate(definition):
            start = bit["start"]
            width = bit["width"]
            end = start + width
            sfx = "ULL" if end > 32 else "U"
            base = f"{prefix.upper()}{bit['name'].upper()}"
            if index != 0:
                lines.append("")
            if width == 1:
                val = 1 << start
                lines.append(f"#define {base} {val:#x}{sfx}")
            else:
                mask = ((1 << width) - 1) << start
                lines.extend([
                    f"#define {base}_SHIFT {start}",
                    f"#define {base}_MASK {mask:#x}{sfx}",
                    f"#define {base}_GET( _reg ) \\",
                    f"  ( ( ( _reg ) & {base}_MASK ) >> \\",
                    f"    {base}_SHIFT )",
                    f"#define {base}_SET( _reg, _val ) \\",
                    f"  ( ( ( _reg ) & ~{base}_MASK ) | \\",
                    f"    ( ( ( _val ) << {base}_SHIFT ) & \\",
                    f"      {base}_MASK ) )", f"#define {base}( _val ) \\",
                    f"  ( ( ( _val ) << {base}_SHIFT ) & \\",
                    f"    {base}_MASK )"
                ])
        return lines

    def _get_register_define_definition(self, item: Item, _prefix: str,
                                        definition: Any,
                                        ctx: _RegisterMemberContext,
                                        offset: int) -> _Lines:
        name, alias = _get_register_name(definition)
        count = definition["count"]
        assert count == 1
        content = CContent()
        with content.doxygen_block():
            content.add(f"@brief See @ref {ctx.regs[name]['group']}.")
        content.append(
            f"#define {item['name'].upper()}_{alias.upper()} {offset:#x}")
        return content.lines

    def _get_register_member_definition(self, _item: Item, _prefix: str,
                                        definition: Any,
                                        ctx: _RegisterMemberContext) -> _Lines:
        name, alias = _get_register_name(definition)
        count = definition["count"]
        array = f"[ {count} ]" if count > 1 else ""
        if ctx.reg_counts[alias] > 1:
            index = ctx.reg_indices[alias]
            ctx.reg_indices[alias] = index + 1
            idx = f"_{index}"
        else:
            idx = ""
        content = CContent()
        with content.doxygen_block():
            content.add(f"@brief See @ref {ctx.regs[name]['group']}.")
        content.append(
            f"{ctx.regs[name]['type']} {alias.lower()}{idx}{array};")
        return content.lines

    def _get_typedef_definition(self, _item: Item, prefix: str,
                                definition: Any) -> _Lines:
        return f"typedef {self.substitute_code(definition, prefix)};"

    def _get_variable_definition(self, _item: Item, prefix: str,
                                 definition: Any) -> _Lines:
        return f"extern {self.substitute_code(definition, prefix)};"

    def _get_description(self, item: Item, ingroups: _ItemMap) -> CContent:
        content = CContent()
        with content.doxygen_block():
            content.add_ingroup(_get_group_identifiers(ingroups))
            content.add_brief_description(self.substitute_text(item["brief"]))
            if "params" in item:
                content.add_param_description(item["params"],
                                              self.substitute_text)
            content.wrap(self.substitute_text(item["description"]))
            ret = item.get("return", None)
            if ret:
                for retval in ret["return-values"]:
                    content.wrap(self.substitute_text(retval["description"]),
                                 initial_indent=self.substitute_text(
                                     f"@retval {retval['value']} "))
                content.wrap(self.substitute_text(ret["return"]),
                             initial_indent="@return ")
            content.add_paragraph("Notes", self.substitute_text(item["notes"]))
            constraints = [
                self.substitute_text(parent["text"], parent)
                for parent in item.parents("constraint")
                if parent.is_enabled(self.header_file.enabled)
            ]
            if constraints:
                constraint_content = CContent()
                target = _CONSTRAINT_TARGET[item.type]
                constraint_content.add_list(
                    constraints,
                    f"The following constraints apply to {target}:")
                content.add_paragraph("Constraints", constraint_content)
        return content

    def _add_generic_definition(self, get_lines: _GetLines) -> None:
        self.content.add(self._get_description(self.item, self.ingroups))
        self.content.append(
            _add_definition(self, self.item, "definition",
                            self.item["definition"], get_lines))


_NODE_GENERATORS = {
    "enum": _Node.generate_enum,
    "define": _Node.generate_define,
    "forward-declaration": _Node.generate_forward_declaration,
    "function": _Node.generate_function,
    "group": _Node.generate_group,
    "macro": _Node.generate_macro,
    "register-block": _Node.generate_register_block,
    "struct": _Node.generate_compound,
    "typedef": _Node.generate_typedef,
    "union": _Node.generate_compound,
    "variable": _Node.generate_variable
}


class _ZephyrNode(_Node):

    def generate_directly(self) -> None:
        interface_type = self.item["interface-type"]
        _ZEPHYR_NODE_GENERATORS.get(interface_type,
                                    _NODE_GENERATORS[interface_type])(self)

    def _get_register_bits_definition(self, _item: Item, _prefix: str,
                                      definition: Any,
                                      reg_name: str) -> _Lines:
        lines = []  # list[str]
        prefix = self.item["register-prefix"]
        if prefix is None:
            prefix = self.item["name"]
        prefix = f"{prefix}_{reg_name}_" if prefix else f"{reg_name}_"
        for bit in sorted(definition, key=lambda x: x["start"]):
            start = bit["start"]
            width = bit["width"]
            end = start + width
            sfx = "64" if end > 32 else ""
            base = f"{prefix.upper()}{bit['name'].upper()}"
            if width == 1:
                lines.append(f"#define {base} BIT{sfx}({start})")
            else:
                lines.append(
                    f"#define {base} GENMASK{sfx}({end - 1}, {start})")
        return lines

    def _add_register_bits(self, group: str) -> _RegisterMemberContext:
        ctx = _RegisterMemberContext({}, {}, collections.defaultdict(int),
                                     collections.defaultdict(int))
        for index, register in enumerate(self.item["registers"]):
            name = register["name"]
            width = register["width"]
            assert width in [8, 16, 32, 64]
            ctx.regs[name] = {"size": width // 8, "type": f"uint{width}_t"}
            self.content.add(f"/* {name} bits */")
            for index_2, bits in enumerate(register["bits"]):
                self.content.append(
                    _add_definition(
                        self, self.item, f"registers[{index}]/bits[{index_2}]",
                        bits,
                        functools.partial(
                            _ZephyrNode._get_register_bits_definition,
                            reg_name=name)))
        return ctx

    def _get_register_define_definition(self, item: Item, _prefix: str,
                                        definition: Any,
                                        ctx: _RegisterMemberContext,
                                        offset: int) -> _Lines:
        name, alias = _get_register_name(definition)
        define = f"#define {item['name'].upper()}_{alias.upper()}"
        count = definition["count"]
        if count == 1:
            return f"{define} {offset:#x}U"
        return f"{define}(i) ({offset:#x}U + {ctx.regs[name]['size']}U * (i))"

    def _add_register_defines(self, ctx: _RegisterMemberContext) -> None:
        for index, member in enumerate(self.item["definition"]):
            self.content.append(
                _add_definition(
                    self, self.item, f"definition[{index}]", member,
                    functools.partial(
                        _ZephyrNode._get_register_define_definition,
                        ctx=ctx,
                        offset=member["offset"])))

    def generate_register_block(self) -> None:
        self.header_file.add_includes(self.item.map("/zephyr/if/genmask"))
        for parent in self.item.parents("register-block-include"):
            self.header_file.add_includes(parent)
            self.header_file.add_dependency(self, parent)
        group = self.item["identifier"]
        name = self.item["register-block-group"]
        ctx = self._add_register_bits(group)
        self._add_register_block_includes(ctx)
        self._get_register_member_info(ctx)
        self.content.add(f"/* {name} address offsets */")
        self._add_register_defines(ctx)


_ZEPHYR_NODE_GENERATORS = {
    "register-block": _ZephyrNode.generate_register_block
}


def _is_ready_to_bubble(before: _Node, after: _Node) -> bool:
    if after in before.dependents:
        return False

    # Move the groups towards the top of the header file
    group = "interface/group"
    if (before.item.type == group) ^ (after.item.type == group):
        return after.item.type == group

    # Move items with an explicit placement order towards the bottom of the
    # file
    if before.index and after.index:
        return after.index < before.index
    if after.index:
        return False

    return after < before


def _bubble_sort(nodes: list[_Node]) -> list[_Node]:
    node_count = len(nodes)
    for i in range(node_count - 1):
        for j in range(node_count - 1 - i):
            if _is_ready_to_bubble(nodes[j], nodes[j + 1]):
                nodes[j], nodes[j + 1] = nodes[j + 1], nodes[j]
    return nodes


def _merge_enabled_by(options: dict[str, str], link: Link) -> Any:
    enabled_by = _discard_non_options(options, link["enabled-by"])
    enabled_by_2 = _discard_non_options(options, link.item["enabled-by"])
    if enabled_by == enabled_by_2:
        return enabled_by
    if isinstance(enabled_by, bool):
        if enabled_by:
            return enabled_by_2
        return False
    if isinstance(enabled_by_2, bool):
        if enabled_by_2:
            return enabled_by
        return False
    return {"and": [enabled_by, enabled_by_2]}


class _HeaderFile:
    """ A header file. """

    def __init__(self, item: Item, options: dict[str, str],
                 enabled: list[str]):
        self._item = item
        self._content = CContent()
        self._content.register_license_and_copyrights_of_item(item)
        self._ingroups = _get_ingroups(item)
        self._includes: list[Item] = []
        self._nodes: dict[str, _Node] = {}
        self.options = options
        self.enabled = enabled

    def add_includes(self, item: Item) -> None:
        """ Add the includes of the item to the header file includes. """
        for parent in item.parents("interface-placement"):
            if parent.type in [
                    "interface/header-file",
                    "interface/unspecified-header-file"
            ]:
                self._includes.append(parent)

    def add_node(self, item: Item) -> None:
        """ Add a node for the item. """
        self._nodes[item.uid] = _Node(self, item)

    def add_dependency(self, node: _Node, item: Item) -> None:
        """
        Add a dependency from a node to another node identified by an item if
        the item corresponds to a node and it is not a self reference.
        """
        if item.uid in self._nodes and item.uid != node.item.uid:
            other = self._nodes[item.uid]
            node.depends_on.add(other)
            other.dependents.add(node)

    def generate_nodes(self) -> None:
        """ Generate all nodes of this header file. """
        for child in self._item.children("interface-placement"):
            self.add_node(child)
            self._content.register_license_and_copyrights_of_item(child)
        for node in self._nodes.values():
            node.generate()

    def _get_nodes_in_dependency_order(self) -> list[_Node]:
        """
        Get the nodes of this header file ordered according to node
        dependencies and other criteria.

        The nodes form a partially ordered set.  The ordering is done in two
        steps.  Firstly, a topological sort using Kahn's algorithm is carried
        out.  Secondly, the nodes are sorted using a bubble sort which takes
        node dependencies into account.  There are more efficient ways to do
        this, however, if you experience run time problems due to this method,
        then maybe you should reconsider your header file organization.
        """
        nodes_in_dependency_order: list[_Node] = []

        # Get incoming edge degrees for all nodes
        in_degree: dict[str, int] = {}
        for node in self._nodes.values():
            in_degree[node.item.uid] = len(node.dependents)

        # Create a queue with all nodes with no incoming edges
        queue: list[_Node] = []
        for node in sorted(self._nodes.values()):
            if in_degree[node.item.uid] == 0:
                queue.append(node)

        # Topological sort
        while queue:
            node = queue.pop(0)
            nodes_in_dependency_order.insert(0, node)

            for other in sorted(node.depends_on):
                in_degree[other.item.uid] -= 1
                if in_degree[other.item.uid] == 0:
                    queue.append(other)

        return _bubble_sort(nodes_in_dependency_order)

    def _combine_enabled_by(self, enabled_by: Any) -> Any:
        enabled_by_2 = _discard_non_options(self.options,
                                            self._item["enabled-by"])
        if enabled_by == enabled_by_2 or enabled_by is None:
            return True
        return enabled_by

    def add_prologue(self) -> None:
        """ Add the header file prologue to the content. """
        self._content.prepend_spdx_license_identifier()
        with self._content.file_block():
            self._content.add_ingroup(_get_group_identifiers(self._ingroups))
            self._content.add_brief_description(self._item["brief"])
        self._content.add_copyrights_and_licenses()
        self._content.add_automatically_generated_warning()
        self._content.add(f"/* Generated from spec:{self._item.uid} */")

    def finalize(self) -> None:
        """ Finalize the header file. """
        self.add_prologue()
        with self._content.header_guard(self._item["path"]):
            exp_mapper = _HeaderExpressionMapper(self._item, self.options)
            includes = [
                CInclude(
                    item["path"],
                    enabled_by_to_exp(
                        self._combine_enabled_by(
                            _discard_non_options(self.options,
                                                 item["enabled-by"])),
                        exp_mapper)) for item in self._includes
                if item != self._item
            ]
            includes.extend([
                CInclude(
                    link.item["path"],
                    enabled_by_to_exp(
                        self._combine_enabled_by(
                            _merge_enabled_by(self.options, link)),
                        exp_mapper))
                for link in self._item.links_to_parents("interface-include")
            ])
            self._content.add_includes(includes)
            with self._content.extern_c():
                for node in self._get_nodes_in_dependency_order():
                    self._content.add(node.content)

    def write(self, domain_path: Optional[str],
              file_path: Optional[str]) -> None:
        """ Write the header file. """
        if domain_path is None:
            assert file_path
        else:
            file_path = os.path.join(domain_path, self._item["prefix"],
                                     self._item["path"])
        self._content.write(file_path)


class _ZephyrHeaderFile(_HeaderFile):

    def add_prologue(self) -> None:
        with self._content.comment_block():
            self._content.add(self._content.copyrights.get_statements())
            self._content.add("SPDX-License-Identifier: Apache-2.0")

    def add_node(self, item: Item) -> None:
        self._nodes[item.uid] = _ZephyrNode(self, item)


_HEADER_FILE = {"default": _HeaderFile, "zephyr": _ZephyrHeaderFile}


def _generate_header_file(item: Item, domains: dict[str, str],
                          options: dict[str, str], enabled: list[str],
                          style: str, file_path: Optional[str]) -> None:
    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-positional-arguments

    if file_path is None:
        domain = item.parent("interface-placement")
        assert domain["interface-type"] == "domain"
        domain_path = domains.get(domain.uid, None)
        if domain_path is None:
            return
    else:
        domain_path = None
    header_file = _HEADER_FILE[style](item, options, enabled)
    header_file.generate_nodes()
    header_file.finalize()
    header_file.write(domain_path, file_path)


def _gather_options(item_level_interfaces: list[str],
                    item_cache: ItemCache) -> dict[str, str]:
    options: dict[str, str] = {}
    for uid in item_level_interfaces:
        for child in item_cache[uid].children("interface-ingroup"):
            if child.type == "interface/unspecified-define":
                define = f"defined(${{{child.uid}:/name}})"
                options[child["name"]] = define
    return options


def generate_interfaces(config: dict, item_cache: ItemCache) -> None:
    """
    Generate header files according to the configuration.

    Args:
        config: A dictionary with configuration entries.
        item_cache: The specification item cache containing the interfaces.
    """
    domains = config["domains"]
    enabled = config["enabled"]
    style = config.get("style", "default")
    options = _gather_options(config["item-level-interfaces"], item_cache)
    for item in item_cache.items_by_type.get("interface/header-file", []):
        _generate_header_file(item, domains, options, enabled, style, None)


def generate_header_file(config: dict,
                         header_file: Item,
                         file_path: Optional[str] = None) -> None:
    """
    Generate the header file according to the configuration.

    Args:
        config: A dictionary with configuration entries.
        header_file: The header file specification item.
        file_path: The optional file path of the header file.
    """
    options = _gather_options(config["item-level-interfaces"],
                              header_file.cache)
    _generate_header_file(header_file, config["domains"], options,
                          config["enabled"], config["style"], file_path)
