"""Vendor-namespaced XDG paths for Linux desktop apps.

Standard XDG Base Directory Spec (https://specifications.freedesktop.org/basedir-spec/)
with a mandatory vendor + product namespace, so multiple products from the
same publisher live under one directory.

Example::

    from codechu_xdg import App

    app = App(vendor="codechu", product="disk-cleaner")
    app.ensure()

    settings_path = app.config_dir / "settings.json"
    cache_db      = app.cache_dir  / "du_cache.db"
    pid_file      = app.runtime_dir / "watchdog.pid"
    sock_file     = app.runtime_dir / "control.sock"

Migration::

    moved = app.migrate({
        Path.home() / ".config" / "disk_cleaner" / "settings.json":
            app.config_dir / "settings.json",
        Path.home() / ".config" / "disk_cleaner" / "du_cache.db":
            app.cache_dir / "du_cache.db",
    })
    print(f"migrated {moved} files")
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

__version__ = "0.2.0"
__all__ = [
    "App",
    "config_home",
    "cache_home",
    "data_home",
    "state_home",
    "runtime_dir",
    "XDG_CONFIG_HOME",
    "XDG_CACHE_HOME",
    "XDG_DATA_HOME",
    "XDG_RUNTIME_DIR",
    "XDG_STATE_HOME",
]


def _xdg(env: str, default: str) -> Path:
    """Read an XDG env var, fall back to ``~/<default>``."""
    value = os.environ.get(env)
    if value:
        return Path(value)
    return Path.home() / default


# ── Lazy XDG base accessors ─────────────────────────────────────────
#
# These read the environment on every call, so tests can monkeypatch
# env vars after import without reloading the module.


def config_home() -> Path:
    """``$XDG_CONFIG_HOME`` or ``~/.config``."""
    return _xdg("XDG_CONFIG_HOME", ".config")


def cache_home() -> Path:
    """``$XDG_CACHE_HOME`` or ``~/.cache``."""
    return _xdg("XDG_CACHE_HOME", ".cache")


def data_home() -> Path:
    """``$XDG_DATA_HOME`` or ``~/.local/share``."""
    return _xdg("XDG_DATA_HOME", ".local/share")


def state_home() -> Path:
    """``$XDG_STATE_HOME`` or ``~/.local/state``."""
    return _xdg("XDG_STATE_HOME", ".local/state")


def runtime_dir() -> Path:
    """``$XDG_RUNTIME_DIR`` or ``/run/user/<uid>``.

    Reads env + ``os.getuid()`` on every call (not at import time), so
    tests can monkeypatch ``XDG_RUNTIME_DIR`` freely.
    """
    env = os.environ.get("XDG_RUNTIME_DIR")
    if env:
        return Path(env)
    return Path(f"/run/user/{os.getuid()}")


# ── Module-level constants (backwards compatibility) ────────────────
#
# Snapshots captured at import time. Prefer the accessor functions
# above (or the ``App`` properties) for code that needs to see env
# changes without a module reload.

XDG_CONFIG_HOME: Path = config_home()
XDG_CACHE_HOME: Path = cache_home()
XDG_DATA_HOME: Path = data_home()
XDG_STATE_HOME: Path = state_home()
XDG_RUNTIME_DIR: Path = runtime_dir()


@dataclass(frozen=True)
class App:
    """Vendor-namespaced application paths.

    ``vendor`` is the publisher / organization slug (e.g. ``"codechu"``).
    ``product`` is the product slug (e.g. ``"disk-cleaner"``).

    Both are namespace components — they appear in every directory path
    so multiple products from the same vendor live together under one
    directory (``~/.config/<vendor>/`` shows them all).

    All path properties resolve lazily: they read the XDG environment
    variables on each access, so tests can monkeypatch env vars freely
    without reloading the module.
    """

    vendor: str
    product: str

    def __post_init__(self) -> None:
        if not self.vendor or "/" in self.vendor:
            raise ValueError(f"invalid vendor: {self.vendor!r}")
        if not self.product or "/" in self.product:
            raise ValueError(f"invalid product: {self.product!r}")

    @property
    def config_dir(self) -> Path:
        """``$XDG_CONFIG_HOME/<vendor>/<product>``."""
        return config_home() / self.vendor / self.product

    @property
    def cache_dir(self) -> Path:
        """``$XDG_CACHE_HOME/<vendor>/<product>`` — regeneratable."""
        return cache_home() / self.vendor / self.product

    @property
    def data_dir(self) -> Path:
        """``$XDG_DATA_HOME/<vendor>/<product>`` — persistent user data."""
        return data_home() / self.vendor / self.product

    @property
    def state_dir(self) -> Path:
        """``$XDG_STATE_HOME/<vendor>/<product>`` — log files, history, recovery."""
        return state_home() / self.vendor / self.product

    @property
    def runtime_dir(self) -> Path:
        """``$XDG_RUNTIME_DIR/<vendor>/<product>`` — sockets, pid files, locks."""
        return runtime_dir() / self.vendor / self.product

    def ensure(self) -> None:
        """Create all five directories if missing (mkdir -p semantics)."""
        for d in (self.config_dir, self.cache_dir, self.data_dir, self.state_dir, self.runtime_dir):
            d.mkdir(parents=True, exist_ok=True)

    def migrate(self, mapping: dict[Path, Path]) -> int:
        """Idempotent legacy → new path migration.

        For each ``old -> new`` pair: if ``old`` exists and ``new`` does
        not, move ``old`` to ``new``. Existing ``new`` is never overwritten.
        Errors on individual entries are swallowed (best-effort).

        Returns the number of files actually moved.
        """
        moved = 0
        self.ensure()
        for old, new in mapping.items():
            if old.exists() and not new.exists():
                try:
                    new.parent.mkdir(parents=True, exist_ok=True)
                    old.replace(new)
                    moved += 1
                except OSError:
                    pass
        return moved

    # ── Convenience file path helpers ───────────────────────────────

    def settings_file(self, name: str = "settings.json") -> Path:
        """Canonical settings file: ``config_dir / <name>`` (default: settings.json)."""
        return self.config_dir / name

    def cache_file(self, name: str) -> Path:
        """Canonical cache file: ``cache_dir / <name>``."""
        return self.cache_dir / name

    def data_file(self, name: str) -> Path:
        """Canonical persistent-data file: ``data_dir / <name>``."""
        return self.data_dir / name

    def log_file(self, name: str = "app.log") -> Path:
        """Canonical log file: ``state_dir / <name>`` (default: app.log)."""
        return self.state_dir / name

    def runtime_file(self, name: str) -> Path:
        """Canonical runtime file (sockets, pid files): ``runtime_dir / <name>``."""
        return self.runtime_dir / name

    # ── Cleanup ─────────────────────────────────────────────────────

    def remove_cache(self) -> int:
        """Delete contents of ``cache_dir`` (regeneratable — safe to wipe).

        Returns the number of items removed (files + directories).
        Swallows individual OSErrors.
        """
        return _wipe(self.cache_dir)

    def remove_runtime(self) -> int:
        """Delete contents of ``runtime_dir`` (sockets, pids — recreated on next run).

        Useful for shutdown cleanup (stale pids, dead sockets).
        """
        return _wipe(self.runtime_dir)

    def __repr__(self) -> str:
        return f"App(vendor={self.vendor!r}, product={self.product!r})"


def _wipe(root: Path) -> int:
    """Recursively remove contents of ``root`` (but not the dir itself).

    Returns count of removed entries. Swallows individual OSErrors.
    """
    if not root.exists():
        return 0
    removed = 0
    # leaves first (deepest paths) so rmdir succeeds for parents
    for item in sorted(root.rglob("*"), key=lambda p: -len(str(p))):
        try:
            if item.is_file() or item.is_symlink():
                item.unlink()
                removed += 1
            elif item.is_dir():
                item.rmdir()
                removed += 1
        except OSError:
            pass
    return removed
