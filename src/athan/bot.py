"""Main bot entry point with event handlers."""

import logging
import sys

import discord
from discord import Intents

from athan.commands import AthanCommands
from athan.config import BotSettings, ensure_data_directory
from athan.db import Database
from athan.scheduler import PrayerScheduler

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


class AthanBot(discord.Client):
    """Athan Discord bot client."""

    def __init__(self, settings: BotSettings):
        # Set required intents
        intents = Intents.default()
        intents.message_content = False  # Not needed for slash commands
        intents.guilds = True
        intents.voice_states = True  # Required for voice channel access

        super().__init__(intents=intents)

        self.settings = settings
        self.db: Database = None
        self.scheduler: PrayerScheduler = None
        self.commands: AthanCommands = None

    async def setup_hook(self):
        """Initialize bot components and sync commands."""
        logger.info("Setting up bot components...")

        # Initialize database
        ensure_data_directory()
        self.db = Database(self.settings.database_path)
        await self.db.connect()

        # Initialize scheduler
        self.scheduler = PrayerScheduler(self, self.db, self.settings)

        # Initialize commands
        self.commands = AthanCommands(self, self.db, self.scheduler)

        # Sync slash commands globally
        try:
            synced = await self.commands.tree.sync()
            logger.info(f"Synced {len(synced)} command(s)")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")

        logger.info("Bot setup complete")

    async def on_ready(self):
        """Handle bot ready event."""
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        logger.info(f"Connected to {len(self.guilds)} guild(s)")

        # Set activity status
        await self.change_presence(
            activity=discord.Activity(type=discord.ActivityType.watching, name="prayer times 🕌")
        )

        # Start scheduler
        await self.scheduler.start()
        logger.info("Scheduler started")

    async def on_guild_join(self, guild: discord.Guild):
        """Handle bot joining a new guild."""
        logger.info(f"Joined guild: {guild.name} (ID: {guild.id})")

    async def on_guild_remove(self, guild: discord.Guild):
        """Handle bot leaving a guild."""
        logger.info(f"Left guild: {guild.name} (ID: {guild.id})")

        # Clean up scheduler for this guild
        await self.scheduler.unschedule_guild(guild.id)

    async def close(self):
        """Clean up resources on shutdown."""
        logger.info("Shutting down bot...")

        if self.scheduler:
            await self.scheduler.stop()

        if self.db:
            await self.db.close()

        await super().close()
        logger.info("Bot shutdown complete")


def main():
    """Main entry point."""
    try:
        # Load settings from environment
        settings = BotSettings()

        # Validate token
        if not settings.discord_token or settings.discord_token == "your_bot_token_here":
            logger.error("DISCORD_TOKEN not set or invalid in environment")
            logger.error("Please set DISCORD_TOKEN in .env file or environment variables")
            sys.exit(1)

        # Create and run bot
        bot = AthanBot(settings)
        bot.run(settings.discord_token, log_handler=None)  # We handle logging ourselves

    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
