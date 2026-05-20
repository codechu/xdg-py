# Migration Guide — v0.1 → v0.2

v0.2 introduces the **explicit-config rule**: the library never reads
ambient state on its own. Callers pass `env` (and `uid` for runtime)
explicitly. This is a breaking change for anyone who imported the
module-level path constants or constructed `App` with positional args
only.

## Why the change

v0.1 captured `os.environ` and `os.getuid()` at *import time* and
exposed them as module constants:

```python
# v0.1 — DON'T do this anymore
from codechu_xdg import XDG_CONFIG_HOME
```

This had two real problems:

1. **Tests could not monkeypatch.** Setting `XDG_CONFIG_HOME` after
   import was a no-op because the constant was already snapshotted.
   The only workarounds were `importlib.reload()` (fragile) or
   subprocess isolation (slow).
2. **Ambient reads are surprising.** Code that worked in one process
   silently misbehaved when run under `sudo`, in a container, or with
   a stripped env.

v0.2 makes the resolution explicit. `App` and the base accessors now
take `env` (and, where needed, `uid`) as parameters. Tests pass a
plain `dict`; production code passes `default_env()`.

---

## Breaking changes

### 1. Module-level constants removed

`XDG_CONFIG_HOME`, `XDG_CACHE_HOME`, `XDG_DATA_HOME`, `XDG_STATE_HOME`,
and `XDG_RUNTIME_DIR` are **gone** from the public API. They were
import-time snapshots and broke test monkeypatching.

```python
# v0.1
from codechu_xdg import XDG_CONFIG_HOME
settings = XDG_CONFIG_HOME / "myapp" / "settings.json"

# v0.2
from codechu_xdg import config_home, default_env
settings = config_home(default_env()) / "myapp" / "settings.json"
```

### 2. `App` constructor signature

`env` and `uid` are now part of the constructor. `env` defaults to an
empty dict (so missing args do not fall through to `os.environ`); pass
`default_env()` for real-environment behavior.

```python
# v0.1
app = App("codechu", "disk-cleaner")

# v0.2
from codechu_xdg import App, default_env
app = App("codechu", "disk-cleaner", env=default_env())
```

Without `env=default_env()`, all XDG vars fall back to their `~/...`
defaults — which is usually fine but not what most production code
wants.

### 3. Base accessors require `env`

The five base accessors (`config_home`, `cache_home`, `data_home`,
`state_home`, `runtime_dir`) now require an explicit `env` argument.
`runtime_dir` additionally requires `uid`.

```python
# v0.1 (illustrative — these were constants, not functions)
from codechu_xdg import XDG_CACHE_HOME

# v0.2
from codechu_xdg import cache_home, default_env
cache_root = cache_home(default_env())
```

---

## New in v0.2

### `default_env()`

```python
from codechu_xdg import default_env
env = default_env()  # snapshot of os.environ as dict
```

Wrap-up of `dict(os.environ)`. Use in production code; do not use in
tests (just build a `dict` literal).

### Explicit `uid` for runtime

`runtime_dir(env, uid)` no longer reads `os.getuid()` internally.
`App` defaults its `uid` field to `os.getuid()` resolved **once** at
construction — no later ambient reads.

---

## Before / after

| Pattern | v0.1 | v0.2 |
|---|---|---|
| Read config root | `XDG_CONFIG_HOME` | `config_home(default_env())` |
| Read cache root | `XDG_CACHE_HOME` | `cache_home(default_env())` |
| Read data root | `XDG_DATA_HOME` | `data_home(default_env())` |
| Read state root | `XDG_STATE_HOME` | `state_home(default_env())` |
| Read runtime root | `XDG_RUNTIME_DIR` | `runtime_dir(default_env(), os.getuid())` |
| Construct App | `App("v", "p")` | `App("v", "p", env=default_env())` |
| Test with custom env | `monkeypatch.setenv(...)` + `importlib.reload` | `App("v", "p", env={"XDG_CONFIG_HOME": "/tmp/x"})` |

---

## Suggested migration steps

1. Search for `XDG_CONFIG_HOME`, `XDG_CACHE_HOME`, `XDG_DATA_HOME`,
   `XDG_STATE_HOME`, `XDG_RUNTIME_DIR` imports from `codechu_xdg`.
   Replace each with the corresponding function call.
2. Find every `App(...)` constructor call. Add `env=default_env()`.
   If you also rely on `XDG_RUNTIME_DIR` behavior in non-default
   environments (containers, fakeroot), consider passing `uid=` too.
3. Delete any `importlib.reload(codechu_xdg)` calls in tests — they
   are no longer needed.
4. Replace `monkeypatch.setenv("XDG_...", ...)` in tests with a plain
   `env={...}` dict passed to `App`.
5. Run your test suite. The explicit-env design surfaces previously
   silent ambient-state leaks; this is the goal, not regression.
