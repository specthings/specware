# SPDX-License-Identifier: BSD-2-Clause
""" Provides methods to gather the files used for a build. """

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

from collections.abc import Iterator, Mapping
import glob
import os
import string
from typing import Any

from specitems import (EnabledSet, IS_ENABLED_OPS, Item, ItemCache, Link,
                       is_enabled_with_ops)

BaseDirectoryMap = list[dict[str, str]]


def get_build_base_directory(item: Item,
                             base_directory_map: BaseDirectoryMap) -> str:
    """
    Get the build base directory associated with the item using the base
    directory map.
    """
    for mapping in base_directory_map:
        source = mapping["source"]
        if os.path.commonpath([source, item.file]) == source:
            return mapping["target"]
    return ""


def _extend_by_install(item: Item, base_directory_map: BaseDirectoryMap,
                       source_files: list[str]) -> None:
    for install in item["install"]:
        source = install["source"]
        if "glob" in install:
            base_directory = os.path.join(
                get_build_base_directory(item, base_directory_map), source)
            source_files.extend(
                os.path.join(source, path) for path in glob.glob(
                    install["glob"], root_dir=base_directory, recursive=True)
                if os.path.islink(path) or not os.path.isdir(path))
        else:
            source_files.extend(source)


def _extend_by_source(item: Item, _base_directory_map: BaseDirectoryMap,
                      source_files: list[str]) -> None:
    source_files.extend(item["source"])


def _extend_by_install_and_source(item: Item,
                                  base_directory_map: BaseDirectoryMap,
                                  source_files: list[str]) -> None:
    _extend_by_install(item, base_directory_map, source_files)
    _extend_by_source(item, base_directory_map, source_files)


def _extend_by_nothing(_item: Item, _base_directory_map: BaseDirectoryMap,
                       _source_files: list[str]) -> None:
    pass


_EXTEND_SOURCE_FILES = {
    "ada-test-program": _extend_by_nothing,
    "bsp": _extend_by_install_and_source,
    "config-file": _extend_by_nothing,
    "config-header": _extend_by_nothing,
    "extension": _extend_by_nothing,
    "test-program": _extend_by_source,
    "group": _extend_by_install,
    "library": _extend_by_install_and_source,
    "objects": _extend_by_install_and_source,
    "option": _extend_by_nothing,
    "script": _extend_by_nothing,
    "start-file": _extend_by_source,
}

_BUILD_ROLES = ["build-dependency", "build-dependency-conditional"]


class _Template(string.Template):
    idpattern = "[_A-Za-z][_A-Za-z0-9:#]*"


class _Variables(Mapping[str, str]):
    """
    Maps a variable name to the value of the option of this name.

    A name without a value maps to 1 if it is a member of the enabled set,
    otherwise to 0.  A colon separates a format specification from the name.
    """

    def __init__(self, values: dict[str, Any], enabled_set: list[str]) -> None:
        self._values = values
        self._enabled_set = enabled_set

    def __getitem__(self, name: str) -> str:
        key, colon, spec = name.partition(":")
        if key in self._values:
            value = self._values[key]
        else:
            value = int(key in self._enabled_set)
        fmt = "{" + colon + spec + "}"
        if isinstance(value, list):
            return " ".join(fmt.format(element) for element in value)
        return fmt.format(value)

    def __iter__(self) -> Iterator[str]:
        return iter(self._values)

    def __len__(self) -> int:
        return len(self._values)


class _BuildContext:  # pylint: disable=too-few-public-methods
    """
    Evaluates the enabled-by expressions of build items with the operators of
    the build system.

    The operators is-directory and is-file take a path relative to the top
    directory.
    """

    def __init__(self, enabled_set: list[str], top_directory: str) -> None:
        self.enabled_set = enabled_set
        self.values: dict[str, Any] = {}
        variables = _Variables(self.values, enabled_set)

        def _eq(_ops: dict, _enabled_set: EnabledSet, enabled_by: Any) -> bool:
            first = _Template(enabled_by[0]).substitute(variables)
            return all(
                _Template(value).substitute(variables) == first
                for value in enabled_by[1:])

        def _is_directory(_ops: dict, _enabled_set: EnabledSet,
                          enabled_by: Any) -> bool:
            return os.path.isdir(os.path.join(top_directory, enabled_by))

        def _is_file(_ops: dict, _enabled_set: EnabledSet,
                     enabled_by: Any) -> bool:
            return os.path.isfile(os.path.join(top_directory, enabled_by))

        self._ops = IS_ENABLED_OPS | {
            "eq": _eq,
            "is-directory": _is_directory,
            "is-file": _is_file,
        }

    def is_enabled(self, enabled_by: Any) -> bool:
        """ Evaluate the enabled-by expression. """
        return is_enabled_with_ops(self._ops, self.enabled_set, enabled_by)


