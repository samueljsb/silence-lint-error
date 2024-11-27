# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## Unreleased

## 1.5.1 (2024-11-27)

### Fixed

- Handle syntax errors from `ruff>=0.8.0`.

## 1.5.0 (2024-08-27)

### Added

- Silence errors with `mypy`.

## 1.4.2 (2024-07-01)

### Fixed

- Use `ruff check` instead of `ruff` for running `ruff`.
  This makes the tool compatible with ruff>=0.5.0.

## 1.4.1 (2024-05-09)

The tests are no longer included in the built package.

## 1.4.0 (2024-04-11)

### Added

- Silence errors with `semgrep`.

## 1.3.0 (2023-12-15)

### Added

- Apply auto-fixes with `ruff`.

## 1.2.1 (2023-12-11)

### Fixed

- Fix bug where `noqa` is used for all linters' silence comments

  We forgot to pass through the comment type when adding to existing comments.
  These were always added as `noqa` comments, even for `fixit`.

## 1.2.0 (2023-12-11)

### Added

- Silence `fixit` errors with *inline* comments.

  `fixit` does not always respect `lint-fixme` comments when they are on the
  line above the line causing the error. This is a known bug and is reported
  in https://github.com/Instagram/Fixit/issues/405.

  In some of these cases (e.g. decorators), placing the comment on the same line
  as the error can ensure it is respected. The `fixme-inline` linter option
  allows the comments to be added inline instead of on the lien above.

  N.B. This might prevent the comments from being successfully removed by the
  `fix fixit` command, if there are other errors ignored on the same line.

## 1.1.0 (2023-11-24)

### Added

- Silence errors with `ruff`

### Fixed

- Show helpful error message if the linting tool is not installed

  Until this release, if the tool you were trying to use to find errors wasn't
  installed, this tool would succeed with a 'no errors found' message. This is
  unhelpful, so we now show the 'No module named ...' error from Python and exit
  with a non-zero return code.

## 1.0.0 (2023-11-17)

This tool replaces
[`ignore-flake8-error`](https://github.com/samueljsb/ignore-flake8-error) and
[`silence-fixit-error`](https://github.com/samueljsb/silence-fixit-error). It is
feature-compatible with those tools.
