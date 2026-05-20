"""Vendor-namespaced XDG paths for Linux desktop apps.

Standard XDG Base Directory Spec (https://specifications.freedesktop.org/basedir-spec/)
with a mandatory vendor + product namespace, so multiple products from the
same publisher live under one directory.

**Explicit-config rule:** This library never reads ambient state on its own.
Every function and ``App`` instance takes an explicit ``env`` mapping (and,
for ``runtime_dir``, an explicit ``uid``). Callers pass ``default_env()`` /
``os.getuid()`` when they want the real environment; tests pass a plain
``dict`` and get full isolation without monkeypatching.

Example::

    from codechu_xdg import App, default_env

    app = App(vendor="codechu", product="disk-cleaner", env=default_env())
    app.ensure()

    settings_path = app.config_dir / "settings.json"
    cache_db      = app.cache_dir  / "du_cache.db"
    pid_file      = app.runtime_dir / "watchdog.pid"
    sock_file     = app.runtime_dir / "control.sock"

Migration::

    moved = app.migrate({
        Path.home() / ".config" / "disk_cleaner" / "settings.json":
            app.config_dir / "settings.json",
    })
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

__version__ = "0.3.0"
__all__ = [
    "App",
    "config_home",
    "cache_home",
    "data_home",
    "state_home",
    "runtime_dir",
    "data_dirs",
    "config_dirs",
    "default_env",
]


def default_env() -> Mapping[str, str]:
    """Return a snapshot of ``os.environ`` as a plain ``dict``.

    Use this when you want the real environment::

        app = App("acme", "widget", env=default_env())

    Tests should construct a ``dict`` directly instead.
    """
    return dict(os.environ)


def _xdg(env: Mapping[str, str], var: str, default: str) -> Path:
    """Read XDG var from ``env``, fall back to ``~/<default>``."""
    value = env.get(var)
    if value:
        return Path(value)
    return Path.home() / default


# ── Pure XDG base accessors ─────────────────────────────────────────
#
# All take an explicit ``env`` mapping. No ambient reads.


def config_home(env: Mapping[str, str]) -> Path:
    """``$XDG_CONFIG_HOME`` from ``env`` or ``~/.config``."""
    return _xdg(env, "XDG_CONFIG_HOME", ".config")


def cache_home(env: Mapping[str, str]) -> Path:
    """``$XDG_CACHE_HOME`` from ``env`` or ``~/.cache``."""
    return _xdg(env, "XDG_CACHE_HOME", ".cache")


def data_home(env: Mapping[str, str]) -> Path:
    """``$XDG_DATA_HOME`` from ``env`` or ``~/.local/share``."""
    return _xdg(env, "XDG_DATA_HOME", ".local/share")


def state_home(env: Mapping[str, str]) -> Path:
    """``$XDG_STATE_HOME`` from ``env`` or ``~/.local/state``."""
    return _xdg(env, "XDG_STATE_HOME", ".local/state")


def runtime_dir(env: Mapping[str, str], uid: int) -> Path:
    """``$XDG_RUNTIME_DIR`` from ``env`` or ``/run/user/<uid>``.

    ``uid`` is required (no implicit ``os.getuid()``). Callers that
    want the real uid should pass ``os.getuid()`` explicitly.
    """
    value = env.get("XDG_RUNTIME_DIR")
    if value:
        return Path(value)
    return Path(f"/run/user/{uid}")


def _xdg_dirs(env: Mapping[str, str], var: str, default: str) -> list[Path]:
    """Read colon-separated XDG dirs list from ``env``, fall back to ``default``.

    Empty / unset env vars fall back to the spec default. Empty entries within
    a non-empty list are skipped.
    """
    value = env.get(var)
    if not value:
        value = default
    return [Path(p) for p in value.split(":") if p]


def data_dirs(env: Mapping[str, str]) -> list[Path]:
    """``$XDG_DATA_DIRS`` from ``env`` or ``/usr/local/share:/usr/share``.

    Returns the list of system data dirs (read-only, search across them).
    """
    return _xdg_dirs(env, "XDG_DATA_DIRS", "/usr/local/share:/usr/share")


def config_dirs(env: Mapping[str, str]) -> list[Path]:
    """``$XDG_CONFIG_DIRS`` from ``env`` or ``/etc/xdg``.

    Returns the list of system config dirs (read-only, search across them).
    """
    return _xdg_dirs(env, "XDG_CONFIG_DIRS", "/etc/xdg")


@dataclass(frozen=True)
class App:
    """Vendor-namespaced application paths.

    ``vendor`` is the publisher / organization slug (e.g. ``"codechu"``).
    ``product`` is the product slug (e.g. ``"disk-cleaner"``).
    ``env`` is the environment mapping used to resolve XDG vars. Pass
    :func:`default_env` for the real environment, or a plain ``dict``
    in tests.
    ``uid`` is the user id used for the ``runtime_dir`` fallback when
    ``XDG_RUNTIME_DIR`` is unset. Defaults to ``os.getuid()`` resolved
    once at construction time (no later ambient reads).
    """

    vendor: str
    product: str
    env: Mapping[str, str] = field(default_factory=dict)
    uid: int = field(default_factory=os.getuid)

    def __post_init__(self) -> None:
        if not self.vendor or "/" in self.vendor:
            raise ValueError(f"invalid vendor: {self.vendor!r}")
        if not self.product or "/" in self.product:
            raise ValueError(f"invalid product: {self.product!r}")

    @property
    def config_dir(self) -> Path:
        """``$XDG_CONFIG_HOME/<vendor>/<product>``."""
        return config_home(self.env) / self.vendor / self.product

    @property
    def cache_dir(self) -> Path:
        """``$XDG_CACHE_HOME/<vendor>/<product>`` — regeneratable."""
        return cache_home(self.env) / self.vendor / self.product

    @property
    def data_dir(self) -> Path:
        """``$XDG_DATA_HOME/<vendor>/<product>`` — persistent user data."""
        return data_home(self.env) / self.vendor / self.product

    @property
    def state_dir(self) -> Path:
        """``$XDG_STATE_HOME/<vendor>/<product>`` — log files, history, recovery."""
        return state_home(self.env) / self.vendor / self.product

    @property
    def runtime_dir(self) -> Path:
        """``$XDG_RUNTIME_DIR/<vendor>/<product>`` — sockets, pid files, locks."""
        return runtime_dir(self.env, self.uid) / self.vendor / self.product

    @property
    def data_dirs(self) -> list[Path]:
        """``[<base>/<vendor>/<product> for base in XDG_DATA_DIRS]`` — system data dirs.

        Read-only; caller searches across them (see :meth:`find_file`).
        """
        return [base / self.vendor / self.product for base in data_dirs(self.env)]

    @property
    def config_dirs(self) -> list[Path]:
        """``[<base>/<vendor>/<product> for base in XDG_CONFIG_DIRS]`` — system config dirs.

        Read-only; caller searches across them (see :meth:`find_file`).
        """
        return [base / self.vendor / self.product for base in config_dirs(self.env)]

    def find_file(self, name: str, kind: str = "config") -> Path | None:
        """Search user dir first, then system dirs, for ``name``. Return first hit or ``None``.

        ``kind="config"`` searches ``[config_dir, *config_dirs]``.
        ``kind="data"`` searches ``[data_dir, *data_dirs]``.

        Raises ``ValueError`` for any other ``kind``.
        """
        if kind == "config":
            search = [self.config_dir, *self.config_dirs]
        elif kind == "data":
            search = [self.data_dir, *self.data_dirs]
        else:
            raise ValueError(f"invalid kind: {kind!r} (expected 'config' or 'data')")
        for base in search:
            candidate = base / name
            if candidate.exists():
                return candidate
        return None

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
