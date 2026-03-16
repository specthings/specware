# SPDX-License-Identifier: BSD-2-Clause
""" Provides a command line interface to view the specification. """

# Copyright (C) 2021, 2026 embedded brains GmbH & Co. KG
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

import argparse
import contextlib
import itertools
import sys
from typing import Any, Optional, Iterable

from specitems import (COL_SPAN, Item, ItemCache, ItemCacheConfig,
                       ItemGetValueContext, ItemMapper, ROW_SPAN,
                       SphinxContent, create_config)

from specware import (augment_with_test_case_links, augment_with_test_links,
                      gather_api_items, gather_build_files,
                      load_specware_config, recursive_is_enabled, Transition,
                      TransitionMap, validate, SpecWareTypeProvider)

_CHILD_ROLES = [
    "requirement-refinement", "interface-ingroup", "interface-ingroup-hidden",
    "interface-function", "glossary-member", "performance-runtime-limits",
    "test-case", "verification-member"
]

_PARENT_ROLES = [
    "function-implementation", "interface-enumerator",
    "performance-runtime-limits-provider", "test-timeouts",
    "verification-provider"
]


def _get_value_dummy(_ctx: ItemGetValueContext) -> Any:
    return ""


def _visit_action_conditions(item: Item, mapper: ItemMapper,
                             name: str) -> None:
    for index, condition in enumerate(item[name]):
        for index_2, state in enumerate(condition["states"]):
            mapper.substitute(state["text"], item,
                              f"{name}[{index}]/states[{index_2}]/text")


def _visit_action(item: Item, mapper: ItemMapper) -> None:
    _visit_action_conditions(item, mapper, "pre-conditions")
    _visit_action_conditions(item, mapper, "post-conditions")


_VISITORS = {
    "requirement/functional/action": _visit_action,
}


def _info(item: Item) -> str:
    if not item.view.get("pre-qualified", True):
        return ", not-pre-qualified"
    if item.view.get("validated", True):
        return ""
    return ", not-validated"


_TEXT_ATTRIBUTES = [
    "brief",
    "description",
    "notes",
    "rationale",
    "test-brief",
    "test-description",
    "text",
]


def _visit_item(item: Item, mapper: ItemMapper, level: int,
                role: Optional[str], validated_filter: str) -> bool:
    validated = item.view.get("validated", True)
    if validated_filter == "yes" and not validated:
        return False
    if validated_filter == "no" and validated:
        return False
    role_info = "" if role is None else f", role={role}"
    print(
        f"{'  ' * level}{item.uid} (type={item.type}{role_info}{_info(item)})")
    for name in _TEXT_ATTRIBUTES:
        if name in item:
            mapper.substitute(item[name], item)
    try:
        visitor = _VISITORS[item.type]
    except KeyError:
        pass
    else:
        visitor(item, mapper)
    return True


def _view_interface_placment(item: Item, mapper: ItemMapper, level: int,
                             validated_filter: str) -> None:
    for link in item.links_to_children("interface-placement"):
        if _visit_item(link.item, mapper, level, link.role, validated_filter):
            _view_interface_placment(link.item, mapper, level + 1,
                                     validated_filter)


def _view(item: Item, mapper: ItemMapper, level: int, role: Optional[str],
          validated_filter: str) -> None:
    if not _visit_item(item, mapper, level, role, validated_filter):
        return
    for child in item.children("validation"):
        _visit_item(child, mapper, level + 1, "validation", validated_filter)
        for child_2 in child.children("runtime-measurement-request"):
            _visit_item(child_2, mapper, level + 2,
                        "runtime-measurement-request", validated_filter)
    _view_interface_placment(item, mapper, level + 1, validated_filter)
    for link in item.links_to_children(_CHILD_ROLES):
        _view(link.item, mapper, level + 1, link.role, validated_filter)
    for link in item.links_to_parents(_PARENT_ROLES):
        _view(link.item, mapper, level + 1, link.role, validated_filter)


def _validation_count(item: Item) -> int:
    return len(list(child for child in item.children("validation")))


def _no_validation(item: Item, path: list[str]) -> list[str]:
    path_2 = path + [item.uid]
    leaf = _validation_count(item) == 0
    for child in item.children(_CHILD_ROLES):
        path_2 = _no_validation(child, path_2)
        leaf = False
    for parent in item.parents(_PARENT_ROLES):
        path_2 = _no_validation(parent, path_2)
        leaf = False
    if leaf and not item.view.get("validated", True):
        for index, component in enumerate(path_2):
            if component:
                print(f"{'  ' * index}{component}")
            path_2[index] = ""
    return path_2[:-1]


_REFINEMENTS = ["interface-function", "requirement-refinement"]

_GROUPS = ["requirement/non-functional/design-group", "interface/group"]


def _is_refinement(item: Item, other: Item) -> bool:
    for parent in item.parents(_REFINEMENTS):
        if parent == other:
            return True
        if _is_refinement(parent, other):
            return True
    return False


