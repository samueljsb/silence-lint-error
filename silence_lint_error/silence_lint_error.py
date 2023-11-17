from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import defaultdict
from collections.abc import Sequence
from typing import NamedTuple
from typing import Protocol
from typing import TYPE_CHECKING

import attrs
import tokenize_rt

if TYPE_CHECKING:
    from typing import TypeAlias

    FileName: TypeAlias = str
    RuleName: TypeAlias = str


# Linters
# =======

class Violation(NamedTuple):
    rule_name: RuleName
    lineno: int


class Linter(Protocol):
    name: str

    def find_violations(
        self, rule_name: RuleName, filenames: Sequence[FileName],
    ) -> dict[FileName, list[Violation]]:
        ...

    def silence_violations(
        self, src: str, violations: Sequence[Violation],
    ) -> str:
        ...


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

        tokens = tokenize_rt.src_to_tokens(src)

        for idx, token in tokenize_rt.reversed_enumerate(tokens):
            if token.line not in linenos_to_silence:
                continue
            if not token.src.strip():
                continue

            if token.name == 'COMMENT':
                new_comment = self._add_code_to_comment(token.src, rule_name)
                tokens[idx] = tokens[idx]._replace(src=new_comment)
            else:
                tokens.insert(
                    idx+1, tokenize_rt.Token('COMMENT', f'# noqa: {rule_name}'),
                )
                tokens.insert(idx+1, tokenize_rt.Token('UNIMPORTANT_WS', '  '))

            linenos_to_silence.remove(token.line)

        return tokenize_rt.tokens_to_src(tokens)

    def _add_code_to_comment(self, comment: str, code: str) -> str:
        if 'noqa: ' in comment:
            return comment.replace(
                'noqa: ', f'noqa: {code},',
            )
        else:
            return comment + f'  # noqa: {code}'


LINTERS: dict[str, type[Linter]] = {
    'fixit': Fixit,
    'flake8': Flake8,
}


# CLI
# ===

class Context(NamedTuple):
    rule_name: RuleName
    file_names: list[FileName]
    linter: Linter


def _parse_args(argv: Sequence[str] | None) -> Context:
    parser = argparse.ArgumentParser(
        description='Ignore linting errors by adding ignore/fixme comments.',
    )
    parser.add_argument(
        'linter', choices=LINTERS,
        help='The linter for which to ignore errors',
    )
    parser.add_argument('rule_name')
    parser.add_argument('filenames', nargs='*')
    args = parser.parse_args(argv)

    return Context(
        rule_name=args.rule_name,
        file_names=args.filenames,
        linter=LINTERS[args.linter](),
    )


class NoViolationsFound(Exception):
    pass


@attrs.frozen
class MultipleRulesViolated(Exception):
    rule_names: set[RuleName]


def _find_violations(
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


def _silence_violations(
        linter: Linter, filename: FileName, violations: Sequence[Violation],
) -> bool:
    with open(filename) as f:
        src = f.read()

    src_with_comments = linter.silence_violations(src, violations)

    with open(filename, 'w') as f:
        f.write(src_with_comments)

    return src_with_comments != src


def main(argv: Sequence[str] | None = None) -> int:
    rule_name, file_names, linter = _parse_args(argv)

    print(f'-> finding errors with {linter.name}', file=sys.stderr)
    try:
        violations = _find_violations(linter, rule_name, file_names)
    except NoViolationsFound:
        print('no errors found', file=sys.stderr)
        return 0
    except MultipleRulesViolated as e:
        print(
            'ERROR: errors found for multiple rules:', sorted(e.rule_names),
            file=sys.stderr,
        )
        return 1
    else:
        print(f'found errors in {len(violations)} files', file=sys.stderr)

    print('-> adding comments to silence errors', file=sys.stderr)
    ret = 0
    for filename, file_violations in violations.items():
        print(filename)
        ret |= _silence_violations(linter, filename, file_violations)

    return ret


if __name__ == '__main__':
    raise SystemExit(main())
