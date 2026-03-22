def load_config() -> Config:
    """Return the active configuration, merging global then project config.

    Returns:
        Config: The loaded configuration.
    """
    cfg = Config()
    _merge(cfg, _load_toml(_global_config_path()))
    project = _find_project_config()
    if project is not None:
        _merge(cfg, _load_toml(project))
    return cfg