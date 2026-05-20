```text
   ~/  codechu-xdg
   ├── .config/    <vendor>/<product>/   settings live here
   ├── .cache/     <vendor>/<product>/   throwaway, regenerable
   ├── .local/share/  <vendor>/<product>/   user data, keep it
   ├── .local/state/  <vendor>/<product>/   logs, history
   └── $XDG_RUNTIME_DIR/<vendor>/<product>/  sockets, pids
```

[![PyPI](https://img.shields.io/pypi/v/codechu-xdg.svg)](https://pypi.org/project/codechu-xdg/)
[![Python](https://img.shields.io/pypi/pyversions/codechu-xdg.svg)](https://pypi.org/project/codechu-xdg/)
[![CI](https://github.com/codechu/xdg-py/actions/workflows/ci.yml/badge.svg)](https://github.com/codechu/xdg-py/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

> *Vendor-namespaced XDG Base Directory paths — five dirs, one rule.*

# codechu-xdg

Vendor-namespaced
[XDG Base Directory](https://specifications.freedesktop.org/basedir-spec/)
paths for Linux desktop apps. Every path lives at
`$XDG_BASE/<vendor>/<product>/` — multiple products from one
publisher share a tidy directory tree, and any user can find or
clean *all* your products at once.

```text
~/.config/codechu/                ← every Codechu product
├── disk-cleaner/  settings.json
├── ascii-painter/ settings.json
└── snap-monitor/  settings.json

~/.cache/codechu/disk-cleaner/    ← regenerable
~/.local/share/codechu/...        ← user data
~/.local/state/codechu/...        ← logs, history
$XDG_RUNTIME_DIR/codechu/...      ← sockets, pids
```

## Install

```bash
pip install codechu-xdg
```

Python 3.10+. ~80 LOC, stdlib-only.

## Quick example

```python
from codechu_xdg import App

app = App(vendor="codechu", product="disk-cleaner")
app.ensure()                       # mkdir -p for all 5 dirs

settings  = app.settings_file()    # config_dir / settings.json
db_cache  = app.cache_file("du_cache.db")
snapshots = app.data_file("snapshots.db")
log_file  = app.log_file()         # state_dir / app.log
sock_file = app.runtime_file("control.sock")

n = app.remove_cache()             # cleanup is one call
```

## What you get

- **`App(vendor, product)`** — five paths in one object:
  `config_dir`, `cache_dir`, `data_dir`, `state_dir`, `runtime_dir`.
- **Convenience helpers** — `settings_file()`, `cache_file()`,
  `data_file()`, `log_file()`, `runtime_file()` for the common
  cases.
- **`ensure()`** — idempotent `mkdir -p` for all 5 dirs.
- **`migrate(mapping)`** — idempotent legacy → new path mover for
  upgrading users across directory-layout changes; safe to call on
  every startup (existing target paths are never overwritten).
- **`remove_cache()` / `remove_runtime()`** — bounded cleanup
  helpers that return the count of removed entries.
- **Vendor namespacing enforced** — there is no
  `App(product="…")` constructor without a vendor; product-only
  layouts can't sneak in by mistake.

## Read more

- [API reference](docs/API.md) — every public symbol with
  signatures and edge-case tables.
- [Recipes](docs/RECIPES.md) — multi-product layouts, migration
  patterns, cleanup-at-shutdown, lock files.
- [Migration guide](docs/MIGRATION.md) — between major versions.
- [Changelog](CHANGELOG.md)

## Family

| Library | Purpose |
|---------|---------|
| [codechu-fs](https://pypi.org/project/codechu-fs/) | Filesystem primitives — atomic write, XDG trash, safe walk |
| [codechu-config](https://pypi.org/project/codechu-config/) | Schema-driven config — atomic save, migrations |
| [codechu-log](https://pypi.org/project/codechu-log/) | Structured logging — context, JSON, rotation |
| [codechu-ipc](https://pypi.org/project/codechu-ipc/) | Local IPC — Unix socket, FIFO, JSON-line protocol |
| [codechu-events](https://pypi.org/project/codechu-events/) | Thread-safe multi-channel pub/sub bus |

Full ecosystem: [github.com/codechu](https://github.com/codechu).

## Credits

- Path conventions per the freedesktop.org
  [XDG Base Directory Specification](https://specifications.freedesktop.org/basedir-spec/).

## License

MIT — see [LICENSE](LICENSE).

Part of [Codechu](https://github.com/codechu).
