from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from typing import NamedTuple

from silence_lint_error.linters import fixit
from silence_lint_error.linters import flake8
from silence_lint_error.linters import mypy
from silence_lint_error.linters import ruff
from silence_lint_error.linters import semgrep
from silence_lint_error.silencing import ErrorRunningTool
from silence_lint_error.silencing import Linter
from silence_lint_error.silencing import Silencer


LINTERS: dict[str, type[Linter]] = {
    'fixit': fixit.Fixit,
    'fixit-inline': fixit.FixitInline,
    'flake8': flake8.Flake8,
    'mypy': mypy.Mypy,
    'ruff': ruff.Ruff,
    'semgrep': semgrep.Semgrep,
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
    silencer = Silencer(linter)

    print(f'-> finding errors with {linter.name}', file=sys.stderr)
    try:
        violations = silencer.find_violations(
            rule_name=rule_name, file_names=file_names,
        )
    except ErrorRunningTool as e:
        print(f'ERROR: {e.proc.stderr.strip()}', file=sys.stderr)
        return e.proc.returncode
    except silencer.NoViolationsFound:
        print('no errors found', file=sys.stderr)
        return 0
    except silencer.MultipleRulesViolated as e:
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
        ret |= silencer.silence_violations(
            filename=filename, violations=file_violations,
        )

    return ret


if __name__ == '__main__':
    raise SystemExit(main())
