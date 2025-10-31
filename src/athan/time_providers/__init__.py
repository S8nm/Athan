"""Prayer time provider interfaces and implementations."""

from abc import ABC, abstractmethod

from athan.config import Location, PrayerTimes


class TimeProvider(ABC):
    """Abstract base for prayer time providers."""

    @abstractmethod
    async def get_prayer_times(
        self, location: Location, date: str, method: str | None = None
    ) -> PrayerTimes:
        """
        Fetch prayer times for a location and date.

        Args:
            location: Location specification
            date: Date in YYYY-MM-DD format
            method: Optional calculation method

        Returns:
            PrayerTimes object with times in HH:MM format
        """
        pass

    @abstractmethod
    async def close(self):
        """Clean up resources (HTTP sessions, etc.)."""
        pass
