from __future__ import annotations

import subprocess
import sys
from collections.abc import Iterator
from collections.abc import Sequence
from typing import NamedTuple
from typing import Protocol
from typing import TYPE_CHECKING

from . import comments


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


class Fixit:
    name = 'fixit'

    def remove_silence_comments(self, src: str, rule_name: RuleName) -> str:
        return ''.join(
            self._remove_comments(
                src.splitlines(keepends=True), rule_name,
            ),
        )

    def _remove_comments(
            self, lines: Sequence[str], rule_name: RuleName,
    ) -> Iterator[str]:
        __, rule_id = rule_name.rsplit(':', maxsplit=1)
        fixme_comment = f'# lint-fixme: {rule_id}'
        for line in lines:
            if line.strip() == fixme_comment:  # fixme comment only
                continue
            elif line.rstrip().endswith(fixme_comment):  # code then fixme comment
                trailing_ws = line.removeprefix(line.rstrip())
                line_without_comment = (
                    line.rstrip().removesuffix(fixme_comment)  # remove comment
                    .rstrip()  # and remove any intermediate ws
                )
                yield line_without_comment + trailing_ws
            else:
                yield line

    def apply_fixes(
            self, rule_name: RuleName, filenames: Sequence[str],
    ) -> tuple[int, str]:
        proc = subprocess.run(
            (
                sys.executable, '-mfixit',
                '--rules', rule_name,
                'fix', '--automatic', *filenames,
            ),
            capture_output=True, text=True,
        )
        return proc.returncode, proc.stderr.strip()


class Ruff:
    name = 'ruff'

    def remove_silence_comments(self, src: str, rule_name: RuleName) -> str:
        return comments.remove_error_silencing_comments(
            src, comment_type='noqa', error_code=rule_name,
        )

    def apply_fixes(
            self, rule_name: RuleName, filenames: Sequence[str],
    ) -> tuple[int, str]:
        proc = subprocess.run(
            (
                sys.executable, '-mruff',
                'check', '--fix',
                '--select', rule_name,
                *filenames,
            ),
            capture_output=True, text=True,
        )
        return proc.returncode, proc.stdout.strip()


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
