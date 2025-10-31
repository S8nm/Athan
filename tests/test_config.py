"""Tests for configuration models."""

from athan.config import (
    GuildSettings,
    Location,
    LocationType,
    Prayer,
    PrayerTimes,
    UserSettings,
)


def test_location_is_qatar():
    """Test Qatar location detection."""
    qatar_loc = Location(location_type=LocationType.QATAR)
    assert qatar_loc.is_qatar()

    city_qatar = Location(location_type=LocationType.CITY, city="Doha", country="Qatar")
    assert city_qatar.is_qatar()

    city_other = Location(location_type=LocationType.CITY, city="Dubai", country="UAE")
    assert not city_other.is_qatar()


def test_guild_settings_offsets():
    """Test guild settings prayer offsets."""
    settings = GuildSettings(
        guild_id=123,
        prayer_offsets={"Fajr": 5, "Maghrib": -2},
    )

    assert settings.get_offset(Prayer.FAJR) == 5
    assert settings.get_offset(Prayer.MAGHRIB) == -2
    assert settings.get_offset(Prayer.DHUHR) == 0  # Default


def test_user_settings_offsets():
    """Test user settings prayer offsets."""
    settings = UserSettings(
        user_id=456,
        prayer_offsets={"Isha": 10},
    )

    assert settings.get_offset(Prayer.ISHA) == 10
    assert settings.get_offset(Prayer.FAJR) == 0  # Default


def test_prayer_times_get_time():
    """Test PrayerTimes get_time method."""
    times = PrayerTimes(
        date="2024-01-01",
        fajr="05:30",
        sunrise="06:50",
        dhuhr="12:00",
        asr="15:00",
        maghrib="17:30",
        isha="19:00",
        timezone="Asia/Qatar",
    )

    assert times.get_time(Prayer.FAJR) == "05:30"
    assert times.get_time(Prayer.MAGHRIB) == "17:30"
