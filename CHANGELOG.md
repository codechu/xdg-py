# Changelog

[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) + [SemVer](https://semver.org/).

## [Unreleased]

## [0.3.0] — 2026-05-20

### Added
- `data_dirs(env)` and `config_dirs(env)` module-level accessors for
  `XDG_DATA_DIRS` (fallback `/usr/local/share:/usr/share`) and
  `XDG_CONFIG_DIRS` (fallback `/etc/xdg`). Empty or unset env vars
  fall back to the spec defaults.
- `App.data_dirs` / `App.config_dirs` properties — vendor-namespaced
  list of system dirs (`<base>/<vendor>/<product>/`).
- `App.find_file(name, kind="config")` — searches user dir first,
  then system dirs, returning the first existing `Path` or `None`.
  `kind="config"` searches config dirs, `kind="data"` searches data
  dirs.

## [0.2.0] — 2026-05-20

### Changed
- XDG base directory resolution is now lazy: `App` path properties read
  the XDG environment variables on each access (not at import time), so
  tests can monkeypatch env vars without reloading the module.
- `XDG_RUNTIME_DIR` no longer calls `os.getuid()` at import time.

### Added
- Module-level accessor functions: `config_home()`, `cache_home()`,
  `data_home()`, `state_home()`, `runtime_dir()`. Each reads the
  environment on every call.

### Deprecated
- Module-level constants `XDG_CONFIG_HOME`, `XDG_CACHE_HOME`,
  `XDG_DATA_HOME`, `XDG_STATE_HOME`, `XDG_RUNTIME_DIR` remain as
  import-time snapshots for backwards compatibility. Prefer the
  accessor functions or `App` properties.

## [0.1.0] — 2026-05-19

### Added
- Initial release
- `App(vendor, product)` dataclass with 5 XDG path properties:
  `config_dir`, `cache_dir`, `data_dir`, `state_dir`, `runtime_dir`
- `ensure()` — mkdir -p all directories
- `migrate(mapping)` — idempotent legacy → new path mover
- Validation: vendor and product must be non-empty and contain no `/`
- Standard XDG env var honoring: `XDG_CONFIG_HOME`, `XDG_CACHE_HOME`,
  `XDG_DATA_HOME`, `XDG_STATE_HOME`, `XDG_RUNTIME_DIR`
