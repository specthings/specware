# SPDX-License-Identifier: BSD-2-Clause
""" Provides utility methods. """

# Copyright (C) 2020, 2023 embedded brains GmbH & Co. KG
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

import logging
import os
from pathlib import Path
import subprocess
from typing import Optional, Union

from specitems import (ItemDataByUID, load_config, pickle_load_data_by_uid,
                       SpecTypeProvider)


class SpecWareTypeProvider(SpecTypeProvider):
    """ This class provides a type system for specification ware items. """

    def __init__(self, data_by_uid: ItemDataByUID) -> None:
        data_by_uid.update(
            pickle_load_data_by_uid(
                os.path.join(os.path.dirname(__file__), "spec.pickle")))
        super().__init__(data_by_uid)


def load_specware_config(config_file: str | None) -> tuple[dict, str]:
    """
    Load the specware configuration file and determines the working
    directory.
    """
    if config_file is None:
        base = Path(".").absolute()
        while True:
            path = base / "specware.yml"
            if path.is_file():
                break
            next_base = base.parent
            if next_base == base:
                raise FileNotFoundError(
                    "cannot find file specware.yml "
                    "in the current directory or its parent directories")
            base = next_base
    else:
        path = Path(config_file)
    return load_config(str(path)), str(path.parent.absolute())


def run_command(args: list[str],
                cwd: Union[str, Path] = ".",
                stdout: Optional[list[str]] = None,
                env=None,
                status: Optional[int] = None) -> int:
    """
    Run the command in a subprocess in the working directory and environment.

    Optionally, the standard output of the subprocess is returned.  Returns the
    exit status of the subprocess.
    """
    logging.info("run in '%s': %s", cwd, " ".join(f"'{arg}'" for arg in args))
    with subprocess.Popen(args,
                          stdin=subprocess.PIPE,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT,
                          cwd=cwd,
                          env=env) as task:
        assert task.stdout is not None
        if stdout is None:
            stdout = []
        while True:
            raw_line = task.stdout.readline()
            if raw_line:
                line = raw_line.decode("utf-8", "ignore").rstrip("\r\n")
                logging.debug("%s", line)
                stdout.append(line)
            elif task.poll() is not None:
                break
        actual_status = task.wait()
        if status is not None and actual_status != status:
            raise RuntimeError(
                f"in '{cwd}' command '{' '.join(args)}' returned "
                f"unexpected status {actual_status} with output: {stdout}")
        return actual_status
