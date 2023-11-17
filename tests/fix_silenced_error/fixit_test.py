from __future__ import annotations

from pathlib import Path

import pytest

from silence_lint_error.fix_silenced_error import main


def test_main(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    src = """\
x = None
# lint-fixme: CollapseIsinstanceChecks
isinstance(x, str) or isinstance(x, int)
isinstance(x, bool) or isinstance(x, float)  # lint-fixme: CollapseIsinstanceChecks

def f(x):
    # lint-ignore: CollapseIsinstanceChecks
    return isinstance(x, str) or isinstance(x, int)
"""

    python_module = tmp_path / 't.py'
    python_module.write_text(src)

    ret = main(('fixit', 'fixit.rules:CollapseIsinstanceChecks', str(python_module)))

    assert ret == 0
    assert python_module.read_text() == """\
x = None
isinstance(x, (str, int))
isinstance(x, (bool, float))

def f(x):
    # lint-ignore: CollapseIsinstanceChecks
    return isinstance(x, str) or isinstance(x, int)
"""

    captured = capsys.readouterr()
    assert captured.out == f"""\
{python_module}
"""
    assert captured.err == """\
-> removing comments that silence errors
-> applying auto-fixes with fixit
🛠️  1 file checked, 1 file with errors, 2 auto-fixes available, 2 fixes applied 🛠️
"""


def test_main_no_violations(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    src = """\
def foo():
    print('hello there')
"""

    python_module = tmp_path / 't.py'
    python_module.write_text(src)

    ret = main(('fixit', 'fixit.rules:CollapseIsinstanceChecks', str(python_module)))

    assert ret == 0
    assert python_module.read_text() == src

    captured = capsys.readouterr()
    assert captured.out == ''
    assert captured.err == """\
-> removing comments that silence errors
no silenced errors found
"""
