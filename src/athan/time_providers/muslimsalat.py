"""MuslimSalat.com API time provider."""

import logging
from datetime import datetime
from zoneinfo import ZoneInfo

import aiohttp

from athan.config import Location, LocationType, Prayer, PrayerTimes

logger = logging.getLogger(__name__)


class MuslimSalatProvider:
    """Fetch prayer times from MuslimSalat.com API."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://muslimsalat.com"
        self.session: aiohttp.ClientSession | None = None
        self.cache: dict[str, tuple[PrayerTimes, datetime]] = {}

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close(self):
        """Close the aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()

    def _build_cache_key(self, location: Location, date: str) -> str:
        """Build cache key for location and date."""
        if location.location_type == LocationType.CITY:
            return f"{location.city}_{location.country}_{date}"
        elif location.location_type == LocationType.COORDINATES:
            return f"{location.latitude}_{location.longitude}_{date}"
        return f"location_{date}"

    def _build_url(
        self, 
        location: Location, 
        date: str, 
        daylight_saving: bool = False,
        calculation_method: str | None = None
    ) -> str:
        """Build API URL for location with optional method and daylight saving."""
        # Get city name
        if location.location_type == LocationType.CITY:
            city = location.city.lower().replace(" ", "-") if location.city else "doha"
        elif location.location_type == LocationType.COORDINATES:
            logger.warning("Coordinates not supported, using default location")
            city = "doha"
        else:
            city = "doha"
        
        # Format date as DD-MM-YYYY for API
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            api_date = date_obj.strftime("%d-%m-%Y")
        except ValueError:
            api_date = datetime.now().strftime("%d-%m-%Y")
        
        # Build URL with parameters: location/date/daylight/method.json
        daylight_str = "true" if daylight_saving else "false"
        
        if calculation_method and calculation_method.isdigit():
            # Full URL with all parameters
            url = f"{self.base_url}/{city}/weekly/{api_date}/{daylight_str}/{calculation_method}.json"
        elif daylight_saving:
            # URL with daylight saving only
            url = f"{self.base_url}/{city}/weekly/{api_date}/{daylight_str}.json"
        else:
            # Simple daily URL (auto settings)
            url = f"{self.base_url}/{city}.json"
        
        return url

    async def get_prayer_times(
        self, 
        location: Location, 
        date: str, 
        timezone: str,
        daylight_saving: bool = False,
        calculation_method: str | None = None
    ) -> PrayerTimes | None:
        """
        Fetch prayer times from MuslimSalat.com API.

        Args:
            location: Location object
            date: Date string in YYYY-MM-DD format
            timezone: Timezone string

        Returns:
            PrayerTimes object or None if failed
        """
        # Check cache first
        cache_key = self._build_cache_key(location, date)
        if cache_key in self.cache:
            cached_times, cached_at = self.cache[cache_key]
            # Cache valid for 1 hour
            if (datetime.now(ZoneInfo("UTC")) - cached_at).total_seconds() < 3600:
                logger.debug(f"Using cached prayer times for {cache_key}")
                return cached_times

        try:
            session = await self._get_session()
            url = self._build_url(location, date, daylight_saving, calculation_method)

            # Add API key as parameter
            params = {"key": self.api_key}

            logger.info(f"Fetching prayer times...")

            async with session.get(url, params=params, timeout=10) as response:
                if response.status != 200:
                    logger.error(f"Prayer times API returned status {response.status}")
                    return None

                data = await response.json()

                if not data or "items" not in data or len(data["items"]) == 0:
                    logger.error("Invalid response from prayer times API")
                    return None

                # Get today's times (first item)
                times = data["items"][0]

                # MuslimSalat returns times in format "HH:MM am/pm"
                tz = ZoneInfo(timezone)
                today = datetime.strptime(date, "%Y-%m-%d").date()

                # Parse all prayer times
                prayer_data = {}

                for prayer, key in [
                    (Prayer.FAJR, "fajr"),
                    (Prayer.DHUHR, "dhuhr"),
                    (Prayer.ASR, "asr"),
                    (Prayer.MAGHRIB, "maghrib"),
                    (Prayer.ISHA, "isha"),
                ]:
                    if key in times:
                        time_str = times[key].strip()
                        try:
                            # Parse "5:58 am" or "12:44 pm" format
                            time_obj = datetime.strptime(time_str, "%I:%M %p")
                            # Combine with today's date and timezone
                            prayer_dt = datetime.combine(today, time_obj.time()).replace(tzinfo=tz)
                            prayer_data[prayer] = prayer_dt
                        except ValueError as e:
                            logger.warning(f"Failed to parse {prayer.value} time: {time_str} - {e}")
                            return None

                # Parse sunrise if available
                sunrise_dt = None
                if "shurooq" in times:
                    time_str = times["shurooq"].strip()
                    try:
                        time_obj = datetime.strptime(time_str, "%I:%M %p")
                        sunrise_dt = datetime.combine(today, time_obj.time()).replace(tzinfo=tz)
                    except ValueError:
                        logger.warning(f"Failed to parse sunrise time: {time_str}")

                # Create PrayerTimes object with all required fields
                prayer_times = PrayerTimes(
                    date=date,
                    fajr=prayer_data[Prayer.FAJR].strftime("%H:%M"),
                    sunrise=sunrise_dt.strftime("%H:%M") if sunrise_dt else "06:00",
                    dhuhr=prayer_data[Prayer.DHUHR].strftime("%H:%M"),
                    asr=prayer_data[Prayer.ASR].strftime("%H:%M"),
                    maghrib=prayer_data[Prayer.MAGHRIB].strftime("%H:%M"),
                    isha=prayer_data[Prayer.ISHA].strftime("%H:%M"),
                    timezone=timezone,
                )

                # Cache the result
                self.cache[cache_key] = (prayer_times, datetime.now(ZoneInfo("UTC")))

                logger.info("Successfully fetched prayer times")
                return prayer_times

        except aiohttp.ClientError as e:
            logger.error(f"Network error fetching prayer times: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching prayer times: {e}", exc_info=True)
            return None
