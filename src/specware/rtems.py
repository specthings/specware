# SPDX-License-Identifier: BSD-2-Clause
""" Provides methods specific to the RTEMS specification. """

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

import itertools
import re
from typing import Any, Callable, Iterable

from specitems import (EnabledSet, Item, ItemCache, create_unique_link,
                       link_is_enabled, to_iterable)

_NOT_PRE_QUALIFIED = frozenset((
    "/acfg/constraint/option-not-pre-qualified",
    "/constraint/constant-not-pre-qualified",
    "/constraint/directive-not-pre-qualified",
))


def is_pre_qualified(item: Item) -> bool:
    """ Return true, if the item is pre-qualified, otherwise false. """
    return not bool(
        set(parent.uid for parent in item.parents("constraint")).intersection(
            _NOT_PRE_QUALIFIED))


_ENABLEMENT_ROLES = ("interface-function", "interface-ingroup",
                     "interface-ingroup-hidden", "requirement-refinement",
                     "validation")


def recursive_is_enabled(enabled_set: EnabledSet, item: Item) -> bool:
    """
    Return true, if the item is enabled and there exists a path to the root
    item where each item on the path is enabled, otherwise false.
    """
    if not item.is_enabled(enabled_set):
        return False
    result = True
    for parent in item.parents(_ENABLEMENT_ROLES,
                               is_link_enabled=link_is_enabled):
        if recursive_is_enabled(enabled_set, parent):
            return True
        result = False
    return result


def _add_link(item_cache: ItemCache, child: Item, data: dict) -> None:
    parent = item_cache[child.to_abs_uid(data["uid"])]
    create_unique_link(child, parent, data)


def augment_with_test_links(item_cache: ItemCache) -> None:
    """ Augment links of test case items with links from their actions. """
    for item in item_cache.items_by_type.get("test-case", []):
        for actions in item["test-actions"]:
            for checks in actions["checks"]:
                for link in checks["links"]:
                    _add_link(item_cache, item, link)
            for link in actions["links"]:
                _add_link(item_cache, item, link)


_SELF_VALIDATION = {
    "memory-benchmark": "memory benchmark",
    "requirement/functional/action": "validation by test",
    "requirement/non-functional/performance-runtime": "validation by test",
    "runtime-measurement-test": "validation by test"
}

_VALIDATION_METHOD = {
    "memory-benchmark": "validation by inspection",
    "requirement/functional/action": "validation by test",
    "requirement/functional/fatal-error": "validation by test",
    "requirement/non-functional/performance-runtime": "validation by test",
    "runtime-measurement-test": "validation by test",
    "test-case": "validation by test",
    "validation/by-analysis": "validation by analysis",
    "validation/by-inspection": "validation by inspection",
    "validation/by-review-of-design": "validation by review of design",
}

_CONTAINER_TYPE = ("interface/domain", "interface/header-file",
                   "interface/unspecified-header-file")

# In the first pass using _validate_tree() we consider interface domains and
# header files as validated.  We have to do this since a traversal to interface
# placements would lead to an infinite recursion in _validate_tree().  In the
# second pass using _validate_containers() the interface domain and header file
# validations are fixed.
_VALIDATION_LEAF = tuple(
    itertools.chain(_VALIDATION_METHOD.keys(), _CONTAINER_TYPE))

_CHILD_ROLES = ("requirement-refinement", "interface-ingroup",
                "interface-ingroup-hidden", "interface-function", "test-case",
                "validation")

_PARENT_ROLES = ("function-implementation", "interface-enumerator",
                 "performance-runtime-limits")

# WARNING: This role set works only with _visit_tree() which stops the
# recursion once it sees an item the second time.  It is there to support older
# versions of the RTEMS specification where not every interface was assigned to
# an interface group or other group membership roles were used.
_BACKWARD_COMPATIBLE_CHILD_ROLES = _CHILD_ROLES + ("appl-config-group-member",
                                                   "interface-placement")


def _visit_tree(item: Item, related_items: set[Item]) -> None:
    if item in related_items:
        return
    related_items.add(item)
    for item_2 in itertools.chain(
            item.children(_BACKWARD_COMPATIBLE_CHILD_ROLES),
            item.parents(_PARENT_ROLES)):
        _visit_tree(item_2, related_items)


def gather_related_items(root: Item) -> list[Item]:
    """ Gather a sorted list of all items related to the root item.  """
    related_items: set[Item] = set()
    _visit_tree(root, related_items)
    return sorted(related_items)