def _gather_design_components(item: Item, components: list[Item]) -> bool:
    if item.type in _GROUPS:
        components.append(item)
        return True
    if item.type.startswith("requirement"):
        for parent in item.parents("interface-function"):
            components.append(parent)
        for parent in item.parents("requirement-refinement"):
            _gather_design_components(parent, components)
        return True
    return False


def _design(item_cache: ItemCache) -> None:
    for item in item_cache.values():
        if not item.enabled:
            continue
        components: list[Item] = []
        if not _gather_design_components(item, components):
            continue
        compact: set[Item] = set()
        for component in components:
            for component_2 in components:
                if component != component_2:
                    if _is_refinement(component_2, component):
                        break
            else:
                compact.add(component)
        if compact:
            text = ", ".join(component.uid for component in compact)
        else:
            text = "N/A"
        print(f"{item.uid}\t{text}")


def _skip(transition_map: TransitionMap, variant: Transition) -> str:
    if variant.skip:
        return transition_map.skip_idx_to_name(variant.skip)
    return " "


def _make_row(transition_map: TransitionMap, map_idx: int, variant: Transition,
              show_skip: bool) -> tuple[str, ...]:
    head = [str(map_idx), str(variant.desc_idx)]
    if show_skip:
        head.append(_skip(transition_map, variant))
    return tuple(
        itertools.chain(
            head, (transition_map.pre_co_idx_st_idx_to_st_name(co_idx, st_idx)
                   for co_idx, st_idx in enumerate(
                       transition_map.map_idx_to_pre_co_states(
                           map_idx, variant.pre_cond_na))),
            (transition_map.post_co_idx_st_idx_to_st_name(co_idx, st_idx)
             for co_idx, st_idx in enumerate(variant.post_cond))))


def _action_table(item: Item, show_skip: bool) -> None:
    header = ["Entry", "Descriptor"]
    if show_skip:
        header.append("Skip")
    rows = [
        tuple(
            itertools.chain(header, (condition["name"]
                                     for condition in item["pre-conditions"]),
                            (condition["name"]
                             for condition in item["post-conditions"])))
    ]
    transition_map = TransitionMap(item, "N/A")
    for map_idx, variant in transition_map.get_variants(
            item.cache.enabled_set):
        if show_skip or not variant.skip:
            rows.append(_make_row(transition_map, map_idx, variant, show_skip))
    content = SphinxContent()
    content.add_simple_table(rows)
    print(str(content))


def _states(transition_map: TransitionMap, co_idx: int,
            states: list[int]) -> str:
    return ", ".join(
        transition_map.pre_co_idx_st_idx_to_st_name(co_idx, st_idx)
        for st_idx in set(states))


def _action_compact_table(item: Item) -> None:
    transition_map = TransitionMap(item, "N/A")
    rows: list[Iterable[str | int]] = [
        ("Pre-Conditions", ) + (ROW_SPAN, ) *
        (transition_map.pre_co_count - 1) + ("Post-Conditions", ) +
        (ROW_SPAN, ) * (transition_map.post_co_count - 1)
    ]
    rows.append(
        tuple(
            itertools.chain(
                (condition["name"] for condition in item["pre-conditions"]),
                (condition["name"] for condition in item["post-conditions"]))))
    for post_co, pre_co_collection in transition_map.get_post_conditions(
            item.cache.enabled_set):
        if post_co[0]:
            post_co_row = ((transition_map.skip_idx_to_name(post_co[0]), ) +
                           (ROW_SPAN, ) * (transition_map.post_co_count - 1))
            post_co_col_span: tuple[str | int,
                                    ...] = ((COL_SPAN, ) +
                                            (COL_SPAN | ROW_SPAN, ) *
                                            (transition_map.post_co_count - 1))
        else:
            post_co_row = tuple(
                transition_map.post_co_idx_st_idx_to_st_name(co_idx, st_idx)
                for co_idx, st_idx in enumerate(post_co[1:]))
            post_co_col_span = (COL_SPAN, ) * transition_map.post_co_count
        for pre_co in pre_co_collection:
            pre_co_row = tuple(
                _states(transition_map, co_idx, co_states)
                for co_idx, co_states in enumerate(pre_co))
            rows.append(pre_co_row + post_co_row)
            post_co_row = post_co_col_span
    content = SphinxContent()
    content.add_grid_table(rows, header_rows=2)
    print(str(content))


