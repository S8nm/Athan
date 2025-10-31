"""Tests for prayer time providers."""

import pytest

from athan.config import Location, LocationType
from athan.time_providers.muslimsalat import MuslimSalatProvider


class TestMuslimSalatProvider:
    """Test MuslimSalat.com provider."""

    @pytest.fixture
    def provider(self):
        """Create provider instance."""
        return MuslimSalatProvider()

    def test_build_cache_key(self, provider):
        """Test cache key generation."""
        # Qatar location
        location = Location(location_type=LocationType.QATAR)
        key = provider._build_cache_key(location, "2025-10-31")
        assert key == "qatar_2025-10-31"

        # City location
        location = Location(location_type=LocationType.CITY, city="London", country="UK")
        key = provider._build_cache_key(location, "2025-10-31")
        assert key == "London_UK_2025-10-31"

    def test_build_url_qatar(self, provider):
        """Test URL building for Qatar."""
        location = Location(location_type=LocationType.QATAR)
        url = provider._build_url(location)
        assert url == "https://muslimsalat.com/doha.json"

    def test_build_url_city(self, provider):
        """Test URL building for city."""
        location = Location(location_type=LocationType.CITY, city="London", country="UK")
        url = provider._build_url(location)
        assert url == "https://muslimsalat.com/london.json"

    def test_build_url_city_with_spaces(self, provider):
        """Test URL building for city with spaces."""
        location = Location(location_type=LocationType.CITY, city="New York", country="USA")
        url = provider._build_url(location)
        assert url == "https://muslimsalat.com/new-york.json"

    @pytest.mark.asyncio
    async def test_close(self, provider):
        """Test provider cleanup."""
        await provider.close()
        assert provider.session is None or provider.session.closed
