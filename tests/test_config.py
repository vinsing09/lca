from pathlib import Path

import pytest

from lca.config import (
    Config,
    _find_project_config,
    _global_config_path,
    _load_toml,
    _merge,
    load_config,
)


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

def test_load_config_returns_config_instance():
    assert isinstance(load_config(), Config)


def test_model_defaults():
    cfg = Config()
    assert cfg.model.name == "qwen2.5-coder:7b"
    assert cfg.model.base_url == "http://localhost:11434"


def test_limits_defaults():
    cfg = Config()
    assert cfg.limits.max_explain_lines == 300
    assert cfg.limits.max_review_lines == 300
    assert cfg.limits.warn_token_threshold == 2000


def test_instructions_defaults():
    cfg = Config()
    assert cfg.instructions.extra == ""


# ---------------------------------------------------------------------------
# _load_toml
# ---------------------------------------------------------------------------

def test_load_toml_missing_file(tmp_path):
    assert _load_toml(tmp_path / "nonexistent.toml") == {}


def test_load_toml_invalid_toml(tmp_path):
    f = tmp_path / "bad.toml"
    f.write_text("this is [not valid toml {{", encoding="utf-8")
    assert _load_toml(f) == {}


def test_load_toml_valid(tmp_path):
    f = tmp_path / "good.toml"
    f.write_text('[model]\nname = "llama3"\n', encoding="utf-8")
    result = _load_toml(f)
    assert result == {"model": {"name": "llama3"}}


# ---------------------------------------------------------------------------
# _merge
# ---------------------------------------------------------------------------

def test_merge_model_name():
    cfg = Config()
    _merge(cfg, {"model": {"name": "mistral"}})
    assert cfg.model.name == "mistral"


def test_merge_model_base_url():
    cfg = Config()
    _merge(cfg, {"model": {"base_url": "http://remote:11434"}})
    assert cfg.model.base_url == "http://remote:11434"


def test_merge_max_explain_lines():
    cfg = Config()
    _merge(cfg, {"limits": {"max_explain_lines": 500}})
    assert cfg.limits.max_explain_lines == 500


def test_merge_max_review_lines():
    cfg = Config()
    _merge(cfg, {"limits": {"max_review_lines": 400}})
    assert cfg.limits.max_review_lines == 400


def test_merge_warn_token_threshold():
    cfg = Config()
    _merge(cfg, {"limits": {"warn_token_threshold": 5000}})
    assert cfg.limits.warn_token_threshold == 5000


def test_merge_extra_instructions():
    cfg = Config()
    _merge(cfg, {"instructions": {"extra": "Use type hints."}})
    assert cfg.instructions.extra == "Use type hints."


def test_merge_ignores_unknown_keys():
    cfg = Config()
    _merge(cfg, {"model": {"unknown_key": "ignored"}, "bogus_section": {"x": 1}})
    # No exception, defaults unchanged
    assert cfg.model.name == "qwen2.5-coder:7b"


# ---------------------------------------------------------------------------
# _find_project_config
# ---------------------------------------------------------------------------

def test_find_project_config_in_cwd(tmp_path, monkeypatch):
    config_file = tmp_path / ".lca" / "config.toml"
    config_file.parent.mkdir()
    config_file.write_text('[model]\nname = "test"\n', encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert _find_project_config() == config_file


def test_find_project_config_in_parent(tmp_path, monkeypatch):
    config_file = tmp_path / ".lca" / "config.toml"
    config_file.parent.mkdir()
    config_file.write_text('[model]\nname = "test"\n', encoding="utf-8")
    subdir = tmp_path / "a" / "b"
    subdir.mkdir(parents=True)
    monkeypatch.chdir(subdir)
    assert _find_project_config() == config_file


def test_find_project_config_none(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    # No .lca/config.toml anywhere up the tree from tmp_path
    # (tmp_path is a fresh directory with no parents containing .lca)
    result = _find_project_config()
    # It's valid to find nothing or to find one in the real FS; just ensure no crash.
    assert result is None or isinstance(result, Path)


def test_find_project_config_none_isolated(tmp_path, monkeypatch):
    """Guarantee None by monkeypatching Path.cwd to a deeply nested tmp dir."""
    nested = tmp_path / "x" / "y" / "z"
    nested.mkdir(parents=True)
    monkeypatch.chdir(nested)
    # tmp_path is freshly created so no ancestor has .lca/config.toml
    result = _find_project_config()
    assert result is None


# ---------------------------------------------------------------------------
# load_config() merge order: project overrides global
# ---------------------------------------------------------------------------

def test_load_config_project_overrides_global(tmp_path, monkeypatch):
    global_toml = tmp_path / "global_config.toml"
    global_toml.write_text('[model]\nname = "global-model"\n', encoding="utf-8")

    project_dir = tmp_path / "project"
    project_dir.mkdir()
    lca_dir = project_dir / ".lca"
    lca_dir.mkdir()
    project_toml = lca_dir / "config.toml"
    project_toml.write_text('[model]\nname = "project-model"\n', encoding="utf-8")

    monkeypatch.chdir(project_dir)
    monkeypatch.setattr("lca.config._global_config_path", lambda: global_toml)

    cfg = load_config()
    assert cfg.model.name == "project-model"


def test_load_config_global_applies_when_no_project(tmp_path, monkeypatch):
    global_toml = tmp_path / "global_config.toml"
    global_toml.write_text('[model]\nname = "global-only"\n', encoding="utf-8")

    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    monkeypatch.chdir(empty_dir)
    monkeypatch.setattr("lca.config._global_config_path", lambda: global_toml)

    cfg = load_config()
    assert cfg.model.name == "global-only"
