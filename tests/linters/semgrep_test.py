from __future__ import annotations

from silence_lint_error.linters import semgrep
from silence_lint_error.silencing import Violation


class TestSilenceViolations:
    def test_add_to_existing_silence_comment(self) -> None:
        src = """\
# nosemgrep: some-error-code
violation_here()
"""
        violation = Violation(
            rule_name='another-error-code',
            lineno=2,
        )

        modified_src = semgrep.Semgrep().silence_violations(
            src, (violation,),
        )

        assert modified_src == """\
# nosemgrep: another-error-code, some-error-code
violation_here()
"""
