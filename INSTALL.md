# Installing lca

## Quick install (macOS / Linux)

```bash
bash install.sh
```

The installer handles everything: Python version check, Ollama install, hardware detection, model pull, and `pip install -e .`.

## Manual install

**Requirements:** Python 3.10+, [Ollama](https://ollama.com/download)

```bash
pip install -e .
ollama pull qwen2.5-coder:7b   # or whichever model lca doctor recommends
```

## Choosing a model

Run `lca doctor` to see the recommended model for your hardware.

## Line limits

| Command | Max lines | Notes |
|---------|-----------|-------|
| explain | 1000      | Use `--fn` to target a single function |
| review  | 1000      | Use `--fn` to target a single function |
| edit    | 400       | Use `--fn` for larger files |

If a file exceeds the limit, `lca` will print the exact command to retry with `--fn`.

## Configuration

`lca` merges config from two optional TOML files (last wins):

| File | Scope |
|------|-------|
| `~/.config/lca/config.toml` | global / per-user |
| `.lca/config.toml` | per-project (walks up from cwd) |

Example `.lca/config.toml`:

```toml
[model]
name = "qwen2.5-coder:14b"

[limits]
max_edit_lines = 600

[instructions]
extra = "Always add type hints."
```
