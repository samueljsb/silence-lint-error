from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest import mock

import pytest
from pytest_subprocess import FakeProcess

from silence_lint_error.cli.silence_lint_error import main


class TestFixit:
    def test_main(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]):
        python_module = tmp_path / 't.py'
        python_module.write_text(
            """\
x = None
isinstance(x, str) or isinstance(x, int)

def f(x):
    return isinstance(x, str) or isinstance(x, int)
""",
        )

        ret = main(
            ('fixit', 'fixit.rules:CollapseIsinstanceChecks', str(python_module)),
        )

        assert ret == 1
        assert python_module.read_text() == """\
x = None
# lint-fixme: CollapseIsinstanceChecks
isinstance(x, str) or isinstance(x, int)

def f(x):
    # lint-fixme: CollapseIsinstanceChecks
    return isinstance(x, str) or isinstance(x, int)
"""

        captured = capsys.readouterr()
        assert captured.out == f"""\
{python_module}
"""
        assert captured.err == """\
-> finding errors with fixit
found errors in 1 files
-> adding comments to silence errors
"""

    def test_main_no_violations(
            self, tmp_path: Path, capsys: pytest.CaptureFixture[str],
    ):
        src = """\
def foo():
    print('hello there')
"""

        python_module = tmp_path / 't.py'
        python_module.write_text(src)

        ret = main(
            ('fixit', 'fixit.rules:CollapseIsinstanceChecks', str(python_module)),
        )

        assert ret == 0
        assert python_module.read_text() == src

        captured = capsys.readouterr()
        assert captured.out == ''
        assert captured.err == """\
-> finding errors with fixit
no errors found
"""

    def test_main_multiple_different_violations(
            self, tmp_path: Path, capsys: pytest.CaptureFixture[str],
    ):
        src = """\
x = None
isinstance(x, str) or isinstance(x, int)

if True:
    pass
"""

        python_module = tmp_path / 't.py'
        python_module.write_text(src)

        ret = main(('fixit', 'fixit.rules', str(python_module)))

        assert ret == 1

        captured = capsys.readouterr()
        assert captured.out == ''
        assert captured.err == """\
-> finding errors with fixit
ERROR: errors found for multiple rules: ['CollapseIsinstanceChecks', 'NoStaticIfCondition']
"""  # noqa: B950

    def test_not_installed(self, capsys: pytest.CaptureFixture[str]):
        with FakeProcess() as process:
            process.register(
                (sys.executable, '-mfixit', process.any()),
                returncode=1, stderr='/path/to/python3: No module named fixit\n',
            )

            ret = main(('fixit', 'fixit.rules', 'path/to/file.py'))

        assert ret == 1

        captured = capsys.readouterr()
        assert captured.out == ''
        assert captured.err == """\
-> finding errors with fixit
ERROR: /path/to/python3: No module named fixit
"""


class TestFixitInline:
    def test_main_inline(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]):
        python_module = tmp_path / 't.py'
        python_module.write_text(
            """\
x = None
isinstance(x, str) or isinstance(x, int)

def f(x):
    return isinstance(x, str) or isinstance(x, int)
""",
        )

        ret = main(
            (
                'fixit-inline',
                'fixit.rules:CollapseIsinstanceChecks',
                str(python_module),
            ),
        )

        assert ret == 1
        assert python_module.read_text() == """\
x = None
isinstance(x, str) or isinstance(x, int)  # lint-fixme: CollapseIsinstanceChecks

def f(x):
    return isinstance(x, str) or isinstance(x, int)  # lint-fixme: CollapseIsinstanceChecks
"""  # noqa: B950

        captured = capsys.readouterr()
        assert captured.out == f"""\
{python_module}
"""
        assert captured.err == """\
-> finding errors with fixit
found errors in 1 files
-> adding comments to silence errors
"""


class TestFlake8:
    def test_main(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]):
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
            self, tmp_path: Path, capsys: pytest.CaptureFixture[str],
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

    def test_not_installed(self, capsys: pytest.CaptureFixture[str]):
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


class TestRuff:
    def test_main(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]):
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
            self, tmp_path: Path, capsys: pytest.CaptureFixture[str],
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

    def test_not_installed(self, capsys: pytest.CaptureFixture[str]):
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


class TestSemgrep:
    def test_main(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]):
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
            self, tmp_path: Path, capsys: pytest.CaptureFixture[str],
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

    def test_not_installed(self, capsys: pytest.CaptureFixture[str]):
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
