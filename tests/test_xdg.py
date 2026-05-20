"""Tests for codechu_xdg — XDG path resolution + migration.

These tests exercise the explicit-config API: every ``App`` is built
with a plain ``dict`` for ``env`` and an explicit ``uid``. No
monkeypatching, no module reloads, no ambient state.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

import codechu_xdg
from codechu_xdg import App, default_env


# ── Path resolution ─────────────────────────────────────────────────


def test_app_paths_basic():
    app = App(vendor="codechu", product="my-product", env={}, uid=1000)
    assert app.config_dir.name == "my-product"
    assert app.config_dir.parent.name == "codechu"
    assert "my-product" in str(app.runtime_dir)


def test_paths_distinct():
    app = App("acme", "widget", env={}, uid=1000)
    paths = {app.config_dir, app.cache_dir, app.data_dir, app.state_dir, app.runtime_dir}
    assert len(paths) == 5  # all different


def test_namespace_in_every_path():
    app = App("vendor1", "prod1", env={}, uid=1000)
    for d in (app.config_dir, app.cache_dir, app.data_dir, app.state_dir, app.runtime_dir):
        assert "vendor1" in d.parts
        assert "prod1" in d.parts


def test_xdg_env_override(tmp_path):
    """When XDG_CONFIG_HOME is set in env, paths follow it."""
    custom = tmp_path / "custom_config"
    env = {"XDG_CONFIG_HOME": str(custom)}
    app = App("v", "p", env=env, uid=1000)
    assert str(app.config_dir).startswith(str(custom))


def test_runtime_dir_uses_explicit_uid():
    """Runtime fallback uses the uid passed at construction, not os.getuid()."""
    app = App("v", "p", env={}, uid=4242)
    assert "/run/user/4242/" in str(app.runtime_dir) + "/"


def test_runtime_dir_env_beats_uid_fallback(tmp_path):
    env = {"XDG_RUNTIME_DIR": str(tmp_path / "rt")}
    app = App("v", "p", env=env, uid=4242)
    assert str(app.runtime_dir).startswith(str(tmp_path / "rt"))
    assert "4242" not in str(app.runtime_dir)


# ── Validation ──────────────────────────────────────────────────────


def test_empty_vendor_rejected():
    with pytest.raises(ValueError):
        App(vendor="", product="x", env={}, uid=0)


def test_empty_product_rejected():
    with pytest.raises(ValueError):
        App(vendor="x", product="", env={}, uid=0)


def test_slash_rejected():
    with pytest.raises(ValueError):
        App(vendor="bad/vendor", product="x", env={}, uid=0)
    with pytest.raises(ValueError):
        App(vendor="x", product="bad/product", env={}, uid=0)


# ── ensure() ────────────────────────────────────────────────────────


def _all_xdg_env(tmp_path):
    return {
        "XDG_CONFIG_HOME": str(tmp_path / "c"),
        "XDG_CACHE_HOME": str(tmp_path / "ca"),
        "XDG_DATA_HOME": str(tmp_path / "d"),
        "XDG_STATE_HOME": str(tmp_path / "s"),
        "XDG_RUNTIME_DIR": str(tmp_path / "r"),
    }


def test_ensure_creates_all_dirs(tmp_path):
    app = App("v", "p", env=_all_xdg_env(tmp_path), uid=1000)
    app.ensure()
    for d in (app.config_dir, app.cache_dir, app.data_dir, app.state_dir, app.runtime_dir):
        assert d.exists()
        assert d.is_dir()


def test_ensure_idempotent(tmp_path):
    app = App("v", "p", env=_all_xdg_env(tmp_path), uid=1000)
    app.ensure()
    app.ensure()  # second call — no error
    assert app.config_dir.exists()


# ── migrate() ────────────────────────────────────────────────────────


def test_migrate_moves_existing(tmp_path):
    app = App("v", "p", env=_all_xdg_env(tmp_path), uid=1000)
    legacy = tmp_path / "legacy" / "settings.json"
    legacy.parent.mkdir(parents=True)
    legacy.write_text('{"key": "value"}')
    new_path = app.config_dir / "settings.json"

    moved = app.migrate({legacy: new_path})
    assert moved == 1
    assert new_path.exists()
    assert new_path.read_text() == '{"key": "value"}'
    assert not legacy.exists()


def test_migrate_skips_when_new_exists(tmp_path):
    app = App("v", "p", env=_all_xdg_env(tmp_path), uid=1000)
    app.ensure()
    legacy = tmp_path / "old.json"
    legacy.write_text("legacy")
    new = app.config_dir / "new.json"
    new.write_text("already exists")

    moved = app.migrate({legacy: new})
    assert moved == 0
    assert legacy.exists()  # untouched
    assert new.read_text() == "already exists"  # untouched


def test_migrate_skips_when_legacy_missing(tmp_path):
    app = App("v", "p", env=_all_xdg_env(tmp_path), uid=1000)
    nonexistent = tmp_path / "nope.json"
    new = app.config_dir / "new.json"

    moved = app.migrate({nonexistent: new})
    assert moved == 0
    assert not new.exists()


def test_repr():
    app = App("acme", "widget", env={}, uid=0)
    assert "acme" in repr(app)
    assert "widget" in repr(app)


# ── Convenience helpers ──────────────────────────────────────────────


def test_settings_file_default_name(tmp_path):
    app = App("v", "p", env={"XDG_CONFIG_HOME": str(tmp_path)}, uid=1000)
    assert app.settings_file().name == "settings.json"
    assert app.settings_file("custom.json").name == "custom.json"


def test_file_helpers_return_correct_subdir(tmp_path):
    app = App("v", "p", env=_all_xdg_env(tmp_path), uid=1000)
    assert app.settings_file().parent == app.config_dir
    assert app.cache_file("db.sqlite").parent == app.cache_dir
    assert app.data_file("history.json").parent == app.data_dir
    assert app.log_file().parent == app.state_dir
    assert app.runtime_file("watchdog.pid").parent == app.runtime_dir


# ── Cleanup helpers ──────────────────────────────────────────────────


def test_remove_cache_clears_contents(tmp_path):
    env = {"XDG_CACHE_HOME": str(tmp_path / "cache")}
    app = App("v", "p", env=env, uid=1000)
    app.ensure()
    # Populate cache with files + subdir
    (app.cache_dir / "a.bin").write_text("a")
    (app.cache_dir / "b.bin").write_text("b")
    sub = app.cache_dir / "sub"
    sub.mkdir()
    (sub / "c.bin").write_text("c")

    removed = app.remove_cache()
    assert removed == 4  # 3 files + 1 dir
    # cache_dir itself remains
    assert app.cache_dir.exists()
    assert list(app.cache_dir.iterdir()) == []


def test_remove_runtime_clears_sockets(tmp_path):
    env = {"XDG_RUNTIME_DIR": str(tmp_path / "rt")}
    app = App("v", "p", env=env, uid=1000)
    app.ensure()
    (app.runtime_dir / "watchdog.pid").write_text("12345")
    (app.runtime_dir / "control.sock").touch()

    removed = app.remove_runtime()
    assert removed == 2
    assert app.runtime_dir.exists()


def test_remove_on_nonexistent_dir():
    """Wiping a non-existent dir returns 0, doesn't crash."""
    app = App("nonexistent-vendor-zzz", "nonexistent-prod-zzz", env={}, uid=1000)
    assert app.remove_cache() == 0


