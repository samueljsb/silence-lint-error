from __future__ import annotations

import subprocess
from collections import defaultdict
from collections.abc import Sequence
from typing import TYPE_CHECKING

import tokenize_rt

from silence_lint_error.silencing import ErrorRunningTool
from silence_lint_error.silencing import Violation

if TYPE_CHECKING:
    from typing import TypeAlias

    FileName: TypeAlias = str
    RuleName: TypeAlias = str


class Mypy:
    name = 'mypy'

    def find_violations(
        self, rule_name: RuleName, filenames: Sequence[FileName],
    ) -> dict[FileName, list[Violation]]:
        proc = subprocess.run(
            (
                'mypy',
                '--follow-imports', 'silent',  # do not report errors in other modules
                '--enable-error-code', rule_name,
                '--show-error-codes', '--no-pretty', '--no-error-summary',
                *filenames,
            ),
            capture_output=True,
            text=True,
        )

        if proc.returncode > 1:
            raise ErrorRunningTool(proc)

        # extract filenames and line numbers
        results: dict[FileName, list[Violation]] = defaultdict(list)
        for line in proc.stdout.splitlines():
            if not line.endswith(f'[{rule_name}]'):
                continue

            location, *__ = line.split()
            filename_, lineno_, *__ = location.split(':')

            results[filename_].append(Violation(rule_name, int(lineno_)))

        return results

    def silence_violations(
        self, src: str, violations: Sequence[Violation],
    ) -> str:
        rule_name = violations[0].rule_name
        lines_with_errors = {
            violation.lineno
            for violation in violations
        }

        tokens = tokenize_rt.src_to_tokens(src)
        for idx, token in tokenize_rt.reversed_enumerate(tokens):
            if token.line not in lines_with_errors:
                continue
            if not token.src.strip():
                continue

            if token.name == 'COMMENT':
                if 'type: ignore' in token.src:
                    prefix, __, ignored = token.src.partition('type: ignore')
                    codes = ignored.strip('[]').split(',')
                    codes += [rule_name]
                    new_comment = f'{prefix}type: ignore[{",".join(codes)}]'
                else:
                    new_comment = token.src + f'  # type: ignore[{rule_name}]'
                tokens[idx] = tokens[idx]._replace(src=new_comment)
            else:
                tokens.insert(
                    idx+1, tokenize_rt.Token(
                        'COMMENT', f'# type: ignore[{rule_name}]',
                    ),
                )
                tokens.insert(idx+1, tokenize_rt.Token('UNIMPORTANT_WS', '  '))

            lines_with_errors.remove(token.line)

        return tokenize_rt.tokens_to_src(tokens)
