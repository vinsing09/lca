import difflib
import os
import re
import tempfile
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

_FENCE_RE = re.compile(r"^```[^\n]*\n(.*?)\n```$", re.DOTALL)


def strip_model_fences(text: str) -> str:
    """Remove a markdown code fence if the entire response is a single fenced block."""
    m = _FENCE_RE.match(text.strip())
    if m:
        return m.group(1)
    return text


def make_unified_diff(original: str, edited: str, filename: str = "file") -> str:
    """Return a unified diff string, or empty string if there are no differences."""
    original_lines = original.splitlines(keepends=True)
    edited_lines = edited.splitlines(keepends=True)
    diff_lines = list(
        difflib.unified_diff(
            original_lines,
            edited_lines,
            fromfile=f"a/{filename}",
            tofile=f"b/{filename}",
        )
    )
    return "".join(diff_lines)


def has_changes(diff: str) -> bool:
    """Return True if the diff string is non-empty."""
    return bool(diff)


def display_diff(console: Console, diff: str, filename: str = "") -> None:
    """Render the diff in a yellow Panel using Rich Syntax highlighting."""
    if not diff:
        console.print("[dim]No changes.[/dim]")
        return
    title = f"Diff: {filename}" if filename else "Diff"
    syntax = Syntax(diff, lexer="diff", theme="monokai")
    console.print(Panel(syntax, title=title, border_style="yellow"))


def display_no_changes(console: Console) -> None:
    """Print a dim message explaining the model returned no changes."""
    console.print("[dim]The model returned no changes to apply.[/dim]")


def confirm_apply(console: Console) -> bool:
    """Prompt the user to apply changes. Returns True only for 'y' or 'yes'."""
    try:
        console.print("Apply changes? [y/N] ", end="")
        answer = input().strip().lower()
        return answer in ("y", "yes")
    except (EOFError, KeyboardInterrupt):
        return False


def apply_edit(path: Path, new_content: str) -> None:
    """Write new_content to path atomically via a temp file in the same directory."""
    directory = path.parent
    fd, tmp_path = tempfile.mkstemp(dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(new_content)
        os.replace(tmp_path, path)
    except OSError:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
