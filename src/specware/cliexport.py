# SPDX-License-Identifier: BSD-2-Clause
"""
Provides a command line interface to export the specification to source and
documentation files.
"""

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

import argparse
import functools
import logging
import os
import sys
from typing import Any, Optional

from specitems import (ClangFormatter, ContentContext, DocumentGlossaryConfig,
                       GlossaryConfig, Item, ItemCache, LicenseProvider,
                       MarkdownContent, MarkdownMapper, SpecDocumentConfig,
                       SphinxContent, SphinxMapper, augment_glossary_terms,
                       check_license_items, create_config,
                       create_content_context, generate_glossary,
                       generate_specification_documentation, item_is_enabled,
                       yield_tasks)

from specware import (
    run_with_clang_formatter, open_tree, MarkdownInterfaceMapper,
    SphinxInterfaceMapper, add_clang_format_arguments,
    generate_application_configuration, generate_interface_documentation,
    gather_referencing_items, generate_interfaces, generate_validation,
    get_affected_header_files, get_affected_targets,
    is_application_configuration_affected)

_DOC_FORMAT = {
    "myst": (MarkdownContent, MarkdownMapper, MarkdownInterfaceMapper),
    "rest": (SphinxContent, SphinxMapper, SphinxInterfaceMapper)
}


def _bind_context(fmt: str, context: ContentContext) -> tuple[Any, Any, Any]:
    """
    Bind the context to the content and mapper constructors of the format.

    Args:
        fmt: The documentation format.
        context: The content context of a task.

    Returns:
        The content constructor, the mapper constructor and the interface
        mapper constructor.  Every content which the content constructor
        creates is a work of its own.
    """
    create_content, create_mapper, create_interface_mapper = _DOC_FORMAT[fmt]

    def _create_content(*args: Any, **kwargs: Any) -> Any:
        return create_content(*args,
                              context=context.for_work(context.licenses.name),
                              **kwargs)

    return (_create_content, functools.partial(create_mapper, context=context),
            functools.partial(create_interface_mapper, context=context))


#: The keys of a task which its configuration object takes not.
_TASK_KEYS = ("task-name", "task-type", "params", "license",
              "accepted-licenses", "automatically-generated-warning")


def _task_config(task: dict) -> dict:
    """ Get the settings of the task without the keys of every task. """
    return {key: value for key, value in task.items() if key not in _TASK_KEYS}


def _generate_appl_config(task: dict, group_uids: list[str],
                          item_cache: ItemCache, args: argparse.Namespace,
                          provider: LicenseProvider,
                          formatter: Optional[ClangFormatter],
                          write_documentation: bool) -> None:
    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-positional-arguments
    # The task produces a Doxygen source and documentation sources, and each
    # kind states its own license.
    create_content, _, create_interface_mapper = _bind_context(
        args.format, create_content_context(task, provider, "documentation-"))
    generate_application_configuration(task,
                                       group_uids,
                                       item_cache,
                                       create_interface_mapper,
                                       create_content,
                                       create_content_context(
                                           task, provider, "doxygen-"),
                                       formatter,
                                       write_documentation=write_documentation)


def _get_group_uids(config: Item) -> list[str]:
    return [
        doc["group"] for task in yield_tasks(config, "interface-documentation")
        for doc in task["groups"]
    ]


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=cliexport.__doc__)
    parser.add_argument("--config-file",
                        type=str,
                        default=None,
                        help="use this configuration file")
    parser.add_argument("--format",
                        choices=["myst", "rest"],
                        type=str.lower,
                        default="myst",
                        help="the output format of documentation files")
    parser.add_argument("--no-application-configuration-code",
                        action="store_true",
                        help="do not generate application configuration code")
    parser.add_argument("--no-code",
                        action="store_true",
                        help="do not generate source code")
    parser.add_argument("--no-documentation",
                        action="store_true",
                        help="do not generate documentation sources")
    parser.add_argument("--no-interface-code",
                        action="store_true",
                        help="do not generate interface code")
    parser.add_argument("--no-validation-code",
                        action="store_true",
                        help="do not generate validation code")
    add_clang_format_arguments(parser)
    parser.add_argument(
        "targets",
        metavar="TARGET",
        nargs="*",
        help=("a specification item file if it ends with '.yml', otherwise a "
              "target file of a specification item; only the files "
              "associated with the specification items are exported; "
              "documentation files are not exported if a TARGET is present; "
              "it is an error if a specification item file is associated "
              "with no item, for example if the file was removed, run the "
              "command with no TARGET to export all files in this case"))
    return parser.parse_args(argv[1:])


