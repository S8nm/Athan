"""Tests for database layer."""

import os
import tempfile

import pytest

from athan.config import GuildSettings, Location, LocationType, UserSettings
from athan.db import Database


@pytest.fixture
async def db():
    """Create temporary database for testing."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as f:
        db_path = f.name

    database = Database(db_path)
    await database.connect()

    yield database

    await database.close()
    os.unlink(db_path)


async def test_save_and_get_guild_settings(db):
    """Test saving and retrieving guild settings."""
    location = Location(location_type=LocationType.QATAR)
    settings = GuildSettings(
        guild_id=12345,
        location=location,
        calculation_method="2",
        timezone="Asia/Qatar",
        subscribed_channel_id=67890,
        prayer_offsets={"Fajr": 5},
    )

    await db.save_guild_settings(settings)
    retrieved = await db.get_guild_settings(12345)

    assert retrieved is not None
    assert retrieved.guild_id == 12345
    assert retrieved.subscribed_channel_id == 67890
    assert retrieved.prayer_offsets["Fajr"] == 5
    assert retrieved.location.location_type == LocationType.QATAR


async def test_get_nonexistent_guild_settings(db):
    """Test retrieving settings for non-existent guild."""
    result = await db.get_guild_settings(99999)
    assert result is None


async def test_update_guild_settings(db):
    """Test updating existing guild settings."""
    settings = GuildSettings(guild_id=123, subscribed_channel_id=456)
    await db.save_guild_settings(settings)

    # Update
    settings.subscribed_channel_id = 789
    await db.save_guild_settings(settings)

    retrieved = await db.get_guild_settings(123)
    assert retrieved.subscribed_channel_id == 789


async def test_save_and_get_user_settings(db):
    """Test saving and retrieving user settings."""
    location = Location(location_type=LocationType.CITY, city="Dubai", country="UAE")
    settings = UserSettings(
        user_id=54321,
        location=location,
        calculation_method="2",
        timezone="Asia/Dubai",
        prayer_offsets={"Maghrib": -2},
    )

    await db.save_user_settings(settings)
    retrieved = await db.get_user_settings(54321)

    assert retrieved is not None
    assert retrieved.user_id == 54321
    assert retrieved.prayer_offsets["Maghrib"] == -2
    assert retrieved.location.city == "Dubai"


async def test_get_all_subscribed_guilds(db):
    """Test retrieving all subscribed guilds."""
    # Create guilds with and without subscriptions
    guild1 = GuildSettings(guild_id=1, subscribed_channel_id=100)
    guild2 = GuildSettings(guild_id=2)  # No subscription
    guild3 = GuildSettings(guild_id=3, subscribed_channel_id=300)

    await db.save_guild_settings(guild1)
    await db.save_guild_settings(guild2)
    await db.save_guild_settings(guild3)

    subscribed = await db.get_all_subscribed_guilds()

    assert len(subscribed) == 2
    assert 1 in subscribed
    assert 3 in subscribed
    assert 2 not in subscribed


async def test_prayer_sent_tracking(db):
    """Test prayer sent deduplication."""
    guild_id = 123
    prayer = "Fajr"
    date = "2024-01-01"

    # Initially not sent
    assert not await db.is_prayer_sent(guild_id, prayer, date)

    # Record as scheduled
    await db.record_scheduled_prayer(guild_id, prayer, "05:30", date)

    # Mark as sent
    await db.mark_prayer_sent(guild_id, prayer, date)

    # Should now be marked as sent
    assert await db.is_prayer_sent(guild_id, prayer, date)
