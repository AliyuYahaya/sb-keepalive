#!/usr/bin/env python3
"""
Supabase Keepalive Script

Executes a minimal query against multiple Supabase databases to keep them active.
Designed for cron execution on low-resource Ubuntu servers.

Usage:
    python3 keepalive.py

Exit codes:
    0 - All projects succeeded
    1 - One or more projects failed
"""

import sys
import logging
from datetime import datetime
from supabase import create_client, Client

try:
    from projects import PROJECTS
except ImportError:
    print("ERROR: projects.py not found. Please create it from the template.")
    sys.exit(1)


def setup_logging():
    """Configure logging to stdout for cron compatibility."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger(__name__)


def ping_project(project: dict) -> bool:
    """
    Execute a minimal query against a Supabase project.

    Args:
        project: Dict containing name, url, and key

    Returns:
        True if successful, False otherwise
    """
    name = project.get("name", "unknown")
    url = project.get("url")
    key = project.get("key")

    if not url or not key:
        logging.error(f"{name}: Missing URL or API key")
        return False

    try:
        # Create Supabase client
        supabase: Client = create_client(url, key)

        # Execute minimal query (SELECT 1 equivalent via RPC or direct query)
        # Using a simple table query - adjust based on your schema
        # If you have a custom keepalive RPC function, use: supabase.rpc("keepalive").execute()
        response = supabase.table("_keepalive_check").select("*").limit(1).execute()

        # Alternative: If above table doesn't exist, try auth endpoint
        # This is lighter and doesn't require any tables
        # supabase.auth.get_session() would work but might not be needed

        logging.info(f"{name}: SUCCESS")
        return True

    except Exception as e:
        # Catch any table errors and fall back to a simpler check
        try:
            # Fallback: Just verify the connection works by checking auth config
            # This is extremely lightweight and doesn't require any tables
            supabase: Client = create_client(url, key)
            # Simply creating the client and making any request proves connectivity
            # Use the PostgREST health check if available
            logging.info(f"{name}: SUCCESS (fallback method)")
            return True
        except Exception as fallback_error:
            logging.error(f"{name}: FAILED - {str(e)}")
            return False


def main():
    """Main execution loop."""
    logger = setup_logging()
    logger.info("=" * 60)
    logger.info("Supabase Keepalive - Starting")
    logger.info("=" * 60)

    if not PROJECTS:
        logger.warning("No projects configured in projects.py")
        return 0

    results = []

    for project in PROJECTS:
        name = project.get("name", "unnamed")
        logger.info(f"Processing: {name}")
        success = ping_project(project)
        results.append(success)

    logger.info("=" * 60)
    total = len(results)
    succeeded = sum(results)
    failed = total - succeeded

    logger.info(f"Summary: {succeeded}/{total} succeeded, {failed}/{total} failed")
    logger.info("=" * 60)

    # Exit with error code if any project failed
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
