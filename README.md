# silence-lint-error

Silent linting errors
by adding `ignore` or `fixme` comments.

This tool currently works with:

- [`fixit`](https://github.com/Instagram/Fixit)
- [`flake8`](https://github.com/PyCQA/flake8) (silence only)
- [`mypy`](https://www.mypy-lang.org) (silence only)
- [`ruff`](https://docs.astral.sh/ruff/)
- [`semgrep`](https://semgrep.dev/docs/) (silence only)

# Usage

Install with pip:

```shell
python -m pip install silence-lint-error
```

You must also install the linting tool you wish to use.

## silence linting errors

Find linting errors
and add the `ignore` or `fixme` comments as applicable.

### Fixit

To add `lint-fixme: CollapseIsinstanceChecks` comments
to ignore the `fixit.rules:CollapseIsinstanceChecks` rule from `fixit`,
run:

```shell
silence-lint-error fixit fixit.rules:CollapseIsinstanceChecks path/to/files/ path/to/more/files/
```
### Flake8
To add `noqa: F401` comments
to ignore the `F401` rule in `flake8`,
run:

```shell
silence-lint-error flake8 F401 path/to/files/ path/to/more/files/
```

### Ruff

To add `noqa: F401` comments
to ignore the `F401` rule in `ruff`,
run:

```shell
silence-lint-error ruff F401 path/to/files/ path/to/more/files/
```

### Semgrep

To add `nosemgrep: {namespace-prefix}.best-practice.sleep.arbitrary-sleep` comments
to ignore the `{namespace-prefix}.best-practice.sleep.arbitrary-sleep` rule in `semgrep`,
run:

```shell
SEMGREP_RULES=r/python silence-lint-error semgrep {namespace-prefix}.best-practice.sleep.arbitrary-sleep path/to/files/ path/to/more/files/
```

> The rules must be configured in the `SEMGREP_RULES` environment variable. <br>
> For more information about configuring semgrep rules,
see the `--config` entry in the [`semgrep` documentation](https://semgrep.dev/docs/cli-reference-oss/)


> Semgrep sort of namespaces the rules based on the name of the directory. For example, if you have this folder structure: <br>
> <br>
└── project_root/<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;|____ src<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; |____ semgrep/<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; |____ rule.yml/<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;|____typing_rules<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;  |___another_rule.yml
> 
> If you run semgrep from within `project_root` with `SEMGREP_RULES=./semgrep/typing_rules`, `{namespace-prefix}` will take the value of `semgrep.typing_rules`<br>
> 
> The command to run would then become
> ```shell
> SEMGREP_RULES=./semgrep/typing_rules silence-lint-error semgrep semgrep.typing_rules.rule_name ./src
> ```


### Mypy
To add `type: ignore` comments
to ignore the `truthy-bool` error from `mypy`,
run:

```shell
silence-lint-error mypy truthy-bool path/to/files/ path/to/more/files/
```

## fix silenced errors


If there is an auto-fix for a linting error,
you can remove the `ignore` or `fixme` comments
and apply the auto-fix.

For example
to remove all `lint-fixme: CollapseIsinstanceChecks` comments
and apply the auto-fix for that rule,
run:

```shell
fix-silenced-error fixit fixit.rules:CollapseIsinstanceChecks path/to/files/ path/to/more/files/
```

To remove `noqa: F401` comments
and apply the auto-fix for that rule,
run:

```shell
fix-silenced-error ruff F401 path/to/files/ path/to/more/files/
```

## Rationale

When adding a new rule (or enabling more rules) for a linter
on a large code-base,
fixing the existing violations can be too large a task to do quickly.
However, starting to check the rule sooner
will prevent new violations from being introduced.

Ignoring existing violations is a quick way to allow new rules to be enabled.
You can then burn down those existing violations over time.

This tool makes it easy to find and ignore all current violations of a rule
so that it can be enabled.
