"""Configuration models and settings."""

from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class Prayer(str, Enum):
    """Prayer names."""

    FAJR = "Fajr"
    SUNRISE = "Sunrise"
    DHUHR = "Dhuhr"
    ASR = "Asr"
    MAGHRIB = "Maghrib"
    ISHA = "Isha"


class CalculationMethod(str, Enum):
    """MuslimSalat.com API calculation methods."""

    EGYPT = "1"  # Egyptian General Authority of Survey
    KARACHI_SHAFI = "2"  # University Of Islamic Sciences, Karachi (Shafi)
    KARACHI_HANAFI = "3"  # University Of Islamic Sciences, Karachi (Hanafi)
    ISNA = "4"  # Islamic Circle of North America
    MWL = "5"  # Muslim World League
    UMM_AL_QURA = "6"  # Umm Al-Qura
    FIXED_ISHA = "7"  # Fixed Isha


class LocationType(str, Enum):
    """Location specification type."""

    CITY = "city"
    COORDINATES = "coordinates"


class BotSettings(BaseSettings):
    """Bot-wide configuration from environment."""

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }

    discord_token: str = Field(alias="DISCORD_TOKEN")
    muslimsalat_api_key: str = Field(
        alias="MUSLIMSALAT_API_KEY",
        description="API key for MuslimSalat.com prayer times API"
    )
    database_path: str = Field(default="data/athan.db", alias="DATABASE_PATH")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")


class Location(BaseModel):
    """Location specification for prayer times."""

    location_type: LocationType
    city: str | None = None
    country: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    daylight_saving: bool = False


class GuildSettings(BaseModel):
    """Per-guild configuration."""

    guild_id: int
    location: Location | None = None
    calculation_method: str = CalculationMethod.MWL.value
    timezone: str = "UTC"
    subscribed_channel_id: int | None = None
    voice_channel_id: int | None = None
    ping_role_id: int | None = None  # Role to mention in notifications
    enabled_prayers: list[Prayer] = Field(
        default_factory=lambda: [
            Prayer.FAJR,
            Prayer.DHUHR,
            Prayer.ASR,
            Prayer.MAGHRIB,
            Prayer.ISHA,
        ]
    )
    prayer_offsets: dict[str, int] = Field(default_factory=dict)  # Prayer -> minutes offset

    def get_offset(self, prayer: Prayer) -> int:
        """Get offset for a prayer in minutes."""
        return self.prayer_offsets.get(prayer.value, 0)


class UserSettings(BaseModel):
    """Per-user configuration for DM preferences."""

    user_id: int
    location: Location | None = None
    calculation_method: str = CalculationMethod.MWL.value
    timezone: str = "UTC"
    prayer_offsets: dict[str, int] = Field(default_factory=dict)

    def get_offset(self, prayer: Prayer) -> int:
        """Get offset for a prayer in minutes."""
        return self.prayer_offsets.get(prayer.value, 0)


class PrayerTimes(BaseModel):
    """Prayer times for a single day."""

    date: str  # YYYY-MM-DD
    fajr: str  # HH:MM
    sunrise: str  # HH:MM
    dhuhr: str  # HH:MM
    asr: str  # HH:MM
    maghrib: str  # HH:MM
    isha: str  # HH:MM
    timezone: str

    def get_time(self, prayer: Prayer) -> str:
        """Get time string for a prayer."""
        return getattr(self, prayer.value.lower())


def ensure_data_directory():
    """Ensure data directory exists for database."""
    settings = BotSettings()
    db_path = Path(settings.database_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
