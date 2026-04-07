# SPDX-License-Identifier: BSD-2-Clause
""" Tests for the rtems module. """

# Copyright (C) 2022, 2023 embedded brains GmbH & Co. KG
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

import pytest

from specitems import EmptyItemCache, Item, ItemCache, ItemSelection

from specware import (augment_with_test_case_links, augment_with_test_links,
                      gather_api_items, gather_related_items,
                      gather_test_cases, gather_benchmarks_and_test_suites,
                      get_items_by_type_map, get_constraint_items,
                      get_interface_items, get_interface_and_requirement_items,
                      get_requirement_items, get_validation_items,
                      is_pre_qualified, is_validation_by_test,
                      recursive_is_enabled, validate)

from .util import create_item_cache


def test_is_pre_qualified():
    item_cache = EmptyItemCache()
    uid = "/constraint/constant-not-pre-qualified"
    constraint = item_cache.add_item(uid, {"enabled-by": True, "links": []})
    assert is_pre_qualified(constraint)
    item = item_cache.add_item("/i", {
        "enabled-by": True,
        "links": [{
            "role": "constraint",
            "uid": uid
        }]
    })
    assert not is_pre_qualified(item)


def test_augment_with_test_links():
    item_cache = EmptyItemCache()
    item = item_cache.add_item("/i", {"enabled-by": True, "links": []})
    link = {"role": "validation", "uid": "/i"}
    test_case = item_cache.add_item(
        "/t", {
            "enabled-by": True,
            "links": [],
            "test-actions": [{
                "checks": [{
                    "links": [link]
                }],
                "links": [link]
            }]
        })
    test_case.data["_type"] = "test-case"
    item_cache.items_by_type["test-case"] = [test_case]
    augment_with_test_links(item_cache)
    assert item.child("validation") == test_case
    assert test_case.parent("validation") == item


def test_recursive_is_enabled():
    item_cache = EmptyItemCache()
    a = item_cache.add_item("/a", {"enabled-by": True, "links": []})
    b = item_cache.add_item(
        "/b", {
            "enabled-by": False,
            "links": [{
                "role": "requirement-refinement",
                "uid": "/a"
            }]
        })
    c = item_cache.add_item(
        "/c", {
            "enabled-by": True,
            "links": [{
                "role": "requirement-refinement",
                "uid": "/a"
            }]
        })
    d = item_cache.add_item(
        "/d", {
            "enabled-by":
            True,
            "links": [{
                "role": "requirement-refinement",
                "uid": "/b"
            }, {
                "role": "requirement-refinement",
                "uid": "/c"
            }]
        })
    e = item_cache.add_item(
        "/e", {
            "enabled-by": True,
            "links": [{
                "role": "requirement-refinement",
                "uid": "/b"
            }]
        })
    item_cache.set_selection(
        ItemSelection(item_cache, [], recursive_is_enabled))
    assert d.enabled
    assert not e.enabled


def _validate(item, validated):
    return validated


def _uids(items):
    return [item.uid for item in items]


