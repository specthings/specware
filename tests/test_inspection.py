# SPDX-License-Identifier: BSD-2-Clause
""" Tests the inspection scope checks. """

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

import os

from specitems import ItemCache, load_data

from specware.cliinspect import cliinspect
from specware.inspection import (State, check, check_inspection, is_superseded,
                                 item_digest, renew)

from .util import create_item_cache

_CODE = """int first(void);
int second(void);
int third(void);
"""


def _baseline(item_cache: ItemCache, uid: str) -> None:
    """ Record the current digests of every scope of the inspection. """
    item = item_cache[uid]
    for result, link in zip(check_inspection(item),
                            item.links_to_parents("inspected")):
        assert result.state is State.NOT_BASELINED
    for link in item.links_to_parents("inspected"):
        for scope in link["scopes"]:
            scope["hash"] = _current_digest(item_cache, uid, link, scope)


def _current_digest(item_cache: ItemCache, uid: str, link, scope) -> str:
    # pylint: disable=protected-access
    from specware.inspection import _actual_digest, _findings_of
    digest = _actual_digest(scope, link.item, _findings_of(link.item))
    assert digest is not None, f"{uid} {scope}"
    return digest


def _states(results) -> dict[tuple[str, str], State]:
    return {(result.uid, result.scope): result.state for result in results}


def _create(tmpdir) -> ItemCache:
    tree = os.path.join(tmpdir, "tree")
    os.makedirs(tree, exist_ok=True)
    with open(os.path.join(tree, "code.c"), "w", encoding="utf-8") as out:
        out.write(_CODE)
    item_cache = create_item_cache(tmpdir, ["spec-inspection", "spec-types"])
    item_cache["/tree"]["directory"] = tree
    return item_cache


def test_states(tmpdir):
    item_cache = _create(tmpdir)
    _baseline(item_cache, "/file-ok")
    _baseline(item_cache, "/item-scope")
    _baseline(item_cache, "/finding-ok")
    _baseline(item_cache, "/new-round")
    states = _states(check(item_cache.values()))

    assert states[("/file-ok", "file code.c")] is State.VALID
    assert states[("/file-ok", "file code.c lines 2:3")] is State.VALID
    assert states[("/item-scope", "item")] is State.VALID
    assert states[("/new-round", "file code.c")] is State.VALID

    assert states[("/file-stale", "file code.c")] is State.STALE
    assert states[("/file-absent", "file gone.c")] is State.ABSENT
    assert states[("/file-not-baselined",
                   "file code.c")] is State.NOT_BASELINED

    # The superseded round keeps its stale digest and is not checked.
    assert not any(uid == "/old-round" for uid, _ in states)
    assert is_superseded(item_cache["/old-round"])
    assert not is_superseded(item_cache["/new-round"])

    # One finding of the analysis is dispositioned, the other is not.
    finding = ("/finding-ok", "finding coverity CHECKED_RETURN signalsend.c "
               "_Signal_Action_handler")
    assert states[finding] is State.VALID

    # The finding of the superseded member does not count as a disposition,
    # so it is still reported as undispositioned.
    assert is_superseded(item_cache["/finding-old"])
    assert states[("/group",
                   "FORWARD_NULL hash.c _Hash_Finalize")] is \
        State.UNDISPOSITIONED

    # A corrected defect leaves the report, which retires the inspection
    # rather than invalidating it.
    assert states[("/finding-absent",
                   "finding coverity RESOURCE_LEAK gone.c _Gone")] is \
        State.ABSENT


def test_result_text(tmpdir):
    item_cache = _create(tmpdir)
    text = {str(result) for result in check(item_cache.values())}
    assert "STALE /file-stale file code.c: expected " \
        "4gxjmiIabDDphR7ftUEwoQU-jH0AsHtL9adzn_1Sf1jXWebfKRLU2QLYBOfp7fbXbf" \
        "0Ha4hCTPmMr3vXsJoSGg== but got " \
        "cqump_dvS1BeW-DG-BUVD3TKuZ492GcFMWIfns8_olEwmhXQrLTiQ0NE3XRPhTEOG4" \
        "EV6kZAQy_KjAhat3UMFg==" in text


