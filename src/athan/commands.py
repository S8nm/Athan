"""Discord slash command handlers."""

import asyncio
import contextlib
import logging
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import discord
from discord import app_commands
from discord.app_commands import Transform, Transformer

from athan.config import (
    GuildSettings,
    Location,
    LocationType,
    Prayer,
)
from athan.db import Database
from athan.scheduler import PrayerScheduler

logger = logging.getLogger(__name__)


class VoiceChannelTransformer(Transformer):
    """Custom transformer for voice channels that handles complex names."""

    @property
    def type(self) -> discord.AppCommandOptionType:
        """Return the option type for Discord."""
        return discord.AppCommandOptionType.channel

    @property
    def channel_types(self) -> list[discord.ChannelType]:
        """Specify which channel types to show in dropdown."""
        return [discord.ChannelType.voice, discord.ChannelType.stage_voice]

    async def transform(
        self, interaction: discord.Interaction, value: discord.abc.GuildChannel
    ) -> discord.VoiceChannel:
        """Transform channel to VoiceChannel object."""
        # Since we specify channel_types, Discord only shows voice channels
        # So we can trust that 'value' is already a voice channel
        # Just return it directly without isinstance check
        return value


class AthanCommands:
    """Slash command handlers for Athan bot."""

    def __init__(self, bot: discord.Client, db: Database, scheduler: PrayerScheduler):
        self.bot = bot
        self.db = db
        self.scheduler = scheduler
        self.tree = app_commands.CommandTree(bot)
        self._register_commands()

    async def _get_timezone_from_api(
        self, city: str, country: str | None
    ) -> str | None:
        """
        Fetch timezone from prayer times API.
        This ensures we get the correct timezone for ANY city the API supports.
        """
        try:
            from .time_providers.muslimsalat import MuslimSalatProvider

            # Create a temporary provider instance
            provider = MuslimSalatProvider(
                api_key=self.bot.settings.muslimsalat_api_key
            )

            # Create a temporary location
            location = Location(
                location_type=LocationType.CITY, city=city, country=country or ""
            )

            # Fetch prayer times (this also fetches timezone)
            from datetime import date

            prayer_times = await provider.get_prayer_times(location, date.today())

            if prayer_times and prayer_times.timezone:
                logger.info(
                    f"Fetched timezone {prayer_times.timezone} for {city} from API"
                )
                return prayer_times.timezone

        except Exception as e:
            logger.warning(f"Could not fetch timezone from API for {city}: {e}")

        return None

    def _get_timezone_for_location(
        self, city: str, country: str | None, daylight_saving: bool
    ) -> str:
        """Determine timezone based on location and daylight saving preference."""
        city_lower = city.lower()
        country_lower = (country or "").lower()

        # Major city timezone mappings
        city_timezones = {
            # UK & Ireland
            "london": "Europe/London",
            "manchester": "Europe/London",
            "birmingham": "Europe/London",
            "dublin": "Europe/Dublin",
            # Middle East (Qatar)
            "doha": "Asia/Qatar",
            "qatar": "Asia/Qatar",
            # UAE
            "dubai": "Asia/Dubai",
            "abu dhabi": "Asia/Dubai",
            # Saudi Arabia
            "riyadh": "Asia/Riyadh",
            "jeddah": "Asia/Riyadh",
            "makkah": "Asia/Riyadh",
            "mecca": "Asia/Riyadh",
            "medina": "Asia/Riyadh",
            # USA
            "new york": "America/New_York",
            "los angeles": "America/Los_Angeles",
            "chicago": "America/Chicago",
            # Canada
            "toronto": "America/Toronto",
            "vancouver": "America/Vancouver",
            # Europe
            "paris": "Europe/Paris",
            "berlin": "Europe/Berlin",
            "rome": "Europe/Rome",
            "madrid": "Europe/Madrid",
        }

        # Try to find timezone by city name
        timezone = city_timezones.get(city_lower)

        # If not found, try by country
        if not timezone and country_lower:
            country_timezones = {
                "uk": "Europe/London",
                "united kingdom": "Europe/London",
                "england": "Europe/London",
                "qatar": "Asia/Qatar",
                "uae": "Asia/Dubai",
                "saudi arabia": "Asia/Riyadh",
                "usa": "America/New_York",
                "canada": "America/Toronto",
            }
            timezone = country_timezones.get(country_lower)

        # Fallback to UTC if we can't determine
        return timezone or "UTC"

    def _register_commands(self):
        """Register all slash commands."""

        @self.tree.command(name="setup", description="Configure bot for your server")
        @app_commands.describe(
            city="City name (e.g., Doha, Dubai, London)",
            country="Country name (optional, helps with accuracy)",
            daylight_saving="Whether your location observes daylight saving time",
        )
        async def setup_command(
            interaction: discord.Interaction,
            city: str,
            country: str | None = None,
            daylight_saving: bool = False,
        ):
            await self._setup(interaction, city, country, daylight_saving)

        @self.tree.command(name="set_method", description="Set prayer calculation method")
        @app_commands.describe(
            method="Method: 1=Egypt, 2=Karachi(Shafi), 3=Karachi(Hanafi), "
            "4=ISNA, 5=MWL, 6=Umm Al-Qura, 7=Fixed Isha"
        )
        @app_commands.choices(
            method=[
                app_commands.Choice(name="1 - Egyptian General Authority of Survey", value=1),
                app_commands.Choice(
                    name="2 - University Of Islamic Sciences, Karachi (Shafi)", value=2
                ),
                app_commands.Choice(
                    name="3 - University Of Islamic Sciences, Karachi (Hanafi)", value=3
                ),
                app_commands.Choice(name="4 - Islamic Circle of North America", value=4),
                app_commands.Choice(name="5 - Muslim World League", value=5),
                app_commands.Choice(name="6 - Umm Al-Qura", value=6),
                app_commands.Choice(name="7 - Fixed Isha", value=7),
            ]
        )
        async def set_method_command(interaction: discord.Interaction, method: int):
            await self._set_method(interaction, method)

        @self.tree.command(name="set_offset", description="Set time offset for a specific prayer")
        @app_commands.describe(
            prayer="Prayer name", offset="Offset in minutes (positive or negative)"
        )
        async def set_offset_command(interaction: discord.Interaction, prayer: str, offset: int):
            await self._set_offset(interaction, prayer, offset)

        @self.tree.command(
            name="subscribe",
            description="Enable prayer notifications in this channel",
        )
        @app_commands.describe(
            ping_role="Role to mention when prayer time arrives "
            "(optional, creates @athan if not specified)",
        )
        async def subscribe_command(
            interaction: discord.Interaction,
            ping_role: discord.Role | None = None,
        ):
            await self._subscribe(interaction, ping_role)

        @self.tree.command(
            name="subscribe_vc",
            description="Enable voice Adhan in a voice channel",
        )
        @app_commands.describe(
            voice_channel="Voice channel where bot will play Adhan",
        )
        async def subscribe_vc_command(
            interaction: discord.Interaction,
            voice_channel: Transform[discord.VoiceChannel, VoiceChannelTransformer],
        ):
            await self._subscribe_vc(interaction, voice_channel)

        @self.tree.command(name="unsubscribe", description="Unsubscribe from prayer notifications")
        async def unsubscribe_command(interaction: discord.Interaction):
            await self._unsubscribe(interaction)

        @self.tree.command(name="next_prayer", description="Get next prayer time and countdown")
        async def next_prayer_command(interaction: discord.Interaction):
            await self._next_prayer(interaction)

        @self.tree.command(name="today", description="Show all prayer times for today")
        async def today_command(interaction: discord.Interaction):
            await self._today(interaction)

        @self.tree.command(name="test", description="Test prayer notification")
        async def test_command(interaction: discord.Interaction):
            await self._test(interaction)

        @self.tree.command(name="adhan_voice", description="Play Adhan in voice channel")
        @app_commands.describe(voice_channel="Voice channel to join")
        async def adhan_voice_command(
            interaction: discord.Interaction,
            voice_channel: Transform[discord.VoiceChannel, VoiceChannelTransformer],
        ):
            await self._adhan_voice(interaction, voice_channel)

        @self.tree.command(name="status", description="Bot status and health check")
        async def status_command(interaction: discord.Interaction):
            await self._status(interaction)

    async def _setup(
        self,
        interaction: discord.Interaction,
        city: str,
        country: str | None,
        daylight_saving: bool,
    ):
        """Handle /setup command."""
        # Check if command is used in a guild (not DMs)
        if not interaction.guild_id:
            await interaction.response.send_message(
                "❌ This command can only be used in a server, not in DMs.",
                ephemeral=True
            )
            return
        
        try:
            await interaction.response.defer(ephemeral=False)

            # Create location object
            location = Location(
                location_type=LocationType.CITY,
                city=city,
                country=country or "",
                daylight_saving=daylight_saving,
            )

            # Fetch prayer times from API to get the correct timezone
            # The API knows the timezone for ANY city in the world!
            timezone = await self._get_timezone_from_api(city, country)
            if not timezone:
                # Fallback to basic detection if API fails
                timezone = self._get_timezone_for_location(city, country, daylight_saving)

            # Create guild settings
            settings = GuildSettings(
                guild_id=interaction.guild_id,
                location=location,
                timezone=timezone,
            )

            await self.db.save_guild_settings(settings)

            location_str = f"{city}, {country}" if country else city

            embed = discord.Embed(
                title="✅ Setup Complete!",
                description=f"Prayer times configured for **{location_str}**",
                color=discord.Color.green(),
            )

            embed.add_field(
                name="⚙️ Settings",
                value=f"📍 Location: {location_str}\n"
                f"🕐 Timezone: {timezone}\n"
                f"☀️ Daylight Saving: {'Yes' if daylight_saving else 'No'}",
                inline=False,
            )

            embed.add_field(
                name="📋 Next Steps",
                value="1️⃣ `/subscribe` - Enable notifications in this channel\n"
                "2️⃣ `/subscribe_vc` - Add voice Adhan (optional)\n"
                "3️⃣ `/next_prayer` - Check next prayer time",
                inline=False,
            )

            embed.set_footer(
                text="Use /set_method to change calculation method • /set_offset to adjust times"
            )

            await interaction.followup.send(embed=embed)
            logger.info(f"Setup completed for guild {interaction.guild_id}: {location_str}")

        except discord.errors.NotFound:
            logger.warning(f"Interaction expired for /setup in guild {interaction.guild_id}")
        except Exception as e:
            logger.error(f"Error in /setup: {e}", exc_info=True)
            with contextlib.suppress(discord.errors.NotFound, discord.errors.HTTPException):
                await interaction.followup.send(
                    f"❌ Setup failed: {str(e)}\nPlease try again.", ephemeral=True
                )

    async def _set_method(self, interaction: discord.Interaction, method: int):
        """Handle /set_method command."""
        # Defer immediately to avoid timeout
        await interaction.response.defer(ephemeral=False)

        settings = await self.db.get_guild_settings(interaction.guild_id)
        if not settings:
            await interaction.followup.send("⚠️ Please run `/setup` first.", ephemeral=True)
            return

        # Map method number to name
        method_map = {
            1: ("Egypt", "Egyptian General Authority of Survey"),
            2: ("Karachi", "University Of Islamic Sciences, Karachi (Shafi)"),
            3: ("Karachi", "University Of Islamic Sciences, Karachi (Hanafi)"),
            4: ("ISNA", "Islamic Circle of North America"),
            5: ("MWL", "Muslim World League"),
            6: ("Makkah", "Umm Al-Qura"),
            7: ("MWL", "Fixed Isha"),
        }

        if method not in method_map:
            await interaction.followup.send("❌ Invalid method number. Use 1-7.", ephemeral=True)
            return

        method_code, method_name = method_map[method]

        # Update calculation method
        settings.calculation_method = str(method)
        await self.db.save_guild_settings(settings)

        embed = discord.Embed(
            title="✅ Calculation Method Updated",
            description=f"**{method_name}**",
            color=discord.Color.green(),
        )
        embed.add_field(
            name="Method Code",
            value=f"#{method}",
            inline=True,
        )
        embed.set_footer(
            text="Prayer times will be updated at the next scheduled notification"
        )

        await interaction.followup.send(embed=embed)
        logger.info(f"Guild {interaction.guild_id} set method to {method} ({method_name})")

    async def _set_offset(self, interaction: discord.Interaction, prayer: str, offset: int):
        """Handle /set_offset command."""
        # Defer immediately to avoid timeout
        await interaction.response.defer(ephemeral=False)

        settings = await self.db.get_guild_settings(interaction.guild_id)
        if not settings:
            await interaction.followup.send("Please run `/setup` first.", ephemeral=True)
            return

        try:
            prayer_enum = Prayer(prayer.capitalize())
        except ValueError:
            await interaction.followup.send(
                f"Invalid prayer. Choose from: {', '.join(p.value for p in Prayer)}",
                ephemeral=True,
            )
            return

        settings.prayer_offsets[prayer_enum.value] = offset
        await self.db.save_guild_settings(settings)

        offset_str = f"+{offset}" if offset > 0 else str(offset)
        await interaction.followup.send(
            f"✅ {prayer_enum.value} offset set to: {offset_str} minutes"
        )

    async def _subscribe(
        self,
        interaction: discord.Interaction,
        ping_role: discord.Role | None,
    ):
        """Handle /subscribe command - subscribes current channel."""
        # Defer FIRST before any operations
        try:
            await interaction.response.defer(ephemeral=False)
        except discord.errors.NotFound:
            logger.error(
                f"Interaction expired before defer in /subscribe for guild {interaction.guild_id}"
            )
            return

        try:
            settings = await self.db.get_guild_settings(interaction.guild_id)
            if not settings:
                await interaction.followup.send(
                    "⚠️ Please run `/setup` first to configure your location.", ephemeral=True
                )
                return

            # Use current channel (guaranteed to be a text channel in Discord)
            target_text = interaction.channel

            if not isinstance(target_text, discord.TextChannel):
                await interaction.followup.send(
                    "❌ This command must be used in a text channel.",
                    ephemeral=True,
                )
                return

            # Handle role - find or create "athan" role if not specified
            if not ping_role:
                ping_role = discord.utils.get(interaction.guild.roles, name="athan")
                if not ping_role:
                    try:
                        ping_role = await interaction.guild.create_role(
                            name="athan",
                            mentionable=True,
                            reason="Auto-created for prayer time notifications",
                        )
                        logger.info(f"Created 'athan' role in guild {interaction.guild_id}")
                    except discord.Forbidden:
                        logger.warning(
                            f"Cannot create role in guild {interaction.guild_id} "
                            f"- missing permissions"
                        )
                    except Exception as e:
                        logger.error(f"Failed to create role: {e}")

            # Save settings
            settings.subscribed_channel_id = target_text.id
            settings.ping_role_id = ping_role.id if ping_role else None
            await self.db.save_guild_settings(settings)

            # Start scheduler for this guild
            await self.scheduler.schedule_guild(interaction.guild_id)

            # Build success message
            embed = discord.Embed(
                title="✅ Subscribed!",
                description=f"Prayer notifications enabled in {target_text.mention}",
                color=discord.Color.green(),
            )

            if ping_role:
                embed.add_field(
                    name="🔔 Role",
                    value=f"{ping_role.mention} will be pinged at each prayer time",
                    inline=False,
                )

            if settings.voice_channel_id:
                voice_ch = interaction.guild.get_channel(settings.voice_channel_id)
                if voice_ch:
                    embed.add_field(
                        name="🔊 Voice Adhan",
                        value=f"Enabled in {voice_ch.mention}",
                        inline=False,
                    )
            else:
                embed.add_field(
                    name="💡 Tip",
                    value="Use `/subscribe_vc` to enable voice Adhan in a voice channel",
                    inline=False,
                )

            embed.add_field(
                name="⏰ Next Prayer",
                value="Use `/next_prayer` or `/today` to see prayer times",
                inline=False,
            )

            embed.set_footer(text="Auto notifications active! • Use /unsubscribe to stop")

            await interaction.followup.send(embed=embed)
            logger.info(
                f"Guild {interaction.guild_id} subscribed - Channel: {target_text.id}, "
                f"Role: {ping_role.id if ping_role else 'None'}"
            )

        except discord.errors.NotFound:
            logger.error(f"Interaction expired during /subscribe for guild {interaction.guild_id}")
        except Exception as e:
            logger.error(f"Error in /subscribe: {e}", exc_info=True)
            with contextlib.suppress(discord.errors.NotFound, discord.errors.HTTPException):
                await interaction.followup.send(
                    f"❌ Subscription failed: {str(e)}\nPlease try again.", ephemeral=True
                )

    async def _subscribe_vc(
        self,
        interaction: discord.Interaction,
        voice_channel: discord.VoiceChannel,
    ):
        """Handle /subscribe_vc command - adds voice channel for Adhan."""
        try:
            await interaction.response.defer(ephemeral=False)
        except discord.errors.NotFound:
            logger.error(f"Interaction expired for /subscribe_vc in guild {interaction.guild_id}")
            return

        settings = await self.db.get_guild_settings(interaction.guild_id)
        if not settings:
            await interaction.followup.send(
                "⚠️ Please run `/setup` first to configure your location.", ephemeral=True
            )
            return

        if not settings.subscribed_channel_id:
            await interaction.followup.send(
                "⚠️ Please run `/subscribe` first to enable notifications.", ephemeral=True
            )
            return

        # Save voice channel
        settings.voice_channel_id = voice_channel.id
        await self.db.save_guild_settings(settings)

        embed = discord.Embed(
            title="✅ Voice Adhan Enabled!",
            description=f"Bot will join {voice_channel.mention} "
            f"and play Adhan at each prayer time.",
            color=discord.Color.green(),
        )

        embed.set_footer(
            text="The bot needs 'Connect' and 'Speak' permissions in the voice channel"
        )

        await interaction.followup.send(embed=embed)
        logger.info(f"Guild {interaction.guild_id} voice channel set to {voice_channel.id}")

    async def _unsubscribe(self, interaction: discord.Interaction):
        """Handle /unsubscribe command."""
        # Defer immediately to avoid timeout
        await interaction.response.defer(ephemeral=False)

        settings = await self.db.get_guild_settings(interaction.guild_id)
        if not settings or not settings.subscribed_channel_id:
            await interaction.followup.send(
                "This server is not subscribed to notifications.", ephemeral=True
            )
            return

        settings.subscribed_channel_id = None
        await self.db.save_guild_settings(settings)

        # Stop scheduler for this guild
        await self.scheduler.unschedule_guild(interaction.guild_id)

        await interaction.followup.send("✅ Unsubscribed from prayer notifications.")
        logger.info(f"Guild {interaction.guild_id} unsubscribed")

    async def _today(self, interaction: discord.Interaction):
        """Handle /today command - show all prayer times for today."""
        try:
            await interaction.response.defer(ephemeral=False)
        except discord.errors.NotFound:
            logger.error(f"Failed to defer /today in guild {interaction.guild_id}")
            return

        try:
            settings = await self.db.get_guild_settings(interaction.guild_id)
            if not settings or not settings.location:
                await interaction.followup.send(
                    "⚠️ Please run `/setup` first to configure your location.",
                    ephemeral=True,
                )
                return

            # Get today's date
            today = datetime.now(ZoneInfo(settings.timezone))
            date_str = today.strftime("%Y-%m-%d")

            # Fetch prayer times using the provider
            from athan.time_providers.muslimsalat import MuslimSalatProvider

            provider = MuslimSalatProvider()
            try:
                prayer_times = await asyncio.wait_for(
                    provider.get_prayer_times(settings.location, date_str, settings.timezone),
                    timeout=10.0,
                )
            except TimeoutError:
                await interaction.followup.send(
                    "⏱️ Request timed out fetching prayer times. Please try again.",
                    ephemeral=True,
                )
                return
            finally:
                await provider.close()

            if not prayer_times:
                await interaction.followup.send(
                    "❌ Could not fetch prayer times. Please try again.", ephemeral=True
                )
                return

            # Build embed with all prayer times
            current_time = today.strftime("%I:%M %p")
            embed = discord.Embed(
                title="🕌 Prayer Times for Today",
                description=f"{today.strftime('%A, %B %d, %Y')}\n🕐 Current Time: **{current_time}**",
                color=discord.Color.green(),
            )

            # Add each prayer time
            for prayer in [Prayer.FAJR, Prayer.DHUHR, Prayer.ASR, Prayer.MAGHRIB, Prayer.ISHA]:
                prayer_time_str = prayer_times.get_time(prayer)
                if prayer_time_str:
                    # Parse time string to datetime
                    dt_str = f"{date_str} {prayer_time_str}"
                    prayer_dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
                    prayer_dt = prayer_dt.replace(tzinfo=ZoneInfo(settings.timezone))

                    # Apply offset
                    offset = settings.get_offset(prayer)
                    if offset != 0:
                        prayer_dt = prayer_dt + timedelta(minutes=offset)
                        offset_str = f" ({offset:+d}m)"
                    else:
                        offset_str = ""

                    # Check if prayer has passed
                    status = "✅" if prayer_dt < today else "⏳"

                    embed.add_field(
                        name=f"{status} {prayer.value}",
                        value=f"{prayer_dt.strftime('%I:%M %p')}{offset_str}",
                        inline=True,
                    )

            # Add sunrise
            if prayer_times.sunrise:
                # Parse sunrise string to datetime
                sunrise_str = prayer_times.sunrise
                dt_str = f"{date_str} {sunrise_str}"
                sunrise_dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
                sunrise_dt = sunrise_dt.replace(tzinfo=ZoneInfo(settings.timezone))

                embed.add_field(
                    name="🌅 Sunrise",
                    value=sunrise_dt.strftime("%I:%M %p"),
                    inline=True,
                )

            location_str = settings.location.city or settings.location.country or "Unknown"
            embed.set_footer(
                text=f"Location: {location_str} • Use /subscribe for auto notifications"
            )

            await interaction.followup.send(embed=embed)
            logger.info(f"Sent today's prayer times for guild {interaction.guild_id}")

        except Exception as e:
            logger.error(f"Error in /today: {e}", exc_info=True)
            with contextlib.suppress(discord.errors.NotFound, discord.errors.HTTPException):
                await interaction.followup.send(f"❌ An error occurred: {str(e)}", ephemeral=True)

    async def _next_prayer(self, interaction: discord.Interaction):
        """Handle /next_prayer command."""
        # Defer immediately to acknowledge the interaction
        try:
            await interaction.response.defer(ephemeral=False)
        except discord.errors.NotFound:
            logger.error(
                f"Failed to defer /next_prayer in guild {interaction.guild_id}. "
                "Interaction may have already been acknowledged or expired."
            )
            return

        try:
            settings = await self.db.get_guild_settings(interaction.guild_id)
            if not settings or not settings.location:
                await interaction.followup.send(
                    "⚠️ Please run `/setup` first to configure your location.\n"
                    "Example: `/setup city:london`",
                    ephemeral=True,
                )
                return

            # Use asyncio.wait_for to add timeout protection
            try:
                result = await asyncio.wait_for(
                    self.scheduler.get_next_prayer(settings), timeout=10.0
                )
            except TimeoutError:
                await interaction.followup.send(
                    "⏱️ Request timed out fetching prayer times. The API might be slow.\n"
                    "Please try again in a moment.",
                    ephemeral=True,
                )
                return

            if not result:
                await interaction.followup.send(
                    "❌ Could not fetch prayer times. Please check:\n"
                    "• Your location is set correctly (`/setup`)\n"
                    "• The API is accessible\n"
                    "Try again in a moment.",
                    ephemeral=True,
                )
                return

            prayer, prayer_time = result
            now = datetime.now(ZoneInfo(settings.timezone))
            time_until = prayer_time - now

            hours = int(time_until.total_seconds() // 3600)
            minutes = int((time_until.total_seconds() % 3600) // 60)

            embed = discord.Embed(
                title=f"🕌 Next Prayer: {prayer.value}",
                color=discord.Color.blue(),
            )
            embed.add_field(name="Time", value=prayer_time.strftime("%I:%M %p"), inline=True)
            embed.add_field(
                name="In",
                value=f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m",
                inline=True,
            )

            offset = settings.get_offset(prayer)
            if offset != 0:
                offset_str = f"+{offset}" if offset > 0 else str(offset)
                embed.add_field(name="Offset", value=f"{offset_str} min", inline=True)

            await interaction.followup.send(embed=embed)
            logger.info(f"Sent next prayer info for guild {interaction.guild_id}")

        except discord.errors.NotFound:
            # Followup failed because interaction expired (took > 15 min, very rare)
            logger.error(
                f"Interaction expired while sending followup for /next_prayer "
                f"in guild {interaction.guild_id}. Operation took longer than 15 minutes."
            )
        except Exception as e:
            logger.error(f"Error in /next_prayer: {e}", exc_info=True)
            with contextlib.suppress(discord.errors.NotFound, discord.errors.HTTPException):
                await interaction.followup.send(f"❌ An error occurred: {str(e)}", ephemeral=True)

    async def _test(self, interaction: discord.Interaction):
        """Handle /test command - plays Adhan in voice if configured."""
        logger.info(f"[TEST] Command invoked for guild {interaction.guild_id}")
        
        settings = await self.db.get_guild_settings(interaction.guild_id)
        if not settings:
            logger.error("[TEST] No settings found - setup required")
            try:
                await interaction.response.send_message("Please run `/setup` first.", ephemeral=True)
            except:
                pass
            return

        # Try to defer, but don't fail if it doesn't work
        try:
            await interaction.response.defer(ephemeral=False)
            logger.info("[TEST] Deferred interaction successfully")
        except Exception as e:
            logger.warning(f"[TEST] Could not defer interaction: {e} - continuing anyway")

        # Build test notification embed
        embed = discord.Embed(
            title="🧪 Test Prayer Notification",
            description="Testing Athan bot notifications!",
            color=discord.Color.gold(),
        )
        embed.add_field(name="Location", value=f"{settings.location.city or 'Unknown'}", inline=True)

        # Show voice status
        if settings.voice_channel_id:
            voice_ch = self.bot.get_channel(settings.voice_channel_id)
            if voice_ch:
                embed.add_field(
                    name="Voice Adhan", value=f"🔊 Playing in {voice_ch.mention}", inline=True
                )
            logger.info(f"[TEST] Voice channel configured: {settings.voice_channel_id}")
        else:
            logger.info("[TEST] No voice channel configured")

        embed.set_footer(text="Test Mode • This is a test notification")

        # Try to send text notification (optional - voice will still play if this fails)
        try:
            await interaction.followup.send(embed=embed)
            logger.info("[TEST] Text notification sent successfully")
        except Exception as e:
            logger.warning(f"[TEST] Could not send text notification: {e} - voice will still play")

        # ALWAYS play Adhan in voice if configured, regardless of text message status
        if settings.voice_channel_id:
            logger.info(f"[TEST] Starting voice playback for channel {settings.voice_channel_id}")
            await self._play_test_adhan(settings.voice_channel_id)
        else:
            logger.info("[TEST] No voice channel configured - test complete")

    async def _play_test_adhan(self, voice_channel_id: int):
        """Play Adhan in voice channel for test using Lavalink."""
        from athan.voice import play_adhan_in_voice_channel
        
        logger.info(f"[TEST] Playing test Adhan in channel {voice_channel_id}")
        
        success = await play_adhan_in_voice_channel(
            bot=self.bot,
            voice_channel_id=voice_channel_id,
            adhan_file="assets/adhan.mp3"
        )
        
        if success:
            logger.info("[TEST] ✅ Test Adhan playback started successfully")
        else:
            logger.error("[TEST] ❌ Failed to play test Adhan")

    async def _adhan_voice(
        self,
        interaction: discord.Interaction,
        voice_channel: discord.VoiceChannel | None,
    ):
        """Handle /adhan_voice command using Lavalink."""
        from athan.voice import play_adhan_in_voice_channel
        
        # Defer immediately to avoid timeout
        await interaction.response.defer(ephemeral=False)

        # Determine voice channel
        if voice_channel is None:
            if interaction.user.voice and interaction.user.voice.channel:
                voice_channel = interaction.user.voice.channel
            else:
                await interaction.followup.send(
                    "You must be in a voice channel or specify one.", ephemeral=True
                )
                return

        # Check for adhan file
        adhan_path = Path("assets/adhan.mp3")
        if not adhan_path.exists():
            await interaction.followup.send(
                "⚠️ Adhan audio file not found. Please add `assets/adhan.mp3`.",
                ephemeral=True,
            )
            return

        # Play Adhan using Lavalink
        success = await play_adhan_in_voice_channel(
            bot=self.bot,
            voice_channel_id=voice_channel.id,
            adhan_file=adhan_path
        )
        
        if success:
            await interaction.followup.send(f"🔊 Playing Adhan in {voice_channel.mention}")
            logger.info(f"Played Adhan in guild {interaction.guild_id}")
        else:
            await interaction.followup.send(
                "❌ Failed to play Adhan. Make sure Lavalink server is running.",
                ephemeral=True
            )

    async def _status(self, interaction: discord.Interaction):
        """Handle /status command."""
        # Defer immediately to avoid timeout
        await interaction.response.defer(ephemeral=False)

        guilds_count = len(self.bot.guilds)
        subscribed_count = len(await self.db.get_all_subscribed_guilds())

        embed = discord.Embed(
            title="🤖 Athan Bot Status",
            color=discord.Color.green(),
        )
        embed.add_field(name="Guilds", value=str(guilds_count), inline=True)
        embed.add_field(name="Subscribed Guilds", value=str(subscribed_count), inline=True)
        embed.add_field(name="Latency", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        embed.set_footer(text="Bot Version • v0.1.0")

        await interaction.followup.send(embed=embed)
