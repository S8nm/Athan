"""Integration tests for the Athan bot."""

from pathlib import Path

import pytest

from athan.config import GuildSettings, Location, LocationType, Prayer
from athan.db import Database


@pytest.mark.asyncio
async def test_full_guild_setup_workflow():
    """Test complete guild setup and configuration workflow."""
    # Setup
    db_path = "test_integration.db"
    db = Database(db_path)
    await db.connect()

    try:
        guild_id = 123456789
        channel_id = 987654321
        voice_channel_id = 111111111
        role_id = 222222222

        # 1. Create initial guild settings (simulating /setup)
        location = Location(location_type=LocationType.QATAR)
        settings = GuildSettings(
            guild_id=guild_id,
            location=location,
            timezone="Asia/Qatar",
            subscribed_channel_id=None,
        )
        await db.save_guild_settings(settings)

        # 2. Subscribe to notifications (simulating /subscribe)
        settings.subscribed_channel_id = channel_id
        settings.voice_channel_id = voice_channel_id
        settings.ping_role_id = role_id
        await db.save_guild_settings(settings)

        # 3. Set prayer offsets (simulating /set_offset)
        settings.prayer_offsets[Prayer.FAJR] = 5
        settings.prayer_offsets[Prayer.MAGHRIB] = -2
        await db.save_guild_settings(settings)

        # 4. Verify settings were saved correctly
        retrieved = await db.get_guild_settings(guild_id)
        assert retrieved is not None
        assert retrieved.guild_id == guild_id
        assert retrieved.location.location_type == LocationType.QATAR
        assert retrieved.subscribed_channel_id == channel_id
        assert retrieved.voice_channel_id == voice_channel_id
        assert retrieved.ping_role_id == role_id
        assert retrieved.prayer_offsets[Prayer.FAJR] == 5
        assert retrieved.prayer_offsets[Prayer.MAGHRIB] == -2
        assert retrieved.prayer_offsets.get(Prayer.DHUHR, 0) == 0  # Default

        # 5. Verify guild appears in subscribed list
        subscribed = await db.get_all_subscribed_guilds()
        assert guild_id in subscribed

        # 6. Unsubscribe (simulating /unsubscribe)
        settings.subscribed_channel_id = None
        settings.voice_channel_id = None
        settings.ping_role_id = None
        await db.save_guild_settings(settings)

        subscribed = await db.get_all_subscribed_guilds()
        assert guild_id not in subscribed

    finally:
        await db.close()
        Path(db_path).unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_multiple_guilds_isolation():
    """Test that multiple guilds maintain separate settings."""
    db_path = "test_multi_guild.db"
    db = Database(db_path)
    await db.connect()

    try:
        # Setup guild 1 with Qatar
        settings1 = GuildSettings(
            guild_id=1,
            location=Location(location_type=LocationType.QATAR),
            timezone="Asia/Qatar",
            subscribed_channel_id=100,
        )
        settings1.prayer_offsets[Prayer.FAJR] = 5
        await db.save_guild_settings(settings1)

        # Setup guild 2 with city
        settings2 = GuildSettings(
            guild_id=2,
            location=Location(location_type=LocationType.CITY, city="Dubai", country="UAE"),
            timezone="Asia/Dubai",
            subscribed_channel_id=200,
            voice_channel_id=201,
            ping_role_id=202,
        )
        settings2.prayer_offsets[Prayer.MAGHRIB] = -3
        await db.save_guild_settings(settings2)

        # Verify guild 1 settings
        retrieved1 = await db.get_guild_settings(1)
        assert retrieved1.location.location_type == LocationType.QATAR
        assert retrieved1.subscribed_channel_id == 100
        assert retrieved1.voice_channel_id is None
        assert retrieved1.ping_role_id is None
        assert retrieved1.prayer_offsets[Prayer.FAJR] == 5
        assert retrieved1.prayer_offsets.get(Prayer.MAGHRIB, 0) == 0

        # Verify guild 2 settings
        retrieved2 = await db.get_guild_settings(2)
        assert retrieved2.location.location_type == LocationType.CITY
        assert retrieved2.location.city == "Dubai"
        assert retrieved2.subscribed_channel_id == 200
        assert retrieved2.voice_channel_id == 201
        assert retrieved2.ping_role_id == 202
        assert retrieved2.prayer_offsets.get(Prayer.FAJR, 0) == 0
        assert retrieved2.prayer_offsets[Prayer.MAGHRIB] == -3

        # Both should be in subscribed list
        subscribed = await db.get_all_subscribed_guilds()
        assert 1 in subscribed
        assert 2 in subscribed

    finally:
        await db.close()
        Path(db_path).unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_location_validation():
    """Test that location objects validate correctly."""
    # Test Qatar location
    qatar_loc = Location(location_type=LocationType.QATAR)
    assert qatar_loc.is_qatar()

    # Test city location
    city_loc = Location(location_type=LocationType.CITY, city="Dubai", country="UAE")
    assert city_loc.city == "Dubai"
    assert city_loc.country == "UAE"

    # Test coordinates location
    coord_loc = Location(
        location_type=LocationType.COORDINATES, latitude=25.276987, longitude=55.296249
    )
    assert coord_loc.latitude == 25.276987
    assert coord_loc.longitude == 55.296249


