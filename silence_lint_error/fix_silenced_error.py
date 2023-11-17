from __future__ import annotations

import argparse
import subprocess
import sys
from collections.abc import Iterator
from collections.abc import Sequence
from typing import NamedTuple
from typing import Protocol
from typing import TYPE_CHECKING


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

    def remove_silence_comments(self, src: str, rule_name: RuleName) -> str:
        ...

    def apply_fixes(
            self, rule_name: RuleName, filenames: Sequence[str],
    ) -> tuple[int, str]:
        ...


class Fixit:
    name = 'fixit'

    def remove_silence_comments(self, src: str, rule_name: RuleName) -> str:
        return ''.join(
            self._remove_comments(
                src.splitlines(keepends=True), rule_name,
            ),
        )

    def _remove_comments(
            self, lines: Sequence[str], rule_name: RuleName,
    ) -> Iterator[str]:
        __, rule_id = rule_name.rsplit(':', maxsplit=1)
        fixme_comment = f'# lint-fixme: {rule_id}'
        for line in lines:
            if line.strip() == fixme_comment:  # fixme comment only
                continue
            elif line.rstrip().endswith(fixme_comment):  # code then fixme comment
                trailing_ws = line.removeprefix(line.rstrip())
                line_without_comment = (
                    line.rstrip().removesuffix(fixme_comment)  # remove comment
                    .rstrip()  # and remove any intermediate ws
                )
                yield line_without_comment + trailing_ws
            else:
                yield line

    def apply_fixes(
            self, rule_name: RuleName, filenames: Sequence[str],
    ) -> tuple[int, str]:
        proc = subprocess.run(
            (
                sys.executable, '-mfixit',
                '--rules', rule_name,
                'fix', '--automatic', *filenames,
            ),
            capture_output=True, text=True,
        )
        return proc.returncode, proc.stderr.strip()


LINTERS: dict[str, type[Linter]] = {
    'fixit': Fixit,
}


# CLI
# ===

class Context(NamedTuple):
    rule_name: RuleName
    file_names: list[FileName]
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


class NoChangesMade(Exception):
    pass


def _unsilence_violations(
        linter: Linter, rule_name: RuleName, filename: FileName,
) -> None:
    with open(filename) as f:
        src = f.read()

    src_without_comments = linter.remove_silence_comments(src, rule_name)

    if src_without_comments == src:
        raise NoChangesMade

    with open(filename, 'w') as f:
        f.write(src_without_comments)


def main(argv: Sequence[str] | None = None) -> int:
    rule_name, file_names, linter = _parse_args(argv)

    print('-> removing comments that silence errors', file=sys.stderr)
    changed_files = []
    for filename in file_names:
        try:
            _unsilence_violations(linter, rule_name, filename)
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
