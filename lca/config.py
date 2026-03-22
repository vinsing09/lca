"""Configuration dataclasses and loader for lca.

Merge order (last wins):
  1. Hardcoded defaults
  2. Global config:  ~/.config/lca/config.toml  (XDG_CONFIG_HOME respected)
  3. Project config: first .lca/config.toml found walking up from cwd
"""

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib  # type: ignore[no-redef]


@dataclass
class ModelConfig:
    name: str = "qwen2.5-coder:7b"
    base_url: str = "http://localhost:11434"


@dataclass
class LimitsConfig:
    max_edit_lines: int = 150
    max_explain_lines: int = 300
    max_review_lines: int = 300
    warn_token_threshold: int = 2000


@dataclass
class InstructionsConfig:
    extra: str = ""


@dataclass
class Config:
    model: ModelConfig = field(default_factory=ModelConfig)
    limits: LimitsConfig = field(default_factory=LimitsConfig)
    instructions: InstructionsConfig = field(default_factory=InstructionsConfig)


def _load_toml(path: Path) -> dict:
    """Return parsed TOML dict, or {} if the file is missing or unreadable."""
    try:
        with open(path, "rb") as f:
            return tomllib.load(f)
    except Exception:
        return {}


def _merge(cfg: Config, data: dict) -> None:
    """Apply a parsed TOML dict onto cfg in-place. Unknown keys are ignored."""
    model_data = data.get("model", {})
    if "name" in model_data:
        cfg.model.name = model_data["name"]
    if "base_url" in model_data:
        cfg.model.base_url = model_data["base_url"]

    limits_data = data.get("limits", {})
    if "max_edit_lines" in limits_data:
        cfg.limits.max_edit_lines = limits_data["max_edit_lines"]
    if "max_explain_lines" in limits_data:
        cfg.limits.max_explain_lines = limits_data["max_explain_lines"]
    if "max_review_lines" in limits_data:
        cfg.limits.max_review_lines = limits_data["max_review_lines"]
    if "warn_token_threshold" in limits_data:
        cfg.limits.warn_token_threshold = limits_data["warn_token_threshold"]

    instructions_data = data.get("instructions", {})
    if "extra" in instructions_data:
        cfg.instructions.extra = instructions_data["extra"]


def _global_config_path() -> Path:
    """Return ~/.config/lca/config.toml, honouring XDG_CONFIG_HOME."""
    xdg = os.environ.get("XDG_CONFIG_HOME", "")
    base = Path(xdg) if xdg else Path.home() / ".config"
    return base / "lca" / "config.toml"


def _find_project_config() -> Path | None:
    """Walk up from cwd looking for .lca/config.toml; return first match or None."""
    current = Path.cwd()
    while True:
        candidate = current / ".lca" / "config.toml"
        if candidate.is_file():
            return candidate
        parent = current.parent
        if parent == current:
            return None
        current = parent


def load_config() -> Config:
    """Return the active configuration, merging global then project config."""
    cfg = Config()
    _merge(cfg, _load_toml(_global_config_path()))
    project = _find_project_config()
    if project is not None:
        _merge(cfg, _load_toml(project))
    return cfg
