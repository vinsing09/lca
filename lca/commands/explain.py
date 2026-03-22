import sys
from pathlib import Path

from rich.console import Console

from lca.config import load_config
from lca.context.limiter import LimitError, check_limits
from lca.context.reader import ReaderError, read_code_string, read_file, read_function, read_stdin
from lca.llm.client import OllamaError, check_model_available, stream_chat
from lca.llm.prompts import EXPLAIN_SYSTEM, EXPLAIN_TEMPERATURE, explain_user
from lca.output.stream import (
    print_error,
    print_info,
    print_token_warning,
    stream_plain,
)

console = Console()


def run(
    file: Path | None,
    code: str | None,
    model_override: str | None,
    fn: str | None = None,
) -> None:
    cfg = load_config()
    model = model_override or cfg.model.name
    base_url = cfg.model.base_url

    # 1. Read input
    try:
        if fn is not None:
            if file is None:
                print_error(console, "--fn requires -f/--file.")
                sys.exit(2)
            text, *_ = read_function(file, fn)
            source = f"{file}::{fn}"
        elif file is not None:
            text = read_file(file)
            source = str(file)
        elif code is not None:
            text = read_code_string(code)
            source = "<snippet>"
        else:
            text = read_stdin()
            source = "<stdin>"
    except ReaderError as exc:
        print_error(console, str(exc))
        sys.exit(2)

    # 2. Check limits
    try:
        report = check_limits(
            text,
            max_lines=cfg.limits.max_explain_lines,
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

    # 6 & 7. Stream and render
    try:
        chunks = stream_chat(
            base_url=base_url,
            model=model,
            system_prompt=EXPLAIN_SYSTEM,
            user_prompt=explain_user(text, cfg.instructions.extra),
            temperature=EXPLAIN_TEMPERATURE,
        )
        stream_plain(console, chunks, header=f"Explanation: {source}")
    except OllamaError as exc:
        print_error(console, str(exc))
        sys.exit(2)
