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
    splice_edit,
    strip_model_fences,
)
from lca.output.stream import print_error, print_info, print_token_warning

console = Console()


def run(file: Path, instruction: str, model_override: str | None, fn: str | None = None) -> None:
    cfg = load_config()
    model = model_override or cfg.model.name
    base_url = cfg.model.base_url

    # 1. Read input — when --fn is used we also need the full file source for splicing
    try:
        if fn is not None:
            original_fn, _, start_char, end_char = read_function(file, fn)
            original_file = read_file(file)
            original = original_fn          # send only the function to the model
            source = f"{file}::{fn}"
        else:
            original = read_file(file)
            original_file = original        # same object; no splice needed
            source = str(file)
            start_char = end_char = 0       # unused when fn is None
    except ReaderError as exc:
        print_error(console, str(exc))
        sys.exit(2)

    # 2. Check limits (against the function text, not the whole file)
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
        edited_fn = "".join(chunks)
    except OllamaError as exc:
        print_error(console, str(exc))
        sys.exit(2)

    # 8. Strip fences from the model's function output
    edited_fn = strip_model_fences(edited_fn)

    # 9. Splice back into the full file (or use as-is for whole-file edits)
    if fn is not None:
        edited_file = splice_edit(original_file, edited_fn, start_char, end_char)
    else:
        edited_file = edited_fn

    # 10. Diff the full file before vs after
    diff = make_unified_diff(original_file, edited_file, filename=file.name)

    # 11. No changes
    if not has_changes(diff):
        display_no_changes(console)
        sys.exit(0)

    # 12. Display diff
    display_diff(console, diff, filename=file.name)

    # 13. Confirm
    if not confirm_apply(console):
        console.print("Cancelled — file unchanged.")
        sys.exit(1)

    # 14. Apply the complete file
    try:
        apply_edit(file, edited_file)
    except OSError as exc:
        print_error(console, str(exc))
        sys.exit(2)

    # 15. Done
    console.print(f"✓ Applied to {file}")