def _split_targets(targets: list[str],
                   invocation_directory: str) -> tuple[list[str], list[str]]:
    """
    Split the targets into the target files and the specification item files.

    The specification item files are made absolute with respect to the
    directory in which the command was invoked.
    """
    target_files: list[str] = []
    item_files: list[str] = []
    for target in targets:
        if os.path.splitext(target)[1] == ".yml":
            item_files.append(
                os.path.abspath(os.path.join(invocation_directory, target)))
        else:
            target_files.append(target)
    return target_files, item_files


def _resolve_item_files(item_cache: ItemCache,
                        item_files: list[str]) -> Optional[set[str]]:
    """
    Resolve the specification item files to the UIDs of the corresponding
    items.

    Return None if a file is associated with no item.  Several files may
    denote the same item, so the count of the UIDs tells nothing about the
    success of the resolution.
    """
    uid_by_file = dict((item.file, item.uid) for item in item_cache.values())
    uids: set[str] = set()
    unresolved: list[str] = []
    for item_file in item_files:
        uid = uid_by_file.get(item_file)
        if uid is None:
            unresolved.append(item_file)
        else:
            uids.add(uid)
    if not unresolved:
        return uids
    # The item files are absolute, however, they may denote a symbolic link or
    # the specification may be reached through one.  Resolving the links of
    # every item is expensive, so it is done only if necessary.
    uid_by_file = dict(
        (os.path.realpath(file), uid) for file, uid in uid_by_file.items())
    resolved = True
    for item_file in unresolved:
        uid = uid_by_file.get(os.path.realpath(item_file))
        if uid is None:
            logging.error(
                "no specification item is associated with the file "
                "'%s'", item_file)
            resolved = False
        else:
            uids.add(uid)
    return uids if resolved else None


def _generate_selected(item_cache: ItemCache, config: Item,
                       args: argparse.Namespace, provider: LicenseProvider,
                       formatter: Optional[ClangFormatter],
                       uids: set[str]) -> None:
    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-positional-arguments
    if args.no_code:
        return
    group_uids = _get_group_uids(config)
    if not args.no_interface_code:
        header_file_uids = get_affected_header_files(item_cache, uids)
        if header_file_uids:
            for task in yield_tasks(config, "interface"):
                generate_interfaces(task, item_cache,
                                    create_content_context(task, provider),
                                    formatter, header_file_uids)
    if not args.no_application_configuration_code:
        for task in yield_tasks(config, "appl-config"):
            if not is_application_configuration_affected(
                    task, item_cache, uids):
                continue
            _generate_appl_config(task, group_uids, item_cache, args, provider,
                                  formatter, False)


def _generate_validation(item_cache: ItemCache, config: Item,
                         args: argparse.Namespace, provider: LicenseProvider,
                         formatter: Optional[ClangFormatter],
                         working_directory: str, target_files: list[str],
                         uids: set[str]) -> None:
    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-positional-arguments
    for task in yield_tasks(config, "validation"):
        for mapping in task["base-directory-map"]:
            for key, value in mapping.items():
                mapping[key] = os.path.normpath(
                    os.path.join(working_directory, value))
        context = create_content_context(task, provider)
        if not args.targets:
            generate_validation(task, item_cache, context, None, formatter)
            continue
        targets = list(target_files)
        if uids:
            targets.extend(sorted(get_affected_targets(item_cache, uids)))
        # An empty target list makes generate_validation() generate all test
        # source files.  Generate nothing if a selection was made which is
        # associated with no test source file at all.
        if targets:
            generate_validation(task, item_cache, context, targets, formatter)


def _generate_code(item_cache: ItemCache, config: Item,
                   args: argparse.Namespace, provider: LicenseProvider,
                   formatter: Optional[ClangFormatter]) -> None:
    group_uids = _get_group_uids(config)
    if not args.no_interface_code:
        for task in yield_tasks(config, "interface"):
            generate_interfaces(task, item_cache,
                                create_content_context(task, provider),
                                formatter)
    if args.no_application_configuration_code:
        return
    for task in yield_tasks(config, "appl-config"):
        _generate_appl_config(task, group_uids, item_cache, args, provider,
                              formatter, True)


