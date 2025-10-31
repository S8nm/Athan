"""Voice playback using Lavalink/Wavelink."""

import logging
from pathlib import Path

import discord
import wavelink

logger = logging.getLogger(__name__)


async def play_adhan_in_voice_channel(
    bot: discord.Client,
    voice_channel_id: int,
    adhan_file: str | Path = "assets/adhan.mp3",
) -> bool:
    """
    Play Adhan audio file in a voice channel using Lavalink.

    Args:
        bot: Discord bot client
        voice_channel_id: ID of the voice channel to play in
        adhan_file: Path to the adhan audio file

    Returns:
        True if playback started successfully, False otherwise
    """
    try:
        # Get voice channel
        voice_channel = bot.get_channel(voice_channel_id)
        if not voice_channel or not isinstance(
            voice_channel, (discord.VoiceChannel, discord.StageChannel)
        ):
            logger.error(f"Voice channel {voice_channel_id} not found or invalid")
            return False

        # Check if adhan file exists
        adhan_path = Path(adhan_file)
        if not adhan_path.exists():
            logger.error(f"Adhan file not found: {adhan_path}")
            return False

        # Get or create player for the guild
        guild = voice_channel.guild
        player: wavelink.Player | None = guild.voice_client

        if not player:
            # Connect to voice channel
            logger.info(f"Connecting to voice channel {voice_channel_id}")
            player: wavelink.Player = await voice_channel.connect(cls=wavelink.Player)
        elif player.channel.id != voice_channel_id:
            # Move to different channel if needed
            logger.info(f"Moving to voice channel {voice_channel_id}")
            await player.move_to(voice_channel)

        # Load and play the audio file
        logger.info(f"Playing adhan from {adhan_path}")
        
        # Wavelink requires a search query, we'll use the local file path
        # Convert to absolute path for Lavalink to access
        abs_path = adhan_path.absolute()
        
        # Play the track
        track = await wavelink.Playable.search(f"local:{abs_path}")
        if not track:
            logger.error(f"Could not load track from {abs_path}")
            return False

        await player.play(track[0] if isinstance(track, list) else track)
        logger.info("Adhan playback started successfully")

        # Disconnect after playback finishes
        # Note: Wavelink will handle auto-disconnect, but we can also do it manually
        # We'll let it auto-disconnect after track ends

        return True

    except wavelink.LavalinkException as e:
        logger.error(f"Lavalink error during playback: {e}")
        return False
    except discord.errors.ClientException as e:
        logger.error(f"Discord error during voice connection: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during adhan playback: {e}", exc_info=True)
        return False


async def stop_adhan_playback(guild_id: int, bot: discord.Client) -> bool:
    """
    Stop adhan playback and disconnect from voice channel.

    Args:
        guild_id: Guild ID where playback should be stopped
        bot: Discord bot client

    Returns:
        True if stopped successfully, False otherwise
    """
    try:
        guild = bot.get_guild(guild_id)
        if not guild:
            logger.warning(f"Guild {guild_id} not found")
            return False

        player: wavelink.Player | None = guild.voice_client
        if not player:
            logger.debug(f"No active player in guild {guild_id}")
            return False

        logger.info(f"Stopping adhan playback in guild {guild_id}")
        await player.disconnect()
        return True

    except Exception as e:
        logger.error(f"Error stopping adhan playback: {e}")
        return False

