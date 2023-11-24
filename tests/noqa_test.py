from __future__ import annotations

import pytest

from silence_lint_error.noqa import add_code_to_comment


@pytest.mark.parametrize(
    'original, expected', (
        ('something', 'something  # noqa: ABC1'),
        ('noqa: XYZ0', 'noqa: ABC1,XYZ0'),
        ('something  # noqa: XYZ0', 'something  # noqa: ABC1,XYZ0'),
        ('noqa: XYZ0  # something', 'noqa: ABC1,XYZ0  # something'),
    ),
)
def test_add_code_to_comment(original, expected):
    assert add_code_to_comment(original, 'ABC1') == expected
