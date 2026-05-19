# Changelog

[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) + [SemVer](https://semver.org/).

## [Unreleased]

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