def _generate_spec_documentation(item_cache: ItemCache, config: Item,
                                 args: argparse.Namespace,
                                 provider: LicenseProvider) -> None:
    some_item = next(iter(item_cache.values()))
    for task in yield_tasks(config, "spec-documentation"):
        context = create_content_context(task, provider)
        create_content, create_mapper, _ = _bind_context(args.format, context)
        mapper = create_mapper(some_item)
        content = create_content()
        spec_doc_config = create_config(_task_config(task), SpecDocumentConfig)
        spec_doc_config.add_get_spec_name(mapper, content)
        generate_specification_documentation(content, spec_doc_config, mapper)


def _generate_documentation(item_cache: ItemCache, config: Item,
                            args: argparse.Namespace,
                            provider: LicenseProvider) -> None:
    some_item = next(iter(item_cache.values()))
    group_uids = _get_group_uids(config)
    _generate_spec_documentation(item_cache, config, args, provider)
    for task in yield_tasks(config, "glossary"):
        context = create_content_context(task, provider)
        create_content, _, create_interface_mapper = _bind_context(
            args.format, context)
        settings = _task_config(task)
        documents = settings.pop("documents", [])
        glossary_config = create_config(settings, GlossaryConfig)
        for document in documents:
            glossary_config.documents.append(
                create_config(document, DocumentGlossaryConfig))
        generate_glossary(glossary_config, item_cache,
                          create_interface_mapper(some_item, group_uids),
                          create_content)
    for task in yield_tasks(config, "interface-documentation"):
        context = create_content_context(task, provider)
        create_content, _, create_interface_mapper = _bind_context(
            args.format, context)
        generate_interface_documentation(task, item_cache,
                                         create_interface_mapper,
                                         create_content)


def _generate_more(item_cache: ItemCache, config: Item,
                   args: argparse.Namespace, provider: LicenseProvider,
                   formatter: Optional[ClangFormatter]) -> None:
    if not args.no_code:
        _generate_code(item_cache, config, args, provider, formatter)
    if not args.no_documentation:
        _generate_documentation(item_cache, config, args, provider)


def _check_interface_domains(config: Item) -> bool:
    tasks_by_domain: dict[str, list[str]] = {}
    for task in yield_tasks(config, "interface"):
        for domain in task["domains"]:
            tasks_by_domain.setdefault(domain, []).append(task["task-name"])
    unique = True
    for domain, names in sorted(tasks_by_domain.items()):
        if len(names) > 1:
            logging.error("the interface tasks %s map the domain %s",
                          ", ".join(names), domain)
            unique = False
    return unique


def _export(args: argparse.Namespace, formatter: Optional[ClangFormatter],
            invocation_directory: str) -> None:
    target_files, item_files = _split_targets(args.targets,
                                              invocation_directory)
    with open_tree(args.config_file,
                   item_is_enabled) as (config, item_cache, working_directory):
        provider = LicenseProvider(item_cache.values())
        check_license_items(config, provider)
        if not _check_interface_domains(config):
            return
        for task in yield_tasks(config, "glossary"):
            for uid in task["project-groups"]:
                group = item_cache[uid]
                assert group.type == "glossary/group"
                augment_glossary_terms(group, [])

        uids: set[str] = set()
        if item_files:
            resolved = _resolve_item_files(item_cache, item_files)
            if resolved is None:
                return
            uids = resolved
        if uids:
            # An item which substitutes an attribute of a changed item
            # generates different content, so it changed as well.
            uids.update(gather_referencing_items(item_cache, uids))

        if not args.no_code and not args.no_validation_code:
            _generate_validation(item_cache, config, args, provider, formatter,
                                 working_directory, target_files, uids)

        if not args.targets:
            _generate_more(item_cache, config, args, provider, formatter)
        elif uids:
            _generate_selected(item_cache, config, args, provider, formatter,
                               uids)


def cliexport(argv: list[str] = sys.argv):
    """
    Export the specification to the target source and documentation files.
    """
    args = _parse_args(argv)
    invocation_directory = os.getcwd()
    return run_with_clang_formatter(
        args, lambda formatter: _export(args, formatter, invocation_directory))
