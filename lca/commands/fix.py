import sys
from pathlib import Path

from rich.console import Console

from lca.config import load_config
from lca.context.reader import ReaderError, read_file, read_function
from lca.context.limiter import LimitError, check_limits
from lca.context.stack_parser import find_function_at_line, parse_error
from lca.llm.client import OllamaError, check_model_available, stream_chat
from lca.llm.prompts import FIX_SYSTEM, FIX_TEMPERATURE, fix_user
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


def run(
    description: str | None,
    error: str | None,
    file: Path | None,
    directory: Path | None,
    fn: str | None,
    model_override: str | None,
) -> None:
    cfg = load_config()
    model = model_override or cfg.model.name
    base_url = cfg.model.base_url

    # ------------------------------------------------------------------
    # Step 1 — resolve function name
    # ------------------------------------------------------------------
    resolved_fn: str | None = None
    fn_auto_detected = False
    parsed_file_path: Path | None = None
    parsed_line: int | None = None

    if fn is not None:
        resolved_fn = fn  # explicit — skip auto-detection entirely
    elif error is not None:
        parsed_file_str, parsed_fn, parsed_line = parse_error(error)
        if parsed_file_str:
            parsed_file_path = Path(parsed_file_str)
        if parsed_fn:
            resolved_fn = parsed_fn
            fn_auto_detected = True
        elif parsed_line is not None and file is not None:
            resolved_fn = find_function_at_line(file, parsed_line)
            if resolved_fn:
                fn_auto_detected = True

    # ------------------------------------------------------------------
    # Step 2 — resolve file path
    # ------------------------------------------------------------------
    resolved_file: Path | None = None

    if file is not None:
        resolved_file = file
    elif parsed_file_path is not None and parsed_file_path.exists():
        resolved_file = parsed_file_path
    elif directory is not None and resolved_fn is not None:
        from lca.context.finder import index_directory
        results = index_directory(directory)
        matches = [path for path, name, _ in results if name == resolved_fn]
        if not matches:
            print_error(console, f"Function '{resolved_fn}' not found in {directory}.")
            sys.exit(2)
        if len(matches) > 1:
            console.print(
                f"[yellow]Warning: '{resolved_fn}' found in {len(matches)} files; "
                f"using {matches[0]}[/yellow]"
            )
        resolved_file = matches[0]

    if resolved_file is None:
        print_error(
            console,
            "Could not determine the target file. "
            "Use -f FILE or provide a stack trace containing a recognisable file path.",
        )
        sys.exit(2)

    # ------------------------------------------------------------------
    # Step 3 — build instruction
    # ------------------------------------------------------------------
    if description and error:
        instruction = f"{description}. Error: {error}"
    elif error:
        instruction = f"Fix this error: {error}"
    else:
        instruction = description or ""

    # ------------------------------------------------------------------
    # Step 4 — print targeting info
    # ------------------------------------------------------------------
    fn_display = resolved_fn or "whole file"
    console.print(f"[dim]Targeting: {resolved_file}::{fn_display}[/dim]")
    if fn_auto_detected:
        console.print(f"[dim]Auto-detected function from error: {resolved_fn}[/dim]")

    # ------------------------------------------------------------------
    # Step 5 — read code
    # ------------------------------------------------------------------
    try:
        if resolved_fn is not None:
            original_fn, _, start_char, end_char = read_function(resolved_file, resolved_fn)
            original_file = read_file(resolved_file)
            original = original_fn
            source = f"{resolved_file}::{resolved_fn}"
        else:
            original = read_file(resolved_file)
            original_file = original
            source = str(resolved_file)
            start_char = end_char = 0
    except ReaderError as exc:
        print_error(console, str(exc))
        sys.exit(2)

    # ------------------------------------------------------------------
    # Step 6 — check limits
    # ------------------------------------------------------------------
    try:
        report = check_limits(
            original,
            max_lines=cfg.limits.max_edit_lines,
            warn_token_threshold=cfg.limits.warn_token_threshold,
            source=source,
            command="edit",
        )
    except LimitError as exc:
        print_error(console, str(exc))
        sys.exit(3)

    if report.over_warn_threshold:
        print_token_warning(console, report.estimated_tokens, cfg.limits.warn_token_threshold)

    print_info(console, f"model={model}  lines={report.line_count}  ~{report.estimated_tokens} tokens")

    # ------------------------------------------------------------------
    # Step 7 — model availability check (soft warning)
    # ------------------------------------------------------------------
    if not check_model_available(base_url, model):
        console.print(f"[yellow]Warning: model '{model}' not found at {base_url}[/yellow]")

    # ------------------------------------------------------------------
    # Step 8 — call model with FIX_SYSTEM
    # ------------------------------------------------------------------
    console.print("[dim]Generating fix…[/dim]")
    try:
        chunks = stream_chat(
            base_url=base_url,
            model=model,
            system_prompt=FIX_SYSTEM,
            user_prompt=fix_user(original, instruction, cfg.instructions.extra),
            temperature=FIX_TEMPERATURE,
        )
        edited_fn = "".join(chunks)
    except OllamaError as exc:
        print_error(console, str(exc))
        sys.exit(2)

    # ------------------------------------------------------------------
    # Step 9 — strip fences, splice, diff, confirm, apply
    # ------------------------------------------------------------------
    edited_fn = strip_model_fences(edited_fn)

    if resolved_fn is not None:
        edited_file = splice_edit(original_file, edited_fn, start_char, end_char)
    else:
        edited_file = edited_fn

    diff = make_unified_diff(original_file, edited_file, filename=resolved_file.name)

    if not has_changes(diff):
        display_no_changes(console)
        sys.exit(0)

    display_diff(console, diff, filename=resolved_file.name)

    if not confirm_apply(console):
        console.print("Cancelled — file unchanged.")
        sys.exit(1)

    try:
        apply_edit(resolved_file, edited_file)
    except OSError as exc:
        print_error(console, str(exc))
        sys.exit(2)

    console.print(f"✓ Applied to {resolved_file}")
