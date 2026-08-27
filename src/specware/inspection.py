# SPDX-License-Identifier: BSD-2-Clause
""" Provides the inspection scope checks. """

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

import enum
import os
from dataclasses import dataclass
from typing import Iterable, Iterator

from specitems import Item, data_digest, hash_file, hash_file_lines

#: The item data keys which are not covered by the digest of an item scope.
#:
#: A copyright year bump is not a technical change and must not invalidate an
#: inspection.
ITEM_DIGEST_EXCLUDED_KEYS = ("SPDX-License-Identifier", "copyrights")

_INSPECTION_TYPE = "inspection"
_GROUP_TYPE = "inspection-group"


class State(enum.Enum):
    """ This class represents the state of an inspected scope. """

    VALID = "valid"
    STALE = "stale"
    ABSENT = "absent"
    NOT_BASELINED = "not baselined"
    NOT_CHECKED = "not checked"
    UNDISPOSITIONED = "undispositioned"

    @property
    def fails(self) -> bool:
        """ Return true if the state fails the gate. """
        return self in _FAILING_STATES


#: A stale scope is a judgement about content which changed.  An
#: undispositioned finding defeats the purpose of a group.  Both fail.
#:
#: An absent scope means the inspected artefact is gone, which is usually the
#: good outcome of a corrected defect.  A scope which is not baselined or not
#: checked is honestly reported as such.  None of them fail.
_FAILING_STATES = frozenset([State.STALE, State.UNDISPOSITIONED])


@dataclass(frozen=True)
class Result:
    """ This class represents the check result of one inspected scope. """

    uid: str
    state: State
    scope: str
    detail: str

    def __str__(self) -> str:
        return f"{self.state.value.upper()} {self.uid} {self.scope}" \
            f": {self.detail}"


def item_digest(item: Item) -> str:
    """ Return the digest of the item covered by an item scope. """
    data = {
        key: value
        for key, value in item.data.items()
        if key not in ITEM_DIGEST_EXCLUDED_KEYS
    }
    return data_digest(data)


def _ranges(scope: dict) -> list[tuple[int, int]]:
    return [(int(begin), int(last)) for begin, last in scope["ranges"]]


def _file_digest(path: str, scope: dict) -> str:
    if scope["ranges"] is None:
        return hash_file(path)
    return hash_file_lines(path, _ranges(scope))


def _scope_name(scope: dict) -> str:
    kind = scope["scope"]
    if kind == "file":
        if scope["ranges"] is None:
            return f"file {scope['file']}"
        ranges = ",".join(f"{begin}:{last}" for begin, last in _ranges(scope))
        return f"file {scope['file']} lines {ranges}"
    if kind == "finding":
        return f"finding {scope['tool']} {scope['checker']} " \
            f"{scope['file']} {scope['function']}"
    return "item"


def _finding_key(record: dict) -> tuple[str, str, str]:
    return (str(record["checker"]), str(record["file"]),
            str(record["function"]))


def _finding_digest(record: dict) -> str:
    return data_digest({
        "checker": record["checker"],
        "file": record["file"],
        "function": record["function"],
    })


def _actual_digest(scope: dict, target: Item,
                   findings: dict[tuple[str, str, str], dict]) -> str | None:
    """
    Return the digest of the inspected content, or None if it is absent.
    """
    kind = scope["scope"]
    if kind == "item":
        return item_digest(target)
    if kind == "finding":
        record = findings.get(_finding_key(scope))
        if record is None:
            return None
        return _finding_digest(record)
    path = os.path.join(target["directory"], scope["file"])
    if not os.path.isfile(path):
        return None
    return _file_digest(path, scope)


def _is_reachable(scope: dict, target: Item) -> bool:
    if scope["scope"] != "file":
        return True
    directory = target.get("directory")
    return isinstance(directory, str) and os.path.isdir(directory)


