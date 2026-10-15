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

from specitems import (EmptyItemCache, Item, ItemCache, ItemSelection,
                       create_unique_link)

from specware import (
    SpecWareTypeProvider, augment_with_test_case_links,
    augment_with_test_links, gather_api_items, gather_export_related_items,
    gather_referencing_items, gather_related_items, gather_test_cases,
    gather_benchmarks_and_test_suites, get_benchmark_and_test_suite_items,
    get_items_by_type_map, get_constraint_items, get_interface_items,
    get_interface_and_requirement_items, get_requirement_items,
    get_validation_items, is_export_affected, is_pre_qualified,
    is_validation_by_test, recursive_is_enabled, validate)

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


def _block(links):
    return {
        "enabled-by": True,
        "interface-type": "register-block",
        "links": links
    }


def _header(enabled_by, uids):
    return {
        "enabled-by":
        enabled_by,
        "interface-type":
        "header-file",
        "links": [{
            "role": "register-block-host",
            "style": "default",
            "uid": uid
        } for uid in uids]
    }


def test_recursive_is_enabled_register_block():
    item_cache = EmptyItemCache()
    item_cache.add_items(
        {
            "/h-alpha":
            _header("alpha", ["/derived"]),
            "/h-beta":
            _header("beta", ["/includer"]),
            "/base":
            _block([]),
            "/derived":
            _block([{
                "role": "register-block-base",
                "uid": "/base"
            }]),
            "/includer":
            _block([{
                "name": "INC",
                "role": "register-block-include",
                "uid": "/included"
            }]),
            "/included":
            _block([]),
            "/orphan":
            _block([]),
            "/g-alpha": {
                "enabled-by": "alpha",
                "interface-type": "group",
                "links": [{
                    "role": "interface-group-member",
                    "uid": "/member"
                }]
            },
            "/member":
            _block([]),
            "/h-member": {
                "enabled-by":
                True,
                "interface-type":
                "header-file",
                "links": [{
                    "role": "interface-ingroup",
                    "uid": "/member"
                }, {
                    "role": "register-block-host",
                    "style": "default",
                    "uid": "/member"
                }]
            },
            "/h-place": {
                "enabled-by": True,
                "interface-type": "header-file",
                "links": [{
                    "role": "interface-ingroup",
                    "uid": "/g-place"
                }]
            },
            "/h-host": {
                "enabled-by":
                "beta",
                "interface-type":
                "header-file",
                "links": [{
                    "role": "interface-host",
                    "uid": uid
                } for uid in ("/hosted", "/placed-hosted")]
            },
            "/hosted": {
                "enabled-by": True,
                "interface-type": "define",
                "links": []
            },
            "/placed-hosted": {
                "enabled-by":
                True,
                "interface-type":
                "define",
                "links": [{
                    "role": "interface-placement",
                    "uid": "/h-place"
                }, {
                    "role": "interface-ingroup",
                    "uid": "/g-place"
                }]
            },
            "/g-place": {
                "enabled-by": True,
                "interface-type": "group",
                "links": [{
                    "role": "interface-placement",
                    "uid": "/h-place"
                }]
            }
        },
        set_types=False)
    enabled = {
        "alpha": [
            "/base", "/derived", "/g-alpha", "/g-place", "/h-alpha",
            "/h-member", "/h-place", "/included", "/includer", "/member",
            "/orphan", "/placed-hosted"
        ],
        "beta": [
            "/base", "/derived", "/g-place", "/h-beta", "/h-host", "/h-place",
            "/hosted", "/included", "/includer", "/orphan", "/placed-hosted"
        ]
    }
    for config, uids in enabled.items():
        item_cache.set_selection(
            ItemSelection(item_cache, [config], recursive_is_enabled))
        assert sorted(item.uid for item in item_cache.values()
                      if item.enabled) == uids


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
    assert item_cache["/glossary-general"].view["validated"]
    assert not item_cache["/glossary-empty"].view["validated"]
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
        "/constraint/not-enabled",
        "/constraint/terminate",
        "/disposition/urgent-mechanism",
        "/glossary-empty",
        "/glossary-general",
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
        "/req/unpushed-data",
        "/req/urgent-mechanism",
        "/req/usage-constraints",
        "/req/window-unsigned",
        "/val/disable-newlib-reentrancy",
        "/val/perf",
        "/val/tc",
        "/val/ts",
        "/val/window-unsigned",
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
        "interface/appl-config-group",
        "interface/appl-config-option/feature-enable",
        "interface/domain",
        "interface/group",
        "interface/header-file",
        "interface/unspecified-define",
        "interface/unspecified-function",
        "requirement-disposition",
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
        "/constraint/not-enabled",
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
        "/glossary-empty",
        "/glossary-general",
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
        "/req/unpushed-data",
        "/req/urgent-mechanism",
        "/req/usage-constraints",
        "/req/window-unsigned",
    ]
    assert _uids(get_interface_and_requirement_items(items_by_type)) == [
        "/glossary-empty",
        "/glossary-general",
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
        "/req/unpushed-data",
        "/req/urgent-mechanism",
        "/req/usage-constraints",
        "/req/window-unsigned",
    ]
    assert _uids(get_validation_items(items_by_type)) == [
        "/req/clock-gettime",
        "/req/clock-nanosleep",
        "/req/perf-runtime",
        "/val/disable-newlib-reentrancy",
        "/val/perf",
        "/val/tc",
        "/val/window-unsigned",
    ]
    assert _uids(get_benchmark_and_test_suite_items(items_by_type)) == [
        "/val/ts",
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
            "type": "interface"
        })
    with pytest.raises(ValueError,
                       match=("/if/header-empty container member "
                              "/orphan has no validated status")):
        validate(root, _validate)