# The interface group membership roles are deliberately absent.  A group
# contributes its identifier to the content generated for each of its members,
# this is covered by the shallow parent roles.  Descending from a group to its
# members would relate a header file which contains a group to every header
# file which contains a member of that group.  The application configuration
# aggregates the members of its groups, it descends on its own.
_EXPORT_CHILD_ROLES = ("interface-function", "interface-placement",
                       "requirement-refinement", "test-case", "validation")

_EXPORT_PARENT_ROLES = _PARENT_ROLES + ("constraint", "errno",
                                        "register-block-include")

# Items reached through the shallow roles contribute to the generated content
# of the visiting item, however, the items related to them do not.  Expanding
# them would relate a header file to every item of each included header file
# and to every member of each interface group.
_EXPORT_SHALLOW_CHILD_ROLES = ("placement-order", )

_EXPORT_SHALLOW_PARENT_ROLES = ("interface-include", "interface-ingroup",
                                "interface-ingroup-hidden", "interface-target")


def _visit_export_tree(item: Item, related_items: set[Item],
                       expanded_items: set[Item]) -> None:
    related_items.add(item)
    if item in expanded_items:
        return
    # An item reached through a shallow role is added to the related items
    # only.  It must not be added to the expanded items, otherwise it would
    # block its expansion through a non-shallow role visited later on.
    expanded_items.add(item)
    related_items.update(
        itertools.chain(item.children(_EXPORT_SHALLOW_CHILD_ROLES),
                        item.parents(_EXPORT_SHALLOW_PARENT_ROLES)))
    for item_2 in itertools.chain(item.children(_EXPORT_CHILD_ROLES),
                                  item.parents(_EXPORT_PARENT_ROLES)):
        _visit_export_tree(item_2, related_items, expanded_items)


def _gather_export_related(root: Item) -> set[Item]:
    related_items: set[Item] = set()
    _visit_export_tree(root, related_items, set())
    return related_items


def gather_export_related_items(root: Item) -> list[Item]:
    """
    Gather a sorted list of all items which contribute to the content
    generated for the root item.
    """
    return sorted(_gather_export_related(root))


def is_export_affected(root: Item, uids: set[str]) -> bool:
    """
    Return true, if the content generated for the root item is affected by one
    of the items specified by the UIDs, otherwise false.
    """
    # This runs once per generated file, so the related items are not sorted.
    return any(item.uid in uids for item in _gather_export_related(root))


# Matches the item UID of a substitution such as ${/some/item:/name}.  A
# doubled designator escapes the substitution, this is not accounted for, it
# merely adds a reference which does not exist.
_REFERENCE = re.compile(r"[$@][{`]([a-zA-Z0-9._/-]+):")


def _gather_references(item: Item, value: Any, references: set[str]) -> None:
    if isinstance(value, str):
        for match in _REFERENCE.finditer(value):
            references.add(item.to_abs_uid(match.group(1)))
    elif isinstance(value, dict):
        for value_2 in value.values():
            _gather_references(item, value_2, references)
    elif isinstance(value, list):
        for value_2 in value:
            _gather_references(item, value_2, references)


def gather_referencing_items(item_cache: ItemCache,
                             uids: set[str]) -> set[str]:
    """
    Gather the UIDs of the items which reference one of the items specified by
    the UIDs through a substitution such as ``${/some/item:/name}``.

    A substitution is no link, so it is invisible to
    gather_export_related_items().  An item which substitutes an attribute of
    a changed item generates different content, so it changed as well.  Adding
    the referencing items to a selection of changed items catches for example
    a renamed interface.

    The references are followed one level only.  Following them to a fixed
    point would cover an attribute which is itself defined by a substitution,
    however, it relates almost every item to every other item.
    """
    referencing: set[str] = set()
    for item in item_cache.values():
        if item.uid in uids:
            continue
        references: set[str] = set()
        _gather_references(item, item.data, references)
        if references & uids:
            referencing.add(item.uid)
    return referencing


def gather_benchmarks_and_test_suites(item: Item,
                                      test_suites: list[Item]) -> None:
    """ Gather all benchmarks and test suites associated with the item. """
    for child in item.children(("requirement-refinement", "validation")):
        if child.type in ("memory-benchmark", "test-suite"):
            test_suites.append(child)
        else:
            gather_benchmarks_and_test_suites(child, test_suites)


def gather_test_cases(item: Item, test_cases: list[Item]) -> None:
    """ Gather all test cases associated with the item. """
    for child in item.children(("runtime-measurement-request", "test-case")):
        assert child.type in ("runtime-measurement-test",
                              "requirement/functional/action",
                              "requirement/non-functional/performance-runtime",
                              "test-case")
        test_cases.append(child)
        gather_test_cases(child, test_cases)


