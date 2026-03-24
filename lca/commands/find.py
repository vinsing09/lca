import json
import re
import sys
from pathlib import Path

from rich.console import Console

from lca.config import load_config
from lca.context.finder import index_directory, list_functions_in_file
from lca.llm.client import OllamaError, stream_chat
from lca.output.diff import strip_model_fences
from lca.output.stream import print_error

console = Console()

MAX_FUNCTIONS_FOR_MODEL = 80

FIND_SYSTEM = """You are a code search engine.
Given a list of function names and their first lines of code,
return ONLY the names that match the description.
Output a JSON array of matching function names.
Example output: ["validate_token", "check_auth"]
If nothing matches, output: []
Output JSON only. No explanation. No markdown."""

_FIND_TEMPERATURE = 0.0


def _build_prompt(query: str, functions: list[tuple[Path, str, int]]) -> str:
    """Build the user prompt: query + list of 'name: first_line' pairs."""
    # Cache file reads: path -> list of source lines
    file_lines: dict[Path, list[str]] = {}
    entries: list[str] = []
    for path, name, line in functions:
        if path not in file_lines:
            try:
                file_lines[path] = path.read_text(encoding="utf-8").splitlines()
            except Exception:
                file_lines[path] = []
        src = file_lines[path]
        first = src[line - 1].strip() if 0 < line <= len(src) else ""
        entries.append(f"{name}: {first}")
    return f'Find functions matching: "{query}"\n\nFunctions:\n' + "\n".join(entries)


def _parse_matches(response: str) -> list[str]:
    """Parse JSON array from model response, stripping fences if needed."""
    cleaned = strip_model_fences(response.strip())
    try:
        result = json.loads(cleaned)
        if isinstance(result, list):
            return result
    except json.JSONDecodeError:
        pass
    # Fallback: find first [...] in the response
    m = re.search(r"\[.*?\]", cleaned, re.DOTALL)
    if m:
        try:
            result = json.loads(m.group())
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass
    return []


def run(
    query: str,
    file: Path | None,
    directory: Path | None,
    model_override: str | None,
) -> None:
    cfg = load_config()
    model = model_override or cfg.model.name
    base_url = cfg.model.base_url

    # 1. Build function list
    if file is not None:
        raw = list_functions_in_file(file)
        functions: list[tuple[Path, str, int]] = [(file, name, line) for name, line in raw]
    else:
        functions = index_directory(directory)  # type: ignore[arg-type]

    # 2. No functions found at all
    if not functions:
        console.print(f"No functions found matching: {query}")
        return

    # 3. Warn and truncate if too many
    if len(functions) > MAX_FUNCTIONS_FOR_MODEL:
        console.print(
            f"[yellow]Warning: found {len(functions)} functions; "
            f"showing first {MAX_FUNCTIONS_FOR_MODEL}[/yellow]"
        )
        functions = functions[:MAX_FUNCTIONS_FOR_MODEL]

    # 4. Build prompt
    prompt = _build_prompt(query, functions)

    # 5. Call model and buffer full response
    try:
        chunks = stream_chat(
            base_url=base_url,
            model=model,
            system_prompt=FIND_SYSTEM,
            user_prompt=prompt,
            temperature=_FIND_TEMPERATURE,
        )
        response = "".join(chunks)
    except OllamaError as exc:
        print_error(console, str(exc))
        sys.exit(2)

    matches = _parse_matches(response)

    # 6 & 7. Print results
    if not matches:
        console.print(f"No functions found matching: {query}")
        return

    match_set = set(matches)
    if file is not None:
        for _, name, line in functions:
            if name in match_set:
                console.print(f"{file}::{name} (line {line})")
    else:
        # Directory mode: group by file (functions already sorted by file then line)
        current_file: Path | None = None
        for path, name, line in functions:
            if name in match_set:
                if path != current_file:
                    console.print(str(path))
                    current_file = path
                console.print(f"  ::{name} (line {line})")