def _check_scope(item: Item, scope: dict, target: Item,
                 findings: dict[tuple[str, str, str], dict]) -> Result:
    name = _scope_name(scope)
    if not _is_reachable(scope, target):
        return Result(item.uid, State.NOT_CHECKED, name,
                      f"the directory of {target.uid} is not present")
    expected = scope["hash"]
    if expected is None:
        return Result(item.uid, State.NOT_BASELINED, name,
                      "no digest is recorded")
    actual = _actual_digest(scope, target, findings)
    if actual is None:
        return Result(item.uid, State.ABSENT, name,
                      "the inspected content no longer exists")
    if actual != expected:
        return Result(item.uid, State.STALE, name,
                      f"expected {expected} but got {actual}")
    return Result(item.uid, State.VALID, name, "the digest matches")


def _findings_of(target: Item) -> dict[tuple[str, str, str], dict]:
    records = target.get("findings-list")
    if not isinstance(records, list):
        return {}
    return {_finding_key(record): record for record in records}


def is_superseded(item: Item) -> bool:
    """
    Return true if a newer inspection supersedes the item.

    A supersedes link is declared by the newer round, so the superseded round
    sees it as an incoming link.
    """
    return any(item.links_to_children("supersedes"))


def check_inspection(item: Item) -> Iterator[Result]:
    """ Check every scope of the inspection item. """
    for link in item.links_to_parents("inspected"):
        target = link.item
        findings = _findings_of(target)
        for scope in link["scopes"]:
            yield _check_scope(item, scope, target, findings)


def _inspected_finding_keys(group: Item) -> set[tuple[str, str, str]]:
    keys = set()
    for member in group.links_to_children("inspection-member"):
        inspection = member.item
        if is_superseded(inspection):
            continue
        for link in inspection.links_to_parents("inspected"):
            for scope in link["scopes"]:
                if scope["scope"] == "finding":
                    keys.add(_finding_key(scope))
    return keys


def check_group(group: Item) -> Iterator[Result]:
    """ Check that every covered finding is inspected by a member. """
    inspected = _inspected_finding_keys(group)
    for link in group.links_to_parents("covered-analysis"):
        for key in sorted(_findings_of(link.item)):
            if key not in inspected:
                yield Result(
                    group.uid, State.UNDISPOSITIONED, " ".join(key),
                    f"no member inspects this finding of "
                    f"{link.item.uid}")


def _items_of_type(items: Iterable[Item], spec_type: str) -> list[Item]:
    return sorted((item for item in items if item.type == spec_type),
                  key=lambda item: item.uid)


def check(items: Iterable[Item]) -> list[Result]:
    """
    Check every inspection and every inspection group of the items.

    Superseded inspections are historical evidence.  They keep the digests
    they were baselined with and are not checked.
    """
    items = list(items)
    results: list[Result] = []
    for item in _items_of_type(items, _INSPECTION_TYPE):
        if is_superseded(item):
            continue
        results.extend(check_inspection(item))
    for group in _items_of_type(items, _GROUP_TYPE):
        results.extend(check_group(group))
    return results


def renew(item: Item) -> dict:
    """
    Return the data of a new inspection round which supersedes the item.

    The digests are the current ones.  The judgement of the inspectors is
    left unset, so that the new round fails the check until a person fills
    it in.
    """
    links: list[dict] = [{"role": "supersedes", "uid": item.uid}]
    for link in item.links_to_parents("inspected"):
        target = link.item
        findings = _findings_of(target)
        scopes = []
        for scope in link["scopes"]:
            fresh = dict(scope)
            fresh["hash"] = _actual_digest(scope, target, findings)
            scopes.append(fresh)
        links.append({"role": "inspected", "uid": link.uid, "scopes": scopes})
    for link in item.links_to_parents():
        if link.role in ("inspected", "supersedes"):
            continue
        links.append({"role": link.role, "uid": link.uid})
    return {
        "SPDX-License-Identifier": item["SPDX-License-Identifier"],
        "copyrights": item["copyrights"],
        "date": None,
        "enabled-by": item["enabled-by"],
        "findings": None,
        "inspectors": [],
        "links": links,
        "method": None,
        "type": _INSPECTION_TYPE,
        "verdict": None,
    }
