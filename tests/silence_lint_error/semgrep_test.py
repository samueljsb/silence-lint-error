from __future__ import annotations

import os
from pathlib import Path
from unittest import mock

import pytest
from pytest_subprocess import FakeProcess

from silence_lint_error.silence_lint_error import main


def test_main(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    python_module = tmp_path / 't.py'
    python_module.write_text(
        """\
import time

time.sleep(5)

# a different error (open-never-closed)
fd = open('foo')
""",
    )

    with mock.patch.dict(os.environ, {'SEMGREP_RULES': 'r/python'}):
        ret = main(
            (
                'semgrep',
                'python.lang.best-practice.sleep.arbitrary-sleep',
                str(python_module),
            ),
        )

    assert ret == 1
    assert python_module.read_text() == """\
import time

# nosemgrep: python.lang.best-practice.sleep.arbitrary-sleep
time.sleep(5)

# a different error (open-never-closed)
fd = open('foo')
"""

    captured = capsys.readouterr()
    assert captured.out == f"""\
{python_module}
"""
    assert captured.err == """\
-> finding errors with semgrep
found errors in 1 files
-> adding comments to silence errors
"""


def test_main_no_violations(
        tmp_path: Path, capsys: pytest.CaptureFixture[str],
):
    src = """\
def foo():
    print('hello there')
"""

    python_module = tmp_path / 't.py'
    python_module.write_text(src)

    with mock.patch.dict(os.environ, {'SEMGREP_RULES': 'r/python'}):
        ret = main(
            (
                'semgrep',
                'python.lang.best-practice.sleep.arbitrary-sleep',
                str(python_module),
            ),
        )

    assert ret == 0
    assert python_module.read_text() == src

    captured = capsys.readouterr()
    assert captured.out == ''
    assert captured.err == """\
-> finding errors with semgrep
no errors found
"""


def test_not_installed(capsys: pytest.CaptureFixture[str]):
    with FakeProcess() as process:
        process.register(
            ('semgrep', process.any()),
            returncode=1, stderr='zsh: command not found: semgrep\n',
        )

        ret = main(('semgrep', 'semgrep.rule', 'path/to/file.py'))

    assert ret == 1

    captured = capsys.readouterr()
    assert captured.out == ''
    assert captured.err == """\
-> finding errors with semgrep
ERROR: zsh: command not found: semgrep
"""
