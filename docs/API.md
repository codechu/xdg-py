# API Reference — codechu-xdg 0.3.0

Vendor-namespaced [XDG Base Directory](https://specifications.freedesktop.org/basedir-spec/)
paths for Linux desktop apps. Stdlib-only, ~80 LOC, no ambient reads.

## Explicit-config rule

This library never reads ambient state on its own. Every accessor takes
an explicit `env` mapping; `runtime_dir` additionally takes an explicit
`uid`. Callers pass [`default_env()`](#default_env) and `os.getuid()` to
get real behavior; tests pass a plain `dict` and need no monkeypatching.

---

## `class App`

```python
from codechu_xdg import App, default_env

app = App(vendor="codechu", product="disk-cleaner", env=default_env())
```

Frozen dataclass. Vendor-namespaced application paths.

### Constructor

| Parameter | Type | Default | Description |
|---|---|---|---|
| `vendor` | `str` | — | Publisher slug, e.g. `"codechu"`. Must be non-empty and contain no `/`. |
| `product` | `str` | — | Product slug, e.g. `"disk-cleaner"`. Must be non-empty and contain no `/`. |
| `env` | `Mapping[str, str]` | `{}` | Environment mapping used to resolve XDG vars. Pass `default_env()` for real env. |
| `uid` | `int` | `os.getuid()` | User id for the `runtime_dir` fallback when `XDG_RUNTIME_DIR` is unset. Resolved once at construction. |

Raises `ValueError` if `vendor` or `product` is empty or contains `/`.

### Path properties

Every path is `<XDG base>/<vendor>/<product>/`.

| Property | Resolves to | Purpose |
|---|---|---|
| `config_dir` | `$XDG_CONFIG_HOME/<vendor>/<product>` | Settings, user config files |
| `cache_dir` | `$XDG_CACHE_HOME/<vendor>/<product>` | Regeneratable cache (safe to wipe) |
| `data_dir` | `$XDG_DATA_HOME/<vendor>/<product>` | Persistent user data |
| `state_dir` | `$XDG_STATE_HOME/<vendor>/<product>` | Logs, history, recovery |
| `runtime_dir` | `$XDG_RUNTIME_DIR/<vendor>/<product>` | Sockets, pid files, locks |
| `data_dirs` | `[<base>/<vendor>/<product> for base in $XDG_DATA_DIRS]` | System data dirs (read-only, search) |
| `config_dirs` | `[<base>/<vendor>/<product> for base in $XDG_CONFIG_DIRS]` | System config dirs (read-only, search) |

All properties return `pathlib.Path`. They do not create directories —
call [`ensure()`](#ensure) for that.

### Methods

#### `ensure() -> None`

`mkdir -p` for all five directories. Idempotent. Safe to call on every
startup.

#### `migrate(mapping: dict[Path, Path]) -> int`

Idempotent legacy → new path mover. For each `old -> new` pair:

- If `old` exists and `new` does **not**, move `old` to `new`.
- Existing `new` is **never** overwritten.
- Individual `OSError`s are swallowed (best-effort).

Calls `ensure()` first. Returns the number of files actually moved.

#### `remove_cache() -> int`

Delete the **contents** of `cache_dir` (the directory itself stays).
Files, symlinks, and empty subdirs are removed deepest-first so parents
become empty before they are unlinked. Returns count of removed entries.
Swallows individual `OSError`s.

#### `remove_runtime() -> int`

Same semantics as `remove_cache()`, but targets `runtime_dir`. Useful at
shutdown for stale sockets and pid files.

#### `find_file(name: str, kind: str = "config") -> Path | None`

Search the user dir first, then the system dirs, for a file named `name`.
Returns the first matching `Path`, or `None` if no match exists.

- `kind="config"` searches `[config_dir, *config_dirs]`.
- `kind="data"` searches `[data_dir, *data_dirs]`.
- Any other `kind` raises `ValueError`.

Matches use `Path.exists()`, so files, dirs, and symlinks (to existing
targets) all count. Use this to implement "user override, system
default" lookups for shared resources (themes, schemas, fixtures).

### Convenience file-path helpers

These return a `Path` only; they do not touch the filesystem.

| Method | Returns |
|---|---|
| `settings_file(name="settings.json")` | `config_dir / name` |
| `cache_file(name)` | `cache_dir / name` |
| `data_file(name)` | `data_dir / name` |
| `log_file(name="app.log")` | `state_dir / name` |
| `runtime_file(name)` | `runtime_dir / name` |

### `__repr__`

`App(vendor='codechu', product='disk-cleaner')` — `env` and `uid` are
omitted for readability.

---

## `default_env() -> Mapping[str, str]`

Returns a snapshot of `os.environ` as a plain `dict`.

```python
app = App("acme", "widget", env=default_env())
```

Use this when you want real-environment behavior. Tests should construct
a `dict` directly instead of calling `default_env()`.

---

## Pure XDG base accessors

Module-level functions that resolve a single XDG base directory from an
explicit `env`. Use these when you do not need the vendor/product
namespace (rare — `App` is usually what you want).

### `config_home(env: Mapping[str, str]) -> Path`

`env["XDG_CONFIG_HOME"]` if set, else `~/.config`.

### `cache_home(env: Mapping[str, str]) -> Path`

`env["XDG_CACHE_HOME"]` if set, else `~/.cache`.

### `data_home(env: Mapping[str, str]) -> Path`

`env["XDG_DATA_HOME"]` if set, else `~/.local/share`.

### `state_home(env: Mapping[str, str]) -> Path`

`env["XDG_STATE_HOME"]` if set, else `~/.local/state`.

### `runtime_dir(env: Mapping[str, str], uid: int) -> Path`

`env["XDG_RUNTIME_DIR"]` if set, else `/run/user/<uid>`.

`uid` is required — there is no implicit `os.getuid()` here. Callers
that want the real uid pass `os.getuid()` explicitly.

### `data_dirs(env: Mapping[str, str]) -> list[Path]`

Colon-separated paths from `env["XDG_DATA_DIRS"]`, else the spec
fallback `/usr/local/share:/usr/share`. Empty or unset env var falls
back. Empty entries inside a non-empty list are skipped.

### `config_dirs(env: Mapping[str, str]) -> list[Path]`

Same shape as `data_dirs`, for `env["XDG_CONFIG_DIRS"]`. Fallback:
`/etc/xdg`.

---

## XDG fallback table

| Function / property | Env var | Fallback when env var unset |
|---|---|---|
| `config_home` | `XDG_CONFIG_HOME` | `~/.config` |
| `cache_home` | `XDG_CACHE_HOME` | `~/.cache` |
| `data_home` | `XDG_DATA_HOME` | `~/.local/share` |
| `state_home` | `XDG_STATE_HOME` | `~/.local/state` |
| `runtime_dir` | `XDG_RUNTIME_DIR` | `/run/user/<uid>` |
| `data_dirs` | `XDG_DATA_DIRS` | `/usr/local/share:/usr/share` |
| `config_dirs` | `XDG_CONFIG_DIRS` | `/etc/xdg` |

An "unset" var means either missing from `env` **or** present as an
empty string — both fall back. `Path.home()` is used for the `~`
expansion in the first four fallbacks (this honors `$HOME`).

---

## Validation rules

- `vendor` must be truthy and contain no `/`.
- `product` must be truthy and contain no `/`.
- Violations raise `ValueError` from `App.__post_init__`.
- No other validation is performed; XDG vars containing weird values
  are passed through to `pathlib.Path` as-is.

---

## Thread / fork safety

`App` is a frozen dataclass; instances are immutable. The mutating
methods (`ensure`, `migrate`, `remove_cache`, `remove_runtime`) touch
the filesystem and rely on the kernel's atomicity for `mkdir -p`,
`rename`, and `unlink`. There is no internal lock; concurrent calls
from multiple processes are safe under standard POSIX semantics.
