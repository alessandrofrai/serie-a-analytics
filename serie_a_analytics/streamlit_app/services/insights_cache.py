"""
Serie A Analytics - Insights Cache Service

This module provides caching of AI-generated player insights on Supabase
for persistent storage across sessions.

Table schema (player_insights):
- id: SERIAL PRIMARY KEY
- player_id: INTEGER NOT NULL
- team_id: INTEGER NOT NULL
- manager_id: INTEGER NOT NULL
- player_name: TEXT
- role_name_it: TEXT
- strength_insights: JSONB (array of strings)
- weakness_insights: JSONB (array of strings)
- model_used: TEXT
- created_at: TIMESTAMP DEFAULT NOW()

Unique constraint on (player_id, team_id, manager_id) to avoid duplicates.
"""

import os
import json
import logging
from typing import Optional, List
from dataclasses import asdict

logger = logging.getLogger(__name__)

# Try to import Supabase
try:
    from supabase import Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    logger.warning("Supabase not available for insights caching")


def get_supabase_client() -> Optional["Client"]:
    """Get Supabase client if available."""
    if not SUPABASE_AVAILABLE:
        return None

    try:
        # Import from config
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

        from config import get_supabase_client as get_client
        return get_client(use_service_key=True)
    except Exception as e:
        logger.debug(f"Could not get Supabase client: {e}")
        return None


def save_player_insights(
    player_id: int,
    team_id: int,
    manager_id: int,
    player_name: str,
    role_name_it: str,
    strength_insights: List[str],
    weakness_insights: List[str],
    model_used: str = "unknown"
) -> bool:
    """
    Save player insights to Supabase.

    Args:
        player_id: Player ID
        team_id: Team ID
        manager_id: Manager ID
        player_name: Player name
        role_name_it: Role in Italian
        strength_insights: List of strength bullet points
        weakness_insights: List of weakness bullet points
        model_used: AI model used to generate insights

    Returns:
        True if saved successfully, False otherwise
    """
    client = get_supabase_client()
    if client is None:
        return False

    try:
        # Check if record already exists
        existing = client.table("player_insights").select("id").eq(
            "player_id", player_id
        ).eq(
            "team_id", team_id
        ).eq(
            "manager_id", manager_id
        ).execute()

        data = {
            "player_id": player_id,
            "team_id": team_id,
            "manager_id": manager_id,
            "player_name": player_name,
            "role_name_it": role_name_it,
            "strength_insights": strength_insights,
            "weakness_insights": weakness_insights,
            "model_used": model_used
        }

        if existing.data and len(existing.data) > 0:
            # Update existing record
            client.table("player_insights").update(data).eq(
                "player_id", player_id
            ).eq(
                "team_id", team_id
            ).eq(
                "manager_id", manager_id
            ).execute()
        else:
            # Insert new record
            client.table("player_insights").insert(data).execute()

        logger.info(f"Saved insights for player {player_id}")
        return True

    except Exception as e:
        logger.error(f"Failed to save insights: {e}")
        return False


def get_player_insights(
    player_id: int,
    team_id: int,
    manager_id: int
) -> Optional[dict]:
    """
    Get cached player insights from Supabase.

    Args:
        player_id: Player ID
        team_id: Team ID
        manager_id: Manager ID

    Returns:
        Dict with strength_insights and weakness_insights, or None if not found
    """
    client = get_supabase_client()
    if client is None:
        return None

    try:
        result = client.table("player_insights").select(
            "strength_insights, weakness_insights, model_used, created_at"
        ).eq(
            "player_id", player_id
        ).eq(
            "team_id", team_id
        ).eq(
            "manager_id", manager_id
        ).execute()

        if result.data and len(result.data) > 0:
            logger.debug(f"Found cached insights for player {player_id}")
            return result.data[0]

        return None

    except Exception as e:
        logger.debug(f"Failed to get cached insights: {e}")
        return None


def clear_player_insights(player_id: int = None) -> bool:
    """
    Clear cached insights.

    Args:
        player_id: If provided, clear only for this player. Otherwise clear all.

    Returns:
        True if successful, False otherwise
    """
    client = get_supabase_client()
    if client is None:
        return False

    try:
        if player_id is not None:
            client.table("player_insights").delete().eq(
                "player_id", player_id
            ).execute()
        else:
            client.table("player_insights").delete().neq("id", -1).execute()

        return True

    except Exception as e:
        logger.error(f"Failed to clear insights: {e}")
        return False


def ensure_table_exists() -> bool:
    """
    Check if the player_insights table exists.
    Note: Table creation should be done via Supabase dashboard or migration.

    Returns:
        True if table exists, False otherwise
    """
    client = get_supabase_client()
    if client is None:
        return False

    try:
        # Try to query the table
        client.table("player_insights").select("id").limit(1).execute()
        return True
    except Exception as e:
        logger.warning(f"player_insights table may not exist: {e}")
        return False


# SQL to create the table (run this in Supabase SQL editor):
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS player_insights (
    id SERIAL PRIMARY KEY,
    player_id INTEGER NOT NULL,
    team_id INTEGER NOT NULL,
    manager_id INTEGER NOT NULL,
    player_name TEXT,
    role_name_it TEXT,
    strength_insights JSONB DEFAULT '[]'::jsonb,
    weakness_insights JSONB DEFAULT '[]'::jsonb,
    model_used TEXT DEFAULT 'unknown',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(player_id, team_id, manager_id)
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_player_insights_lookup
ON player_insights(player_id, team_id, manager_id);

-- Trigger to update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_player_insights_updated_at ON player_insights;
CREATE TRIGGER update_player_insights_updated_at
    BEFORE UPDATE ON player_insights
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
"""