def test_gate(tmpdir):
    item_cache = _create(tmpdir)
    results = check(item_cache.values())
    failing = sorted(
        {result.state.value
         for result in results if result.state.fails})
    assert failing == ["stale", "undispositioned"]
    assert not State.ABSENT.fails
    assert not State.NOT_BASELINED.fails
    assert not State.NOT_CHECKED.fails
    assert not State.VALID.fails


def test_not_checked(tmpdir):
    item_cache = _create(tmpdir)
    item_cache["/tree"]["directory"] = os.path.join(tmpdir, "gone")
    states = _states(check(item_cache.values()))
    assert states[("/file-ok", "file code.c")] is State.NOT_CHECKED


def test_item_digest_ignores_copyrights(tmpdir):
    item_cache = _create(tmpdir)
    item = item_cache["/analysis"]
    before = item_digest(item)
    item.data["copyrights"] = ["Copyright (C) 2027 somebody else"]
    item.data["SPDX-License-Identifier"] = "MIT"
    assert item_digest(item) == before
    item.data["findings-list"] = []
    assert item_digest(item) != before


def test_renew(tmpdir):
    item_cache = _create(tmpdir)
    data = renew(item_cache["/file-stale"])
    assert data["type"] == "inspection"
    # The judgement is left to a person.
    assert data["date"] is None
    assert data["verdict"] is None
    assert data["method"] is None
    assert data["findings"] is None
    assert data["inspectors"] == []
    supersedes = [
        link for link in data["links"] if link["role"] == "supersedes"
    ]
    assert [link["uid"] for link in supersedes] == ["/file-stale"]
    inspected = [link for link in data["links"] if link["role"] == "inspected"]
    assert len(inspected) == 1
    # The digests are the current ones, so the new round is baselined.
    for scope in inspected[0]["scopes"]:
        assert scope["hash"] is not None
        assert scope["hash"] != "4gxjmiIabDDphR7ftUEwoQU-jH0AsHtL9adzn_1Sf1jX" \
            "WebfKRLU2QLYBOfp7fbXbf0Ha4hCTPmMr3vXsJoSGg=="


def _config(tmpdir) -> str:
    _create(tmpdir)
    return os.path.join(os.path.dirname(__file__), "specware-inspection.yml")


def test_cli_check(tmpdir, capsys):
    status = cliinspect(["x", "--config-file", _config(tmpdir)])
    out = capsys.readouterr().out
    # The tree of the fixture does not exist, so the file scopes are honestly
    # reported as not checked rather than as passing.
    assert "NOT CHECKED /file-ok file code.c" in out
    assert "UNDISPOSITIONED /group FORWARD_NULL hash.c _Hash_Finalize" in out
    # A valid scope is not news and is not reported by default.
    assert "VALID" not in out
    assert status == 1


def test_cli_state_filter(tmpdir, capsys):
    status = cliinspect(
        ["x", "--config-file",
         _config(tmpdir), "--state=absent"])
    out = capsys.readouterr().out
    # A missing tree yields "not checked" for every file scope, so the only
    # absent scope is the finding which the analysis no longer reports.
    assert "ABSENT /finding-absent finding coverity RESOURCE_LEAK" in out
    assert "NOT CHECKED" not in out
    # Filtering the report does not change the gate.
    assert status == 1


def test_cli_renew(tmpdir, capsys):
    output = os.path.join(tmpdir, "renewed.yml")
    status = cliinspect([
        "x", "--config-file",
        _config(tmpdir), "--renew=/finding-ok", f"--output={output}"
    ])
    assert status == 0
    assert f"wrote {output}" in capsys.readouterr().out
    data = load_data(output)
    assert data["type"] == "inspection"
    # The links which are not inspected scopes are carried over.
    roles = sorted(link["role"] for link in data["links"])
    assert roles == ["inspected", "inspection-member", "supersedes"]


def test_cli_renew_needs_output(tmpdir, capsys):
    # Writing a new evidence item to a guessed path would silently clobber
    # the previous renew, so the destination is explicit.
    status = cliinspect(
        ["x", "--config-file",
         _config(tmpdir), "--renew=/finding-ok"])
    assert status == 1
    assert "--renew needs an --output file" in capsys.readouterr().err


def test_cli_renew_unknown_uid(tmpdir, capsys):
    status = cliinspect([
        "x", "--config-file",
        _config(tmpdir), "--renew=/nope", "--output=/dev/null"
    ])
    assert status == 1
    assert "there is no item /nope" in capsys.readouterr().err
