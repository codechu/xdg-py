"""Tests for codechu_xdg — XDG path resolution + migration."""

from __future__ import annotations


import pytest

import codechu_xdg


# ── Path resolution ─────────────────────────────────────────────────


def test_app_paths_basic():
    app = codechu_xdg.App(vendor="codechu", product="my-product")
    assert app.config_dir.name == "my-product"
    assert app.config_dir.parent.name == "codechu"
    assert "my-product" in str(app.runtime_dir)


def test_paths_distinct():
    app = codechu_xdg.App("acme", "widget")
    paths = {app.config_dir, app.cache_dir, app.data_dir, app.state_dir, app.runtime_dir}
    assert len(paths) == 5  # all different


def test_namespace_in_every_path():
    app = codechu_xdg.App("vendor1", "prod1")
    for d in (app.config_dir, app.cache_dir, app.data_dir, app.state_dir, app.runtime_dir):
        assert "vendor1" in d.parts
        assert "prod1" in d.parts


def test_xdg_env_override(monkeypatch, tmp_path):
    """When XDG_CONFIG_HOME is set, paths follow it."""
    custom = tmp_path / "custom_config"
    monkeypatch.setenv("XDG_CONFIG_HOME", str(custom))
    # Reimport to pick up env
    import importlib
    import codechu_xdg

    importlib.reload(codechu_xdg)
    app = codechu_xdg.App("v", "p")
    assert str(app.config_dir).startswith(str(custom))


# ── Validation ──────────────────────────────────────────────────────


def test_empty_vendor_rejected():
    with pytest.raises(ValueError):
        codechu_xdg.App(vendor="", product="x")


def test_empty_product_rejected():
    with pytest.raises(ValueError):
        codechu_xdg.App(vendor="x", product="")


def test_slash_rejected():
    with pytest.raises(ValueError):
        codechu_xdg.App(vendor="bad/vendor", product="x")
    with pytest.raises(ValueError):
        codechu_xdg.App(vendor="x", product="bad/product")


# ── ensure() ────────────────────────────────────────────────────────


def test_ensure_creates_all_dirs(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "c"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "ca"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "d"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "s"))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "r"))
    import importlib
    import codechu_xdg

    importlib.reload(codechu_xdg)

    app = codechu_xdg.App("v", "p")
    app.ensure()
    for d in (app.config_dir, app.cache_dir, app.data_dir, app.state_dir, app.runtime_dir):
        assert d.exists()
        assert d.is_dir()


def test_ensure_idempotent(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "c"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "ca"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "d"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "s"))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "r"))
    import importlib
    import codechu_xdg

    importlib.reload(codechu_xdg)

    app = codechu_xdg.App("v", "p")
    app.ensure()
    app.ensure()  # second call — no error
    assert app.config_dir.exists()


# ── migrate() ────────────────────────────────────────────────────────


def test_migrate_moves_existing(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "c"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "ca"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "d"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "s"))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "r"))
    import importlib
    import codechu_xdg

    importlib.reload(codechu_xdg)

    app = codechu_xdg.App("v", "p")
    # Create legacy file
    legacy = tmp_path / "legacy" / "settings.json"
    legacy.parent.mkdir(parents=True)
    legacy.write_text('{"key": "value"}')
    new_path = app.config_dir / "settings.json"

    moved = app.migrate({legacy: new_path})
    assert moved == 1
    assert new_path.exists()
    assert new_path.read_text() == '{"key": "value"}'
    assert not legacy.exists()


def test_migrate_skips_when_new_exists(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "c"))
    import importlib
    import codechu_xdg

    importlib.reload(codechu_xdg)

    app = codechu_xdg.App("v", "p")
    app.ensure()
    legacy = tmp_path / "old.json"
    legacy.write_text("legacy")
    new = app.config_dir / "new.json"
    new.write_text("already exists")

    moved = app.migrate({legacy: new})
    assert moved == 0
    assert legacy.exists()  # untouched
    assert new.read_text() == "already exists"  # untouched


def test_migrate_skips_when_legacy_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "c"))
    import importlib
    import codechu_xdg

    importlib.reload(codechu_xdg)

    app = codechu_xdg.App("v", "p")
    nonexistent = tmp_path / "nope.json"
    new = app.config_dir / "new.json"

    moved = app.migrate({nonexistent: new})
    assert moved == 0
    assert not new.exists()


def test_repr():
    app = codechu_xdg.App("acme", "widget")
    assert "acme" in repr(app)
    assert "widget" in repr(app)


# ── Convenience helpers ──────────────────────────────────────────────


def test_settings_file_default_name(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    import importlib
    import codechu_xdg

    importlib.reload(codechu_xdg)
    app = codechu_xdg.App("v", "p")
    assert app.settings_file().name == "settings.json"
    assert app.settings_file("custom.json").name == "custom.json"


def test_file_helpers_return_correct_subdir(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "c"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "ca"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "d"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "s"))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "r"))
    import importlib
    import codechu_xdg

    importlib.reload(codechu_xdg)

    app = codechu_xdg.App("v", "p")
    assert app.settings_file().parent == app.config_dir
    assert app.cache_file("db.sqlite").parent == app.cache_dir
    assert app.data_file("history.json").parent == app.data_dir
    assert app.log_file().parent == app.state_dir
    assert app.runtime_file("watchdog.pid").parent == app.runtime_dir


# ── Cleanup helpers ──────────────────────────────────────────────────


def test_remove_cache_clears_contents(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    import importlib
    import codechu_xdg

    importlib.reload(codechu_xdg)

    app = codechu_xdg.App("v", "p")
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


def test_remove_runtime_clears_sockets(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "rt"))
    import importlib
    import codechu_xdg

    importlib.reload(codechu_xdg)

    app = codechu_xdg.App("v", "p")
    app.ensure()
    (app.runtime_dir / "watchdog.pid").write_text("12345")
    (app.runtime_dir / "control.sock").touch()

    removed = app.remove_runtime()
    assert removed == 2
    assert app.runtime_dir.exists()


def test_remove_on_nonexistent_dir():
    """Wiping a non-existent dir returns 0, doesn't crash."""
    import codechu_xdg

    app = codechu_xdg.App("nonexistent-vendor-zzz", "nonexistent-prod-zzz")
    # Cache_dir doesn't exist — should not raise
    assert app.remove_cache() == 0
