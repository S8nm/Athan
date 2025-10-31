"""Utility functions for the Athan bot."""

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


def load_discord_token() -> str | None:
    """
    Load Discord token from multiple sources, trying in order:
    1. DISCORD_TOKEN.txt (simple file with just the token)
    2. .env file (DISCORD_TOKEN=...)
    3. Environment variable DISCORD_TOKEN
    4. data/DISCORD_TOKEN.txt (alternative location)
    5. ../DISCORD_TOKEN.txt (parent directory)

    Returns the first token found, or None.
    """
    token_locations = [
        "DISCORD_TOKEN.txt",
        ".env",
        "data/DISCORD_TOKEN.txt",
        "../DISCORD_TOKEN.txt",
    ]

    # Try file locations first
    for location in token_locations:
        path = Path(location)
        if path.exists() and path.is_file():
            try:
                content = path.read_text().strip()

                # Handle .env format
                if location.endswith(".env"):
                    for line in content.split("\n"):
                        if line.startswith("DISCORD_TOKEN"):
                            token = line.split("=", 1)[1].strip()
                            if token:
                                logger.info(f"Token loaded from {location}")
                                return token
                # Plain token file
                elif content:
                    logger.info(f"Token loaded from {location}")
                    return content
            except Exception as e:
                logger.warning(f"Failed to read token from {location}: {e}")
                continue

    # Try environment variable
    token = os.getenv("DISCORD_TOKEN")
    if token:
        logger.info("Token loaded from environment variable")
        return token

    logger.error("Discord token not found in any location")
    return None


def humanize_time_delta(seconds: int) -> str:
    """
    Convert seconds to human-readable format.

    Examples:
        30 -> "30 seconds"
        90 -> "1 minute"
        3665 -> "1 hour 1 minute"
        7200 -> "2 hours"
    """
    if seconds < 0:
        return "now"

    if seconds < 60:
        return f"{seconds} second{'s' if seconds != 1 else ''}"

    minutes = seconds // 60
    hours = minutes // 60
    remaining_minutes = minutes % 60

    if hours == 0:
        return f"{minutes} minute{'s' if minutes != 1 else ''}"

    if remaining_minutes == 0:
        return f"{hours} hour{'s' if hours != 1 else ''}"

    return f"{hours} hour{'s' if hours != 1 else ''} {remaining_minutes} min"


def format_prayer_offset(offset: int) -> str:
    """
    Format prayer offset for display.

    Examples:
        5 -> "+5 min"
        -3 -> "-3 min"
        0 -> "No offset"
    """
    if offset == 0:
        return "No offset"
    sign = "+" if offset > 0 else ""
    return f"{sign}{offset} min"


def ensure_directories():
    """Create necessary directories if they don't exist."""
    directories = ["data", "assets"]
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
