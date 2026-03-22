# lca — Local Code Assistant

`lca` is a Python CLI tool that acts as a local code assistant, helping developers navigate, understand, and modify codebases through a conversational interface powered by a configurable LLM backend — all without leaving the terminal.

---

## Quick Install

Paste this in your terminal from inside the cloned repo directory:

```bash
curl -fsSL https://raw.githubusercontent.com/YOUR_USERNAME/lca/main/install.sh | bash
```

> **Note:** Replace `YOUR_USERNAME` with your GitHub username before sharing this link.

### What it installs

| Component | Details |
|-----------|---------|
| Python 3.10+ | Checked; install via `brew install python@3.12` if missing |
| [Ollama](https://ollama.com) | Local LLM runtime, installed via Homebrew if absent |
| `qwen2.5-coder:7b` | Default code model (~4.7 GB download, may take several minutes) |
| `lca` | Installed in editable mode (`pip install -e .`) so `git pull` updates it instantly |

### Example commands after install

```bash
# Explain an entire file
lca explain -f src/app.py

# Explain a single function
lca explain --fn load_config -f lca/config.py

# Review a file for bugs, edge cases, and style
lca review -f src/app.py

# Review a specific function
lca review --fn parse_args -f src/cli.py

# Edit a file with a natural language instruction
lca edit -f src/app.py "add type hints to all function signatures"

# Edit a single function
lca edit --fn validate -f src/app.py "raise ValueError instead of returning False"
```

---

## Manual Install

If you prefer step-by-step control:

### 1. Install Python 3.10+

```bash
brew install python@3.12
```

### 2. Install and start Ollama

```bash
brew install ollama
brew services start ollama
```

Or download the macOS app from <https://ollama.com/download>.

### 3. Pull the default model

```bash
ollama pull qwen2.5-coder:7b
```

> This downloads ~4.7 GB. Run once; subsequent invocations use the local cache.

### 4. Install lca

From the repo root:

```bash
pip install -e .
```

### 5. Verify

```bash
lca --version
```

---

## Configuration

Create `.lca/config.toml` in your project root to override defaults:

```toml
[model]
name     = "qwen2.5-coder:14b"   # use a larger model for this project
base_url = "http://localhost:11434"

[limits]
max_explain_lines    = 500
max_review_lines     = 500
warn_token_threshold = 4000

[instructions]
extra = "This project uses async/await throughout. Prefer explicit types."
```

Global config lives at `~/.config/lca/config.toml` (respects `XDG_CONFIG_HOME`).
Project config at `.lca/config.toml` overrides global config.
