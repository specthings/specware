# SPDX-License-Identifier: BSD-2-Clause
""" Provides interfaces for C language content generation. """

# Copyright (C) 2019, 2020 embedded brains GmbH & Co. KG
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

from contextlib import contextmanager
import math
import re
import sys
from typing import (Any, Callable, Iterable, Iterator, Match, NamedTuple,
                    Optional)

from specitems import (Content, GenericContent, Item, ItemGetValueContext,
                       MARKDOWN_ROLES)

BSD_2_CLAUSE_LICENSE = """Redistribution and use in source and binary \
forms, with or without
modification, are permitted provided that the following conditions
are met:
1. Redistributions of source code must retain the above copyright
   notice, this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright
   notice, this list of conditions and the following disclaimer in the
   documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE."""

MIT_LICENSE = """Permission is hereby granted, free of charge, to any person \
obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE."""

_PARAM = {
    None: "@param ",
    "in": "@param[in] ",
    "out": "@param[out] ",
    "inout": "@param[in,out] ",
}


class CInclude(NamedTuple):
    """ Represents a C include file. """
    path: str
    enabled_by: str = ""


def _split_includes(
        includes: list[CInclude]) -> tuple[set[str], dict[str, set[str]]]:
    includes_unconditional: set[str] = set()
    includes_enabled_by: dict[str, set[str]] = {}
    for inc in list(dict.fromkeys(includes)):
        if inc.enabled_by and inc.enabled_by != "1":
            try:
                includes_unconditional.remove(inc.path)
            except KeyError:
                pass
            includes_enabled_by.setdefault(inc.path, set()).add(inc.enabled_by)
        elif inc.path not in includes_enabled_by:
            includes_unconditional.add(inc.path)
    return includes_unconditional, includes_enabled_by


_FUNCTION_POINTER = re.compile(r"^[^(]+\(\s\*([^)]+)\)\s*\(")
_DESIGNATOR = re.compile(r"([a-zA-Z0-9_]+)(\[[^\]]+])?$")


def _get_align_pos(param: str) -> tuple[int, int]:
    if param == "...":
        return 0, sys.maxsize
    match = _DESIGNATOR.search(param)
    if not match:
        match = _FUNCTION_POINTER.search(param)
        assert match
    star = param.find("*")
    if star >= 0:
        return star, match.start(1)
    return match.start(1), match.start(1)


def align_declarations(decls: list[str]) -> list[str]:
    """ Align the list of C/C++ declarations. """
    positions = list(map(_get_align_pos, decls))
    max_pos = max(positions)[1]
    return [
        param[:pos[0]] + (max_pos - pos[1]) * " " + param[pos[0]:]
        for param, pos in zip(decls, positions)
    ]


_NOT_ALPHANUM = re.compile(r"[^a-zA-Z0-9_]")


def _make_str(value: Optional[str]) -> str:
    return value if value else ""


def _role_to_doxygen(match: Match) -> str:
    return f"`{match.group(2)}`"


