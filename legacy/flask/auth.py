"""Backward-compatible imports for older code.

The auth implementation now lives in steam_hour_booster.auth.
"""

from steam_hour_booster.auth.service import register_user, verify_user

__all__ = ["register_user", "verify_user"]
