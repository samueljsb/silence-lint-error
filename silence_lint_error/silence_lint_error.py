from __future__ import annotations

import subprocess
from collections.abc import Sequence
from typing import NamedTuple
from typing import Protocol
from typing import TYPE_CHECKING

import attrs


if TYPE_CHECKING:
    from typing import TypeAlias

    FileName: TypeAlias = str
    RuleName: TypeAlias = str


class Violation(NamedTuple):
    rule_name: RuleName
    lineno: int


@attrs.frozen
class ErrorRunningTool(Exception):
    proc: subprocess.CompletedProcess[str]


class Linter(Protocol):
    name: str

    def find_violations(
        self, rule_name: RuleName, filenames: Sequence[FileName],
    ) -> dict[FileName, list[Violation]]:
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


class NoViolationsFound(Exception):
    pass


@attrs.frozen
class MultipleRulesViolated(Exception):
    rule_names: set[RuleName]


def find_violations(
        linter: Linter, rule_name: RuleName, file_names: Sequence[FileName],
) -> dict[FileName, list[Violation]]:
    violations = linter.find_violations(rule_name, file_names)

    if not violations:
        raise NoViolationsFound

    violation_names = {
        violation.rule_name
        for file_violations in violations.values()
        for violation in file_violations
    }
    if len(violation_names) != 1:
        raise MultipleRulesViolated(violation_names)

    return violations


def silence_violations(
        linter: Linter, filename: FileName, violations: Sequence[Violation],
) -> bool:
    with open(filename) as f:
        src = f.read()

    src_with_comments = linter.silence_violations(src, violations)

    with open(filename, 'w') as f:
        f.write(src_with_comments)

    return src_with_comments != src
