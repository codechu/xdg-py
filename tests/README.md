# Tests — codechu-xdg

Run the suite from the repo root:

```bash
pytest -q
```

With coverage:

```bash
pytest --cov=codechu_xdg --cov-report=term-missing
```

## Coverage gate

The coverage floor is **90 %**. PRs that drop below it are rejected;
add tests with your change.

## Conventions

- Drive every path through `tmp_path` plus
  `monkeypatch.setenv("XDG_*", …)`. Never touch the real
  `~/.config/`, `~/.cache/`, or `$XDG_RUNTIME_DIR`.
- Cover spec corner cases: `XDG_*` unset, `XDG_*` set to a relative
  path (must be ignored), `XDG_RUNTIME_DIR` missing (fallback rules).
- The "cleanup helpers never traverse outside the vendor/product
  subtree" invariant is covered — keep that test green.