class CContent(Content):
    """ Builds C language content. """

    # pylint: disable=too-many-public-methods
    def __init__(self):
        super().__init__("BSD-2-Clause")
        self.set_pop_indent_gap(False)

    def convert(self, text: str) -> str:
        return MARKDOWN_ROLES.sub(_role_to_doxygen, text)

    def add_directive_begin(self, prefix: str, directive: str) -> None:
        self.add("@code")
        self.gap = False

    def add_directive_end(self, prefix: str) -> None:
        self.add("@endcode")

    def prepend_spdx_license_identifier(self):
        """
        Add an SPDX License Identifier according to the registered licenses.
        """
        self.prepend([f"/* SPDX-License-Identifier: {self.licenses} */", ""])

    def add_copyrights_and_licenses(self):
        """
        Add the copyrights and licenses according to the registered copyrights
        and licenses.
        """
        with self.comment_block():
            self.add(self.copyrights.get_statements())
            self.add(BSD_2_CLAUSE_LICENSE)

    def prepend_copyrights_and_licenses(self):
        """
        Prepend the copyrights and licenses according to the registered
        copyrights and licenses.
        """
        content = CContent()
        with content.comment_block():
            content.add(self.copyrights.get_statements())
            content.add(BSD_2_CLAUSE_LICENSE)
        content.append("")
        self.prepend(content)

    def add_have_config(self):
        """ Add a guarded config.h include. """
        self.add(["#ifdef HAVE_CONFIG_H", "#include \"config.h\"", "#endif"])

    def _add_includes(self, includes: set[str], local: bool) -> None:

        class IncludeKey:  # pylint: disable=too-few-public-methods
            """ Provide a key to sort includes. """

            def __init__(self, inc: str):
                self._inc = inc

            def __lt__(self, other: "IncludeKey") -> bool:
                left = self._inc.split("/")
                right = other._inc.split("/")
                left_len = len(left)
                right_len = len(right)
                if left_len == right_len:
                    for left_part, right_part in zip(left[:-1], right[:-1]):
                        if left_part != right_part:
                            return left_part < right_part
                    return left[-1] < right[-1]
                return left_len < right_len

        left = "\"" if local else "<"
        right = "\"" if local else ">"
        self.add([
            f"#include {left}{inc}{right}"
            for inc in sorted(includes, key=IncludeKey)
        ])

    def _add_includes_enabled_by(self, includes: dict[str, set[str]],
                                 local: bool) -> None:
        enabled_by_includes: dict[str, set[str]] = {}
        for inc, enabled_bys in iter(includes.items()):
            enabled_by_includes.setdefault(" && ".join(sorted(enabled_bys)),
                                           set()).add(inc)
        for enabled_by, incs in sorted(iter(enabled_by_includes.items())):
            self.add(f"#if {enabled_by}")
            with self.indent():
                self._add_includes(incs, local)
            self.add("#endif")

    def add_includes(self,
                     includes: list[CInclude],
                     local: bool = False) -> None:
        """ Add the block of includes. """
        includes_unconditional, includes_enabled_by = _split_includes(includes)
        self._add_includes(includes_unconditional, local)
        self._add_includes_enabled_by(includes_enabled_by, local)

    def _open_comment_block(self, begin) -> None:
        self.add(begin)
        self.push_indent(" * ", " *")

    def open_comment_block(self) -> None:
        """ Open a comment block. """
        if self.gap:
            self.ensure_blank_line()
        self._open_comment_block("/*")

    def open_doxygen_block(self) -> None:
        """ Open a Doxygen comment block. """
        self._open_comment_block("/**")

    def open_file_block(self) -> None:
        """ Open a Doxygen @file comment block. """
        self._open_comment_block(["/**", " * @file"])
        self.gap = True

    def open_defgroup_block(self, identifier: str, name: str) -> None:
        """ Open a Doxygen @defgroup comment block. """
        defgroup = [f" * @defgroup {identifier} {name}"]
        if len(self._indent) + len(defgroup[0]) > self.text_width:
            defgroup = [f" * @defgroup {identifier} \\", f" *   {name}"]
        self._open_comment_block(["/**"] + defgroup)
        self.gap = True

    def open_function_block(self, function: str) -> None:
        """ Open a Doxygen @fn comment block. """
        self._open_comment_block(["/**", f" * @fn {function}"])
        self.gap = True

    def close_comment_block(self) -> None:
        """ Close a comment block. """
        self.pop_indent()
        if self.lines[-1].lstrip().startswith("/*"):
            # Discard empty comment blocks
            self.lines = self.lines[:-2]
        else:
            self.append(" */")
            self.gap = True

    @contextmanager
    def doxygen_block(self) -> Iterator[None]:
        """ Open a Doxygen comment block context. """
        self.open_doxygen_block()
        yield
        self.close_comment_block()

    @contextmanager
    def file_block(self) -> Iterator[None]:
        """ Open a Doxygen @file comment block context. """
        self.open_file_block()
        yield
        self.close_comment_block()

    @contextmanager
    def defgroup_block(self, identifier: str, name: str) -> Iterator[None]:
        """ Open a Doxygen @defgroup comment block context. """
        self.open_defgroup_block(identifier, name)
        yield
        self.close_comment_block()

    @contextmanager
    def function_block(self, function: str) -> Iterator[None]:
        """ Open a Doxygen @fn comment block context. """
        self.open_function_block(function)
        yield
        self.close_comment_block()

    def open_add_to_group(self, group: str) -> None:
        """ Open an add to group. """
        with self.doxygen_block():
            self.append([f"@addtogroup {group}", "", "@{"])

    def add_close_group(self) -> None:
        """ Close a group. """
        self.add("/** @} */")

    @contextmanager
    def add_to_group(self, group: str) -> Iterator[None]:
        """ Open an add to group context. """
        self.open_add_to_group(group)
        yield
        self.add_close_group()

    def open_for_loop(self, begin: str, end: str, step: str) -> None:
        """ Open a for loop. """
        for_loop = [f"for ( {begin}; {end}; {step} ) {{"]
        if len(self._indent) + len(for_loop[0]) > self.text_width:
            for_loop = [
                "for (", f"{self.tab}{begin};", f"{self.tab}{end};",
                f"{self.tab}{step}", ") {"
            ]
        self.add(for_loop)
        self.push_indent()

    def close_for_loop(self) -> None:
        """ Close a for loop. """
        self.pop_indent()
        self.append(["}"])
        self.gap = True

    @contextmanager
    def for_loop(self, begin: str, end: str, step: str) -> Iterator[None]:
        """ Open a for loop context. """
        self.open_for_loop(begin, end, step)
        yield
        self.close_for_loop()

    def _function(self, ret: str, name: str, params: list[str],
                  param_line: str, space: str, semicolon: str) -> None:
        # pylint: disable=too-many-arguments
        # pylint: disable=too-many-positional-arguments
        line = f"{ret}{space}{name}("
        if len(self._indent) + len(line) > self.text_width:
            line = f"{name}{param_line}{semicolon}"
            if len(self._indent) + len(line) > self.text_width:
                self.add([ret, f"{name}("])
            else:
                self.add([ret, line])
                return
        else:
            self.add(line)
        with self.indent():
            self.add(",\n".join(params))
        self.add(f"){semicolon}")

    def call_function(self,
                      ret: Optional[str],
                      name: str,
                      params: Optional[list[str]] = None,
                      semicolon: str = ";") -> None:
        """ Add the function call. """
        if ret:
            space = " "
        else:
            ret = ""
            space = ""
        if params:
            params = [param.strip() for param in params]
            param_line = "( " + ", ".join(params) + " )"
        else:
            param_line = "()"
        line = f"{ret}{space}{name}{param_line}{semicolon}"
        if len(self._indent) + len(line) > self.text_width:
            if params:
                self._function(ret, name, params, param_line, space, semicolon)
            elif ret:
                self.add(ret)
                with self.indent():
                    self.add(f"{name}(){semicolon}")
            else:
                self.add(f"{name}(){semicolon}")
        else:
            self.add(line)

    def declare_function(self,
                         ret: str,
                         name: str,
                         params: Optional[list[str]] = None,
                         define: bool = False,
                         align: bool = True) -> None:
        # pylint: disable=too-many-arguments
        # pylint: disable=too-many-positional-arguments
        """ Add the function declaration. """
        if params:
            params = [param.strip() for param in params]
        else:
            params = ["void"]
        param_line = f"( {', '.join(params)} )"
        space = "" if not ret or ret.endswith("*") else " "
        semicolon = "" if define else ";"
        line = f"{ret}{space}{name}{param_line}{semicolon}"
        if len(self._indent) + len(line) > self.text_width:
            if align:
                params = align_declarations(params)
            self._function(ret, name, params, param_line, space, semicolon)
        else:
            self.add(line)

    def open_function(self,
                      ret: str,
                      name: str,
                      params: Optional[list[str]] = None,
                      align: bool = True) -> None:
        """ Open a function definition. """
        self.declare_function(ret, name, params, define=True, align=align)
        self.append("{")
        self.push_indent()

    def close_function(self) -> None:
        """ Close a function definition. """
        self.pop_indent()
        self.add("}")

    @contextmanager
    def function(self,
                 ret: str,
                 name: str,
                 params: Optional[list[str]] = None,
                 align: bool = True) -> Iterator[None]:
        """ Open a function context. """
        self.open_function(ret, name, params, align=align)
        yield
        self.close_function()

    def open_condition(self,
                       expression: Optional[str],
                       chain: bool = False) -> None:
        """ Open a condition. """
        begin = "} else " if chain else ""
        ifelse = f"if ( {expression} ) " if expression else ""
        self.add(f"{begin}{ifelse}{{")
        self.push_indent()

    def close_condition(self) -> None:
        """ Close a condition. """
        self.pop_indent()
        self.add("}")

    @contextmanager
    def condition(self, expression: Optional[str] = None) -> Iterator[None]:
        """ Open a condition context. """
        self.open_condition(expression)
        yield
        self.close_condition()

    @contextmanager
    def first_condition(self,
                        expression: Optional[str] = None) -> Iterator[None]:
        """ Open a first condition context. """
        self.open_condition(expression, False)
        yield
        self.pop_indent()

    @contextmanager
    def next_condition(self,
                       expression: Optional[str] = None) -> Iterator[None]:
        """ Open a next condition context. """
        self.open_condition(expression, True)
        yield
        self.pop_indent()

    @contextmanager
    def final_condition(self,
                        expression: Optional[str] = None) -> Iterator[None]:
        """ Open a final condition context. """
        self.open_condition(expression, True)
        yield
        self.close_condition()

    def add_brief_description(self, description: Optional[str]) -> None:
        """ Add the brief description. """
        self.wrap(description, initial_indent="@brief ")

    def add_param_description(
            self,
            params: Iterable[dict[str, str]],
            substitute: Callable[[Optional[str]], str] = _make_str) -> None:
        """ Add the list of parameter descriptions. """
        for param in params:
            description = param["description"]
            if description:
                self.wrap(param["name"] + " " + substitute(description),
                          initial_indent=_PARAM[param["dir"]])

    def add_description_block(self, brief: Optional[str],
                              description: Optional[str]) -> None:
        """ Add the description block. """
        if brief or description:
            with self.doxygen_block():
                self.add_brief_description(brief)
                self.wrap(description)
            self.gap = False

    def add_ingroup(self, ingroups: list[str]) -> None:
        """ Adds an ingroup comment block. """
        self.add(["@ingroup " + ingroup for ingroup in sorted(set(ingroups))])

    def add_group(self, identifier: str, name: str, ingroups: list[str],
                  brief: Optional[str], description: Optional[str]) -> None:
        # pylint: disable=too-many-arguments
        # pylint: disable=too-many-positional-arguments
        """ Add the group definition. """
        with self.defgroup_block(identifier, name):
            self.add_ingroup(ingroups)
            self.add_brief_description(brief)
            self.wrap(description)

    @contextmanager
    def header_guard(self, filename: str) -> Iterator[None]:
        """ Open a header guard context. """
        guard = "_" + _NOT_ALPHANUM.sub("_", filename).upper()
        self.add([f"#ifndef {guard}", f"#define {guard}"])
        yield
        self.add(f"#endif /* {guard} */")

    @contextmanager
    def extern_c(self) -> Iterator[None]:
        """ Open an extern "C" context. """
        self.add(["#ifdef __cplusplus", "extern \"C\" {", "#endif"])
        yield
        self.add(["#ifdef __cplusplus", "}", "#endif"])

    def add_paragraph(self, name: str,
                      content: Optional[GenericContent]) -> None:
        """ Add the Doxygen paragraph block. """
        if content:
            self.add(f"@par {name}")
            self.gap = False
            last = len(self.lines)
            self.wrap(content)
            if self._empty_line_indent in self.lines[last:]:
                self.lines.insert(last, f"{self._indent}@parblock")
                self.lines.append(f"{self._indent}@endparblock")