@pytest.mark.asyncio
async def test_prayer_offset_edge_cases():
    """Test prayer offset calculations with edge cases."""
    db_path = "test_offsets.db"
    db = Database(db_path)
    await db.connect()

    try:
        settings = GuildSettings(
            guild_id=999,
            location=Location(location_type=LocationType.QATAR),
            timezone="Asia/Qatar",
        )

        # Test large positive offset
        settings.prayer_offsets[Prayer.FAJR] = 120  # 2 hours
        await db.save_guild_settings(settings)

        retrieved = await db.get_guild_settings(999)
        assert retrieved.prayer_offsets[Prayer.FAJR] == 120

        # Test large negative offset
        settings.prayer_offsets[Prayer.ISHA] = -60  # -1 hour
        await db.save_guild_settings(settings)

        retrieved = await db.get_guild_settings(999)
        assert retrieved.prayer_offsets[Prayer.ISHA] == -60

        # Test zero offset
        settings.prayer_offsets[Prayer.DHUHR] = 0
        await db.save_guild_settings(settings)

        retrieved = await db.get_guild_settings(999)
        assert retrieved.prayer_offsets[Prayer.DHUHR] == 0

    finally:
        await db.close()
        Path(db_path).unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_enabled_prayers_management():
    """Test enabling and disabling specific prayers."""
    db_path = "test_enabled.db"
    db = Database(db_path)
    await db.connect()

    try:
        guild_id = 555
        settings = GuildSettings(
            guild_id=guild_id,
            location=Location(location_type=LocationType.QATAR),
            timezone="Asia/Qatar",
            subscribed_channel_id=123,
        )

        # By default, all prayers should be enabled
        assert len(settings.enabled_prayers) == 5
        assert Prayer.FAJR in settings.enabled_prayers
        assert Prayer.DHUHR in settings.enabled_prayers
        assert Prayer.ASR in settings.enabled_prayers
        assert Prayer.MAGHRIB in settings.enabled_prayers
        assert Prayer.ISHA in settings.enabled_prayers

        # Disable Fajr
        settings.enabled_prayers.remove(Prayer.FAJR)
        await db.save_guild_settings(settings)

        # Verify it was disabled
        retrieved = await db.get_guild_settings(guild_id)
        assert Prayer.FAJR not in retrieved.enabled_prayers
        assert len(retrieved.enabled_prayers) == 4

    finally:
        await db.close()
        Path(db_path).unlink(missing_ok=True)
