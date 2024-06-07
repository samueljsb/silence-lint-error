from __future__ import annotations

from pathlib import Path

import pytest

from silence_lint_error.linters.fixit import Fixit
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
