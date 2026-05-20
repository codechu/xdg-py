# Recipes — codechu-xdg 0.3.0

Seven common patterns. Copy-paste, adapt vendor / product slugs.

---

## 1. Standard app paths setup

The one you will use 95% of the time. Construct `App` once at startup,
call `ensure()`, then read paths off the instance.

```python
from codechu_xdg import App, default_env

app = App(vendor="codechu", product="disk-cleaner", env=default_env())
app.ensure()  # mkdir -p all five dirs

settings = app.settings_file()              # config_dir / settings.json
cache_db = app.cache_file("du_cache.db")    # cache_dir / du_cache.db
log_path = app.log_file()                   # state_dir / app.log
sock     = app.runtime_file("control.sock") # runtime_dir / control.sock
```

`ensure()` is idempotent — safe to call on every startup. Treat the
`App` instance as a singleton you pass through your DI graph.

---

## 2. Test with a custom env dict (no monkeypatch)

The explicit-env design exists for this. Build a `dict`, pass it as
`env=`, no monkeypatch, no `importlib.reload`.

```python
import pytest
from codechu_xdg import App

def test_config_dir_honors_xdg(tmp_path):
    env = {
        "XDG_CONFIG_HOME": str(tmp_path / "config"),
        "XDG_CACHE_HOME":  str(tmp_path / "cache"),
        "XDG_DATA_HOME":   str(tmp_path / "data"),
        "XDG_STATE_HOME":  str(tmp_path / "state"),
        "XDG_RUNTIME_DIR": str(tmp_path / "runtime"),
    }
    app = App("acme", "widget", env=env, uid=1000)
    app.ensure()

    assert app.config_dir == tmp_path / "config" / "acme" / "widget"
    assert app.config_dir.is_dir()


def test_fallbacks_when_env_empty(tmp_path, monkeypatch):
    # Only HOME needs to be patched — everything else is in the dict.
    monkeypatch.setenv("HOME", str(tmp_path))
    app = App("acme", "widget", env={}, uid=1000)

    assert app.config_dir == tmp_path / ".config" / "acme" / "widget"
    assert app.runtime_dir == Path("/run/user/1000") / "acme" / "widget"
```

Note: `Path.home()` still consults `$HOME`, so to fully isolate the
fallback path you patch `HOME` and pass `env={}` — that one env var is
the floor below which the library cannot go without re-implementing
`Path.home()`.

---

## 3. Migrate from legacy `~/.app-name/` to XDG layout

Most apps start out dumping everything under a single dotfile dir.
`migrate()` is built to move those files to their XDG homes on the
first run after the upgrade, idempotently.

```python
from pathlib import Path
from codechu_xdg import App, default_env

app = App("codechu", "disk-cleaner", env=default_env())

legacy = Path.home() / ".disk-cleaner"
moved = app.migrate({
    legacy / "settings.json": app.config_dir / "settings.json",
    legacy / "du_cache.db":   app.cache_dir / "du_cache.db",
    legacy / "snapshots.db":  app.data_dir / "snapshots.db",
    legacy / "app.log":       app.state_dir / "app.log",
})

if moved:
    print(f"migrated {moved} files from {legacy}")
    # Best practice: leave the legacy dir alone. If empty after migrate,
    # remove it manually — never recursively delete user data automatically.
    try:
        legacy.rmdir()  # only succeeds if empty
    except OSError:
        pass
```

Key properties:

- Files at the new path are **never** overwritten.
- Individual `OSError`s are swallowed (a missing legacy file is not a
  failure; that pair is just skipped).
- Returns count of files actually moved — `0` means nothing to do, a
  positive number means at least one file was migrated.

Run this every startup. After the first successful migration, the
legacy paths no longer exist and subsequent calls are no-ops.

---

## 4. Vendor-namespacing rationale — why `codechu/disk-cleaner/` not just `disk-cleaner/`

The library **requires** a vendor + product slug. This is deliberate.

### The problem with bare product names

Without a vendor namespace, every Linux app drops its directory at
the top level of `~/.config/`:

```
~/.config/
├── disk-cleaner/
├── file-explorer/
├── htop/
├── nvim/
├── system-monitor/
└── ... 47 more entries
```

You cannot tell at a glance which dirs are from which publisher. When
you uninstall a vendor's products, you have to know the exact list of
slugs to clean up. When a name collides across publishers (two
"disk-cleaner"s), one wins silently.

### With a vendor namespace

```
~/.config/codechu/
├── disk-cleaner/
├── file-explorer/
└── system-monitor/

~/.config/nvim/        ← unrelated, stays at the top level
```

One directory lists every product from a publisher. Uninstall sweeps
become `rm -rf ~/.config/codechu/`. Name collisions are scoped to the
vendor.

### Prior art

