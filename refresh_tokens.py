#!/usr/bin/env python3
"""Refreshes the Strava access token in .tokens.json.

Suitable for running headlessly via cron. Requires a valid refresh token
to already exist in .tokens.json (from a prior interactive OAuth flow).
"""
from auth import refresh_local_tokens


if __name__ == "__main__":
    refresh_local_tokens()
