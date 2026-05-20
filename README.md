```text
   ~/  codechu-xdg
   ├── .config/    <vendor>/<product>/   settings live here
   ├── .cache/     <vendor>/<product>/   throwaway, regenerable
   ├── .local/share/  <vendor>/<product>/   user data, keep it
   ├── .local/state/  <vendor>/<product>/   logs, history
   └── $XDG_RUNTIME_DIR/<vendor>/<product>/  sockets, pids
```

> *Vendor-namespaced XDG Base Directory paths — five dirs, one rule.*

# codechu-xdg

Vendor-namespaced [XDG Base Directory](https://specifications.freedesktop.org/basedir-spec/)
paths for Linux desktop apps. Tiny — ~80 LOC, stdlib-only, no dependencies.

```bash
pip install codechu-xdg
```

## What it gives you

- 5 standard XDG path types: **config, cache, data, state, runtime**
- **Mandatory vendor + product namespace** — every path is
  `$XDG_BASE/<vendor>/<product>/`, so multiple products from the same
  publisher live under one directory (one `~/.config/<vendor>/` reveals
  all your products)
- `ensure()` — `mkdir -p` for all 5 dirs
- `migrate()` — idempotent legacy → new path mover (run once at startup
  to upgrade users from earlier layouts)

## Quick examples

### Basic

```python
from codechu_xdg import App

app = App(vendor="codechu", product="disk-cleaner")
app.ensure()  # create all 5 dirs

# Paths
settings  = app.config_dir  / "settings.json"
db_cache  = app.cache_dir   / "du_cache.db"
snapshots = app.data_dir    / "snapshots.db"
log_file  = app.state_dir   / "app.log"
pid_file  = app.runtime_dir / "watchdog.pid"
sock_file = app.runtime_dir / "control.sock"
```

### Convenience helpers

For common file types, helpers eliminate `dir / "name"` boilerplate:

```python
app.settings_file()                # config_dir / settings.json (default name)
app.settings_file("themes.json")   # config_dir / themes.json
app.cache_file("du_cache.db")
app.data_file("snapshots.db")
app.log_file()                     # state_dir / app.log
app.runtime_file("watchdog.pid")
```

### Cleanup at shutdown / on demand

```python
# Wipe stale sockets and pid files — recreated on next run.
app.remove_runtime()

# Or full cache wipe (regeneratable). Returns count of removed entries.
n = app.remove_cache()
print(f"cleared {n} cache entries")
```

## Migration from earlier layouts

When you change directory conventions across versions, `migrate()`
moves files idempotently — runs safely on every startup:

```python
from pathlib import Path

moved = app.migrate({
    # v0.0 layout: everything under ~/.config/<product>/
    Path.home() / ".config" / "disk_cleaner" / "settings.json":
        app.config_dir / "settings.json",
    Path.home() / ".config" / "disk_cleaner" / "du_cache.db":
        app.cache_dir / "du_cache.db",
    Path.home() / ".config" / "disk_cleaner" / "snapshots.db":
        app.data_dir / "snapshots.db",
})
print(f"migrated {moved} files")
```

Files at the new path are **never overwritten** — if `new` exists, the
`old` is left in place. This makes it safe to run on every startup.

## Why a vendor namespace

Single-vendor apps put files at `~/.config/<product>/` — fine for one
product. Multi-product publishers benefit from grouping:

```
~/.config/codechu/
├── disk-cleaner/
├── file-explorer/
└── system-monitor/
```

One directory, full inventory. Pattern used by JetBrains
(`~/.config/JetBrains/`) and Mozilla (`~/.mozilla/`).

## Path resolution

Standard XDG environment variables:

| Path | Env var | Default |
|---|---|---|
| config | `XDG_CONFIG_HOME` | `~/.config` |
| cache | `XDG_CACHE_HOME` | `~/.cache` |
| data | `XDG_DATA_HOME` | `~/.local/share` |
| state | `XDG_STATE_HOME` | `~/.local/state` |
| runtime | `XDG_RUNTIME_DIR` | `/run/user/$UID` |

Resolved per-call from the `env` mapping you pass to `App` (or to the
base accessors). No ambient reads, no import-time snapshots — tests
pass a plain `dict` and get full isolation. See
[`docs/MIGRATION.md`](docs/MIGRATION.md) if you are upgrading from v0.1.

## Documentation

- [`docs/API.md`](docs/API.md) — full API reference
- [`docs/MIGRATION.md`](docs/MIGRATION.md) — v0.1 → v0.2 upgrade guide
- [`docs/RECIPES.md`](docs/RECIPES.md) — common patterns (testing,
  legacy migration, multi-user runtime dirs, vendor-namespacing
  rationale)

## Validation

- `vendor` and `product` must be non-empty and not contain `/`.
- All directories use safe `mkdir -p` semantics — no race-on-create.

## Multi-platform?

This library is **Linux-only** (XDG is a Linux/Unix spec). For macOS
or Windows in addition to Linux, see `platformdirs` on PyPI — note
that it does not enforce a vendor namespace on Linux.

## License

MIT — see [LICENSE](LICENSE).

Part of [Codechu](https://github.com/codechu).
