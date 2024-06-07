from __future__ import annotations

import json
import subprocess
from collections import defaultdict
from collections.abc import Sequence
from typing import TYPE_CHECKING

from silence_lint_error.silencing import ErrorRunningTool
from silence_lint_error.silencing import Violation

if TYPE_CHECKING:
    from typing import TypeAlias

    FileName: TypeAlias = str
    RuleName: TypeAlias = str


class Semgrep:
    name = 'semgrep'

    def find_violations(
        self, rule_name: RuleName, filenames: Sequence[FileName],
    ) -> dict[FileName, list[Violation]]:
        proc = subprocess.run(
            (
                'semgrep', 'scan',
                '--metrics=off', '--oss-only',
                '--json',
                *filenames,
            ),
            capture_output=True,
            text=True,
        )

        if proc.returncode:
            raise ErrorRunningTool(proc)

        # extract filenames and line numbers
        results: dict[FileName, list[Violation]] = defaultdict(list)
        data = json.loads(proc.stdout)
        for result in data['results']:
            if result['check_id'] != rule_name:
                continue

            results[result['path']].append(
                Violation(
                    rule_name=result['check_id'],
                    lineno=result['start']['line'],
                ),
            )

        return dict(results)

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
                new_lines.append(f'{leading_ws}# nosemgrep: {rule_name}\n')
            new_lines.append(line)

        return ''.join(new_lines)
