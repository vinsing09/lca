from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from lca import __version__

app = typer.Typer(
    name="lca",
    rich_markup_mode="rich",
    add_completion=False,
)

console = Console()


def version_callback(value: bool) -> None:
    if value:
        typer.echo(f"lca {__version__}")
        raise typer.Exit()


def _setup(model: str, base_url: str, skip: bool = False) -> None:
    """No-op stub — will be replaced in Phase 4 (runtime layer)."""
    pass


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
    fn: Optional[str] = typer.Option(None, "--fn", help="Target a specific function by name.", show_default=False),
    no_setup: bool = typer.Option(False, "--no-setup", hidden=True),
) -> None:
    """Explain code from a file, snippet, or stdin."""
    from lca.config import load_config
    cfg = load_config()
    resolved_model = model or cfg.model.name
    _setup(resolved_model, cfg.model.base_url, skip=no_setup)
    from lca.commands.explain import run
    run(file, code, model, fn=fn)


@app.command()
def review(
    file: Optional[Path] = typer.Option(None, "-f", "--file", help="Path to file to review."),
    model: Optional[str] = typer.Option(None, "-m", "--model", help="Model name override."),
    fn: Optional[str] = typer.Option(None, "--fn", help="Target a specific function by name.", show_default=False),
    no_setup: bool = typer.Option(False, "--no-setup", hidden=True),
) -> None:
    """Review code from a file or stdin."""
    from lca.config import load_config
    cfg = load_config()
    resolved_model = model or cfg.model.name
    _setup(resolved_model, cfg.model.base_url, skip=no_setup)
    from lca.commands.review import run
    run(file, model, fn=fn)


@app.command()
def edit(
    instruction: str = typer.Argument(..., help="Edit instruction to apply to the file."),
    file: Optional[Path] = typer.Option(None, "-f", "--file", help="Path to file to edit."),
    model: Optional[str] = typer.Option(None, "-m", "--model", help="Model name override."),
    fn: Optional[str] = typer.Option(None, "--fn", help="Target a specific function by name.", show_default=False),
    no_setup: bool = typer.Option(False, "--no-setup", hidden=True),
) -> None:
    """Edit a file using a natural language instruction."""
    if file is None:
        typer.echo("[bold red]Error:[/bold red]  -f/--file is required for edit.", err=True)
        raise typer.Exit(code=2)
    from lca.config import load_config
    cfg = load_config()
    resolved_model = model or cfg.model.name
    _setup(resolved_model, cfg.model.base_url, skip=no_setup)
    from lca.commands.edit import run
    run(file=file, instruction=instruction, model_override=model, fn=fn)


@app.command()
def fix(
    description: Optional[str] = typer.Argument(
        None, help="Description of the bug to fix.", show_default=False,
    ),
    file: Optional[Path] = typer.Option(
        None, "-f", "--file", help="File containing the bug.", exists=False, show_default=False,
    ),
    directory: Optional[Path] = typer.Option(
        None, "-d", "--dir", help="Directory to search for the function.", show_default=False,
    ),
    fn: Optional[str] = typer.Option(
        None, "--fn", help="Target a specific function by name.", show_default=False,
    ),
    error: Optional[str] = typer.Option(
        None, "--error", help="Error message or stack trace.", show_default=False,
    ),
    model: Optional[str] = typer.Option(None, "-m", "--model", show_default=False),
    no_setup: bool = typer.Option(False, "--no-setup", hidden=True),
) -> None:
    """Fix a bug by description or error message. Auto-locates the function."""
    if description is None and error is None:
        console.print("[bold red]Error:[/bold red] provide a description or --error")
        raise typer.Exit(2)
    from lca.config import load_config
    cfg = load_config()
    _setup(model or cfg.model.name, cfg.model.base_url, skip=no_setup)
    from lca.commands.fix import run
    run(description=description, error=error, file=file,
        directory=directory, fn=fn, model_override=model)


@app.command()
def find(
    query: str = typer.Argument(..., help="Description of the function to find."),
    file: Optional[Path] = typer.Option(
        None, "-f", "--file", help="Search within this file.", show_default=False,
    ),
    directory: Optional[Path] = typer.Option(
        None, "-d", "--dir", help="Search within this directory.", show_default=False,
    ),
    model: Optional[str] = typer.Option(None, "-m", "--model", show_default=False),
    no_setup: bool = typer.Option(False, "--no-setup", hidden=True),
) -> None:
    """Find functions by natural language description."""
    if file is None and directory is None:
        console.print("[bold red]Error:[/bold red] provide -f FILE or -d DIRECTORY")
        raise typer.Exit(2)
    if file is not None and directory is not None:
        console.print("[bold red]Error:[/bold red] use -f or -d, not both")
        raise typer.Exit(2)
    from lca.config import load_config
    cfg = load_config()
    _setup(model or cfg.model.name, cfg.model.base_url, skip=no_setup)
    from lca.commands.find import run
    run(query=query, file=file, directory=directory, model_override=model)


@app.command()
def doctor() -> None:
    """Check hardware and show recommended model for this machine."""
    from lca.runtime.hardware import detect_hardware, print_hardware_report
    profile = detect_hardware()
    print_hardware_report(profile, console)
    model_name = profile.recommended_model
    console.print(
        f"\n[dim]To use the recommended model:[/dim] "
        f"[bold]lca --model {model_name} explain -f file.py[/bold]\n"
    )
    console.print("[dim]To set it permanently, add to .lca/config.toml:[/dim]")
    console.print("[model]", markup=False)
    console.print(f'name = "{model_name}"\n', markup=False)

