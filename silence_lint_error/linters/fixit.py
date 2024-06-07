from __future__ import annotations

import re
import subprocess
import sys
from collections import defaultdict
from collections.abc import Sequence
from typing import TYPE_CHECKING

from silence_lint_error import comments
from silence_lint_error.silence_lint_error import ErrorRunningTool
from silence_lint_error.silence_lint_error import Violation

if TYPE_CHECKING:
    from typing import TypeAlias

    FileName: TypeAlias = str
    RuleName: TypeAlias = str


class Fixit:
    name = 'fixit'

    def __init__(self) -> None:
        self.error_line_re = re.compile(r'^.*?@\d+:\d+ ')

    def find_violations(
        self, rule_name: RuleName, filenames: Sequence[FileName],
    ) -> dict[FileName, list[Violation]]:
        proc = subprocess.run(
            (
                sys.executable, '-mfixit',
                '--rules', rule_name,
                'lint', *filenames,
            ),
            capture_output=True,
            text=True,
        )

        if proc.returncode and proc.stderr.endswith('No module named fixit\n'):
            raise ErrorRunningTool(proc)

        # extract filenames and line numbers
        results: dict[str, list[Violation]] = defaultdict(list)
        for line in proc.stdout.splitlines():
            found_error = self._parse_output_line(line)
            if found_error:
                filename, violation = found_error
                results[filename].append(violation)
            else:  # pragma: no cover
                pass

        return results

    def _parse_output_line(
            self, line: str,
    ) -> tuple[FileName, Violation] | None:
        if not self.error_line_re.match(line):
            return None

        location, violated_rule_name, *__ = line.split(maxsplit=2)
        filename, position = location.split('@', maxsplit=1)
        lineno, *__ = position.split(':', maxsplit=1)

        rule_name_ = violated_rule_name.removesuffix(':')
        return filename, Violation(rule_name_, int(lineno))

    def silence_violations(
        self, src: str, violations: Sequence[Violation],
    ) -> str:
        [rule_name] = {violation.rule_name for violation in violations}
        linenos_to_silence = {violation.lineno for violation in violations}

        lines = src.splitlines(keepends=True)

        new_lines = []
        for current_lineno, line in enumerate(lines, start=1):
            if current_lineno in linenos_to_silence:
                leading_ws = line.removesuffix(line.lstrip())
                new_lines.append(f'{leading_ws}# lint-fixme: {rule_name}\n')
            new_lines.append(line)

        return ''.join(new_lines)


class FixitInline(Fixit):
    """An alternative `fixit` implementation that adds `lint-fixme` comment inline.

    This is sometimes necessary because `fixit` does not always respect `lint-fixme`
    comments when they are on the line above the line causing the error. This is a
    known bug and is reported in https://github.com/Instagram/Fixit/issues/405.

    In some of these cases, placing the comment on the same line as the error can
    ensure it is respected (e.g. for decorators).
    """

    def silence_violations(
        self, src: str, violations: Sequence[Violation],
    ) -> str:
        [rule_name] = {violation.rule_name for violation in violations}
        linenos_to_silence = {violation.lineno for violation in violations}
        return comments.add_error_silencing_comments(
            src, linenos_to_silence,
            'lint-fixme', rule_name,
        )
