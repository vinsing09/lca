"""Detect local hardware and recommend the best Ollama model for lca."""

import platform
import sys
from dataclasses import dataclass

import psutil

MODEL_TIERS = {
    "small":  "qwen2.5-coder:1.5b",
    "medium": "qwen2.5-coder:3b",
    "large":  "qwen2.5-coder:7b",
    "xlarge": "qwen2.5-coder:14b",
}


@dataclass
class HardwareProfile:
    ram_gb: float
    cpu_cores: int
    is_apple_silicon: bool
    is_macos: bool
    is_linux: bool
    recommended_model: str
    recommendation_reason: str


def _recommend(ram_gb: float, is_apple_silicon: bool) -> tuple[str, str]:
    """Return (model, reason) based on RAM and architecture."""
    if is_apple_silicon:
        if ram_gb < 8:
            return MODEL_TIERS["small"],  "Limited RAM — fast model recommended"
        if ram_gb < 16:
            return MODEL_TIERS["large"],  "Apple Silicon 8GB — Metal acceleration makes 7B fast"
        if ram_gb < 32:
            return MODEL_TIERS["large"],  "Apple Silicon 16GB — 7B runs comfortably"
        return MODEL_TIERS["xlarge"], "Apple Silicon 32GB+ — 14B fits with room to spare"
    else:
        if ram_gb < 8:
            return MODEL_TIERS["small"],  "Limited RAM — fast model recommended"
        if ram_gb < 16:
            return MODEL_TIERS["medium"], "8-16GB RAM — 3B balances speed and quality"
        if ram_gb < 32:
            return MODEL_TIERS["large"],  "16-32GB RAM — 7B runs well"
        return MODEL_TIERS["xlarge"], "32GB+ RAM — 14B gives best output quality"


def detect_hardware() -> HardwareProfile:
    """Detect hardware and return a profile with model recommendation."""
    is_macos = sys.platform == "darwin"
    is_linux = sys.platform == "linux"
    is_apple_silicon = is_macos and platform.machine() == "arm64"
    ram_gb = psutil.virtual_memory().total / (1024 ** 3)
    cpu_cores = psutil.cpu_count(logical=True) or 1

    recommended_model, recommendation_reason = _recommend(ram_gb, is_apple_silicon)

    return HardwareProfile(
        ram_gb=ram_gb,
        cpu_cores=cpu_cores,
        is_apple_silicon=is_apple_silicon,
        is_macos=is_macos,
        is_linux=is_linux,
        recommended_model=recommended_model,
        recommendation_reason=recommendation_reason,
    )


def print_hardware_report(profile: HardwareProfile, console=None) -> None:
    """Print a rich hardware summary table to console."""
    from rich.console import Console
    from rich.table import Table

    if console is None:
        console = Console()

    table = Table(title="Hardware Profile", show_header=True, header_style="bold")
    table.add_column("Property", style="dim", min_width=22)
    table.add_column("Value")

    platform_str = "macOS (Apple Silicon)" if profile.is_apple_silicon else \
                   "macOS (Intel)" if profile.is_macos else \
                   "Linux" if profile.is_linux else sys.platform

    table.add_row("RAM",              f"{profile.ram_gb:.1f} GB")
    table.add_row("CPU cores",        str(profile.cpu_cores))
    table.add_row("Platform",         platform_str)
    table.add_row("Recommended model", f"[green]{profile.recommended_model}[/green]")
    table.add_row("Reason",           profile.recommendation_reason)

    console.print(table)
