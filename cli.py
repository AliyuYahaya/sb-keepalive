#!/usr/bin/env python3
"""
Supabase Keepalive CLI

Terminal-based project management and keepalive execution for Supabase projects.

Usage:
    python cli.py dashboard              # Show project status
    python cli.py run                    # Run keepalive for all enabled projects
    python cli.py add                    # Add a new project (interactive)
    python cli.py enable <id>            # Enable a project
    python cli.py disable <id>           # Disable a project
    python cli.py delete <id>            # Delete a project
    python cli.py show <id>              # Show project details
"""

import sys
import logging
from typing import Optional

import typer
from rich.console import Console
from rich.prompt import Prompt, Confirm

from app.db import Database
from app.keepalive import KeepaliveEngine
from app.dashboard import Dashboard


# Initialize Typer app
app = typer.Typer(
    help="Supabase Keepalive - Terminal-based project management",
    add_completion=False,
)

console = Console()


def setup_logging(verbose: bool = False):
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


@app.command()
def dashboard(
    enabled_only: bool = typer.Option(
        False, "--enabled", "-e", help="Show only enabled projects"
    ),
    db_path: str = typer.Option("data/sb.db", "--db", help="Database path"),
):
    """Show project status dashboard."""
    with Database(db_path) as db:
        dash = Dashboard(db)
        dash.show(enabled_only=enabled_only)


@app.command()
def run(
    verbose: bool = typer.Option(True, "--verbose/--quiet", "-v/-q", help="Verbose output"),
    db_path: str = typer.Option("data/sb.db", "--db", help="Database path"),
):
    """Run keepalive for all enabled projects."""
    setup_logging(verbose)

    with Database(db_path) as db:
        engine = KeepaliveEngine(db)
        results = engine.run_all(verbose=verbose)

        # Exit with error code if any failed
        failed_count = sum(1 for r in results if not r.success)
        if failed_count > 0:
            sys.exit(1)


@app.command()
def add(
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Project name"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="Supabase URL"),
    key: Optional[str] = typer.Option(None, "--key", "-k", help="API key"),
    method: str = typer.Option("rpc", "--method", "-m", help="Keepalive method (rpc or table)"),
    table: Optional[str] = typer.Option(None, "--table", "-t", help="Table name (for table method)"),
    enabled: bool = typer.Option(True, "--enabled/--disabled", help="Enable project"),
    db_path: str = typer.Option("data/sb.db", "--db", help="Database path"),
):
    """Add a new Supabase project."""

    console.print("\n[bold cyan]Add New Supabase Project[/bold cyan]\n")

    # Interactive prompts if not provided
    if name is None:
        name = Prompt.ask("Project name", default="my-project")

    if url is None:
        url = Prompt.ask("Supabase URL", default="https://xxxxx.supabase.co")

    if key is None:
        key = Prompt.ask("API key (anon or service_role)")

    if method not in ["rpc", "table"]:
        method = Prompt.ask(
            "Keepalive method",
            choices=["rpc", "table"],
            default="rpc",
        )

    if method == "table" and table is None:
        table = Prompt.ask("Table name", default="users")

    # Validate inputs
    if not name or not url or not key:
        console.print("[red]Error: Name, URL, and API key are required.[/red]")
        sys.exit(1)

    if not url.startswith("https://"):
        console.print("[yellow]Warning: URL should start with https://[/yellow]")

    # Add to database
    try:
        with Database(db_path) as db:
            project_id = db.add_project(
                name=name,
                url=url,
                api_key=key,
                keepalive_method=method,
                table_name=table if method == "table" else None,
                enabled=enabled,
            )

        console.print(f"\n[green]✓[/green] Project added successfully (ID: {project_id})")
        console.print(f"  Name: {name}")
        console.print(f"  Method: {method}")
        console.print(f"  Enabled: {'Yes' if enabled else 'No'}")
        console.print()

    except Exception as e:
        console.print(f"\n[red]✗ Error adding project: {str(e)}[/red]\n")
        sys.exit(1)


@app.command()
def enable(
    project_id: int = typer.Argument(..., help="Project ID"),
    db_path: str = typer.Option("data/sb.db", "--db", help="Database path"),
):
    """Enable a project."""
    try:
        with Database(db_path) as db:
            project = db.get_project(project_id)
            if not project:
                console.print(f"[red]Project {project_id} not found.[/red]")
                sys.exit(1)

            db.enable_project(project_id)
            console.print(f"[green]✓[/green] Project '{project['name']}' enabled")

    except Exception as e:
        console.print(f"[red]✗ Error: {str(e)}[/red]")
        sys.exit(1)


@app.command()
def disable(
    project_id: int = typer.Argument(..., help="Project ID"),
    db_path: str = typer.Option("data/sb.db", "--db", help="Database path"),
):
    """Disable a project."""
    try:
        with Database(db_path) as db:
            project = db.get_project(project_id)
            if not project:
                console.print(f"[red]Project {project_id} not found.[/red]")
                sys.exit(1)

            db.disable_project(project_id)
            console.print(f"[green]✓[/green] Project '{project['name']}' disabled")

    except Exception as e:
        console.print(f"[red]✗ Error: {str(e)}[/red]")
        sys.exit(1)


@app.command()
def delete(
    project_id: int = typer.Argument(..., help="Project ID"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
    db_path: str = typer.Option("data/sb.db", "--db", help="Database path"),
):
    """Delete a project permanently."""
    try:
        with Database(db_path) as db:
            project = db.get_project(project_id)
            if not project:
                console.print(f"[red]Project {project_id} not found.[/red]")
                sys.exit(1)

            if not force:
                confirm = Confirm.ask(
                    f"Delete project '{project['name']}' (ID: {project_id})?"
                )
                if not confirm:
                    console.print("Cancelled.")
                    return

            db.delete_project(project_id)
            console.print(f"[green]✓[/green] Project '{project['name']}' deleted")

    except Exception as e:
        console.print(f"[red]✗ Error: {str(e)}[/red]")
        sys.exit(1)


@app.command()
def show(
    project_id: int = typer.Argument(..., help="Project ID"),
    db_path: str = typer.Option("data/sb.db", "--db", help="Database path"),
):
    """Show detailed information for a project."""
    with Database(db_path) as db:
        dash = Dashboard(db)
        dash.show_project_details(project_id)


@app.command()
def list(
    enabled_only: bool = typer.Option(
        False, "--enabled", "-e", help="Show only enabled projects"
    ),
    db_path: str = typer.Option("data/sb.db", "--db", help="Database path"),
):
    """Alias for dashboard command."""
    dashboard(enabled_only=enabled_only, db_path=db_path)


@app.command()
def version():
    """Show version information."""
    from app import __version__
    console.print(f"Supabase Keepalive v{__version__}")


if __name__ == "__main__":
    app()