def get_items_by_type_map(items: Iterable[Item]) -> dict[str, list[Item]]:
    """ Get a dictionary with item sets by type. """
    items_by_type: dict[str, list[Item]] = {}
    for item in items:
        items_by_type.setdefault(item.type, []).append(item)
    return items_by_type


def get_items_by_types(items_by_type: dict[str, list[Item]],
                       types: str | Iterable[str]) -> list[Item]:
    """ Get a sorted list of items by an iterable of types. """
    items: list[Item] = []
    for type_name in to_iterable(types):
        items.extend(item for item in items_by_type.get(type_name, tuple()))
    return sorted(items)


def get_item_types_by_prefix(
    items_by_type: dict[str, list[Item]],
    prefix: str | tuple[str, ...],
    exclude: tuple[str, ...] = tuple()
) -> list[str]:
    """
    Get the types of items matching with one of the type prefixes.
    """
    return sorted(type_name for type_name in items_by_type
                  if type_name.startswith(prefix) and type_name not in exclude)


def get_constraint_items(items_by_type: dict[str, list[Item]]) -> list[Item]:
    """ Get a sorted list of the constraint items. """
    return get_items_by_types(
        items_by_type, get_item_types_by_prefix(items_by_type, "constraint"))


def get_interface_items(items_by_type: dict[str, list[Item]]) -> list[Item]:
    """ Get a sorted list of the interface items. """
    return get_items_by_types(
        items_by_type,
        get_item_types_by_prefix(
            items_by_type,
            ("interface/",
             "requirement/non-functional/interface-requirement")))


def get_requirement_items(items_by_type: dict[str, list[Item]]) -> list[Item]:
    """ Get a sorted list of the requirement items. """
    return get_items_by_types(
        items_by_type,
        get_item_types_by_prefix(
            items_by_type, ("glossary/group", "requirement/"),
            ("requirement/non-functional/interface-requirement", )))


def get_interface_and_requirement_items(
        items_by_type: dict[str, list[Item]]) -> list[Item]:
    """ Get a sorted list of the interface and requirement items. """
    return get_items_by_types(
        items_by_type,
        get_item_types_by_prefix(
            items_by_type, ("interface/", "glossary/group", "requirement/")))


def get_validation_items(items_by_type: dict[str, list[Item]]) -> list[Item]:
    """ Get a sorted list of the validation items. """
    return get_items_by_types(
        items_by_type,
        get_item_types_by_prefix(
            items_by_type,
            ("requirement/functional/action",
             "requirement/non-functional/performance-runtime",
             "runtime-measurement-test", "test-case", "validation")))


def get_benchmark_and_test_suite_items(
        items_by_type: dict[str, list[Item]]) -> list[Item]:
    """ Get a sorted list of the benchmark and test suite items. """
    return get_items_by_types(
        items_by_type,
        get_item_types_by_prefix(items_by_type,
                                 ("memory-benchmark", "test-suite")))


def is_validation_by_test(item: Item) -> bool:
    """ Return true, if the item is a validation by test, otherwise false. """
    return _VALIDATION_METHOD.get(item.type, "") == "validation by test"


def _validate_glossary_group(item: Item, validated: bool) -> bool:
    # A glossary group shall have at least one term and all members shall be
    # terms.
    terms = list(item.children("glossary-member"))
    has_term = bool(terms)
    all_terms_valid = all(term.type == "glossary/term" for term in terms)
    return validated and has_term and all_terms_valid


def _validate_design_target(_item: Item, validated: bool) -> bool:
    # Design targets are validated through tests results.  A design target is
    # validated, if at least one test result is available and there are no
    # unexpected failures in the test results.  Test results are not available
    # within the scope of the specware package.
    return validated


def _validate_test_case(item: Item, validated: bool) -> bool:
    # Make sure that the test case links to proper test suites.  For this a
    # corresponding build specification is required.
    status = False
    for test_suite in item.parents("test-case"):
        try:
            test_suite.parent("requirement-refinement")
        except IndexError:
            return False
        status = validated
    return status


def _validate_constraint(item: Item, validated: bool) -> bool:
    for item_2 in item.parents("requirement-refinement"):
        if item_2.uid != "/req/usage-constraints":
            return False
    return validated


_VALIDATOR = {
    "constraint": _validate_constraint,
    "glossary/group": _validate_glossary_group,
    "requirement/non-functional/design-target": _validate_design_target,
    "test-case": _validate_test_case
}


