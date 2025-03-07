# SPDX-License-Identifier: BSD-2-Clause
""" Provides methods to gather the files used for a build. """

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

import glob
import os

from specitems import is_enabled, Item, ItemCache, Link

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


def _gather_source_files(item: Item, enabled_set: list[str],
                         base_directory_map: BaseDirectoryMap,
                         source_files: list[str]) -> None:

    def _is_enabled(link: Link) -> bool:
        if not link.item.is_enabled(enabled_set):
            return False
        if link.role == "build-dependency":
            return True
        return is_enabled(enabled_set, link["enabled-by"])

    for parent in item.parents(_BUILD_ROLES, is_link_enabled=_is_enabled):
        _gather_source_files(parent, enabled_set, base_directory_map,
                             source_files)
    for uid in item.get("build-extension-points", []):
        extension_point = item.map(uid)
        if extension_point.is_enabled(enabled_set):
            _gather_source_files(extension_point, enabled_set,
                                 base_directory_map, source_files)
    source_files.extend(item.get("extra-files", []))
    _EXTEND_SOURCE_FILES[item["build-type"]](item, base_directory_map,
                                             source_files)


def _gather_test_header(item_cache: ItemCache, enabled_set: list[str],
                        source_files: list[str]) -> None:
    for item in item_cache.values():
        tests = ["test-case", "requirement/functional/action"]
        if item.type in tests and item["test-header"] and item.is_enabled(
                enabled_set):
            source_files.append(item["test-header"]["target"])


def gather_build_files(config: dict,
                       item_cache: ItemCache,
                       test_header: bool = True) -> list[str]:
    """ Generate a list of files form the build specification. """
    source_files: list[str] = []
    arch = config["arch"]
    bsp = config["bsp"]
    base_directory_map = config["base-directory-map"]
    enabled_set = config["enabled-set"]
    if arch is not None and bsp is not None:
        bsps: dict[str, dict[str, Item]] = {}
        for item in item_cache.values():
            if item["type"] == "build" and item["build-type"] == "bsp":
                arch_bsps = bsps.setdefault(item["arch"].strip(), {})
                arch_bsps[item["bsp"].strip()] = item
        _gather_source_files(bsps[arch][bsp], enabled_set, base_directory_map,
                             source_files)
    for uid in config["build-uids"]:
        _gather_source_files(item_cache[uid], enabled_set, base_directory_map,
                             source_files)
    if test_header:
        _gather_test_header(item_cache, enabled_set, source_files)
    return source_files