def _status(item_cache, uid):
    item = item_cache[uid]
    return (item.view["validated"], item.view["validation-dependencies"])


def _create_errata_cache(tmpdir):
    item_cache = create_item_cache(tmpdir, "spec-errata")
    item_cache.set_selection(ItemSelection(item_cache, []))
    return item_cache


def _add_errata_link(item_cache, child, parent, role):
    create_unique_link(item_cache[child], item_cache[parent], {
        "role": role,
        "uid": parent
    })


def test_validate_errata(tmpdir):
    item_cache = _create_errata_cache(tmpdir)
    root = item_cache["/req/root"]
    related_items = validate(root, _validate)
    assert _uids(sorted(related_items)) == [
        "/errata/e1",
        "/errata/e2",
        "/errata/e4",
        "/ref/sheet-1",
        "/ref/sheet-2",
        "/ref/sheet-3",
        "/req/errata-a",
        "/req/errata-b",
        "/req/root",
        "/val/a-e1",
        "/val/a-e2",
        "/val/b-e1",
    ]
    assert not root.view["validated"]
    assert _status(item_cache, "/req/errata-a") == (True, [
        ("/ref/sheet-1", "errata work"),
        ("/ref/sheet-2", "errata work"),
        ("/val/a-e1", "validation by analysis"),
        ("/val/a-e2", "validation by analysis"),
    ])
    assert _status(item_cache, "/req/errata-b") == (False, [
        ("/ref/sheet-1", "errata work"),
        ("/ref/sheet-3", "errata work"),
        ("/val/b-e1", "validation by analysis"),
    ])

    # The status of an erratum and of a work is not validated if one errata
    # group which reaches it lacks a resolution.
    assert _status(item_cache, "/ref/sheet-1") == (False, [
        ("/errata/e1", "erratum"),
        ("/errata/e2", "erratum"),
    ])
    assert _status(item_cache, "/ref/sheet-2") == (True, [
        ("/errata/e4", "erratum"),
    ])

    # A disabled erratum needs no resolution.
    assert _status(item_cache, "/ref/sheet-3") == (True, [])
    assert _status(item_cache, "/errata/e1") == (True, [
        ("/val/a-e1", "errata resolution"),
        ("/val/b-e1", "errata resolution"),
    ])
    assert _status(item_cache, "/errata/e2") == (False, [
        ("/val/a-e2", "errata resolution"),
    ])
    assert _status(item_cache, "/errata/e4") == (True, [
        ("/val/a-e2", "errata resolution"),
    ])
    for uid in ("/errata/e1", "/errata/e2", "/ref/sheet-1"):
        assert item_cache[uid].view["pre-qualified"]

    # The first visit gives the order.
    order = item_cache["/req/errata-a"].view["order"]
    assert item_cache["/ref/sheet-1"].view["order"] == order[:-1] + (
        order[-1] + 3, 0)
    assert item_cache["/errata/e1"].view["order"] == order[:-1] + (order[-1] +
                                                                   3, 1, 0)


