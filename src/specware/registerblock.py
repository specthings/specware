# SPDX-License-Identifier: BSD-2-Clause
""" Provides the placement and the layout of register blocks. """

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

from typing import Any, NamedTuple, Optional

from specitems import Item, Link

__all__ = [
    "RegisterBlockLayout", "RegisterBlockPart", "get_group_members",
    "get_interface_container", "get_interface_groups", "get_interface_members",
    "get_register_block_base", "get_register_block_group",
    "get_register_block_host_of_domain", "get_register_block_hosts",
    "get_register_block_identifier", "get_register_block_layout",
    "get_register_block_prefixes"
]


def get_register_block_hosts(item: Item) -> list[Link]:
    """
    Get the links of the header files which host the register block.

    Each link is a link from the header file to the register block, so
    ``link.item`` is the header file.  The links are sorted by the UID of the
    header file.
    """
    return sorted(item.links_to_children("register-block-host"),
                  key=lambda link: link.item.uid)


def get_register_block_host_of_domain(item: Item, domain: Item) -> Link:
    """
    Get the link of the header file of the domain which hosts the register
    block.

    Raises:
        ValueError: No header file or more than one header file of the domain
            hosts the register block.
    """
    hosts = [
        link for link in get_register_block_hosts(item)
        if link.item.parent("interface-placement") == domain
    ]
    if not hosts:
        raise ValueError(f"no header file of domain '{domain.uid}' hosts "
                         f"register block '{item.uid}'")
    if len(hosts) > 1:
        raise ValueError(f"more than one header file of domain "
                         f"'{domain.uid}' hosts register block '{item.uid}': "
                         f"{', '.join(link.item.uid for link in hosts)}")
    return hosts[0]


def get_interface_members(item: Item) -> list[Item]:
    """
    Get the interfaces which the interface container places.

    These are the children of the ``interface-placement`` links and the
    register blocks of the ``register-block-host`` links of the container.
    """
    return list(item.children("interface-placement")) + list(
        item.parents("register-block-host"))


def get_interface_groups(item: Item) -> list[Item]:
    """
    Get the interface groups of the interface.

    These are the parents of the ``interface-ingroup`` links of the interface
    and the groups which link to the interface through the
    ``interface-group-member`` role.

    Raises:
        ValueError: A group links to an interface which is no register block.
    """
    members = list(item.children("interface-group-member"))
    if members and item.type != "interface/register-block":
        raise ValueError(f"group '{members[0].uid}' has the member "
                         f"'{item.uid}' which is no register block")
    groups = dict(
        (group.uid, group) for group in item.parents("interface-ingroup"))
    groups.update((group.uid, group) for group in members)
    return list(groups.values())


def get_group_members(item: Item) -> list[Item]:
    """
    Get the members of the interface group.

    These are the children of the ``interface-ingroup`` links of the group
    and the parents of its ``interface-group-member`` links.
    """
    return list(item.children("interface-ingroup")) + list(
        item.parents("interface-group-member"))


def get_interface_container(item: Item) -> Item:
    """
    Get the interface container of the interface.

    The container is the parent of the ``interface-placement`` link.  A
    register block without such a link resides in the first header file which
    hosts it.

    Raises:
        IndexError: The interface resides in no container.
    """
    try:
        return item.parent("interface-placement")
    except IndexError:
        hosts = get_register_block_hosts(item)
        if not hosts:
            raise
        return hosts[0].item


def _get_block_value(item: Item, host: Optional[Link], key: str) -> Any:
    if host is not None:
        value = host.data.get(key, None)
        if value is not None:
            return value
    else:
        values = set(link.data[key] for link in get_register_block_hosts(item)
                     if link.data.get(key, None) is not None)
        if len(values) > 1:
            raise ValueError(f"the header files which host register block "
                             f"'{item.uid}' state different values for "
                             f"'{key}': {', '.join(sorted(values))}")
        if values:
            return values.pop()
    value = item.get(key, None)
    if value is None:
        raise ValueError(f"register block '{item.uid}' has no '{key}' and no "
                         "host link states one")
    return value


