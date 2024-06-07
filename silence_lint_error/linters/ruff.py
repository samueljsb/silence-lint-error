from __future__ import annotations

import json
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


class Ruff:
    name = 'ruff'

    def find_violations(
        self, rule_name: RuleName, filenames: Sequence[FileName],
    ) -> dict[FileName, list[Violation]]:
        proc = subprocess.run(
            (
                sys.executable, '-mruff',
                '--select', rule_name,
                '--output-format', 'json',
                *filenames,
            ),
            capture_output=True,
            text=True,
        )

        if proc.returncode and proc.stderr.endswith('No module named ruff\n'):
            raise ErrorRunningTool(proc)

        # extract filenames and line numbers
        all_violations = json.loads(proc.stdout)
        results: dict[FileName, list[Violation]] = defaultdict(list)
        for violation in all_violations:
            results[violation['filename']].append(
                Violation(
                    rule_name=violation['code'],
                    lineno=violation['location']['row'],
                ),
            )

        return results

    def silence_violations(
        self, src: str, violations: Sequence[Violation],
    ) -> str:
        [rule_name] = {violation.rule_name for violation in violations}
        linenos_to_silence = {violation.lineno for violation in violations}
        return comments.add_noqa_comments(src, linenos_to_silence, rule_name)
