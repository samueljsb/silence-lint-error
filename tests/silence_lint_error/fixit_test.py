from __future__ import annotations

import sys
from pathlib import Path

import pytest
from pytest_subprocess import FakeProcess

from silence_lint_error.silence_lint_error import Fixit
from silence_lint_error.silence_lint_error import main
from silence_lint_error.silence_lint_error import Violation


class TestFixit:
    @pytest.mark.parametrize(
        'lines, expected_violations', (
            pytest.param(
                ['t.py@1:2 MyRuleName: the error message'],
                [('t.py', Violation('MyRuleName', 1))],
                id='single-line',
            ),
            pytest.param(
                ['t.py@1:2 MyRuleName: '],
                [('t.py', Violation('MyRuleName', 1))],
                id='no-message',
            ),
            pytest.param(
                [
                    't.py@1:2 MyRuleName: the error message',
                    'which continue over multiple lines',
                    'just like this one does.',
                ],
                [
                    ('t.py', Violation('MyRuleName', 1)),
                    None,
                    None,
                ],
                id='multi-line',
            ),
            pytest.param(
                [
                    't.py@1:2 MyRuleName: ',
                    'the error message on a new line',
                    'which continue over multiple lines',
                    'just like this one does.',
                ],
                [
                    ('t.py', Violation('MyRuleName', 1)),
                    None,
                    None,
                    None,
                ],
                id='multi-line-leading-ws',
            ),
            pytest.param(
                [
                    't.py@1:2 MyRuleName: the error message',
                    'which continue over multiple lines',
                    'just like this one does.',
                    '',
                ],
                [
                    ('t.py', Violation('MyRuleName', 1)),
                    None,
                    None,
                    None,
                ],
                id='multi-line-trailing-ws',
            ),
        ),
    )
    def test_parse_output_line(
            self,
            lines: list[str],
            expected_violations: list[tuple[str, Violation] | None],
    ):
        violations = [
            Fixit()._parse_output_line(line)
            for line in lines
        ]

        assert violations == expected_violations

    def test_find_violations(self, tmp_path: Path):
        python_module = tmp_path / 't.py'
        python_module.write_text(
            """\
x = None
isinstance(x, str) or isinstance(x, int)
""",
        )

        violations = Fixit().find_violations(
            'fixit.rules:CollapseIsinstanceChecks', [str(python_module)],
        )

        assert violations == {
            str(python_module): [
                Violation('CollapseIsinstanceChecks', 2),
            ],
        }


def test_main(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
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


def test_main_inline(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
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
        ('fixit-inline', 'fixit.rules:CollapseIsinstanceChecks', str(python_module)),
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


def test_main_no_violations(
        tmp_path: Path, capsys: pytest.CaptureFixture[str],
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
        tmp_path: Path, capsys: pytest.CaptureFixture[str],
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


def test_not_installed(capsys: pytest.CaptureFixture[str]):
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
