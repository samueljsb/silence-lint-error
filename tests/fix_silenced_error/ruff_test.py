from __future__ import annotations

from pathlib import Path

import pytest

from silence_lint_error.fix_silenced_error import main


def test_main(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    src = """\
import math
import os  # noqa: F401
import sys

print(math.pi, file=sys.stderr)
"""

    python_module = tmp_path / 't.py'
    python_module.write_text(src)

    ret = main(('ruff', 'F401', str(python_module)))

    assert ret == 0
    assert python_module.read_text() == """\
import math
import sys

print(math.pi, file=sys.stderr)
"""

    captured = capsys.readouterr()
    assert captured.out == f"""\
{python_module}
"""
    assert captured.err == """\
-> removing comments that silence errors
-> applying auto-fixes with ruff
Found 1 error (1 fixed, 0 remaining).
"""


def test_main_no_violations(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    src = """\
import math
import sys

print(math.pi, file=sys.stderr)
"""

    python_module = tmp_path / 't.py'
    python_module.write_text(src)

    ret = main(('ruff', 'F401', str(python_module)))

    assert ret == 0
    assert python_module.read_text() == src

    captured = capsys.readouterr()
    assert captured.out == ''
    assert captured.err == """\
-> removing comments that silence errors
no silenced errors found
"""