def _validate_tree(item: Item, validator: Callable[[Item, bool], bool],
                   order: tuple[int, ...], related_items: set[Item]) -> bool:
    item.view["order"] = order
    related_items.add(item)
    pre_qualified = is_pre_qualified(item)
    item.view["pre-qualified"] = pre_qualified
    validated = True
    validation_dependencies: list[tuple[str, str]] = []
    for index, link in enumerate(
            sorted(
                itertools.chain(item.links_to_children(_CHILD_ROLES),
                                item.links_to_parents(_PARENT_ROLES)))):
        item_2 = link.item
        validated = _validate_tree(item_2, validator, order[:-1] +
                                   (order[-1] + index + 1, 0),
                                   related_items) and validated
        if link.role == "validation":
            role = _VALIDATION_METHOD[item_2.type]
        elif link.role == "requirement-refinement":
            role = "refinement"
        elif link.role.startswith("interface-ingroup"):
            role = "group member"
        else:
            role = link.role.replace("-", " ")
        validation_dependencies.append((item_2.uid, role))
    type_name = item.type
    if type_name in _SELF_VALIDATION:
        validation_dependencies.append((item.uid, _SELF_VALIDATION[type_name]))
    elif type_name in _VALIDATOR:
        validated = _VALIDATOR[type_name](item, validated)
    elif not validation_dependencies:
        validated = (not pre_qualified) or (type_name in _VALIDATION_LEAF)
    if type_name in _CONTAINER_TYPE:
        validation_dependencies.extend(
            (item_2.uid, "interface placement")
            for item_2 in item.children("interface-placement"))
    validated = validator(item, validated)
    item.view["validated"] = validated
    item.view["validation-dependencies"] = sorted(validation_dependencies)
    return validated


def _validate_containers(item: Item) -> bool:
    validated = item.view["validated"]
    if item.type in _CONTAINER_TYPE:
        # If at least one not validated child exists, then the container is not
        # validated
        for item_2 in item.children("interface-placement"):
            try:
                if not item_2.view["validated"]:
                    validated = False
                    item.view["validated"] = validated
                    break
            except KeyError as err:
                raise ValueError(
                    f"{item.uid} container member "
                    f"{item_2.uid} has no validated status") from err
    for item_2 in itertools.chain(item.children(_CHILD_ROLES),
                                  item.parents(_PARENT_ROLES)):
        validated = _validate_containers(item_2) and validated
    return validated


def _fixup_pre_qualified(item: Item, types: list[str],
                         roles: str | list[str]) -> None:
    for type_name in types:
        for item_2 in item.cache.items_by_type.get(type_name, []):
            # Count of not pre-qualified (index 0) and pre-qualified (index 1)
            # children
            count = [0, 0]
            for item_3 in item_2.children(roles):
                count[int(item_3.view["pre-qualified"])] += 1
            # If at least one not pre-qualified child exists and no
            # pre-qualified child exists, then the item is not pre-qualified.
            if count[0] > 0 and count[1] == 0:
                item_2.view["pre-qualified"] = False


def validate(root: Item, validator: Callable[[Item, bool], bool]) -> set[Item]:
    """
    Validate the item tree starting at the root item.

    Returns the set of items related to the root item.
    """
    related_items: set[Item] = set()
    _validate_tree(root, validator, (0, ), related_items)
    _validate_containers(root)
    _fixup_pre_qualified(root,
                         ["interface/appl-config-group", "interface/group"],
                         ["interface-ingroup", "interface-ingroup-hidden"])
    _fixup_pre_qualified(root, ["interface/header-file"],
                         "interface-placement")
    return related_items


_API_INTERFACES = [
    "interface/appl-config-option/feature",
    "interface/appl-config-option/feature-enable",
    "interface/appl-config-option/initializer",
    "interface/appl-config-option/integer",
    "interface/function",
    "interface/macro",
    "interface/unspecified-function",
    "interface/unspecified-macro",
]

_API_ROLES = (
    "requirement-refinement",
    "interface-ingroup",
)


def _gather_api_items(item: Item, items: dict[str, list[Item]]) -> None:
    if item.type in _API_INTERFACES and item.view["pre-qualified"]:
        parent = item.parent(_API_ROLES)
        group = items.setdefault(parent.get("name", parent.spec), [])
        group.append(item)
    for child in item.children(_API_ROLES):
        _gather_api_items(child, items)


def gather_api_items(item_cache: ItemCache, items: dict[str,
                                                        list[Item]]) -> None:
    """
    Gather all API related items and groups them by the associated interface
    group name.

    If a group has no name, then the UID is used instead.
    """
    for group in item_cache["/req/api"].children("requirement-refinement"):
        _gather_api_items(group, items)