def test_validate(tmpdir):
    item_cache = create_item_cache(tmpdir, ["spec-rtems", "spec-rtems-2"])
    augment_with_test_links(item_cache)
    augment_with_test_case_links(item_cache)
    root = item_cache["/req/root"]
    assert "validated" not in root.view
    validate(root, _validate)
    assert not root.view["validated"]
    assert not is_validation_by_test(root)
    assert is_validation_by_test(item_cache["/req/clock-gettime"])
    api_items = {}
    gather_api_items(item_cache, api_items)
    assert [(group, [item.uid for item in group_items])
            for group, group_items in sorted(api_items.items())
            ] == [("Application Configuration",
                   ["/if/clock-gettime", "/if/clock-nanosleep"]),
                  ("Application Configuration Group Name",
                   ["/if/disable-newlib-reentrancy"])]

    related_items = gather_related_items(root)
    assert _uids(related_items) == [
        "/constraint/bad",
        "/constraint/constant-not-pre-qualified",
        "/constraint/terminate",
        "/glossary-general",
        "/glossary/api",
        "/glossary/bad",
        "/glossary/ecss",
        "/glossary/softwareproduct",
        "/glossary/sourcecode",
        "/glossary/target",
        "/if/clock-gettime",
        "/if/clock-nanosleep",
        "/if/disable-newlib-reentrancy",
        "/if/domain",
        "/if/errno",
        "/if/errno-header",
        "/if/group",
        "/if/group-general",
        "/if/header-confdefs",
        "/if/header-empty",
        "/if/not-pre-qualified",
        "/if/not-pre-qualified-header",
        "/req/api",
        "/req/clock-gettime",
        "/req/clock-nanosleep",
        "/req/disable-newlib-reentrancy",
        "/req/group",
        "/req/group-2",
        "/req/group-3",
        "/req/mem-catch-snd",
        "/req/perf-runtime",
        "/req/root",
        "/req/signal-count",
        "/req/signal-number",
        "/req/target",
        "/req/usage-constraints",
        "/val/disable-newlib-reentrancy",
        "/val/perf",
        "/val/tc",
        "/val/ts",
    ]
    test_suites = []
    gather_benchmarks_and_test_suites(root, test_suites)
    assert _uids(test_suites) == [
        "/val/ts",
    ]
    test_cases = []
    gather_test_cases(item_cache["/val/ts"], test_cases)
    assert _uids(test_cases) == [
        "/val/tc",
    ]
    items_by_type = get_items_by_type_map(related_items)
    assert sorted(items_by_type) == [
        "constraint",
        "glossary/group",
        "glossary/term",
        "interface/appl-config-group",
        "interface/appl-config-option/feature-enable",
        "interface/domain",
        "interface/group",
        "interface/header-file",
        "interface/unspecified-define",
        "interface/unspecified-function",
        "requirement/functional/action",
        "requirement/functional/function",
        "requirement/non-functional/design",
        "requirement/non-functional/design-group",
        "requirement/non-functional/design-target",
        "requirement/non-functional/interface-requirement",
        "requirement/non-functional/performance-runtime",
        "requirement/non-functional/quality",
        "runtime-measurement-test",
        "test-case",
        "test-suite",
        "validation/by-inspection",
    ]
    assert _uids(get_constraint_items(items_by_type)) == [
        "/constraint/bad",
        "/constraint/constant-not-pre-qualified",
        "/constraint/terminate",
    ]
    assert _uids(get_interface_items(items_by_type)) == [
        "/if/clock-gettime",
        "/if/clock-nanosleep",
        "/if/disable-newlib-reentrancy",
        "/if/domain",
        "/if/errno",
        "/if/errno-header",
        "/if/group",
        "/if/group-general",
        "/if/header-confdefs",
        "/if/header-empty",
        "/if/not-pre-qualified",
        "/if/not-pre-qualified-header",
        "/req/api",
    ]
    assert _uids(get_requirement_items(items_by_type)) == [
        "/req/clock-gettime",
        "/req/clock-nanosleep",
        "/req/disable-newlib-reentrancy",
        "/req/group",
        "/req/group-2",
        "/req/group-3",
        "/req/mem-catch-snd",
        "/req/perf-runtime",
        "/req/root",
        "/req/signal-count",
        "/req/signal-number",
        "/req/target",
        "/req/usage-constraints",
    ]
    assert _uids(get_interface_and_requirement_items(items_by_type)) == [
        "/if/clock-gettime",
        "/if/clock-nanosleep",
        "/if/disable-newlib-reentrancy",
        "/if/domain",
        "/if/errno",
        "/if/errno-header",
        "/if/group",
        "/if/group-general",
        "/if/header-confdefs",
        "/if/header-empty",
        "/if/not-pre-qualified",
        "/if/not-pre-qualified-header",
        "/req/api",
        "/req/clock-gettime",
        "/req/clock-nanosleep",
        "/req/disable-newlib-reentrancy",
        "/req/group",
        "/req/group-2",
        "/req/group-3",
        "/req/mem-catch-snd",
        "/req/perf-runtime",
        "/req/root",
        "/req/signal-count",
        "/req/signal-number",
        "/req/target",
        "/req/usage-constraints",
    ]
    assert _uids(get_validation_items(items_by_type)) == [
        "/req/clock-gettime",
        "/req/clock-nanosleep",
        "/req/perf-runtime",
        "/val/disable-newlib-reentrancy",
        "/val/perf",
        "/val/tc",
    ]

    item_cache.add_item(
        "/orphan", {
            "SPDX-License-Identifier": "CC-BY-SA-4.0 OR BSD-2-Clause",
            "copyrights": ["Copyright (C) 2026 embedded brains GmbH & Co. KG"],
            "enabled-by": True,
            "index-entries": [],
            "interface-type": "unspecified-define",
            "links": [{
                "role": "interface-placement",
                "uid": "/if/header-empty"
            }],
            "name": "ORPHAN",
            "references": [],
            "type": "interface"
        })
    with pytest.raises(ValueError,
                       match=("/if/header-empty container member "
                              "/orphan has no validated status")):
        validate(root, _validate)
