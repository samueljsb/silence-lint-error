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
import os  # noqa: ABC1
import json  # additional comment
import glob  # noqa: F401
""")

    ret = main(('ruff', 'F401', str(python_module)))

    assert ret == 1
    assert python_module.read_text() == """\
import sys  # noqa: F401
import os  # noqa: F401,ABC1
import json  # additional comment  # noqa: F401
import glob  # noqa: F401
"""

    captured = capsys.readouterr()
    assert captured.out == f"""\
{python_module}
"""
    assert captured.err == """\
-> finding errors with ruff
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

    ret = main(('ruff', 'F401', str(python_module)))

    assert ret == 0
    assert python_module.read_text() == src

    captured = capsys.readouterr()
    assert captured.out == ''
    assert captured.err == """\
-> finding errors with ruff
no errors found
"""


def test_not_installed(capsys: pytest.CaptureFixture[str]):
    with FakeProcess() as process:
        process.register(
            (sys.executable, '-mruff', process.any()),
            returncode=1, stderr='/path/to/python3: No module named ruff\n',
        )

        ret = main(('ruff', 'F401', 'path/to/file.py'))

    assert ret == 1

    captured = capsys.readouterr()
    assert captured.out == ''
    assert captured.err == """\
-> finding errors with ruff
ERROR: /path/to/python3: No module named ruff
"""