# ── default_env() helper ─────────────────────────────────────────────


def test_default_env_returns_environ_snapshot():
    env = default_env()
    assert isinstance(env, dict) or hasattr(env, "get")
    # Must reflect a real env var that's almost certainly set
    assert env.get("PATH") == os.environ.get("PATH")


def test_default_env_is_snapshot_not_live():
    """default_env() returns a dict copy, so later os.environ mutation doesn't leak."""
    env = default_env()
    sentinel = "CODECHU_XDG_TEST_SENTINEL_ZZZ"
    assert sentinel not in env
    os.environ[sentinel] = "1"
    try:
        assert sentinel not in env  # snapshot, not live view
    finally:
        del os.environ[sentinel]


# ── Top-level functional accessors ───────────────────────────────────


def test_config_home_from_env(tmp_path):
    assert codechu_xdg.config_home({"XDG_CONFIG_HOME": str(tmp_path)}) == tmp_path


def test_config_home_default():
    assert codechu_xdg.config_home({}).name == ".config"


def test_runtime_dir_requires_uid(tmp_path):
    # No XDG_RUNTIME_DIR → uses uid fallback
    assert codechu_xdg.runtime_dir({}, 1234) == Path("/run/user/1234")
    # With env → uid ignored
    p = codechu_xdg.runtime_dir({"XDG_RUNTIME_DIR": str(tmp_path)}, 1234)
    assert p == tmp_path


# ── XDG_DATA_DIRS / XDG_CONFIG_DIRS ──────────────────────────────────


def test_data_dirs_single_path(tmp_path):
    env = {"XDG_DATA_DIRS": str(tmp_path)}
    assert codechu_xdg.data_dirs(env) == [tmp_path]


