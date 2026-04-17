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
import os
import sys

from specitems import (Content, DocumentGlossaryConfig, GlossaryConfig,
                       ItemCache, ItemCacheConfig, MarkdownContent,
                       MarkdownMapper, SpecDocumentConfig, SphinxContent,
                       SphinxMapper, augment_glossary_terms, create_config,
                       generate_glossary, generate_specification_documentation,
                       item_is_enabled)

from specware import (MarkdownInterfaceMapper, SpecWareTypeProvider,
                      SphinxInterfaceMapper,
                      generate_application_configuration,
                      generate_interface_documentation, generate_interfaces,
                      generate_validation, load_specware_config)

_DOC_FORMAT = {
    "markdown": (MarkdownContent, MarkdownMapper, MarkdownInterfaceMapper),
    "rest": (SphinxContent, SphinxMapper, SphinxInterfaceMapper)
}


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config-file",
                        type=str,
                        default=None,
                        help="use this configuration file")
    parser.add_argument("--format",
                        choices=["markdown", "rest"],
                        type=str.lower,
                        default="markdown",
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
    parser.add_argument("targets",
                        metavar="TARGET",
                        nargs="*",
                        help="a target file of a specification item")
    return parser.parse_args(argv[1:])


def _generate_more(item_cache: ItemCache, config: dict,
                   args: argparse.Namespace) -> None:
    create_content, create_mapper, create_interface_mapper = _DOC_FORMAT[
        args.format]
    group_uids = [
        doc["group"] for doc in config["interface-documentation"]["groups"]
    ]
    if not args.no_code:
        if not args.no_interface_code:
            generate_interfaces(config["interface"], item_cache)
        if not args.no_application_configuration_code:
            generate_application_configuration(config["appl-config"],
                                               group_uids, item_cache,
                                               create_interface_mapper,
                                               create_content)
    if not args.no_documentation:
        some_item = next(iter(item_cache.values()))
        generate_specification_documentation(
            create_config(config["spec-documentation"], SpecDocumentConfig),
            item_cache, create_mapper(some_item), create_content)
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


def cliexport(argv: list[str] = sys.argv):
    """ Export the specification to source and documentation files. """
    args = _parse_args(argv)
    config, working_directory = load_specware_config(args.config_file)
    Content.AUTOMATICALLY_GENERATED_WARNING = config.get(
        "automatically-generated-warning",
        Content.AUTOMATICALLY_GENERATED_WARNING)
    with contextlib.chdir(working_directory):
        item_cache = ItemCache(create_config(config["spec"], ItemCacheConfig),
                               type_provider=SpecWareTypeProvider({}),
                               is_item_enabled=item_is_enabled)
        for uid in config["glossary"]["project-groups"]:
            group = item_cache[uid]
            assert group.type == "glossary/group"
            augment_glossary_terms(group, [])

        if not args.no_code and not args.no_validation_code:
            config_validation = config["validation"]
            for mapping in config_validation["base-directory-map"]:
                for key, value in mapping.items():
                    mapping[key] = os.path.normpath(
                        os.path.join(working_directory, value))
            generate_validation(config_validation, item_cache, args.targets)

        if not args.targets:
            _generate_more(item_cache, config, args)
