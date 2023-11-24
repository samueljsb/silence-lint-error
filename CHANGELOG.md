# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## Unreleased

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
