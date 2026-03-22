import sys
from pathlib import Path

from rich.console import Console

from lca.config import load_config
from lca.context.limiter import LimitError, check_limits
from lca.context.reader import ReaderError, read_file, read_stdin
from lca.llm.client import OllamaError, check_model_available, stream_chat
from lca.llm.prompts import REVIEW_SYSTEM, REVIEW_TEMPERATURE, review_user
from lca.output.stream import (
    print_error,
    print_info,
    print_token_warning,
    stream_review,
)

console = Console()


def run(
    file: Path | None,
    model_override: str | None,
) -> None:
    cfg = load_config()
    model = model_override or cfg.model.name
    base_url = cfg.model.base_url

    # 1. Read input
    try:
        if file is not None:
            text = read_file(file)
            source = str(file)
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
            max_lines=cfg.limits.max_review_lines,
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
            system_prompt=REVIEW_SYSTEM,
            user_prompt=review_user(text, cfg.instructions.extra),
            temperature=REVIEW_TEMPERATURE,
        )
        stream_review(console, chunks, source_label=source)
    except OllamaError as exc:
        print_error(console, str(exc))
        sys.exit(2)
