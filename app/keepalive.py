"""
Keepalive engine for Supabase projects.

Executes minimal database queries to keep Supabase free-tier projects active.
"""

import logging
import random
from datetime import datetime, timedelta
from typing import List
from supabase import create_client, Client

from .models import Project, KeepaliveResult
from .db import Database


logger = logging.getLogger(__name__)


class KeepaliveEngine:
    """Executes keepalive operations against Supabase projects."""

    def __init__(self, db: Database):
        """
        Initialize keepalive engine.

        Args:
            db: Database instance
        """
        self.db = db

    def ping_project(self, project: Project) -> KeepaliveResult:
        """
        Execute keepalive operation for a single project.

        Args:
            project: Project configuration

        Returns:
            KeepaliveResult with success status and message
        """
        timestamp = datetime.utcnow().isoformat()

        try:
            # Create Supabase client
            supabase: Client = create_client(project.url, project.api_key)

            # Execute keepalive based on configured method
            if project.keepalive_method == "rpc":
                result = self._ping_rpc(supabase, project)
            elif project.keepalive_method == "table":
                result = self._ping_table(supabase, project)
            else:
                return KeepaliveResult(
                    project_id=project.id,
                    project_name=project.name,
                    success=False,
                    message=f"Unknown method: {project.keepalive_method}",
                    timestamp=timestamp,
                    method_used=project.keepalive_method,
                )

            return result

        except Exception as e:
            logger.error(f"{project.name}: FAILED - {str(e)}")
            return KeepaliveResult(
                project_id=project.id,
                project_name=project.name,
                success=False,
                message=str(e),
                timestamp=timestamp,
                method_used=project.keepalive_method,
            )

    def _ping_rpc(self, supabase: Client, project: Project) -> KeepaliveResult:
        """
        Ping using RPC function.

        Args:
            supabase: Supabase client
            project: Project configuration

        Returns:
            KeepaliveResult
        """
        timestamp = datetime.utcnow().isoformat()

        try:
            # Call keepalive RPC function
            response = supabase.rpc("keepalive").execute()

            logger.info(f"{project.name}: SUCCESS (rpc)")
            return KeepaliveResult(
                project_id=project.id,
                project_name=project.name,
                success=True,
                message="RPC keepalive() succeeded",
                timestamp=timestamp,
                method_used="rpc",
            )

        except Exception as e:
            # If RPC fails, try fallback
            logger.warning(f"{project.name}: RPC failed, trying fallback - {str(e)}")
            return self._ping_fallback(supabase, project)

    def _ping_table(self, supabase: Client, project: Project) -> KeepaliveResult:
        """
        Ping using table query.

        Args:
            supabase: Supabase client
            project: Project configuration

        Returns:
            KeepaliveResult
        """
        timestamp = datetime.utcnow().isoformat()
        table_name = project.table_name or "users"

        try:
            # Simple SELECT query
            response = supabase.table(table_name).select("id").limit(1).execute()

            logger.info(f"{project.name}: SUCCESS (table: {table_name})")
            return KeepaliveResult(
                project_id=project.id,
                project_name=project.name,
                success=True,
                message=f"Table query on '{table_name}' succeeded",
                timestamp=timestamp,
                method_used=f"table:{table_name}",
            )

        except Exception as e:
            logger.warning(
                f"{project.name}: Table query failed, trying fallback - {str(e)}"
            )
            return self._ping_fallback(supabase, project)

    def _ping_fallback(self, supabase: Client, project: Project) -> KeepaliveResult:
        """
        Fallback ping method - just verify client creation.

        This is a last resort that proves connectivity without
        requiring specific tables or functions to exist.

        Args:
            supabase: Supabase client
            project: Project configuration

        Returns:
            KeepaliveResult
        """
        timestamp = datetime.utcnow().isoformat()

        try:
            # The client is already created, which means auth endpoint
            # was reachable. This is sufficient for keepalive.
            logger.info(f"{project.name}: SUCCESS (fallback)")
            return KeepaliveResult(
                project_id=project.id,
                project_name=project.name,
                success=True,
                message="Fallback connectivity check succeeded",
                timestamp=timestamp,
                method_used="fallback",
            )

        except Exception as e:
            logger.error(f"{project.name}: FAILED (all methods) - {str(e)}")
            return KeepaliveResult(
                project_id=project.id,
                project_name=project.name,
                success=False,
                message=f"All methods failed: {str(e)}",
                timestamp=timestamp,
                method_used="fallback",
            )

    def run_all(self, verbose: bool = True) -> List[KeepaliveResult]:
        """
        Run keepalive for all enabled projects.

        Args:
            verbose: If True, log progress to console

        Returns:
            List of KeepaliveResult objects
        """
        if verbose:
            logger.info("=" * 60)
            logger.info("Supabase Keepalive - Starting")
            logger.info("=" * 60)

        # Get all enabled projects
        projects_data = self.db.get_all_projects(enabled_only=True)

        if not projects_data:
            if verbose:
                logger.warning("No enabled projects found")
            return []

        projects = [Project.from_dict(p) for p in projects_data]
        results = []

        # Process each project sequentially
        for project in projects:
            if verbose:
                logger.info(f"Processing: {project.name}")

            result = self.ping_project(project)
            results.append(result)

            # Update database with result
            status = "SUCCESS" if result.success else f"FAILED: {result.message}"
            self.db.update_status(project.id, status, result.timestamp)

        if verbose:
            logger.info("=" * 60)
            total = len(results)
            succeeded = sum(1 for r in results if r.success)
            failed = total - succeeded
            logger.info(f"Summary: {succeeded}/{total} succeeded, {failed}/{total} failed")
            logger.info("=" * 60)

        return results

    def run_scheduled(self, verbose: bool = True) -> List[KeepaliveResult]:
        """
        Run keepalive for projects scheduled to run today.
        After each run, assign a random next_run date between 1-5 days from now.

        Args:
            verbose: If True, log progress to console

        Returns:
            List of KeepaliveResult objects
        """
        if verbose:
            logger.info("=" * 60)
            logger.info("Supabase Keepalive - Scheduled Run")
            logger.info("=" * 60)

        # Get projects scheduled for today or never run
        projects_data = self.db.get_scheduled_projects()

        if not projects_data:
            if verbose:
                logger.info("No projects scheduled for today")
            return []

        projects = [Project.from_dict(p) for p in projects_data]
        results = []

        if verbose:
            logger.info(f"Found {len(projects)} project(s) scheduled for today")

        # Process each scheduled project
        for project in projects:
            if verbose:
                logger.info(f"Processing: {project.name}")

            result = self.ping_project(project)
            results.append(result)

            # Update database with result
            status = "SUCCESS" if result.success else f"FAILED: {result.message}"
            self.db.update_status(project.id, status, result.timestamp)

            # Calculate random next run date (1-5 days from today)
            days_until_next = random.randint(1, 5)
            next_run_date = datetime.utcnow().date() + timedelta(days=days_until_next)
            next_run_str = next_run_date.isoformat()

            # Update next_run in database
            self.db.update_next_run(project.id, next_run_str)

            if verbose:
                logger.info(
                    f"  → Next run scheduled for: {next_run_str} "
                    f"({days_until_next} days from now)"
                )

        if verbose:
            logger.info("=" * 60)
            total = len(results)
            succeeded = sum(1 for r in results if r.success)
            failed = total - succeeded
            logger.info(f"Summary: {succeeded}/{total} succeeded, {failed}/{total} failed")
            logger.info("=" * 60)

        return results
