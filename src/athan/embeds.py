"""Embed creation utilities for consistent message formatting."""

from datetime import datetime

import discord

from athan.config import GuildSettings, Prayer
from athan.utils import format_prayer_offset, humanize_time_delta


def create_prayer_notification_embed(
    prayer: Prayer, prayer_time: datetime, settings: GuildSettings
) -> discord.Embed:
    """Create a beautiful embed for prayer notifications."""
    embed = discord.Embed(
        title=f"🕌 {prayer.value} Prayer Time",
        description=f"It is now time for {prayer.value} prayer.",
        color=discord.Color.green(),
    )

    embed.add_field(
        name="Time",
        value=prayer_time.strftime("%I:%M %p"),
        inline=True,
    )

    offset = settings.get_offset(prayer)
    if offset != 0:
        embed.add_field(
            name="Offset",
            value=format_prayer_offset(offset),
            inline=True,
        )

    embed.set_footer(text="Athan Bot • May Allah accept your prayers")
    embed.timestamp = prayer_time

    return embed


def create_next_prayer_embed(
    prayer: Prayer,
    prayer_time: datetime,
    time_until_seconds: int,
    settings: GuildSettings,
) -> discord.Embed:
    """Create embed showing next prayer time with countdown."""
    embed = discord.Embed(
        title=f"🕌 Next Prayer: {prayer.value}",
        color=discord.Color.blue(),
    )

    embed.add_field(
        name="Time",
        value=prayer_time.strftime("%I:%M %p"),
        inline=True,
    )

    embed.add_field(
        name="In",
        value=humanize_time_delta(time_until_seconds),
        inline=True,
    )

    offset = settings.get_offset(prayer)
    if offset != 0:
        embed.add_field(
            name="Offset",
            value=format_prayer_offset(offset),
            inline=True,
        )

    embed.set_footer(
        text=f"Location: {settings.location.city or settings.location.country or 'Unknown'}"
    )

    return embed


def create_all_prayers_embed(
    prayer_times: dict[Prayer, datetime],
    settings: GuildSettings,
    current_time: datetime,
) -> discord.Embed:
    """Create embed showing all prayer times for the day."""
    embed = discord.Embed(
        title="🕌 Today's Prayer Times",
        color=discord.Color.gold(),
    )

    # Find next prayer
    next_prayer = None
    for prayer in [Prayer.FAJR, Prayer.DHUHR, Prayer.ASR, Prayer.MAGHRIB, Prayer.ISHA]:
        if prayer in prayer_times and prayer_times[prayer] > current_time:
            next_prayer = prayer
            break

    # Add each prayer
    for prayer in [Prayer.FAJR, Prayer.DHUHR, Prayer.ASR, Prayer.MAGHRIB, Prayer.ISHA]:
        if prayer not in prayer_times:
            continue

        time = prayer_times[prayer]
        time_str = time.strftime("%I:%M %p")

        # Add emoji for next prayer
        prefix = "▶️ " if prayer == next_prayer else ""

        offset = settings.get_offset(prayer)
        offset_str = f" ({format_prayer_offset(offset)})" if offset != 0 else ""

        embed.add_field(
            name=f"{prefix}{prayer.value}",
            value=f"{time_str}{offset_str}",
            inline=False,
        )

    embed.set_footer(
        text=f"Location: {settings.location.city or settings.location.country or 'Unknown'} • "
        f"Method: {settings.calculation_method.name}"
    )

    return embed


def create_test_embed(settings: GuildSettings) -> discord.Embed:
    """Create test notification embed."""
    embed = discord.Embed(
        title="🧪 Test Notification",
        description="This is a test prayer notification.",
        color=discord.Color.orange(),
    )

    embed.add_field(
        name="Location",
        value=settings.location.city or settings.location.country or "Unknown",
        inline=True,
    )

    embed.add_field(
        name="Method",
        value=settings.calculation_method.name,
        inline=True,
    )

    if settings.subscribed_channel_id:
        embed.add_field(
            name="Text Channel",
            value=f"<#{settings.subscribed_channel_id}>",
            inline=False,
        )

    if settings.voice_channel_id:
        embed.add_field(
            name="Voice Channel",
            value=f"<#{settings.voice_channel_id}>",
            inline=False,
        )

    if settings.ping_role_id:
        embed.add_field(
            name="Ping Role",
            value=f"<@&{settings.ping_role_id}>",
            inline=False,
        )

    embed.set_footer(text="Athan Bot • Test Mode")

    return embed


def create_setup_success_embed(settings: GuildSettings) -> discord.Embed:
    """Create setup success confirmation embed."""
    embed = discord.Embed(
        title="✅ Setup Complete",
        description="Your Athan bot is configured!",
        color=discord.Color.green(),
    )

    location_str = settings.location.city or settings.location.country or "Unknown"
    embed.add_field(name="Location", value=location_str, inline=True)
    embed.add_field(name="Timezone", value=settings.timezone, inline=True)
    embed.add_field(name="Method", value=settings.calculation_method.name, inline=True)

    embed.add_field(
        name="Next Steps",
        value=(
            "1️⃣ Use `/subscribe` to enable notifications\n"
            "2️⃣ Use `/next_prayer` to see prayer times\n"
            "3️⃣ Use `/set_offset` to adjust timings"
        ),
        inline=False,
    )

    embed.set_footer(text="Athan Bot")

    return embed
