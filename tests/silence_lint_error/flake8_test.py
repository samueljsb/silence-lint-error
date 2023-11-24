from __future__ import annotations

import sys
from pathlib import Path

import pytest
from pytest_subprocess import FakeProcess

from silence_lint_error.silence_lint_error import main


def test_main(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    python_module = tmp_path / 't.py'
    python_module.write_text("""\
import sys
import glob  # noqa: F401
from json import *  # additional comment
from os import *  # noqa: F403
from pathlib import *  # noqa: F403  # additional comment
""")

    ret = main(('flake8', 'F401', str(python_module)))

    assert ret == 1
    assert python_module.read_text() == """\
import sys  # noqa: F401
import glob  # noqa: F401
from json import *  # additional comment  # noqa: F401
from os import *  # noqa: F401,F403
from pathlib import *  # noqa: F401,F403  # additional comment
"""

    captured = capsys.readouterr()
    assert captured.out == f"""\
{python_module}
"""
    assert captured.err == """\
-> finding errors with flake8
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

    ret = main(('flake8', 'F401', str(python_module)))

    assert ret == 0
    assert python_module.read_text() == src

    captured = capsys.readouterr()
    assert captured.out == ''
    assert captured.err == """\
-> finding errors with flake8
no errors found
"""


def test_not_installed(capsys: pytest.CaptureFixture[str]):
    with FakeProcess() as process:
        process.register(
            (sys.executable, '-mflake8', process.any()),
            returncode=1, stderr='/path/to/python3: No module named flake8\n',
        )

        ret = main(('flake8', 'F401', 'path/to/file.py'))

    assert ret == 1

    captured = capsys.readouterr()
    assert captured.out == ''
    assert captured.err == """\
-> finding errors with flake8
ERROR: /path/to/python3: No module named flake8
"""
