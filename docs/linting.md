# Linting Rules

Linting is an automated clean-code, consistency, and basic bug-risk check.

Before pushing code changes, run the lint and test targets from the `code/`
repository:

```bash
PATH=.venv/bin:$PATH make lint
PATH=.venv/bin:$PATH make test
```

`make lint` runs:

```bash
ruff check src tests
mypy src
```

Both Ruff and mypy must pass.

## Ruff Rules

- Keep imports sorted:
  - standard library imports first
  - third-party imports second
  - local project imports last
- Do not leave unused imports or unused variables.
- Do not leave trailing whitespace, especially on blank lines.
- End every file with a newline.
- Use modern Python syntax when Ruff suggests it.
- For `zip(...)`, always specify `strict=True` or `strict=False`.

Example:

```python
zip(items, scores, strict=False)
```

Ruff can fix many formatting issues automatically:

```bash
PATH=.venv/bin:$PATH make format
```

## Mypy Rules

- Add type annotations for empty collections:

```python
items: list[str] = []
scores: dict[str, float] = {}
counts: Counter[str] = Counter()
```

- Type function arguments and return values.
- If a function only reads from a list, prefer `Sequence[...]` instead of
  `list[...]`.
- Make API response data match the Pydantic schema types.
- Avoid unnecessary `# type: ignore` comments.
- If `# type: ignore[...]` is needed, make sure the error code matches the
  actual mypy error.

Only push once lint and tests pass.
