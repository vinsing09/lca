import sys
from pathlib import Path

from rich.console import Console

from lca.commands.edit import run as edit_run
from lca.config import load_config
from lca.context.stack_parser import find_function_at_line, parse_error
from lca.output.stream import print_error

console = Console()


def run(
    description: str | None,
    error: str | None,
    file: Path | None,
    directory: Path | None,
    fn: str | None,
    model_override: str | None,
) -> None:
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
            print_error(
                console,
                f"Function '{resolved_fn}' not found in {directory}.",
            )
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
    # Step 5 — delegate to edit
    # ------------------------------------------------------------------
    edit_run(
        file=resolved_file,
        instruction=instruction,
        model_override=model_override,
        fn=resolved_fn,
    )
