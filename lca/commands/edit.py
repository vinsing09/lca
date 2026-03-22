import sys
from pathlib import Path

from rich.console import Console

from lca.config import load_config
from lca.context.limiter import LimitError, check_limits
from lca.context.reader import ReaderError, read_file, read_function
from lca.llm.client import OllamaError, check_model_available, stream_chat
from lca.llm.prompts import EDIT_SYSTEM, EDIT_TEMPERATURE, edit_user
from lca.output.diff import (
    apply_edit,
    confirm_apply,
    display_diff,
    display_no_changes,
    has_changes,
    make_unified_diff,
    strip_model_fences,
)
from lca.output.stream import print_error, print_info, print_token_warning

console = Console()


def run(file: Path, instruction: str, model_override: str | None, fn: str | None = None) -> None:
    cfg = load_config()
    model = model_override or cfg.model.name
    base_url = cfg.model.base_url

    # 1. Read input
    try:
        if fn is not None:
            original, _ = read_function(file, fn)
            source = f"{file}::{fn}"
        else:
            original = read_file(file)
            source = str(file)
    except ReaderError as exc:
        print_error(console, str(exc))
        sys.exit(2)

    # 2. Check limits
    try:
        report = check_limits(
            original,
            max_lines=cfg.limits.max_edit_lines,
            warn_token_threshold=cfg.limits.warn_token_threshold,
            source=source,
        )
    except LimitError as exc:
        print_error(console, str(exc))
        sys.exit(3)

    # 3. Token warning
    if report.over_warn_threshold:
        print_token_warning(console, report.estimated_tokens, cfg.limits.warn_token_threshold)

    # 4. Info line
    print_info(
        console,
        f"model={model}  lines={report.line_count}  ~{report.estimated_tokens} tokens",
    )

    # 5. Model availability check (soft warning)
    if not check_model_available(base_url, model):
        console.print(f"[yellow]Warning: model '{model}' not found at {base_url}[/yellow]")

    # 6 & 7. Stream and buffer full output
    console.print("[dim]Generating edit…[/dim]")
    try:
        chunks = stream_chat(
            base_url=base_url,
            model=model,
            system_prompt=EDIT_SYSTEM,
            user_prompt=edit_user(original, instruction, cfg.instructions.extra),
            temperature=EDIT_TEMPERATURE,
        )
        edited = "".join(chunks)
    except OllamaError as exc:
        print_error(console, str(exc))
        sys.exit(2)

    # 8. Strip fences
    edited = strip_model_fences(edited)

    # 9. Diff
    diff = make_unified_diff(original, edited, filename=file.name)

    # 10. No changes
    if not has_changes(diff):
        display_no_changes(console)
        sys.exit(0)

    # 11. Display diff
    display_diff(console, diff, filename=file.name)

    # 12. Confirm
    if not confirm_apply(console):
        console.print("Cancelled — file unchanged.")
        sys.exit(1)

    # 13. Apply
    try:
        apply_edit(file, edited)
    except OSError as exc:
        print_error(console, str(exc))
        sys.exit(2)

    # 14. Done
    console.print(f"✓ Applied to {file}")
