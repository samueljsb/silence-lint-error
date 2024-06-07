from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from typing import NamedTuple

from silence_lint_error.fix_silenced_error import Fixit
from silence_lint_error.fix_silenced_error import Linter
from silence_lint_error.fix_silenced_error import NoChangesMade
from silence_lint_error.fix_silenced_error import Ruff
from silence_lint_error.fix_silenced_error import unsilence_violations


LINTERS: dict[str, type[Linter]] = {
    'fixit': Fixit,
    'ruff': Ruff,
}


class Context(NamedTuple):
    rule_name: str
    file_names: list[str]
    linter: Linter


def _parse_args(argv: Sequence[str] | None) -> Context:
    parser = argparse.ArgumentParser(
        description=(
            'Fix linting errors by removing ignore/fixme comments '
            'and running auto-fixes.'
        ),
    )
    parser.add_argument(
        'linter', choices=LINTERS,
        help='The linter to use to fix the errors',
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

    print('-> removing comments that silence errors', file=sys.stderr)
    changed_files = []
    for filename in file_names:
        try:
            unsilence_violations(linter, rule_name, filename)
        except NoChangesMade:
            continue
        else:
            print(filename)
            changed_files.append(filename)

    if not changed_files:
        print('no silenced errors found', file=sys.stderr)
        return 0

    print(f'-> applying auto-fixes with {linter.name}', file=sys.stderr)
    ret, message = linter.apply_fixes(rule_name, changed_files)
    print(message, file=sys.stderr)

    return ret


if __name__ == '__main__':
    raise SystemExit(main())