def get_value_doxygen_function(ctx: ItemGetValueContext) -> Any:
    """ Get the value as a function for Doxygen markup. """
    return f"{ctx.value[ctx.key]}()"


def get_value_doxygen_group(ctx: ItemGetValueContext) -> Any:
    """ Get the value as a group reference for Doxygen markup. """
    return f"@ref {ctx.value['identifier']}"


def get_value_doxygen_ref(ctx: ItemGetValueContext) -> Any:
    """ Get the value as a reference for Doxygen markup. """
    return f"@ref {ctx.value[ctx.key]}"


def get_value_double_colon(ctx: ItemGetValueContext) -> Any:
    """ Get the value with a :: prefix. """
    return f"::{ctx.value[ctx.key]}"


def get_value_header_file(ctx: ItemGetValueContext) -> Any:
    """ Get the value formatted as a header file. """
    return f"``<{ctx.value[ctx.key]}>``"


def get_value_hash(ctx: ItemGetValueContext) -> Any:
    """ Get the value with a # prefix. """
    return f"#{ctx.value[ctx.key]}"


def get_value_params(ctx: ItemGetValueContext) -> Any:
    """ Get the value formatted as a parameter. """
    return f"``{ctx.value[ctx.key]}``"


def forward_declaration(item: Item) -> str:
    """ Gets the forward declare for the item. """
    target = item.parent("interface-target")
    return f"{target['interface-type']} {target['name']}"


