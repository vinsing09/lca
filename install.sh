#!/usr/bin/env bash
# install.sh — One-command installer for lca (Local Code Assistant)
# Supports macOS arm64 and x86_64.
# Does NOT require sudo — everything installs to user space.

set -euo pipefail

# ---------------------------------------------------------------------------
# Color helpers (fall back gracefully if tput is unavailable)
# ---------------------------------------------------------------------------
if command -v tput >/dev/null 2>&1 && tput colors >/dev/null 2>&1; then
    GREEN="$(tput setaf 2)"
    RED="$(tput setaf 1)"
    YELLOW="$(tput setaf 3)"
    BOLD="$(tput bold)"
    RESET="$(tput sgr0)"
else
    GREEN="\033[0;32m"
    RED="\033[0;31m"
    YELLOW="\033[0;33m"
    BOLD="\033[1m"
    RESET="\033[0m"
fi

info()    { printf "%s==>%s %s%s\n" "${BOLD}" "${RESET}" "$*" "${RESET}"; }
success() { printf "%s✓%s  %s\n" "${GREEN}" "${RESET}" "$*"; }
warn()    { printf "%s⚠%s  %s\n" "${YELLOW}" "${RESET}" "$*"; }
die()     { printf "%s✗%s  %s\n" "${RED}" "${RESET}" "$*" >&2; exit 1; }

START_TIME=$(date +%s)

# ---------------------------------------------------------------------------
# Step 1 — Python check
# ---------------------------------------------------------------------------
info "Step 1/6 — Checking Python version..."

if ! command -v python3 >/dev/null 2>&1; then
    die "Python 3 not found. Install it with:  brew install python@3.12"
fi

PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PY_MAJOR=$(python3 -c 'import sys; print(sys.version_info.major)')
PY_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')

if [ "${PY_MAJOR}" -lt 3 ] || { [ "${PY_MAJOR}" -eq 3 ] && [ "${PY_MINOR}" -lt 10 ]; }; then
    die "Python 3.10+ required (found ${PY_VERSION}). Install a newer version with:
    brew install python@3.12"
fi

success "Python ${PY_VERSION} found."

# ---------------------------------------------------------------------------
# Step 2 — Ollama check + install
# ---------------------------------------------------------------------------
info "Step 2/6 — Checking Ollama..."

if ! command -v ollama >/dev/null 2>&1; then
    warn "Ollama not found."

    if ! command -v brew >/dev/null 2>&1; then
        die "Homebrew is also missing. Install Ollama manually from:
    https://ollama.com/download
Then re-run this script."
    fi

    info "  Installing Ollama via Homebrew (this may take a moment)..."
    brew install ollama

    info "  Starting Ollama as a Homebrew service..."
    brew services start ollama
    success "Ollama installed and started."
else
    success "Ollama already installed."
    info "  Ensuring Ollama service is running..."
    if command -v brew >/dev/null 2>&1; then
        brew services start ollama 2>/dev/null || true
    else
        # brew not available — try starting ollama in background if not running
        if ! pgrep -x ollama >/dev/null 2>&1; then
            ollama serve >/dev/null 2>&1 &
            sleep 2
        fi
    fi
fi

# ---------------------------------------------------------------------------
# Step 3 — Hardware detection (pure bash, psutil not yet installed)
# ---------------------------------------------------------------------------
info "Step 3/6 — Detecting hardware..."

ARCH=$(uname -m)

if [[ "$(uname -s)" == "Darwin" ]]; then
    RAM_BYTES=$(sysctl -n hw.memsize)
    RAM_GB=$(( RAM_BYTES / 1024 / 1024 / 1024 ))
else
    RAM_GB=$(awk '/MemTotal/ {print int($2/1024/1024)}' /proc/meminfo)
fi

if [ "${ARCH}" = "arm64" ]; then
    # Apple Silicon: Metal GPU unified memory — more efficient per GB
    if   [ "${RAM_GB}" -lt 8 ];  then MODEL="qwen2.5-coder:1.5b"
    elif [ "${RAM_GB}" -lt 32 ]; then MODEL="qwen2.5-coder:7b"
    else MODEL="qwen2.5-coder:14b"
    fi
else
    # Intel macOS / Linux
    if   [ "${RAM_GB}" -lt 8 ];  then MODEL="qwen2.5-coder:1.5b"
    elif [ "${RAM_GB}" -lt 16 ]; then MODEL="qwen2.5-coder:3b"
    elif [ "${RAM_GB}" -lt 32 ]; then MODEL="qwen2.5-coder:7b"
    else MODEL="qwen2.5-coder:14b"
    fi
fi

success "Detected ${RAM_GB}GB RAM (${ARCH}) — recommended model: ${MODEL}"

# ---------------------------------------------------------------------------
# Step 4 — Model pull
# ---------------------------------------------------------------------------
info "Step 4/6 — Checking for model '${MODEL}'..."

if ollama list 2>/dev/null | grep -q "${MODEL}"; then
    success "Model '${MODEL}' already present."
else
    warn "Model '${MODEL}' not found locally."
    warn "This will download ~4.7 GB and may take several minutes on a slow connection."
    info "  Pulling model '${MODEL}'..."
    ollama pull "${MODEL}"
    success "Model '${MODEL}' ready."
fi

# ---------------------------------------------------------------------------
# Step 4 — lca install
# ---------------------------------------------------------------------------
info "Step 5/6 — Installing lca..."

if [ ! -f "lca/__init__.py" ]; then
    die "lca source not found in the current directory.
Please cd into the lca repository root and re-run:
    cd lca
    bash install.sh"
fi

pip3 install -e .
success "lca installed in editable mode (pip install -e .)."

# ---------------------------------------------------------------------------
# Step 5 — Verify
# ---------------------------------------------------------------------------
info "Step 6/6 — Verifying installation..."

if ! lca --version >/dev/null 2>&1; then
    die "lca --version failed. Troubleshooting tips:
  • Make sure ~/.local/bin (or the pip bin dir) is on your PATH.
  • Try:  export PATH=\"\$HOME/.local/bin:\$PATH\"
  • Then: lca --version"
fi

LCA_VERSION=$(lca --version)
success "${LCA_VERSION} is working."

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
END_TIME=$(date +%s)
ELAPSED=$(( END_TIME - START_TIME ))
MINUTES=$(( ELAPSED / 60 ))
SECONDS=$(( ELAPSED % 60 ))

printf "\n%s%s Installation complete in %dm %ds! %s\n\n" \
    "${GREEN}${BOLD}" "🎉" "${MINUTES}" "${SECONDS}" "${RESET}"

printf "Try it out:\n"
printf "  %slca explain -f path/to/file.py%s\n" "${BOLD}" "${RESET}"
printf "  %slca review  -f path/to/file.py%s\n" "${BOLD}" "${RESET}"
printf "  %slca edit    -f path/to/file.py \"add type hints\"%s\n" "${BOLD}" "${RESET}"
printf "  %slca explain --fn my_function -f path/to/file.py%s\n\n" "${BOLD}" "${RESET}"
