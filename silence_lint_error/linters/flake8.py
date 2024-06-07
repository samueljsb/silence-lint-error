from __future__ import annotations

import subprocess
import sys
from collections import defaultdict
from collections.abc import Sequence
from typing import TYPE_CHECKING

from silence_lint_error import comments
from silence_lint_error.silencing import ErrorRunningTool
from silence_lint_error.silencing import Violation

if TYPE_CHECKING:
    from typing import TypeAlias

    FileName: TypeAlias = str
    RuleName: TypeAlias = str


class Flake8:
    name = 'flake8'

    def find_violations(
        self, rule_name: RuleName, filenames: Sequence[FileName],
    ) -> dict[FileName, list[Violation]]:
        proc = subprocess.run(
            (
                sys.executable, '-mflake8',
                '--select', rule_name,
                '--format', '%(path)s %(row)s',
                *filenames,
            ),
            capture_output=True,
            text=True,
        )

        if proc.returncode and proc.stderr.endswith('No module named flake8\n'):
            raise ErrorRunningTool(proc)

        # extract filenames and line numbers
        results: dict[FileName, list[Violation]] = defaultdict(list)
        for line in proc.stdout.splitlines():
            filename_, lineno_ = line.rsplit(maxsplit=1)
            results[filename_].append(Violation(rule_name, int(lineno_)))

        return results

    def silence_violations(
        self, src: str, violations: Sequence[Violation],
    ) -> str:
        [rule_name] = {violation.rule_name for violation in violations}
        linenos_to_silence = {violation.lineno for violation in violations}
        return comments.add_noqa_comments(src, linenos_to_silence, rule_name)
