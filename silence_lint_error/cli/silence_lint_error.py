from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from typing import NamedTuple

from silence_lint_error.silence_lint_error import ErrorRunningTool
from silence_lint_error.silence_lint_error import find_violations
from silence_lint_error.silence_lint_error import Fixit
from silence_lint_error.silence_lint_error import FixitInline
from silence_lint_error.silence_lint_error import Flake8
from silence_lint_error.silence_lint_error import Linter
from silence_lint_error.silence_lint_error import MultipleRulesViolated
from silence_lint_error.silence_lint_error import NoViolationsFound
from silence_lint_error.silence_lint_error import Ruff
from silence_lint_error.silence_lint_error import Semgrep
from silence_lint_error.silence_lint_error import silence_violations


LINTERS: dict[str, type[Linter]] = {
    'fixit': Fixit,
    'fixit-inline': FixitInline,
    'flake8': Flake8,
    'ruff': Ruff,
    'semgrep': Semgrep,
}


class Context(NamedTuple):
    rule_name: str
    file_names: list[str]
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


def main(argv: Sequence[str] | None = None) -> int:
    rule_name, file_names, linter = _parse_args(argv)

    print(f'-> finding errors with {linter.name}', file=sys.stderr)
    try:
        violations = find_violations(linter, rule_name, file_names)
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
        ret |= silence_violations(linter, filename, file_violations)

    return ret


if __name__ == '__main__':
    raise SystemExit(main())
