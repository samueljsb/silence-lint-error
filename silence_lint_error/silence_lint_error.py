from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from collections.abc import Sequence
from typing import NamedTuple
from typing import Protocol
from typing import TYPE_CHECKING

import attrs

from . import comments

if TYPE_CHECKING:
    from typing import TypeAlias

    FileName: TypeAlias = str
    RuleName: TypeAlias = str


# Linters
# =======

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


LINTERS: dict[str, type[Linter]] = {
    'fixit': Fixit,
    'fixit-inline': FixitInline,
    'flake8': Flake8,
    'ruff': Ruff,
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
    except ErrorRunningTool as e:
        print(f'ERROR: {e.proc.stderr.strip()}', file=sys.stderr)
        return e.proc.returncode
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
