from __future__ import annotations

import pytest

from silence_lint_error.comments import add_code_to_comment
from silence_lint_error.comments import add_noqa_comments


def test_add_noqa_comments():
    src = """\
# a single-line statement on line 2
foo = 'bar'

# a function on line 5
def baz(
a: int,
b: int,
) -> str:
...

# a multi-line string on line 12
s = '''
hello there
'''
"""

    assert add_noqa_comments(
        src, {2, 5, 12}, 'ABC123',
    ) == """\
# a single-line statement on line 2
foo = 'bar'  # noqa: ABC123

# a function on line 5
def baz(  # noqa: ABC123
a: int,
b: int,
) -> str:
...

# a multi-line string on line 12
s = '''
hello there
'''  # noqa: ABC123
"""


@pytest.mark.parametrize(
    'original, expected', (
        ('something', 'something  # noqa: ABC1'),
        ('noqa: XYZ0', 'noqa: ABC1,XYZ0'),
        ('something  # noqa: XYZ0', 'something  # noqa: ABC1,XYZ0'),
        ('noqa: XYZ0  # something', 'noqa: ABC1,XYZ0  # something'),
        ('noqa: XYZ0  # noqa: UVW3', 'noqa: ABC1,XYZ0  # noqa: UVW3'),
    ),
)
def test_add_code_to_comment(original, expected):
    assert add_code_to_comment(original, 'noqa', 'ABC1') == expected
