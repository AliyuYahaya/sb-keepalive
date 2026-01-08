"""
Database operations for Supabase Keepalive.

Uses SQLite to manage project configurations and status tracking.
"""

import sqlite3
import os
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path


class Database:
    """SQLite database manager for Supabase projects."""

    def __init__(self, db_path: str = "data/sb.db"):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        # Ensure data directory exists
        db_file = Path(db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)

        self.db_path = db_path
        self.conn = None
        self._connect()
        self._init_schema()

    def _connect(self):
        """Establish database connection."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # Enable column access by name

    def _init_schema(self):
        """Create database schema if it doesn't exist."""
        schema = """
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            url TEXT NOT NULL,
            api_key TEXT NOT NULL,
            keepalive_method TEXT DEFAULT 'rpc',
            table_name TEXT DEFAULT NULL,
            enabled INTEGER DEFAULT 1,
            last_status TEXT DEFAULT NULL,
            last_checked TEXT DEFAULT NULL,
            next_run DATE DEFAULT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_enabled ON projects(enabled);
        CREATE INDEX IF NOT EXISTS idx_name ON projects(name);
        CREATE INDEX IF NOT EXISTS idx_next_run ON projects(next_run);
        """

        cursor = self.conn.cursor()
        cursor.executescript(schema)
        self.conn.commit()

        # Add next_run column if it doesn't exist (for existing databases)
        self._migrate_add_next_run()

    def _migrate_add_next_run(self):
        """Add next_run column to existing databases if missing."""
        cursor = self.conn.cursor()

        # Check if next_run column exists
        cursor.execute("PRAGMA table_info(projects)")
        columns = [row[1] for row in cursor.fetchall()]

        if "next_run" not in columns:
            cursor.execute("ALTER TABLE projects ADD COLUMN next_run DATE DEFAULT NULL")
            self.conn.commit()

    def add_project(
        self,
        name: str,
        url: str,
        api_key: str,
        keepalive_method: str = "rpc",
        table_name: Optional[str] = None,
        enabled: bool = True,
    ) -> int:
        """
        Add a new Supabase project.

        Args:
            name: Project identifier
            url: Supabase project URL
            api_key: Supabase API key
            keepalive_method: 'rpc' or 'table'
            table_name: Table name for 'table' method
            enabled: Whether project is active

        Returns:
            Project ID

        Raises:
            sqlite3.IntegrityError: If project name already exists
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO projects (name, url, api_key, keepalive_method, table_name, enabled)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (name, url, api_key, keepalive_method, table_name, 1 if enabled else 0),
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_project(self, project_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a project by ID.

        Args:
            project_id: Project ID

        Returns:
            Project data as dict or None if not found
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_all_projects(self, enabled_only: bool = False) -> List[Dict[str, Any]]:
        """
        Get all projects.

        Args:
            enabled_only: If True, return only enabled projects

        Returns:
            List of project dicts
        """
        cursor = self.conn.cursor()

        if enabled_only:
            cursor.execute(
                "SELECT * FROM projects WHERE enabled = 1 ORDER BY name"
            )
        else:
            cursor.execute("SELECT * FROM projects ORDER BY name")

        return [dict(row) for row in cursor.fetchall()]

    def get_scheduled_projects(self) -> List[Dict[str, Any]]:
        """
        Get all enabled projects that are scheduled to run today or have never run.

        Returns:
            List of project dicts where next_run is NULL or <= today
        """
        cursor = self.conn.cursor()
        today = datetime.utcnow().date().isoformat()

        cursor.execute(
            """
            SELECT * FROM projects
            WHERE enabled = 1
            AND (next_run IS NULL OR next_run <= ?)
            ORDER BY name
            """,
            (today,),
        )

        return [dict(row) for row in cursor.fetchall()]

    def update_status(
        self, project_id: int, status: str, timestamp: Optional[str] = None
    ):
        """
        Update project status after keepalive attempt.

        Args:
            project_id: Project ID
            status: Status message (e.g., 'SUCCESS', 'FAILED: error message')
            timestamp: ISO timestamp (defaults to now)
        """
        if timestamp is None:
            timestamp = datetime.utcnow().isoformat()

        cursor = self.conn.cursor()
        cursor.execute(
            """
            UPDATE projects
            SET last_status = ?, last_checked = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (status, timestamp, project_id),
        )
        self.conn.commit()

    def update_next_run(self, project_id: int, next_run_date: str):
        """
        Update the next_run date for a project.

        Args:
            project_id: Project ID
            next_run_date: Next run date in ISO format (YYYY-MM-DD)
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            UPDATE projects
            SET next_run = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (next_run_date, project_id),
        )
        self.conn.commit()

    def enable_project(self, project_id: int):
        """Enable a project."""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE projects SET enabled = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (project_id,),
        )
        self.conn.commit()

    def disable_project(self, project_id: int):
        """Disable a project."""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE projects SET enabled = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (project_id,),
        )
        self.conn.commit()

    def delete_project(self, project_id: int):
        """Delete a project permanently."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        self.conn.commit()

    def update_project(
        self,
        project_id: int,
        name: Optional[str] = None,
        url: Optional[str] = None,
        api_key: Optional[str] = None,
        keepalive_method: Optional[str] = None,
        table_name: Optional[str] = None,
    ):
        """
        Update project fields.

        Args:
            project_id: Project ID
            name: New name (optional)
            url: New URL (optional)
            api_key: New API key (optional)
            keepalive_method: New method (optional)
            table_name: New table name (optional)
        """
        updates = []
        params = []

        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if url is not None:
            updates.append("url = ?")
            params.append(url)
        if api_key is not None:
            updates.append("api_key = ?")
            params.append(api_key)
        if keepalive_method is not None:
            updates.append("keepalive_method = ?")
            params.append(keepalive_method)
        if table_name is not None:
            updates.append("table_name = ?")
            params.append(table_name)

        if not updates:
            return

        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(project_id)

        cursor = self.conn.cursor()
        cursor.execute(
            f"UPDATE projects SET {', '.join(updates)} WHERE id = ?", params
        )
        self.conn.commit()

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
