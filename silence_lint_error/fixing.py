from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

import attrs


class Linter(Protocol):
    name: str

    def remove_silence_comments(self, src: str, rule_name: str) -> str:
        """Remove comments that silence rule violations.

        Returns:
            Modified `src` without comments that silence the `violations`.
        """

    def apply_fixes(
            self, rule_name: str, filenames: Sequence[str],
    ) -> tuple[int, str]:
        """Fix violations of a rule.

        Returns:
            Return code and stdout from the process that fixed the violations.
        """


@attrs.frozen
class Fixer:
    linter: Linter

    class NoChangesMade(Exception):
        pass

    def unsilence_violations(
            self, *, rule_name: str, filename: str,
    ) -> None:
        with open(filename) as f:
            src = f.read()

        src_without_comments = self.linter.remove_silence_comments(src, rule_name)

        if src_without_comments == src:
            raise self.NoChangesMade

        with open(filename, 'w') as f:
            f.write(src_without_comments)

    def apply_fixes(
            self, *, rule_name: str, filenames: Sequence[str],
    ) -> tuple[int, str]:
        return self.linter.apply_fixes(rule_name, filenames)
