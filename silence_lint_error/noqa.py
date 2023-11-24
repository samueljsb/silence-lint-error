from __future__ import annotations


def add_code_to_comment(comment: str, code: str) -> str:
    """Add to a comment to make it a `noqa` comment.

    If the comment already includes a `noqa` section, this will add the code
    to the list of silenced errors.
    """
    if 'noqa: ' in comment:
        return comment.replace(
            'noqa: ', f'noqa: {code},',
        )
    else:
        return comment + f'  # noqa: {code}'