def _action_list(item: Item) -> None:
    transition_map = TransitionMap(item, "N/A")
    for post_cond, pre_conds in transition_map.get_post_conditions(
            item.cache.enabled_set):
        print("")
        if post_cond[0]:
            print(transition_map.skip_idx_to_name(post_cond[0]))
        else:
            names: list[str] = []
            for co_idx, st_idx in enumerate(post_cond[1:]):
                st_name = transition_map.post_co_idx_st_idx_to_st_name(
                    co_idx, st_idx)
                if st_name != "N/A":
                    co_name = transition_map.post_co_idx_to_co_name(co_idx)
                    names.append(f"{co_name} = {st_name}")
            print(", ".join(names))
        for row in pre_conds:
            entries = []
            for co_idx, co_states in enumerate(row):
                co_name = transition_map.pre_co_idx_to_co_name(co_idx)
                states = [
                    transition_map.pre_co_idx_st_idx_to_st_name(
                        co_idx, st_idx) for st_idx in set(co_states)
                ]
                if len(states) == 1:
                    if states[0] != "N/A":
                        entries.append(f"{co_name} = {states[0]}")
                else:
                    entries.append(f"{co_name} = {{ " + ", ".join(states) +
                                   " }")
            print("")
            print("    * " + ", ".join(entries))


def _action_stats(item_cache: ItemCache) -> None:
    stats: list[tuple[int, int, str]] = []
    for item in sorted(item_cache.values()):
        if item.type == "requirement/functional/action":
            transition_map = TransitionMap(item, "N/A")
            stats.append(
                (transition_map.pre_co_count + transition_map.post_co_count,
                 len(transition_map), item.uid))
    for conditions, variants, uid in sorted(stats):
        print(f"{conditions} {variants} {uid}")


def _list_api(item_cache: ItemCache) -> None:
    items: dict[str, list[Item]] = {}
    gather_api_items(item_cache, items)
    for group, group_items in sorted(items.items()):
        print(group)
        for item in group_items:
            print(f"\t{item['name']}")


def _validate(_item: Item, validated: bool) -> bool:
    return validated


def _prepare_mapper(mapper: ItemMapper) -> None:
    for type_path_key in (
            "glossary/term:/plural", "reference:/cite", "reference:/cite-long",
            "requirement/functional/action:/text-template",
            "requirement/non-functional/performance-runtime:/environment",
            "requirement/non-functional/performance-runtime:/limit-condition",
            "requirement/non-functional/performance-runtime:/limit-kind",
            "requirement:/spec"):
        mapper.add_get_value(type_path_key, _get_value_dummy)


def cliview(argv: list[str] = sys.argv):
    """ View the specification. """

    # pylint: disable=too-many-branches
    parser = argparse.ArgumentParser()
    parser.add_argument("--config-file",
                        type=str,
                        default=None,
                        help="use this configuration file")
    parser.add_argument('--filter',
                        choices=[
                            "none", "api", "build", "orphan", "no-validation",
                            "action-compact-table", "action-table",
                            "action-table-show-skip", "action-list",
                            "action-stats", "design", "types"
                        ],
                        type=str.lower,
                        default="none",
                        help="filter the items")
    parser.add_argument('--validated',
                        choices=["all", "yes", "no"],
                        type=str.lower,
                        default="all",
                        help="filter the items by the validated status")
    parser.add_argument(
        "--enabled",
        help=("a comma separated list of enabled options used to evaluate "
              "enabled-by expressions"))
    parser.add_argument("UIDs",
                        metavar="UID",
                        nargs="*",
                        help="an UID of a specification item")
    args = parser.parse_args(argv[1:])
    config, working_directory = load_specware_config(args.config_file)
    with contextlib.chdir(working_directory):
        item_cache_config = create_config(config["spec"], ItemCacheConfig)
        item_cache_config.enabled_set = args.enabled.split(
            ",") if args.enabled else []
        type_provider = SpecWareTypeProvider({})
        item_cache = ItemCache(item_cache_config,
                               type_provider=type_provider,
                               is_item_enabled=recursive_is_enabled)
        augment_with_test_links(item_cache)
        augment_with_test_case_links(item_cache)
        root = item_cache["/req/root"]
        mapper = ItemMapper(root)
        _prepare_mapper(mapper)

        if args.filter == "action-table":
            for uid in args.UIDs:
                _action_table(item_cache[uid], False)
        elif args.filter == "action-table-show-skip":
            for uid in args.UIDs:
                _action_table(item_cache[uid], True)
        elif args.filter == "action-compact-table":
            for uid in args.UIDs:
                _action_compact_table(item_cache[uid])
        elif args.filter == "action-list":
            for uid in args.UIDs:
                _action_list(item_cache[uid])
        elif args.filter == "action-stats":
            _action_stats(item_cache)
        elif args.filter == "orphan":
            validate(root, _validate)
            for item in item_cache.values():
                if item["type"] in ["build", "spec"]:
                    continue
                if item.enabled and "validated" not in item.view:
                    print(item.uid)
        elif args.filter == "no-validation":
            validate(root, _validate)
            _no_validation(root, [])
        elif args.filter == "api":
            validate(root, _validate)
            _list_api(item_cache)
        elif args.filter == "design":
            _design(item_cache)
        elif args.filter == "types":
            for name in sorted(item_cache.items_by_type.keys()):
                print(name)
        elif args.filter == "build":
            for name in gather_build_files(config["build"], item_cache, False):
                print(name)
        else:
            validate(root, _validate)
            _view(root, mapper, 0, None, args.validated)