def get_register_block_identifier(item: Item,
                                  host: Optional[Link] = None) -> str:
    """
    Get the interface group identifier of the register block.

    The value of the host link takes precedence over the value of the block.
    Without a host link, the value of the host links of the block takes
    precedence.
    """
    return _get_block_value(item, host, "identifier")


def get_register_block_group(item: Item, host: Optional[Link] = None) -> str:
    """
    Get the interface group name of the register block.

    The value of the host link takes precedence over the value of the block.
    Without a host link, the value of the host links of the block takes
    precedence.
    """
    return _get_block_value(item, host, "register-block-group")


def get_register_block_prefixes(item: Item,
                                host: Optional[Link] = None
                                ) -> tuple[str, str]:
    """
    Get the register prefix and the offset prefix of the register block.

    The prefix of the host link replaces both prefixes of the block.  A
    missing prefix of the block is the name of the block.
    """
    if host is not None:
        prefix = host.data.get("prefix", None)
        if prefix is not None:
            return prefix, prefix
    register_prefix = item["register-prefix"]
    if register_prefix is None:
        register_prefix = item["name"]
    offset_prefix = item.get("offset-prefix", None)
    if offset_prefix is None:
        offset_prefix = item["name"]
    return register_prefix, offset_prefix


def get_register_block_base(item: Item) -> Optional[Item]:
    """
    Get the base of the register block.

    Raises:
        ValueError: The block has more than one base.
    """
    bases = list(item.parents("register-block-base"))
    if len(bases) > 1:
        raise ValueError(f"register block '{item.uid}' has more than one "
                         "base")
    return bases[0] if bases else None


class RegisterBlockPart(NamedTuple):
    """
    Is a register, a member or an include link of a register block layout.
    """
    item: Item
    prefix: str
    data: Any


class RegisterBlockLayout(NamedTuple):
    """
    Is the layout of a register block which includes the parts of its bases.
    """
    registers: list[RegisterBlockPart]
    definition: list[RegisterBlockPart]
    includes: list[RegisterBlockPart]


def _own_layout(item: Item) -> RegisterBlockLayout:
    return RegisterBlockLayout([
        RegisterBlockPart(item, f"registers[{index}]", register)
        for index, register in enumerate(item["registers"])
    ], [
        RegisterBlockPart(item, f"definition[{index}]", member)
        for index, member in enumerate(item["definition"])
    ], [
        RegisterBlockPart(item, "", link)
        for link in item.links_to_parents("register-block-include")
    ])


def _derive_layout(item: Item, base: RegisterBlockLayout,
                   own: RegisterBlockLayout) -> RegisterBlockLayout:
    include_names = set(part.data["name"] for part in base.includes)
    for part in own.includes:
        name = part.data["name"]
        if name in include_names or any(part_2.data["name"] == name
                                        for part_2 in base.registers):
            raise ValueError(f"register block '{item.uid}' includes a "
                             f"register block named '{name}' which its base "
                             "defines")
    registers = list(base.registers)
    for part in own.registers:
        name = part.data["name"]
        if name in include_names:
            raise ValueError(f"register '{name}' of register block "
                             f"'{item.uid}' has the name of a register block "
                             "which its base includes")
        for index, part_2 in enumerate(registers):
            if part_2.data["name"] == name:
                registers[index] = part
                break
        else:
            registers.append(part)
    members = dict((part.data["offset"], part) for part in base.definition)
    members.update((part.data["offset"], part) for part in own.definition)
    return RegisterBlockLayout(registers,
                               [members[offset] for offset in sorted(members)],
                               base.includes + own.includes)


def _get_layout(item: Item, visited: set[str]) -> RegisterBlockLayout:
    if item.uid in visited:
        raise ValueError(f"register block '{item.uid}' is its own base")
    visited.add(item.uid)
    own = _own_layout(item)
    base = get_register_block_base(item)
    if base is None:
        return own
    return _derive_layout(item, _get_layout(base, visited), own)


def get_register_block_layout(item: Item) -> RegisterBlockLayout:
    """
    Get the layout of the register block.

    A derivative starts with the layout of its base.  A register of the name
    of a base register replaces the base register.  A member at the offset of
    a base member replaces the base member.  The derivative adds its other
    registers, members and includes.
    """
    return _get_layout(item, set())
