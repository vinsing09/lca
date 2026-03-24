import sys
from pathlib import Path

from rich.console import Console

from lca.config import load_config
from lca.context.finder import index_directory
from lca.llm.client import OllamaError, stream_chat
from lca.output.stream import print_error, stream_plain

console = Console()

DESCRIBE_SYSTEM = """\
You are a technical documentation writer.
Given a list of source files and their functions, write a concise
architecture document.

Output format:
## Overview
(2-3 sentences describing what this codebase does overall)

## Modules
(One entry per file:)
### filename.py
(One sentence describing this module's responsibility)
Functions: fn1, fn2, fn3

Rules:
- Be specific about what each module does, not generic.
- Do not invent functionality not shown.
- Keep each module description to one sentence.
- List all functions shown, do not omit any.\
"""

DESCRIBE_TEMPERATURE = 0.4


def _build_prompt(directory: Path, file_map: dict[Path, list[str]]) -> str:
    """Build the describe user prompt: file list with line counts and function names."""
    parts: list[str] = []
    for file_path in sorted(file_map.keys(), key=str):
        try:
            rel = file_path.relative_to(directory)
        except ValueError:
            rel = Path(str(file_path))
        try:
            line_count = len(file_path.read_text(encoding="utf-8").splitlines())
        except Exception:
            line_count = 0
        fn_names = file_map[file_path]
        parts.append(
            f"{rel} ({line_count} lines)\n"
            f"Functions: {', '.join(fn_names)}\n"
        )
    return "Codebase structure:\n\n" + "\n".join(parts)


def run(
    directory: Path,
    output: Path | None,
    model_override: str | None,
) -> None:
    cfg = load_config()
    model = model_override or cfg.model.name
    base_url = cfg.model.base_url

    # 1 & 4. Index and show progress
    console.print(f"[dim]Indexing {directory}...[/dim]")
    results = index_directory(directory)

    # 2. Group by file
    file_map: dict[Path, list[str]] = {}
    for file_path, fn_name, _ in results:
        if file_path not in file_map:
            file_map[file_path] = []
        file_map[file_path].append(fn_name)

    n_files = len(file_map)
    total_fns = sum(len(fns) for fns in file_map.values())
    console.print(f"[dim]{n_files} files, {total_fns} functions[/dim]")

    # 5. No supported files
    if not file_map:
        console.print(f"No supported files found in {directory}")
        return

    # 6. Large codebase warning
    if total_fns > 200:
        console.print(
            f"[yellow]Warning: {total_fns} functions found; "
            f"architecture document may be truncated[/yellow]"
        )

    # 7. Build prompt
    describe_user = _build_prompt(directory, file_map)

    # 8. Call model and stream/buffer
    try:
        chunks = stream_chat(
            base_url=base_url,
            model=model,
            system_prompt=DESCRIBE_SYSTEM,
            user_prompt=describe_user,
            temperature=DESCRIBE_TEMPERATURE,
        )
        if output is not None:
            content = "".join(chunks)
            console.print(content, end="", highlight=False)
            console.print()
            output.write_text(content, encoding="utf-8")
            console.print(f"[green]✓[/green] Architecture saved to {output}")
        else:
            stream_plain(console, chunks, header=f"Architecture: {directory}")
    except OllamaError as exc:
        print_error(console, str(exc))
        sys.exit(2)