def get_value_forward_declaration(ctx: ItemGetValueContext) -> Any:
    """ Get the value as a forward declaration. """
    return forward_declaration(ctx.item)


def get_value_compound(ctx: ItemGetValueContext) -> Any:
    """ Get the value as a compound (struct or union). """
    if ctx.item["definition-kind"] in ["struct-only", "union-only"]:
        return f"{ctx.item['interface-type']} {ctx.item['name']}"
    return ctx.item['name']


def get_value_unspecified_type(ctx: ItemGetValueContext) -> Any:
    """ Get the value as a compound (unspecified struct or union). """
    return f"{ctx.item['interface-type'][12:]} {ctx.item['name']}"


class ExpressionMapper:
    """ Maps symbols and operations to form a C expression. """

    def map_bool(self, value: bool) -> str:
        """ Map the boolean value to build an expression. """
        return str(int(value))

    def map_symbol(self, symbol: str) -> str:
        """ Map the symbol to build an expression. """
        if symbol.startswith("CPU_"):
            return f"( {symbol} == TRUE )"
        return f"defined({symbol})"

    def op_and(self) -> str:
        """ Returns the and operator. """
        return " && "

    def op_or(self) -> str:
        """ Returns the or operator. """
        return " || "

    def op_not(self, symbol: str) -> str:
        """ Returns the negation of the symbol. """
        return f"!{symbol}"


