"""Configuration dataclasses and loader for lca.

Phase 2 will add TOML loading from a user config file.
"""

from dataclasses import dataclass, field


@dataclass
class ModelConfig:
    name: str = "qwen2.5-coder:7b"
    base_url: str = "http://localhost:11434"


@dataclass
class LimitsConfig:
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


def load_config() -> Config:
    """Return the active configuration.

    Phase 2 will add TOML loading from a user config file.
    """
    return Config()
