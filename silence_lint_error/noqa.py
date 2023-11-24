from __future__ import annotations

import tokenize_rt


def add_noqa_comments(src: str, lines: set[int], error_code: str) -> str:
    """Add `noqa` comments to some code.

    Args:
        src: The content of the module to add `nqa` comments to.
        lines: The lines on which to add `noqa` coments.
        code: The error code to silence.

    Returns:
        The content of the module with the additional comments added.
    """
    tokens = tokenize_rt.src_to_tokens(src)

    for idx, token in tokenize_rt.reversed_enumerate(tokens):
        if token.line not in lines:
            continue
        if not token.src.strip():
            continue

        if token.name == 'COMMENT':
            new_comment = add_code_to_comment(token.src, error_code)
            tokens[idx] = tokens[idx]._replace(src=new_comment)
        else:
            tokens.insert(
                idx+1, tokenize_rt.Token('COMMENT', f'# noqa: {error_code}'),
            )
            tokens.insert(idx+1, tokenize_rt.Token('UNIMPORTANT_WS', '  '))

        lines.remove(token.line)

    return tokenize_rt.tokens_to_src(tokens)


def add_code_to_comment(comment: str, code: str) -> str:
    """Add to a comment to make it a `noqa` comment.

    If the comment already includes a `noqa` section, this will add the code
    to the list of silenced errors.
    """
    if 'noqa: ' in comment:
        return comment.replace(
            'noqa: ', f'noqa: {code},', 1,
        )
    else:
        return comment + f'  # noqa: {code}'
