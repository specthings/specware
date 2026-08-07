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
import contextlib
import logging
import os
import subprocess
import sys
from typing import Optional

from specitems import (ClangFormatter, Content, DocumentGlossaryConfig,
                       GlossaryConfig, ItemCache, ItemCacheConfig,
                       MarkdownContent, MarkdownMapper, SpecDocumentConfig,
                       SphinxContent, SphinxMapper, augment_glossary_terms,
                       create_config, generate_glossary,
                       generate_specification_documentation, item_is_enabled,
                       monitor_logging)

from specware import (
    ClangFormatError, MarkdownInterfaceMapper, SpecWareTypeProvider,
    SphinxInterfaceMapper, add_clang_format_arguments, create_clang_formatter,
    generate_application_configuration, generate_interface_documentation,
    gather_referencing_items, generate_interfaces, generate_validation,
    get_affected_header_files, get_affected_targets,
    is_application_configuration_affected, load_specware_config,
    log_clang_format_failure)

_DOC_FORMAT = {
    "myst": (MarkdownContent, MarkdownMapper, MarkdownInterfaceMapper),
    "rest": (SphinxContent, SphinxMapper, SphinxInterfaceMapper)
}


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


def _generate_selected(item_cache: ItemCache, config: dict,
                       args: argparse.Namespace,
                       formatter: Optional[ClangFormatter],
                       uids: set[str]) -> None:
    if args.no_code:
        return
    create_content, _, create_interface_mapper = _DOC_FORMAT[args.format]
    group_uids = [
        doc["group"] for doc in config["interface-documentation"]["groups"]
    ]
    if not args.no_interface_code:
        header_file_uids = get_affected_header_files(item_cache, uids)
        if header_file_uids:
            generate_interfaces(config["interface"], item_cache, formatter,
                                header_file_uids)
    if not args.no_application_configuration_code:
        if is_application_configuration_affected(config["appl-config"],
                                                 item_cache, uids):
            generate_application_configuration(config["appl-config"],
                                               group_uids,
                                               item_cache,
                                               create_interface_mapper,
                                               create_content,
                                               formatter,
                                               write_documentation=False)


def _generate_validation(item_cache: ItemCache, config: dict,
                         args: argparse.Namespace,
                         formatter: Optional[ClangFormatter],
                         working_directory: str, target_files: list[str],
                         uids: set[str]) -> None:
    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-positional-arguments
    config_validation = config["validation"]
    for mapping in config_validation["base-directory-map"]:
        for key, value in mapping.items():
            mapping[key] = os.path.normpath(
                os.path.join(working_directory, value))
    if not args.targets:
        generate_validation(config_validation, item_cache, None, formatter)
        return
    targets = list(target_files)
    if uids:
        targets.extend(sorted(get_affected_targets(item_cache, uids)))
    # An empty target list makes generate_validation() generate all test
    # source files.  Generate nothing if a selection was made which is
    # associated with no test source file at all.
    if targets:
        generate_validation(config_validation, item_cache, targets, formatter)


def _generate_more(item_cache: ItemCache, config: dict,
                   args: argparse.Namespace,
                   formatter: Optional[ClangFormatter]) -> None:
    create_content, create_mapper, create_interface_mapper = _DOC_FORMAT[
        args.format]
    group_uids = [
        doc["group"] for doc in config["interface-documentation"]["groups"]
    ]
    if not args.no_code:
        if not args.no_interface_code:
            generate_interfaces(config["interface"], item_cache, formatter)
        if not args.no_application_configuration_code:
            generate_application_configuration(config["appl-config"],
                                               group_uids, item_cache,
                                               create_interface_mapper,
                                               create_content, formatter)
    if not args.no_documentation:
        some_item = next(iter(item_cache.values()))
        mapper = create_mapper(some_item)
        content = create_content()
        spec_doc_config = create_config(config["spec-documentation"],
                                        SpecDocumentConfig)
        spec_doc_config.add_get_spec_name(mapper, content)
        generate_specification_documentation(content, spec_doc_config, mapper)
        glossary_documents = config["glossary"].pop("documents")
        glossary_config = create_config(config["glossary"], GlossaryConfig)
        for document in glossary_documents:
            glossary_config.documents.append(
                create_config(document, DocumentGlossaryConfig))
        generate_glossary(glossary_config, item_cache,
                          create_interface_mapper(some_item, group_uids),
                          create_content)
        generate_interface_documentation(config["interface-documentation"],
                                         item_cache, create_interface_mapper,
                                         create_content)


def _export(args: argparse.Namespace, formatter: Optional[ClangFormatter],
            invocation_directory: str) -> None:
    config, working_directory = load_specware_config(args.config_file)
    Content.AUTOMATICALLY_GENERATED_WARNING = config.get(
        "automatically-generated-warning",
        Content.AUTOMATICALLY_GENERATED_WARNING)
    target_files, item_files = _split_targets(args.targets,
                                              invocation_directory)
    with contextlib.chdir(working_directory):
        item_cache = ItemCache(create_config(config["spec"], ItemCacheConfig),
                               type_provider=SpecWareTypeProvider({}),
                               is_item_enabled=item_is_enabled)
        for uid in config["glossary"]["project-groups"]:
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
            _generate_validation(item_cache, config, args, formatter,
                                 working_directory, target_files, uids)

        if not args.targets:
            _generate_more(item_cache, config, args, formatter)
        elif uids:
            _generate_selected(item_cache, config, args, formatter, uids)


def cliexport(argv: list[str] = sys.argv):
    """
    Export the specification to the target source and documentation files.
    """
    args = _parse_args(argv)
    invocation_directory = os.getcwd()
    with monitor_logging() as monitor:
        try:
            _export(args, create_clang_formatter(args), invocation_directory)
        except ClangFormatError as err:
            logging.error("%s", err)
        except subprocess.CalledProcessError as err:
            log_clang_format_failure(err)
        return monitor.get_status().exit_code()
