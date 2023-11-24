# silence-lint-error

Silent linting errors by adding `ignore` or `fixme` comments.

This tool currently works with:

- [`fixit`](https://github.com/Instagram/Fixit)
- [`flake8`](https://github.com/PyCQA/flake8) (silence only)
- [`ruff`](https://docs.astral.sh/ruff/) (silence only)

## Usage

Install with pip:

```shell
python -m pip install silence-lint-error
```

You must also install the linting tool you wish to use *in the same virtual
environment*.

### silence linting errors

Find linting errors and add the `ignore` or `fixme` comments as applicable.

For example, to add `lint-fixme: CollapseIsinstanceChecks` comments to ignore
the `fixit.rules:CollapseIsinstanceChecks` rule from `fixit`, run:

```shell
silence-lint-error fixit fixit.rules:CollapseIsinstanceChecks path/to/files/ path/to/more/files/
```

To add `noqa: F401` comments to ignore the `F401` rule in `flake8`, run:

```shell
silence-lint-error flake8 F401 path/to/files/ path/to/more/files/
```

To add `noqa: F401` comments to ignore the `F401` rule in `ruff`, run:

```shell
silence-lint-error ruff F401 path/to/files/ path/to/more/files/
```

### fix silenced errors

If there is an auto-fix for a linting error, you can remove the `ignore` or
`fixme` comments and apply the auto-fix.

For example, to remove all `lint-fixme: CollapseIsinstanceChecks` comments and
apply the auto-fix for that rule, run:

```shell
fix-silenced-error fixit fixit.rules:CollapseIsinstanceChecks path/to/files/ path/to/more/files/
```

## Rationale

When adding a new rule (or enabling more rules) for a linter on a large
code-base, fixing the existing violations can be too large a task to do quickly.
However, starting to check the rule sooner will prevent new violations from
being introduced.

Ignoring existing violations is a quick way to allow new rules to be enabled.
You can then burn down those existing violations over time.

This tool makes it easy to find and ignore all current violations of a rule so
that it can be enabled.