def _build_dependencies(item: Item, context: _BuildContext) -> list[Item]:

    def _is_enabled(link: Link) -> bool:
        if not context.is_enabled(link.item["enabled-by"]):
            return False
        if link.role == "build-dependency":
            return True
        return context.is_enabled(link["enabled-by"])

    dependencies = list(item.parents(_BUILD_ROLES,
                                     is_link_enabled=_is_enabled))
    for uid in item.get("build-extension-points", []):
        extension_point = item.map(uid)
        if context.is_enabled(extension_point["enabled-by"]):
            dependencies.append(extension_point)
    return dependencies


# The value of an option with one of these first actions is its configured
# value or its default value.  The build configuration of the package
# provides each configured value which enables something as a member of the
# enabled set.
_GET_ACTIONS = ("get-boolean", "get-integer", "get-string")


def _default_value(item: Item, context: _BuildContext) -> Any:
    for default in item.get("default", []):
        if context.is_enabled(default["enabled-by"]):
            return default["value"]
    return None


def _enable_by_options(item: Item, context: _BuildContext) -> None:
    for dependency in _build_dependencies(item, context):
        _enable_by_options(dependency, context)
    if item["build-type"] != "option":
        return
    actions = item.get("actions", [])
    if not actions or next(iter(actions[0])) not in _GET_ACTIONS:
        return
    value = _default_value(item, context)
    name = item["name"]
    if name not in context.enabled_set:
        context.values[name] = value
    for action in actions:
        if "env-enable" in action and value:
            enable = action["env-enable"] or name
            if enable not in context.enabled_set:
                context.enabled_set.append(enable)


def _gather_source_files(item: Item, context: _BuildContext,
                         base_directory_map: BaseDirectoryMap,
                         source_files: list[str]) -> None:
    for dependency in _build_dependencies(item, context):
        _gather_source_files(dependency, context, base_directory_map,
                             source_files)
    source_files.extend(item.get("extra-files", []))
    _EXTEND_SOURCE_FILES[item["build-type"]](item, base_directory_map,
                                             source_files)


_TEST_TYPES = ["test-case", "requirement/functional/action"]


def _map_test_target_to_item(item_cache: ItemCache) -> dict[str, Item]:
    return {
        item["test-target"]: item
        for test_type in _TEST_TYPES
        for item in item_cache.items_by_type.get(test_type, [])
        if item["test-header"]
    }


def _gather_test_header(item_cache: ItemCache, enabled_set: list[str],
                        source_files: list[str]) -> None:
    item_by_test_target = _map_test_target_to_item(item_cache)
    test_headers: list[str] = []
    for source_file in source_files:
        item = item_by_test_target.pop(source_file, None)
        if item is not None and item.is_enabled(enabled_set):
            test_headers.append(item["test-header"]["target"])
    source_files.extend(test_headers)


def gather_build_files(config: dict,
                       item_cache: ItemCache,
                       test_header: bool = True) -> list[str]:
    """
    Generate a list of files form the build specification.

    The enabled set of the configuration contains each option which the build
    configuration enables.  The options which their default values enable
    extend the enabled set, as the configure step of the build does.  The
    optional top directory of the configuration is the directory in which the
    build runs.  It defaults to the current working directory.
    """
    source_files: list[str] = []
    arch = config["arch"]
    bsp = config["bsp"]
    base_directory_map = config["base-directory-map"]
    context = _BuildContext(list(config["enabled-set"]),
                            config.get("top-directory", os.getcwd()))
    roots = [item_cache[uid] for uid in config["build-uids"]]
    if arch is not None and bsp is not None:
        bsps: dict[str, dict[str, Item]] = {}
        for item in item_cache.values():
            if item["type"] == "build" and item["build-type"] == "bsp":
                arch_bsps = bsps.setdefault(item["arch"].strip(), {})
                arch_bsps[item["bsp"].strip()] = item
        roots.insert(0, bsps[arch][bsp])
    for root in roots:
        _enable_by_options(root, context)
    for root in roots:
        _gather_source_files(root, context, base_directory_map, source_files)
    if test_header:
        _gather_test_header(item_cache, context.enabled_set, source_files)
    return source_files
