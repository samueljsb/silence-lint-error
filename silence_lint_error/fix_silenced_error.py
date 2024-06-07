from __future__ import annotations

from collections.abc import Sequence
from typing import NamedTuple
from typing import Protocol
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from typing import TypeAlias

    FileName: TypeAlias = str
    RuleName: TypeAlias = str


class Violation(NamedTuple):
    rule_name: RuleName
    lineno: int


class Linter(Protocol):
    name: str

    def remove_silence_comments(self, src: str, rule_name: RuleName) -> str:
        """Remove comments that silence rule violations.

        Returns:
            Modified `src` without comments that silence the `violations`.
        """

    def apply_fixes(
            self, rule_name: RuleName, filenames: Sequence[str],
    ) -> tuple[int, str]:
        """Fix violations of a rule.

        Returns:
            Return code and stdout from the process that fixed the violations.
        """


class NoChangesMade(Exception):
    pass


def unsilence_violations(
        linter: Linter, rule_name: RuleName, filename: FileName,
) -> None:
    with open(filename) as f:
        src = f.read()

    src_without_comments = linter.remove_silence_comments(src, rule_name)

    if src_without_comments == src:
        raise NoChangesMade

    with open(filename, 'w') as f:
        f.write(src_without_comments)