def test_data_dirs_multiple_paths(tmp_path):
    a, b, c = tmp_path / "a", tmp_path / "b", tmp_path / "c"
    env = {"XDG_DATA_DIRS": f"{a}:{b}:{c}"}
    assert codechu_xdg.data_dirs(env) == [a, b, c]


def test_data_dirs_default():
    assert codechu_xdg.data_dirs({}) == [Path("/usr/local/share"), Path("/usr/share")]


def test_data_dirs_empty_env_uses_default():
    """Empty XDG_DATA_DIRS env var → spec fallback, not an empty list."""
    assert codechu_xdg.data_dirs({"XDG_DATA_DIRS": ""}) == [
        Path("/usr/local/share"),
        Path("/usr/share"),
    ]


def test_config_dirs_default():
    assert codechu_xdg.config_dirs({}) == [Path("/etc/xdg")]


def test_config_dirs_from_env(tmp_path):
    env = {"XDG_CONFIG_DIRS": f"{tmp_path / 'a'}:{tmp_path / 'b'}"}
    assert codechu_xdg.config_dirs(env) == [tmp_path / "a", tmp_path / "b"]


def test_config_dirs_empty_env_uses_default():
    assert codechu_xdg.config_dirs({"XDG_CONFIG_DIRS": ""}) == [Path("/etc/xdg")]


def test_app_data_dirs_namespaced(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    env = {"XDG_DATA_DIRS": f"{a}:{b}"}
    app = App("acme", "widget", env=env, uid=1000)
    assert app.data_dirs == [a / "acme" / "widget", b / "acme" / "widget"]


def test_app_config_dirs_namespaced(tmp_path):
    env = {"XDG_CONFIG_DIRS": str(tmp_path / "etc")}
    app = App("acme", "widget", env=env, uid=1000)
    assert app.config_dirs == [tmp_path / "etc" / "acme" / "widget"]


# ── find_file() ──────────────────────────────────────────────────────


def _find_file_env(tmp_path):
    return {
        "XDG_CONFIG_HOME": str(tmp_path / "user-config"),
        "XDG_DATA_HOME": str(tmp_path / "user-data"),
        "XDG_CONFIG_DIRS": f"{tmp_path / 'sys-config-a'}:{tmp_path / 'sys-config-b'}",
        "XDG_DATA_DIRS": f"{tmp_path / 'sys-data-a'}:{tmp_path / 'sys-data-b'}",
    }


def test_find_file_user_wins(tmp_path):
    app = App("v", "p", env=_find_file_env(tmp_path), uid=1000)
    app.ensure()
    # Place in both user and system dirs; user must win.
    (app.config_dir / "settings.json").write_text("user")
    sys_dir = app.config_dirs[0]
    sys_dir.mkdir(parents=True)
    (sys_dir / "settings.json").write_text("system")

    hit = app.find_file("settings.json")
    assert hit is not None
    assert hit.read_text() == "user"


def test_find_file_falls_back_to_system(tmp_path):
    app = App("v", "p", env=_find_file_env(tmp_path), uid=1000)
    # No user-level file. Put one in the second system dir to test ordering.
    sys_b = app.config_dirs[1]
    sys_b.mkdir(parents=True)
    (sys_b / "settings.json").write_text("from system b")

    hit = app.find_file("settings.json")
    assert hit is not None
    assert hit == sys_b / "settings.json"
    assert hit.read_text() == "from system b"


def test_find_file_first_system_dir_beats_second(tmp_path):
    app = App("v", "p", env=_find_file_env(tmp_path), uid=1000)
    sys_a = app.config_dirs[0]
    sys_b = app.config_dirs[1]
    sys_a.mkdir(parents=True)
    sys_b.mkdir(parents=True)
    (sys_a / "settings.json").write_text("a")
    (sys_b / "settings.json").write_text("b")

    hit = app.find_file("settings.json")
    assert hit == sys_a / "settings.json"


def test_find_file_returns_none_when_missing(tmp_path):
    app = App("v", "p", env=_find_file_env(tmp_path), uid=1000)
    assert app.find_file("nonexistent.toml") is None


def test_find_file_kind_data(tmp_path):
    app = App("v", "p", env=_find_file_env(tmp_path), uid=1000)
    app.ensure()
    sys_data = app.data_dirs[0]
    sys_data.mkdir(parents=True)
    (sys_data / "themes.json").write_text("system theme")

    hit = app.find_file("themes.json", kind="data")
    assert hit is not None
    assert hit.read_text() == "system theme"


def test_find_file_invalid_kind(tmp_path):
    app = App("v", "p", env=_find_file_env(tmp_path), uid=1000)
    with pytest.raises(ValueError):
        app.find_file("x", kind="bogus")