def _add_errata_group(item_cache, uid, works):
    item_cache.add_item(
        uid, {
            "SPDX-License-Identifier":
            "CC-BY-SA-4.0 OR BSD-2-Clause",
            "copyrights": ["Copyright (C) 2026 embedded brains GmbH & Co. KG"],
            "enabled-by":
            True,
            "links": [{
                "role": "requirement-refinement",
                "uid": "/req/root"
            }] + [{
                "role": "reference",
                "uid": work
            } for work in works],
            "non-functional-type":
            "errata-group",
            "rationale":
            None,
            "requirement-type":
            "non-functional",
            "text":
            "The library shall take the errata into account.",
            "type":
            "requirement"
        })


def test_validate_errata_group_status(tmpdir):
    item_cache = _create_errata_cache(tmpdir)

    # This group lacks resolutions and the walk visits it first.
    _add_errata_group(item_cache, "/req/errata-0", ["/ref/sheet-1"])

    # This group references a document with disabled errata only.
    _add_errata_group(item_cache, "/req/errata-d", ["/ref/sheet-3"])

    validate(item_cache["/req/root"], _validate)
    assert item_cache["/req/errata-0"].view["order"] < item_cache[
        "/req/errata-a"].view["order"]
    assert not item_cache["/req/errata-0"].view["validated"]
    assert item_cache["/req/errata-a"].view["validated"]
    assert not item_cache["/ref/sheet-1"].view["validated"]
    assert _status(item_cache, "/req/errata-d") == (True, [
        ("/ref/sheet-3", "errata work"),
    ])


def test_validate_errata_work_without_errata(tmpdir):
    item_cache = _create_errata_cache(tmpdir)
    item_cache.add_item(
        "/ref/no-errata", {
            "SPDX-License-Identifier": "CC-BY-SA-4.0 OR BSD-2-Clause",
            "copyrights": ["Copyright (C) 2026 embedded brains GmbH & Co. KG"],
            "enabled-by": True,
            "links": [],
            "reference-type": "manual",
            "title": "No Errata",
            "type": "reference",
            "work-hash": None,
            "work-url": None
        })
    _add_errata_link(item_cache, "/req/errata-b", "/ref/no-errata",
                     "reference")
    with pytest.raises(ValueError,
                       match=("errata group /req/errata-b references "
                              "/ref/no-errata which no erratum references")):
        validate(item_cache["/req/root"], _validate)


def test_validate_errata_resolution_outside_works(tmpdir):
    item_cache = _create_errata_cache(tmpdir)
    _add_errata_link(item_cache, "/val/b-e1", "/errata/e4",
                     "errata-resolution")
    with pytest.raises(ValueError,
                       match=("/val/b-e1 resolves /errata/e4 which no work "
                              "of /req/errata-b contains")):
        validate(item_cache["/req/root"], _validate)


def test_validate_errata_resolution_without_group(tmpdir):
    item_cache = _create_errata_cache(tmpdir)
    _add_errata_link(item_cache, "/req/root", "/errata/e1",
                     "errata-resolution")
    with pytest.raises(ValueError,
                       match=("/req/root resolves an erratum and validates "
                              "no errata group")):
        validate(item_cache["/req/root"], _validate)


