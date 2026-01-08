#!/usr/bin/env python3
"""
Migration script for Supabase Keepalive v1.0 to v2.0

Migrates projects from projects.py config file to SQLite database.

Usage:
    python migrate.py
"""

import sys
from pathlib import Path
from rich.console import Console

from app.db import Database

console = Console()


def main():
    """Run migration from projects.py to SQLite."""

    console.print("\n[bold cyan]Supabase Keepalive Migration[/bold cyan]")
    console.print("Migrating from projects.py to SQLite database\n")

    # Check if projects.py exists
    if not Path("projects.py").exists():
        console.print("[yellow]No projects.py file found.[/yellow]")
        console.print("If you're doing a fresh install, use 'python cli.py add' to add projects.")
        return

    # Import projects from old config
    try:
        from projects import PROJECTS
    except ImportError:
        console.print("[red]Error: Could not import PROJECTS from projects.py[/red]")
        console.print("Make sure projects.py contains a PROJECTS list.")
        sys.exit(1)

    if not PROJECTS:
        console.print("[yellow]No projects found in projects.py[/yellow]")
        return

    console.print(f"Found {len(PROJECTS)} project(s) to migrate\n")

    # Initialize database
    with Database("data/sb.db") as db:
        migrated = 0
        skipped = 0
        errors = 0

        for i, project in enumerate(PROJECTS, 1):
            name = project.get("name", f"project-{i}")
            url = project.get("url")
            key = project.get("key")

            if not url or not key:
                console.print(f"[yellow]⚠[/yellow] Skipping '{name}' - missing URL or API key")
                skipped += 1
                continue

            try:
                # Add project to database
                project_id = db.add_project(
                    name=name,
                    url=url,
                    api_key=key,
                    keepalive_method="rpc",  # Default to RPC
                    table_name=None,
                    enabled=True,
                )

                console.print(f"[green]✓[/green] Migrated: {name} (ID: {project_id})")
                migrated += 1

            except Exception as e:
                if "UNIQUE constraint failed" in str(e):
                    console.print(f"[yellow]⚠[/yellow] Skipping '{name}' - already exists")
                    skipped += 1
                else:
                    console.print(f"[red]✗[/red] Error migrating '{name}': {str(e)}")
                    errors += 1

    # Summary
    console.print()
    console.print(f"[bold]Migration Complete[/bold]")
    console.print(f"  Migrated: {migrated}")
    console.print(f"  Skipped:  {skipped}")
    console.print(f"  Errors:   {errors}")
    console.print()

    if migrated > 0:
        console.print("[green]✓[/green] Projects successfully migrated to SQLite")
        console.print("\nNext steps:")
        console.print("  1. View projects: [cyan]python cli.py dashboard[/cyan]")
        console.print("  2. Test keepalive: [cyan]python cli.py run[/cyan]")
        console.print("  3. Backup old config: [cyan]mv projects.py projects.py.bak[/cyan]")
    else:
        console.print("[yellow]No projects were migrated[/yellow]")

    console.print()


if __name__ == "__main__":
    main()
