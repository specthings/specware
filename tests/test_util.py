# SPDX-License-Identifier: BSD-2-Clause
""" Tests for the util module. """

# Copyright (C) 2020, 2025 embedded brains GmbH & Co. KG
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

import contextlib
import logging
from pathlib import Path
import pytest
import subprocess

from specware import load_specware_config, run_command
import specware

from .util import get_and_clear_log


def test_load_specware_config(tmpdir):
    match = ("^cannot find file specware.yml "
             "in the current directory or its parent directories$")
    with pytest.raises(FileNotFoundError, match=match):
        load_specware_config(None)
    config_file = Path(tmpdir) / "specware.yml"
    with open(config_file, "wb") as out:
        out.write(b"foo:\n  bar\n")
    with contextlib.chdir(tmpdir):
        config, working_directory = load_specware_config(None)
    assert config == {"foo": "bar"}
    assert working_directory == tmpdir
    with contextlib.chdir(tmpdir):
        config, working_directory = load_specware_config(str(config_file))
    assert config == {"foo": "bar"}
    assert working_directory == tmpdir
    directory = Path(tmpdir) / "dir"
    directory.mkdir()
    with contextlib.chdir(directory):
        config, working_directory = load_specware_config(None)
    assert config == {"foo": "bar"}
    assert working_directory == tmpdir


def test_run(caplog, monkeypatch):
    lines = [b"2\r", b"1\n"]
    poll_data = [4, None, 3]

    class _Stdout:

        def readline(self):
            try:
                return lines.pop()
            except IndexError:
                return ""

    class _Process:

        def __init__(self):
            self.stdout = _Stdout()

        def poll(self):
            return poll_data.pop()

        def wait(self):
            return 42

    @contextlib.contextmanager
    def _Popen(cmd, stdin, stdout, stderr, cwd, env):
        assert cmd == ["cmd", "arg"]
        assert stdin == subprocess.PIPE
        assert stdout == subprocess.PIPE
        assert stderr == subprocess.STDOUT
        assert cwd == "cwd"
        assert env == {"env": 123}
        yield _Process()

    monkeypatch.setattr(specware.util.subprocess, "Popen", _Popen)
    caplog.set_level(logging.DEBUG)
    stdout = []
    status = run_command(["cmd", "arg"], "cwd", stdout, {"env": 123})
    assert status == 42
    assert stdout == ["1", "2"]
    assert get_and_clear_log(caplog) == """INFO run in 'cwd': 'cmd' 'arg'
DEBUG 1
DEBUG 2"""
    lines.append(b"x")
    status = run_command(["cmd", "arg"], "cwd", None, {"env": 123})
    assert status == 42
