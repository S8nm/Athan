"""Prayer time scheduler with offset support and persistence."""

import asyncio
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import discord

from athan.config import BotSettings, GuildSettings, Prayer, PrayerTimes
from athan.db import Database
from athan.time_providers.muslimsalat import MuslimSalatProvider

logger = logging.getLogger(__name__)


class PrayerScheduler:
    """Manages scheduled prayer notifications."""

    def __init__(self, bot: discord.Client, database: Database, bot_settings: BotSettings):
        self.bot = bot
        self.db = database
        self.settings = bot_settings
        self.muslimsalat_provider = MuslimSalatProvider(bot_settings.muslimsalat_api_key)
        self.tasks: dict[int, asyncio.Task] = {}
        self._running = False

    async def start(self):
        """Start scheduler for all subscribed guilds."""
        self._running = True
        guild_ids = await self.db.get_all_subscribed_guilds()
        logger.info(f"Starting scheduler for {len(guild_ids)} guilds")

        for guild_id in guild_ids:
            await self.schedule_guild(guild_id)

    async def stop(self):
        """Stop all scheduled tasks."""
        self._running = False
        for task in self.tasks.values():
            task.cancel()
        await self.muslimsalat_provider.close()
        logger.info("Scheduler stopped")

    async def schedule_guild(self, guild_id: int):
        """Schedule prayer notifications for a guild."""
        if guild_id in self.tasks:
            self.tasks[guild_id].cancel()

        self.tasks[guild_id] = asyncio.create_task(self._guild_loop(guild_id))
        logger.info(f"Scheduled guild {guild_id}")

    async def unschedule_guild(self, guild_id: int):
        """Remove scheduled tasks for a guild."""
        if guild_id in self.tasks:
            self.tasks[guild_id].cancel()
            del self.tasks[guild_id]
            logger.info(f"Unscheduled guild {guild_id}")

    async def _guild_loop(self, guild_id: int):
        """Main loop for a single guild's prayer notifications."""
        while self._running:
            try:
                await self._process_guild_prayers(guild_id)
            except asyncio.CancelledError:
                logger.info(f"Guild loop cancelled for {guild_id}")
                break
            except Exception as e:
                logger.error(f"Error in guild loop {guild_id}: {e}", exc_info=True)

            # Check again in 1 minute
            await asyncio.sleep(60)

    async def _process_guild_prayers(self, guild_id: int):
        """Check and send prayer notifications for a guild."""
        settings = await self.db.get_guild_settings(guild_id)
        if not settings:
            logger.debug(f"No settings for guild {guild_id}")
            return
        if not settings.subscribed_channel_id:
            logger.debug(f"Guild {guild_id} has no subscribed channel")
            return
        if not settings.location:
            logger.debug(f"Guild {guild_id} has no location")
            return

        # Get today's prayer times
        today = datetime.now(ZoneInfo(settings.timezone)).strftime("%Y-%m-%d")
        prayer_times = await self.get_prayer_times(settings, today)

        if not prayer_times:
            logger.debug(f"No prayer times fetched for guild {guild_id}")
            return

        # Check each enabled prayer
        logger.debug(f"Guild {guild_id}: Checking {len(settings.enabled_prayers)} enabled prayers")
        for prayer in settings.enabled_prayers:
            if prayer == Prayer.SUNRISE:
                continue  # Sunrise is informational, not a prayer

            await self._check_and_send_prayer(settings, prayer, prayer_times, today)

    async def _check_and_send_prayer(
        self, settings: GuildSettings, prayer: Prayer, times: PrayerTimes, date: str
    ):
        """Check if prayer time has arrived and send notification."""
        # Check if already sent
        if await self.db.is_prayer_sent(settings.guild_id, prayer.value, date):
            logger.debug(f"Guild {settings.guild_id}: {prayer.value} already sent today")
            return

        # Get prayer time with offset
        prayer_time_str = times.get_time(prayer)
        offset = settings.get_offset(prayer)
        prayer_dt = self._parse_prayer_time(prayer_time_str, date, times.timezone, offset)

        # Check if it's time to send
        now = datetime.now(ZoneInfo(times.timezone))
        time_until = (prayer_dt - now).total_seconds()

        logger.debug(
            f"Guild {settings.guild_id}: {prayer.value} at {prayer_dt.strftime('%H:%M')} "
            f"(in {time_until:.0f}s, now={now.strftime('%H:%M')})"
        )

        # Send if:
        # - Prayer time was within the last 15 minutes (grace period for bot restarts)
        # - OR prayer time is within the next 60 seconds
        GRACE_PERIOD = 15 * 60  # 15 minutes in seconds
        if -GRACE_PERIOD <= time_until <= 60:
            logger.info(f"Sending {prayer.value} notification for guild {settings.guild_id}")
            await self._send_prayer_notification(settings, prayer, prayer_dt)
            await self.db.mark_prayer_sent(settings.guild_id, prayer.value, date)
            await self.db.record_scheduled_prayer(
                settings.guild_id, prayer.value, prayer_dt.strftime("%H:%M"), date
            )
            logger.info(f"Sent {prayer.value} notification for guild {settings.guild_id}")

    def _parse_prayer_time(
        self, time_str: str, date: str, timezone: str, offset_minutes: int
    ) -> datetime:
        """Parse prayer time string and apply offset."""
        dt_str = f"{date} {time_str}"
        dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
        dt = dt.replace(tzinfo=ZoneInfo(timezone))
        dt += timedelta(minutes=offset_minutes)
        return dt

    async def _send_prayer_notification(
        self, settings: GuildSettings, prayer: Prayer, prayer_time: datetime
    ):
        """Send prayer notification to subscribed channel and play Adhan in voice if configured."""
        # Send text notification
        channel = self.bot.get_channel(settings.subscribed_channel_id)
        if not channel:
            logger.warning(
                f"Channel {settings.subscribed_channel_id} not found for guild {settings.guild_id}"
            )
            return

        embed = self._create_prayer_embed(prayer, prayer_time, settings)

        # Build message with role mention if configured
        content = None
        if settings.ping_role_id:
            content = f"<@&{settings.ping_role_id}>"

        try:
            await channel.send(content=content, embed=embed)
            logger.info(f"Sent {prayer.value} notification to guild {settings.guild_id}")
        except discord.Forbidden:
            logger.error(f"Missing permissions to send to channel {settings.subscribed_channel_id}")
        except Exception as e:
            logger.error(f"Failed to send prayer notification: {e}")

        # Play Adhan in voice channel if configured
        if settings.voice_channel_id:
            await self._play_voice_adhan(settings.voice_channel_id, prayer)

    async def _play_voice_adhan(self, voice_channel_id: int, prayer: Prayer):
        """Play Adhan in voice channel using Lavalink."""
        from athan.voice import play_adhan_in_voice_channel

        logger.info(f"Playing Adhan for {prayer.value} prayer")
        success = await play_adhan_in_voice_channel(
            bot=self.bot,
            voice_channel_id=voice_channel_id,
            adhan_file="assets/adhan.mp3"
        )
        
        if success:
            logger.info(f"✅ Adhan playback started for {prayer.value}")
        else:
            logger.error(f"❌ Failed to play Adhan for {prayer.value}")

    def _create_prayer_embed(
        self, prayer: Prayer, prayer_time: datetime, settings: GuildSettings
    ) -> discord.Embed:
        """Create Discord embed for prayer notification."""
        embed = discord.Embed(
            title=f"🕌 {prayer.value} Prayer Time",
            description=f"It is now time for **{prayer.value}** prayer.",
            color=discord.Color.green(),
            timestamp=prayer_time,
        )

        time_str = prayer_time.strftime("%I:%M %p")
        embed.add_field(name="Time", value=time_str, inline=True)

        offset = settings.get_offset(prayer)
        if offset != 0:
            offset_str = f"+{offset}" if offset > 0 else str(offset)
            embed.add_field(name="Offset", value=f"{offset_str} min", inline=True)

        embed.set_footer(text="Athan Bot • May Allah accept your prayers")
        return embed

    async def get_prayer_times(self, settings: GuildSettings, date: str) -> PrayerTimes | None:
        """Get prayer times for a guild's location and date."""
        if not settings.location:
            return None

        try:
            # Pass calculation method and daylight saving from settings
            daylight_saving = getattr(settings.location, 'daylight_saving', False)
            calculation_method = settings.calculation_method if hasattr(settings, 'calculation_method') else None
            
            return await self.muslimsalat_provider.get_prayer_times(
                settings.location, 
                date, 
                settings.timezone,
                daylight_saving=daylight_saving,
                calculation_method=calculation_method
            )
        except Exception as e:
            logger.error(f"Failed to fetch prayer times: {e}")
            return None

    async def get_next_prayer(self, settings: GuildSettings) -> tuple[Prayer, datetime] | None:
        """Get next prayer and its time for a guild."""
        if not settings.location:
            return None

        now = datetime.now(ZoneInfo(settings.timezone))
        today = now.strftime("%Y-%m-%d")
        tomorrow = (now + timedelta(days=1)).strftime("%Y-%m-%d")

        # Try today first
        times = await self.get_prayer_times(settings, today)
        if times:
            next_prayer = self._find_next_prayer(now, times, settings)
            if next_prayer:
                return next_prayer

        # Try tomorrow
        times = await self.get_prayer_times(settings, tomorrow)
        if times:
            return self._find_next_prayer(now, times, settings)

        return None

    def _find_next_prayer(
        self, now: datetime, times: PrayerTimes, settings: GuildSettings
    ) -> tuple[Prayer, datetime] | None:
        """Find next prayer from prayer times."""
        for prayer in settings.enabled_prayers:
            if prayer == Prayer.SUNRISE:
                continue

            time_str = times.get_time(prayer)
            offset = settings.get_offset(prayer)
            prayer_dt = self._parse_prayer_time(time_str, times.date, times.timezone, offset)

            if prayer_dt > now:
                return prayer, prayer_dt

        return None
