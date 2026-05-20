# Contributing to codechu-xdg

Thanks for thinking about contributing. `codechu-xdg` is a tiny
wrapper around the [XDG Base Directory Specification](https://specifications.freedesktop.org/basedir-spec/)
with a mandatory `vendor/product` namespace. Patches that stay true to
the spec — and don't invent new path categories — are warmly received.

This library was originally extracted from [Disk Cleaner](https://github.com/codechu/disk-cleaner),
but is maintained independently with its own release cadence.

## Development setup

```bash
git clone https://github.com/codechu/codechu-xdg-py.git
cd codechu-xdg-py
pip install -e ".[dev]"
pytest -q
ruff check src tests
```

## Workflow

- Branch names: `feature/<short>`, `fix/<short>`, `refactor/<short>`,
  `docs/<short>`, `test/<short>`.
- Commit messages: [Conventional Commits](https://www.conventionalcommits.org/)
  (`feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`).
- Open a PR using the template; describe the *why* in the body.
- One change per PR — keep diffs reviewable.

## Bug reports

A useful bug report includes:

- OS + Python version. Mention the desktop environment if relevant
  (GNOME, KDE, sway, headless server, Flatpak sandbox, etc.).
- Values of the `XDG_*` environment variables when the bug reproduces.
- A minimal reproducer — `App(vendor, product)` call plus the path
  method that misbehaves.

## Tests

- `pytest -q` must pass; coverage stays at **≥90 %**.
- New feature → new test. Always drive paths through `tmp_path` and
  `monkeypatch.setenv("XDG_*", …)` — **never** touch the real
  `~/.config/`, `~/.cache/`, or `$XDG_RUNTIME_DIR`.
- Cover the spec corner cases: `XDG_*` unset, `XDG_*` set to a
  relative path (must be ignored per spec), `XDG_RUNTIME_DIR` missing
  (fallback rules).
- Cleanup helpers (`remove_cache`, `remove_runtime`) must never
  traverse outside the vendor/product subtree — there's a test for
  this; please don't relax it.

## Cross-platform considerations

The library targets **Linux / Unix** primarily. macOS and Windows
have their own conventions (`~/Library/Application Support`,
`%APPDATA%`); we do not paper over them here. If you need
macOS/Windows path logic, that belongs in a sibling package, not
this one.

## Public API discipline

The public surface is `App(vendor, product)` plus its `settings_file`,
`cache_file`, `data_file`, `log_file`, `runtime_file`, `remove_cache`,
and `remove_runtime` methods. Anything else is internal.

## Style

- `ruff check` + `ruff format` clean.
- Type hints on public APIs (`from __future__ import annotations`).
- Use `logging.getLogger(__name__)`; avoid `print`.

## Security

If you find a security issue, see [SECURITY.md](SECURITY.md) — do not
open a public issue for it.

## Developer Certificate of Origin (DCO)

Every commit must be signed off with the [DCO](https://developercertificate.org/).
The sign-off certifies that you wrote the patch, or otherwise have the
right to submit it under the project's license. Add a line to your
commit message:

```
Signed-off-by: Your Name <you@example.com>
```

`git commit -s` does this automatically. PRs without sign-off will
be asked to amend before merge.

Contributions are accepted under the project's license (see
[LICENSE](LICENSE)).
