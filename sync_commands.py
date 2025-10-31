"""Force sync Discord slash commands (use when commands don't update)."""
import asyncio
import logging

import discord
from discord.ext import commands

from athan.config import BotSettings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Sync commands with Discord."""
    settings = BotSettings()
    
    intents = discord.Intents.default()
    intents.guilds = True
    
    bot = commands.Bot(command_prefix="!", intents=intents)
    
    @bot.event
    async def on_ready():
        """Sync commands when bot is ready."""
        logger.info(f"Logged in as {bot.user}")
        logger.info("Syncing commands...")
        
        try:
            # Sync globally (takes up to 1 hour to propagate)
            synced = await bot.tree.sync()
            logger.info(f"✅ Synced {len(synced)} global commands")
            
            # Also sync to each guild for immediate update
            for guild in bot.guilds:
                synced_guild = await bot.tree.sync(guild=discord.Object(id=guild.id))
                logger.info(f"✅ Synced {len(synced_guild)} commands to {guild.name}")
            
            logger.info("✅ Command sync complete!")
            logger.info("")
            logger.info("Commands should now update in Discord.")
            logger.info("If they still don't appear, wait 5 minutes or kick/re-invite bot.")
            
        except Exception as e:
            logger.error(f"❌ Failed to sync commands: {e}", exc_info=True)
        finally:
            await bot.close()
    
    await bot.start(settings.discord_token)


if __name__ == "__main__":
    asyncio.run(main())

