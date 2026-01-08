#!/usr/bin/env python3
"""
Migration script to add next_run column to existing databases.

This script adds the next_run DATE column to the projects table
for existing sb-keepalive installations.

Usage:
    python migrate_next_run.py [--db path/to/db]
"""

import sys
import sqlite3
from pathlib import Path

import typer
from rich.console import Console

console = Console()


def migrate_database(db_path: str = "data/sb.db"):
    """
    Add next_run column to projects table.

    Args:
        db_path: Path to SQLite database file
    """
    db_file = Path(db_path)

    if not db_file.exists():
        console.print(f"[red]Database not found at: {db_path}[/red]")
        console.print("[yellow]No migration needed - database will be created with next_run column.[/yellow]")
        return

    console.print(f"\n[cyan]Migrating database: {db_path}[/cyan]\n")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if next_run column already exists
        cursor.execute("PRAGMA table_info(projects)")
        columns = [row[1] for row in cursor.fetchall()]

        if "next_run" in columns:
            console.print("[green]✓[/green] Database already has next_run column")
            console.print("[dim]No migration needed.[/dim]\n")
            return

        # Add next_run column
        console.print("[yellow]Adding next_run column...[/yellow]")
        cursor.execute("ALTER TABLE projects ADD COLUMN next_run DATE DEFAULT NULL")
        conn.commit()

        # Create index on next_run
        console.print("[yellow]Creating index on next_run...[/yellow]")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_next_run ON projects(next_run)")
        conn.commit()

        console.print("[green]✓[/green] Migration completed successfully!\n")

        # Show summary
        cursor.execute("SELECT COUNT(*) FROM projects")
        project_count = cursor.fetchone()[0]

        console.print(f"[dim]Total projects: {project_count}[/dim]")
        console.print(f"[dim]All projects have next_run = NULL (will run on next scheduled execution)[/dim]\n")

        conn.close()

    except Exception as e:
        console.print(f"\n[red]✗ Migration failed: {str(e)}[/red]\n")
        sys.exit(1)


def main(
    db_path: str = typer.Option("data/sb.db", "--db", help="Database path"),
):
    """Migrate database to add next_run column."""
    migrate_database(db_path)


if __name__ == "__main__":
    typer.run(main)