def test_gather_export_related_items(tmpdir):
    item_cache = create_item_cache(tmpdir, "spec-interface")
    related_items = gather_export_related_items(item_cache["/h"])
    assert _uids(related_items) == [
        "/constraint-a",
        "/constraint/other",
        "/constraint/type-opaque",
        "/define",
        "/define-brief",
        "/enum",
        "/enum3",
        "/enumerator-0",
        "/enumerator-1",
        "/enumerator-2",
        "/enumerator-b",
        "/forward-decl",
        "/forward-decl-2",
        "/func",
        "/func2",
        "/func6",
        "/ga",
        "/gb",
        "/gc",
        "/h",
        "/h2",
        "/h4",
        "/h5",
        "/h6",
        "/h7",
        "/h8",
        "/h9",
        "/irqamp",
        "/irqamp-timestamp",
        "/macro",
        "/macro2",
        "/register-block-memory",
        "/register-block-memory-inner",
        "/register-block-no-size",
        "/s",
        "/s2",
        "/td",
        "/td3",
        "/u",
        "/unspecified-struct",
        "/var",
    ]

    # The header file /h2 is included by /h.  It is reached through a shallow
    # role, so it is related, however, it is not expanded.  Its member /enum4
    # is not related to /h.
    uids = _uids(related_items)
    assert "/h2" in uids
    assert "/enum4" in _uids(item_cache["/h2"].children("interface-placement"))
    assert "/enum4" not in uids

    assert is_export_affected(item_cache["/h"], {"/constraint-a"})
    assert not is_export_affected(item_cache["/h"], {"/enum4"})
    assert not is_export_affected(item_cache["/h"], set())


def test_gather_referencing_items(tmpdir):
    item_cache = create_item_cache(tmpdir, "spec-interface")

    assert gather_referencing_items(item_cache, set()) == set()

    # An absolute reference in a text attribute.  The referenced item need not
    # exist, the substitution is reported by the content generation.
    assert "/h" in gather_referencing_items(item_cache, {"/term"})

    # A relative reference is resolved against the referencing item.
    assert "/func" in gather_referencing_items(item_cache,
                                               {"/unspecified-struct"})

    # A reference nested in a list of dictionaries.
    assert "/s2" in gather_referencing_items(item_cache, {"/c/if/uint32_t"})

    # An item of the selection references itself through ${.:/name}, it is no
    # referencing item.
    assert "/h" not in gather_referencing_items(item_cache, {"/h", "/term"})

    assert gather_referencing_items(item_cache, {"/does-not-exist"}) == set()


def test_validate_group_member(tmpdir):
    item_cache = EmptyItemCache(type_provider=SpecWareTypeProvider({}))
    item_cache.add_items({
        "/group": {
            "enabled-by": True,
            "interface-type": "group",
            "links": [{
                "role": "interface-group-member",
                "uid": "/block"
            }],
            "type": "interface"
        },
        "/block": {
            "enabled-by":
            True,
            "interface-type":
            "register-block",
            "links": [{
                "role": "constraint",
                "uid": "/constraint/constant-not-pre-qualified"
            }],
            "type":
            "interface"
        },
        "/constraint/constant-not-pre-qualified": {
            "enabled-by": True,
            "links": [],
            "type": "constraint"
        }
    })
    group = item_cache["/group"]
    validate(group, _validate)
    dependencies = group.view["validation-dependencies"]
    assert dependencies == [("/block", "group member")]
    assert not group.view["pre-qualified"]

    item_cache = create_item_cache(tmpdir,
                                   ["spec-interface", "spec-interface-host"])
    assert _uids(gather_related_items(
        item_cache["/hg"])) == ["/hd", "/hg", "/hi", "/hs"]
    assert _uids(gather_related_items(item_cache["/hh2"])) == ["/hh2", "/hi"]
    assert "/hg" in _uids(gather_export_related_items(item_cache["/hh2"]))
    assert is_export_affected(item_cache["/hh2"], {"/hg"})
