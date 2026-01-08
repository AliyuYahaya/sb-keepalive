"""
Terminal dashboard for Supabase Keepalive.

Displays project status in a clean terminal table using Rich.
"""

from typing import List, Dict, Any
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.text import Text

from .db import Database
from .models import Project


class Dashboard:
    """Terminal dashboard for project status."""

    def __init__(self, db: Database):
        """
        Initialize dashboard.

        Args:
            db: Database instance
        """
        self.db = db
        self.console = Console()

    def show(self, enabled_only: bool = False):
        """
        Display project status table.

        Args:
            enabled_only: If True, show only enabled projects
        """
        projects_data = self.db.get_all_projects(enabled_only=enabled_only)

        if not projects_data:
            self.console.print(
                "[yellow]No projects found. Use 'add' command to add projects.[/yellow]"
            )
            return

        projects = [Project.from_dict(p) for p in projects_data]

        # Create table
        table = Table(
            title="Supabase Keepalive Projects",
            show_header=True,
            header_style="bold cyan",
        )

        table.add_column("ID", style="dim", width=4, justify="right")
        table.add_column("Name", style="bold", min_width=15)
        table.add_column("Enabled", width=8, justify="center")
        table.add_column("Method", width=10)
        table.add_column("Last Status", min_width=15)
        table.add_column("Last Checked", min_width=19)

        # Add rows
        for project in projects:
            # Format enabled status
            enabled_text = Text("✓ Yes", style="green") if project.enabled else Text("✗ No", style="red")

            # Format status
            if project.last_status is None:
                status_text = Text("Never run", style="dim")
            elif project.last_status.startswith("SUCCESS"):
                status_text = Text("SUCCESS", style="green")
            else:
                # Truncate long error messages
                status = project.last_status
                if len(status) > 40:
                    status = status[:37] + "..."
                status_text = Text(status, style="red")

            # Format last checked
            if project.last_checked:
                checked_text = self._format_timestamp(project.last_checked)
            else:
                checked_text = Text("Never", style="dim")

            # Format method
            if project.keepalive_method == "rpc":
                method_text = "RPC"
            elif project.keepalive_method == "table":
                table_name = project.table_name or "default"
                method_text = f"Table:{table_name}"
            else:
                method_text = project.keepalive_method

            table.add_row(
                str(project.id),
                project.name,
                enabled_text,
                method_text,
                status_text,
                checked_text,
            )

        # Print table
        self.console.print()
        self.console.print(table)
        self.console.print()

        # Summary
        total = len(projects)
        enabled = sum(1 for p in projects if p.enabled)
        disabled = total - enabled

        summary = f"Total: {total} projects"
        if enabled_only:
            summary += f" (showing {enabled} enabled)"
        else:
            summary += f" ({enabled} enabled, {disabled} disabled)"

        self.console.print(f"[dim]{summary}[/dim]")
        self.console.print()

    def _format_timestamp(self, timestamp_str: str) -> Text:
        """
        Format ISO timestamp for display.

        Args:
            timestamp_str: ISO format timestamp

        Returns:
            Formatted text
        """
        try:
            dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            now = datetime.utcnow()
            delta = now - dt

            # Calculate time ago
            if delta.days > 0:
                if delta.days == 1:
                    time_ago = "1 day ago"
                else:
                    time_ago = f"{delta.days} days ago"
                style = "yellow" if delta.days > 1 else "dim"
            elif delta.seconds >= 3600:
                hours = delta.seconds // 3600
                time_ago = f"{hours}h ago"
                style = "dim"
            elif delta.seconds >= 60:
                minutes = delta.seconds // 60
                time_ago = f"{minutes}m ago"
                style = "dim"
            else:
                time_ago = "just now"
                style = "green"

            return Text(time_ago, style=style)

        except Exception:
            return Text(timestamp_str[:19], style="dim")

    def show_project_details(self, project_id: int):
        """
        Show detailed information for a specific project.

        Args:
            project_id: Project ID
        """
        project_data = self.db.get_project(project_id)

        if not project_data:
            self.console.print(f"[red]Project {project_id} not found.[/red]")
            return

        project = Project.from_dict(project_data)

        self.console.print()
        self.console.print(f"[bold cyan]Project Details: {project.name}[/bold cyan]")
        self.console.print()

        # Create details table
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Field", style="dim", width=20)
        table.add_column("Value")

        table.add_row("ID", str(project.id))
        table.add_row("Name", project.name)
        table.add_row("URL", project.url)
        table.add_row("API Key", self._mask_key(project.api_key))
        table.add_row("Keepalive Method", project.keepalive_method)

        if project.table_name:
            table.add_row("Table Name", project.table_name)

        enabled_text = "[green]Yes[/green]" if project.enabled else "[red]No[/red]"
        table.add_row("Enabled", enabled_text)

        if project.last_status:
            status_color = "green" if project.last_status.startswith("SUCCESS") else "red"
            table.add_row("Last Status", f"[{status_color}]{project.last_status}[/{status_color}]")

        if project.last_checked:
            table.add_row("Last Checked", project.last_checked)

        if project.created_at:
            table.add_row("Created At", project.created_at)

        if project.updated_at:
            table.add_row("Updated At", project.updated_at)

        self.console.print(table)
        self.console.print()

    def _mask_key(self, api_key: str) -> str:
        """
        Mask API key for security.

        Args:
            api_key: Full API key

        Returns:
            Masked key showing only first/last few characters
        """
        if len(api_key) <= 8:
            return "***"

        return f"{api_key[:4]}...{api_key[-4:]}"