- **JetBrains**: `~/.config/JetBrains/IntelliJIdea2024.1/`, etc.
- **Mozilla**: `~/.mozilla/firefox/`, `~/.mozilla/thunderbird/`.
- **GNOME**: `~/.local/share/gnome-shell/`, etc., though the GNOME
  example is closer to a product family than a vendor.

The pattern is well-established for multi-product publishers.
codechu-xdg makes it mandatory because retroactively introducing a
vendor namespace later is a painful migration.

### What if I'm a solo publisher?

Use your GitHub org or personal handle as the vendor. The cost is
one extra directory level; the benefit is forward-compatibility if
you ever ship a second product.

---

## 5. Multi-user safe runtime dirs

`runtime_dir` falls back to `/run/user/<uid>` when `XDG_RUNTIME_DIR`
is unset. The fallback uid is captured at `App` construction (default:
`os.getuid()`), so the path is stable for the lifetime of the instance
even if the process later changes uid (rare, but possible under
`setuid` or container init).

```python
import os
from codechu_xdg import App, default_env

# Normal desktop session — XDG_RUNTIME_DIR is set by systemd-logind.
app = App("codechu", "disk-cleaner", env=default_env())
print(app.runtime_dir)  # /run/user/1000/codechu/disk-cleaner

# Service running as a different user (e.g. a worker process):
worker_uid = 1001
app = App(
    "codechu", "disk-cleaner",
    env=default_env(),
    uid=worker_uid,
)
print(app.runtime_dir)  # /run/user/1001/codechu/disk-cleaner

# Tests / containers without /run/user populated:
app = App(
    "codechu", "disk-cleaner",
    env={"XDG_RUNTIME_DIR": "/tmp/test-runtime"},
    uid=1000,
)
print(app.runtime_dir)  # /tmp/test-runtime/codechu/disk-cleaner
```

### Cleanup at shutdown

Runtime files (sockets, pid files) should not survive across runs.
`remove_runtime()` wipes the contents of the runtime dir without
removing the dir itself:

```python
import atexit
atexit.register(app.remove_runtime)
```

Or run it eagerly at startup to clear stale state from a crashed
previous run:

```python
app.ensure()
app.remove_runtime()  # clean slate
app.ensure()          # re-create the (now empty) runtime dir
```

`remove_runtime()` is best-effort — individual `OSError`s are
swallowed, so a leftover socket held by another process will not
crash your cleanup.

---

## 6. Read user config with system fallback (`find_file`)

The classic "user override, packaged default" pattern. Ship your
default config under `/usr/share/codechu/disk-cleaner/settings.toml`,
let users drop their own copy at `~/.config/codechu/disk-cleaner/`,
and resolve the right one with one call.

```python
from codechu_xdg import App, default_env

app = App("codechu", "disk-cleaner", env=default_env())

path = app.find_file("settings.toml", kind="config")
if path is None:
    raise SystemExit("settings.toml not found (no user copy, no packaged default)")

print(f"loading config from {path}")
text = path.read_text()
```

Search order is `[app.config_dir, *app.config_dirs]` — i.e. the user's
`~/.config/codechu/disk-cleaner/` wins, then each `$XDG_CONFIG_DIRS`
entry (default `/etc/xdg/codechu/disk-cleaner/`) is tried in order.

For first-run bootstrap (copy the system default to the user dir on
first launch):

```python
user = app.config_dir / "settings.toml"
if not user.exists():
    packaged = app.find_file("settings.toml", kind="config")
    if packaged is not None:
        app.ensure()
        user.write_text(packaged.read_text())
```

Returns `None` cleanly when nothing matches — wrap in your own
"not configured" error if absence is fatal for your app.

---

## 7. Search across `XDG_DATA_DIRS` for a shared resource

Themes, icon sets, schemas, plugin manifests — anything a sysadmin
might install system-wide that the user can override. Pass
`kind="data"` to search the data dirs instead of config dirs.

```python
from codechu_xdg import App, default_env

app = App("codechu", "disk-cleaner", env=default_env())

theme = app.find_file("themes/dark.css", kind="data")
if theme is not None:
    inject_stylesheet(theme.read_text())
```

`find_file` accepts a relative subpath in `name` (it is joined with
`Path.__truediv__`), so `"themes/dark.css"` finds either
`~/.local/share/codechu/disk-cleaner/themes/dark.css` or
`/usr/share/codechu/disk-cleaner/themes/dark.css`, whichever exists
first.

To iterate every match (not just the first) — e.g. when collecting
plugin manifests from every installed location — bypass `find_file`
and walk the namespaced dir list directly:

```python
manifests = []
for base in [app.data_dir, *app.data_dirs]:
    plugins = base / "plugins"
    if plugins.is_dir():
        manifests.extend(plugins.glob("*.toml"))
```

The vendor namespace is applied for you on `app.data_dirs`, so each
`base` already ends in `/codechu/disk-cleaner/`. If you need the raw
system bases (no namespace) for a cross-vendor lookup, call the
module-level `data_dirs(env)` instead.
