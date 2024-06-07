from __future__ import annotations

import subprocess
from collections.abc import Sequence
from typing import Protocol

import attrs


@attrs.frozen
class Violation:
    rule_name: str
    lineno: int


@attrs.frozen
class ErrorRunningTool(Exception):
    proc: subprocess.CompletedProcess[str]


class Linter(Protocol):
    name: str

    def find_violations(
        self, rule_name: str, filenames: Sequence[str],
    ) -> dict[str, list[Violation]]:
        """Find violations of a rule.

        Returns:
            Mapping of file path to the violations found in that file.

        Raises:
            ErrorRunningTool: There was an error whilst running the linter.
        """

    def silence_violations(
        self, src: str, violations: Sequence[Violation],
    ) -> str:
        """Modify module source to silence violations.

        Returns:
            Modified `src` with comments that silence the `violations`.
        """


@attrs.frozen
class Silencer:
    linter: Linter

    class NoViolationsFound(Exception):
        pass

    @attrs.frozen
    class MultipleRulesViolated(Exception):
        rule_names: set[str]

    def find_violations(
            self, *, rule_name: str, file_names: Sequence[str],
    ) -> dict[str, list[Violation]]:
        violations = self.linter.find_violations(rule_name, file_names)

        if not violations:
            raise self.NoViolationsFound

        violation_names = {
            violation.rule_name
            for file_violations in violations.values()
            for violation in file_violations
        }
        if len(violation_names) != 1:
            raise self.MultipleRulesViolated(violation_names)

        return violations

    def silence_violations(
            self, *, filename: str, violations: Sequence[Violation],
    ) -> bool:
        with open(filename) as f:
            src = f.read()

        src_with_comments = self.linter.silence_violations(src, violations)

        with open(filename, 'w') as f:
            f.write(src_with_comments)

        return src_with_comments != src
