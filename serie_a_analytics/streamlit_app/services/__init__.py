"""
Serie A Analytics - Services Package

This package contains service modules for player analysis and AI insights.
"""

from .player_analysis import (
    PlayerAnalyzer,
    RoleGrouping,
    PlayerStrengthWeakness,
    ROLE_GROUPS,
    ROLE_RELEVANT_METRICS,
)

from .ai_insights import (
    OpenRouterClient,
    generate_player_insights,
)

__all__ = [
    # Player Analysis
    "PlayerAnalyzer",
    "RoleGrouping",
    "PlayerStrengthWeakness",
    "ROLE_GROUPS",
    "ROLE_RELEVANT_METRICS",
    # AI Insights
    "OpenRouterClient",
    "generate_player_insights",
]
