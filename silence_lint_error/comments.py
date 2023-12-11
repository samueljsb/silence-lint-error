from __future__ import annotations

import tokenize_rt


def add_error_silencing_comments(
        src: str, error_lines: set[int],
        comment_type: str, error_code: str,
) -> str:
    """Add comments to some code to silence linting errors.

    Args:
        src: The content of the module to add comments to.
        error_lines: The lines on which to silence errors.
        comment_type: The type of comment to add (e.g. `noqa` or `lint-fixme`)
        code: The error code to silence.

    Returns:
        The content of the module with the additional comments added.
    """
    tokens = tokenize_rt.src_to_tokens(src)

    for idx, token in tokenize_rt.reversed_enumerate(tokens):
        if token.line not in error_lines:
            continue
        if not token.src.strip():
            continue

        if token.name == 'COMMENT':
            new_comment = add_code_to_comment(token.src, comment_type, error_code)
            tokens[idx] = tokens[idx]._replace(src=new_comment)
        else:
            tokens.insert(
                idx+1, tokenize_rt.Token(
                    'COMMENT', f'# {comment_type}: {error_code}',
                ),
            )
            tokens.insert(idx+1, tokenize_rt.Token('UNIMPORTANT_WS', '  '))

        error_lines.remove(token.line)

    return tokenize_rt.tokens_to_src(tokens)


def add_noqa_comments(src: str, lines: set[int], error_code: str) -> str:
    """Add `noqa` comments to some code.

    Args:
        src: The content of the module to add `noqa` comments to.
        lines: The lines on which to add `noqa` coments.
        code: The error code to silence.

    Returns:
        The content of the module with the additional comments added.
    """
    return add_error_silencing_comments(src, lines, 'noqa', error_code)


def add_code_to_comment(comment: str, comment_type: str, code: str) -> str:
    """Add to a comment to make it a error-silencing comment.

    If the comment already includes an error silencing section of the same type, this
    will add the code to the list of silenced errors.
    """
    if f'{comment_type}: ' in comment:
        return comment.replace(
            f'{comment_type}: ', f'{comment_type}: {code},', 1,
        )
    else:
        return comment + f'  # {comment_type}: {code}'
