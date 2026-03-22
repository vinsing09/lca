from pathlib import Path
from typing import Optional

import typer

from lca import __version__

app = typer.Typer(
    name="lca",
    rich_markup_mode="rich",
    add_completion=False,
)


def version_callback(value: bool) -> None:
    if value:
        typer.echo(f"lca {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-V",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """Local code assistant — explain, review, and edit code with a local LLM."""


@app.command()
def explain(
    code: Optional[str] = typer.Argument(None, help="Code snippet to explain."),
    file: Optional[Path] = typer.Option(None, "-f", "--file", help="Path to file to explain."),
    model: Optional[str] = typer.Option(None, "-m", "--model", help="Model name override."),
) -> None:
    """Explain code from a file, snippet, or stdin."""
    from lca.commands.explain import run
    run(file, code, model)


@app.command()
def review(
    file: Optional[Path] = typer.Option(None, "-f", "--file", help="Path to file to review."),
    model: Optional[str] = typer.Option(None, "-m", "--model", help="Model name override."),
) -> None:
    """Review code from a file or stdin."""
    from lca.commands.review import run
    run(file, model)


@app.command()
def edit() -> None:
    """`lca edit` is not yet implemented — coming in Phase 2."""
    typer.echo("`lca edit` is not yet implemented — coming in Phase 2.")
    raise typer.Exit(code=1)
