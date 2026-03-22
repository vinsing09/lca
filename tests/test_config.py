from lca.config import Config, load_config


def test_load_config_returns_config_instance():
    assert isinstance(load_config(), Config)


def test_model_defaults():
    cfg = load_config()
    assert cfg.model.name == "qwen2.5-coder:7b"
    assert cfg.model.base_url == "http://localhost:11434"


def test_limits_defaults():
    cfg = load_config()
    assert cfg.limits.max_explain_lines == 300
    assert cfg.limits.max_review_lines == 300
    assert cfg.limits.warn_token_threshold == 2000


def test_instructions_defaults():
    cfg = load_config()
    assert cfg.instructions.extra == ""
