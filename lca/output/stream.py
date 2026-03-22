from collections.abc import Iterable

from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule


def stream_plain(
    console: Console,
    chunks: Iterable[str],
    *,
    header: str | None = None,
) -> int:
    if header is not None:
        console.print(Panel(header))
    total = 0
    for chunk in chunks:
        console.print(chunk, end="", highlight=False)
        total += len(chunk)
    console.print()
    return total


def stream_review(
    console: Console,
    chunks: Iterable[str],
    *,
    source_label: str = "",
) -> int:
    title = f"Review: {source_label}" if source_label else "Review"
    console.print(Rule(title, style="yellow"))
    total = 0
    for chunk in chunks:
        console.print(chunk, end="", highlight=False)
        total += len(chunk)
    console.print()
    console.print(Rule(style="yellow"))
    return total


def print_token_warning(console: Console, estimated_tokens: int, threshold: int) -> None:
    console.print(
        f"[yellow]Warning: estimated {estimated_tokens} tokens exceeds "
        f"the {threshold}-token threshold.[/yellow]"
    )


def print_error(console: Console, message: str) -> None:
    console.print(f"[bold red]Error:[/bold red] {message}")


def print_info(console: Console, message: str) -> None:
    console.print(f"[dim]{message}[/dim]")