class PythonExpressionMapper(ExpressionMapper):
    """ Maps symbols and operations to form a Python expression. """

    def map_bool(self, value: bool) -> str:
        return str(value)

    def map_symbol(self, symbol: str) -> str:
        return symbol

    def op_and(self) -> str:
        return " and "

    def op_or(self) -> str:
        return " or "

    def op_not(self, symbol: str) -> str:
        return f"not {symbol}"


def _to_expression_op(enabled_by: Any, mapper: ExpressionMapper,
                      operation: str) -> str:
    symbols = [
        _to_expression(next_enabled_by, mapper)
        for next_enabled_by in enabled_by
    ]
    if len(symbols) == 1:
        return symbols[0]
    return f"({operation.join(symbols)})"


def _to_expression_op_and(enabled_by: Any, mapper: ExpressionMapper) -> str:
    return _to_expression_op(enabled_by, mapper, mapper.op_and())


def _to_expression_op_not(enabled_by: Any, mapper: ExpressionMapper) -> str:
    return mapper.op_not(_to_expression(enabled_by, mapper))


def _to_expression_op_or(enabled_by: Any, mapper: ExpressionMapper) -> str:
    return _to_expression_op(enabled_by, mapper, mapper.op_or())


_TO_EXPRESSION_OP = {
    "and": _to_expression_op_and,
    "not": _to_expression_op_not,
    "or": _to_expression_op_or
}


def _to_expression(enabled_by: Any, mapper: ExpressionMapper) -> str:
    if isinstance(enabled_by, bool):
        return mapper.map_bool(enabled_by)
    if isinstance(enabled_by, list):
        return _to_expression_op_or(enabled_by, mapper)
    if isinstance(enabled_by, dict):
        if len(enabled_by) == 1:
            key = next(iter(enabled_by))
            return _TO_EXPRESSION_OP[key](enabled_by[key], mapper)
        raise ValueError
    return mapper.map_symbol(enabled_by)


def enabled_by_to_exp(enabled_by: Any, mapper: ExpressionMapper) -> str:
    """
    Return an expression for an enabled-by attribute value.
    """
    exp = _to_expression(enabled_by, mapper)
    if exp.startswith("("):
        return exp[1:-1].strip()
    return exp


def get_integer_type(value: int) -> str:
    """
    Return an unsigned integer type which is large enough to store the value.
    """
    power = 2**max(math.ceil(math.log2(math.floor(math.log2(value)) + 1)), 3)
    return f"uint{power}_t"
