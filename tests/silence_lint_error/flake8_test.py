from __future__ import annotations

from pathlib import Path

import pytest

from silence_lint_error.silence_lint_error import Flake8
from silence_lint_error.silence_lint_error import main
from silence_lint_error.silence_lint_error import Violation


class TestFlake8:
    def test_add_comments(self):
        src = """\
# a single-line statement on line 2
foo = 'bar'

# a function on line 5
def baz(
    a: int,
    b: int,
) -> str:
    ...

# a multi-line string on line 12
s = '''
hello there
'''
"""

        assert Flake8().silence_violations(
            src,
            [
                Violation('ABC123', 2),
                Violation('ABC123', 5),
                Violation('ABC123', 12),
            ],
        ) == """\
# a single-line statement on line 2
foo = 'bar'  # noqa: ABC123

# a function on line 5
def baz(  # noqa: ABC123
    a: int,
    b: int,
) -> str:
    ...

# a multi-line string on line 12
s = '''
hello there
'''  # noqa: ABC123
"""


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
