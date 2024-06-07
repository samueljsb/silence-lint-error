from collections.abc import Sequence
from pathlib import Path

import attrs
import pytest

from silence_lint_error.fixing import Fixer

@attrs.frozen
class FakeLinter:
    name = "fake"

    removed_comments = attrs.field(factory=list)
    fixes = attrs.field(factory=list)


    def remove_silence_comments(self, src: str, rule_name: str) -> str:
        self.removed_comments.append((src, rule_name))
        return f"Removed {rule_name}\n"

    def apply_fixes(
            self, rule_name: str, filenames: Sequence[str],
    ) -> tuple[int, str]:
        self.fixes.append((rule_name, filenames))
        return 0, f"fixed {rule_name}"

class NoChangesLinter:
    name = "no changes"

    def remove_silence_comments(self, src: str, rule_name: str) -> str:
        return src

    def apply_fixes(
            self, rule_name: str, filenames: Sequence[str],
    ) -> tuple[int, str]:
        return 0, ""


def test_unsilence_violations(tmp_path: Path) -> None:
    python_module_content = """\
def f() -> None: pass
"""
    python_module = tmp_path / 't.py'
    python_module.write_text(python_module_content)

    linter = FakeLinter()
    fixer = Fixer(linter)

    fixer.unsilence_violations(rule_name="A-RULE", filename=str(python_module))

    assert linter.removed_comments == [
        (python_module_content, "A-RULE"),
    ]

    assert python_module.read_text() == "Removed A-RULE\n"


def test_unsilence_violations_no_changes(tmp_path: Path) -> None:
    python_module_content = """\
def f() -> None: pass
"""
    python_module = tmp_path / 't.py'
    python_module.write_text(python_module_content)

    linter = NoChangesLinter()
    fixer = Fixer(linter)

    with pytest.raises(fixer.NoChangesMade):
        fixer.unsilence_violations(rule_name="A-RULE", filename=str(python_module))

    assert python_module.read_text() == python_module_content


def test_apply_fixes(tmp_path: Path) -> None:
    python_module_content = """\
def f() -> None: pass
"""
    python_module = tmp_path / 't.py'
    python_module.write_text(python_module_content)

    linter = FakeLinter()
    fixer = Fixer(linter)

    ret = fixer.apply_fixes(rule_name="A-RULE", filenames=("a/file", "a/nother/file"))

    assert ret == (0, "fixed A-RULE")
    assert linter.fixes == [
        ("A-RULE", ("a/file", "a/nother/file")),
    ]
