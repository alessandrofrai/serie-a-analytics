"""
Serie A 2015-2016 Analytics Dashboard - Supabase Configuration

This module handles the Supabase client connection and provides
utility functions for database operations.
"""

import logging
from functools import lru_cache
from typing import Optional

from supabase import Client, create_client

from .settings import SUPABASE_KEY, SUPABASE_SERVICE_KEY, SUPABASE_URL

logger = logging.getLogger(__name__)


class SupabaseConnectionError(Exception):
    """Custom exception for Supabase connection errors."""
    pass


@lru_cache(maxsize=1)
def get_supabase_client(use_service_key: bool = False) -> Client:
    """
    Get a cached Supabase client instance.

    Args:
        use_service_key: If True, use the service key for admin operations.
                        If False, use the anon key for public operations.

    Returns:
        Supabase Client instance

    Raises:
        SupabaseConnectionError: If connection cannot be established
    """
    if not SUPABASE_URL:
        raise SupabaseConnectionError(
            "SUPABASE_URL is not set. Please configure your .env file."
        )

    key = SUPABASE_SERVICE_KEY if use_service_key else SUPABASE_KEY

    if not key:
        key_type = "SUPABASE_SERVICE_KEY" if use_service_key else "SUPABASE_KEY"
        raise SupabaseConnectionError(
            f"{key_type} is not set. Please configure your .env file."
        )

    try:
        client = create_client(SUPABASE_URL, key)
        logger.info(f"Successfully connected to Supabase (service_key={use_service_key})")
        return client
    except Exception as e:
        logger.error(f"Failed to connect to Supabase: {e}")
        raise SupabaseConnectionError(f"Failed to connect to Supabase: {e}")


def test_connection() -> bool:
    """
    Test the Supabase connection.

    Returns:
        True if connection is successful, False otherwise
    """
    try:
        client = get_supabase_client()
        # Try a simple query to test connection
        client.table("teams").select("*").limit(1).execute()
        logger.info("Supabase connection test successful")
        return True
    except Exception as e:
        logger.error(f"Supabase connection test failed: {e}")
        return False


def get_table_count(table_name: str) -> int:
    """
    Get the number of rows in a table.

    Args:
        table_name: Name of the table

    Returns:
        Number of rows in the table
    """
    try:
        client = get_supabase_client()
        response = client.table(table_name).select("*", count="exact").execute()
        return response.count or 0
    except Exception as e:
        logger.error(f"Failed to get count for table {table_name}: {e}")
        return 0


def clear_table(table_name: str) -> bool:
    """
    Clear all data from a table. Use with caution!

    Args:
        table_name: Name of the table to clear

    Returns:
        True if successful, False otherwise
    """
    try:
        client = get_supabase_client(use_service_key=True)
        # Delete all rows (Supabase requires a condition)
        client.table(table_name).delete().neq("id", -1).execute()
        logger.info(f"Successfully cleared table: {table_name}")
        return True
    except Exception as e:
        logger.error(f"Failed to clear table {table_name}: {e}")
        return False


def batch_insert(table_name: str, data: list, batch_size: int = 100) -> bool:
    """
    Insert data in batches to avoid timeout issues.

    Args:
        table_name: Name of the table
        data: List of dictionaries to insert
        batch_size: Number of rows per batch

    Returns:
        True if all batches were inserted successfully, False otherwise
    """
    try:
        client = get_supabase_client(use_service_key=True)
        total = len(data)

        for i in range(0, total, batch_size):
            batch = data[i:i + batch_size]
            client.table(table_name).insert(batch).execute()
            logger.debug(f"Inserted batch {i // batch_size + 1} ({len(batch)} rows)")

        logger.info(f"Successfully inserted {total} rows into {table_name}")
        return True
    except Exception as e:
        logger.error(f"Failed to batch insert into {table_name}: {e}")
        return False
