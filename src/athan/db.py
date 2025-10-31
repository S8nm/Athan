"""Database persistence layer using aiosqlite."""

import json
import logging
from pathlib import Path

import aiosqlite

from athan.config import GuildSettings, Location, Prayer, UserSettings

logger = logging.getLogger(__name__)


class Database:
    """Async SQLite database for persistent settings."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn: aiosqlite.Connection | None = None

    async def connect(self):
        """Open database connection and initialize schema."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = await aiosqlite.connect(self.db_path)
        await self._init_schema()
        logger.info(f"Database connected: {self.db_path}")

    async def close(self):
        """Close database connection."""
        if self.conn:
            await self.conn.close()
            logger.info("Database closed")

    async def _init_schema(self):
        """Create tables if they don't exist."""
        await self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS guild_settings (
                guild_id INTEGER PRIMARY KEY,
                location_json TEXT,
                calculation_method TEXT DEFAULT '2',
                timezone TEXT DEFAULT 'UTC',
                subscribed_channel_id INTEGER,
                voice_channel_id INTEGER,
                ping_role_id INTEGER,
                enabled_prayers TEXT,
                prayer_offsets TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        await self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id INTEGER PRIMARY KEY,
                location_json TEXT,
                calculation_method TEXT DEFAULT '2',
                timezone TEXT DEFAULT 'UTC',
                prayer_offsets TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # Run migrations
        await self._run_migrations()
        await self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS scheduled_prayers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                prayer TEXT NOT NULL,
                scheduled_time TEXT NOT NULL,
                date TEXT NOT NULL,
                sent INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(guild_id, prayer, date)
            )
            """
        )
        await self.conn.commit()

    async def _run_migrations(self):
        """Run database migrations for schema updates."""
        # Migration: Add ping_role_id column if it doesn't exist
        try:
            await self.conn.execute("SELECT ping_role_id FROM guild_settings LIMIT 1")
        except Exception:
            logger.info("Running migration: Adding ping_role_id column to guild_settings")
            await self.conn.execute("ALTER TABLE guild_settings ADD COLUMN ping_role_id INTEGER")
            await self.conn.commit()
            logger.info("Migration completed: ping_role_id column added")

    async def get_guild_settings(self, guild_id: int) -> GuildSettings | None:
        """Retrieve guild settings."""
        cursor = await self.conn.execute(
            """
            SELECT location_json, calculation_method, timezone,
                   subscribed_channel_id, voice_channel_id, ping_role_id,
                   enabled_prayers, prayer_offsets
            FROM guild_settings
            WHERE guild_id = ?
            """,
            (guild_id,),
        )
        row = await cursor.fetchone()
        if not row:
            return None

        location = json.loads(row[0]) if row[0] else None
        enabled_prayers = json.loads(row[6]) if row[6] else []
        prayer_offsets = json.loads(row[7]) if row[7] else {}

        return GuildSettings(
            guild_id=guild_id,
            location=Location(**location) if location else None,
            calculation_method=row[1],
            timezone=row[2],
            subscribed_channel_id=row[3],
            voice_channel_id=row[4],
            ping_role_id=row[5],
            enabled_prayers=[Prayer(p) for p in enabled_prayers],
            prayer_offsets=prayer_offsets,
        )

    async def save_guild_settings(self, settings: GuildSettings):
        """Save or update guild settings."""
        location_json = json.dumps(settings.location.model_dump()) if settings.location else None
        enabled_prayers_json = json.dumps([p.value for p in settings.enabled_prayers])
        prayer_offsets_json = json.dumps(settings.prayer_offsets)

        await self.conn.execute(
            """
            INSERT INTO guild_settings (
                guild_id, location_json, calculation_method, timezone,
                subscribed_channel_id, voice_channel_id, ping_role_id,
                enabled_prayers, prayer_offsets
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET
                location_json = excluded.location_json,
                calculation_method = excluded.calculation_method,
                timezone = excluded.timezone,
                subscribed_channel_id = excluded.subscribed_channel_id,
                voice_channel_id = excluded.voice_channel_id,
                ping_role_id = excluded.ping_role_id,
                enabled_prayers = excluded.enabled_prayers,
                prayer_offsets = excluded.prayer_offsets,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                settings.guild_id,
                location_json,
                settings.calculation_method,
                settings.timezone,
                settings.subscribed_channel_id,
                settings.voice_channel_id,
                settings.ping_role_id,
                enabled_prayers_json,
                prayer_offsets_json,
            ),
        )
        await self.conn.commit()
        logger.info(f"Saved settings for guild {settings.guild_id}")

    async def get_user_settings(self, user_id: int) -> UserSettings | None:
        """Retrieve user settings."""
        cursor = await self.conn.execute(
            """
            SELECT location_json, calculation_method, timezone, prayer_offsets
            FROM user_settings
            WHERE user_id = ?
            """,
            (user_id,),
        )
        row = await cursor.fetchone()
        if not row:
            return None

        location = json.loads(row[0]) if row[0] else None
        prayer_offsets = json.loads(row[3]) if row[3] else {}

        return UserSettings(
            user_id=user_id,
            location=Location(**location) if location else None,
            calculation_method=row[1],
            timezone=row[2],
            prayer_offsets=prayer_offsets,
        )

    async def save_user_settings(self, settings: UserSettings):
        """Save or update user settings."""
        location_json = json.dumps(settings.location.model_dump()) if settings.location else None
        prayer_offsets_json = json.dumps(settings.prayer_offsets)

        await self.conn.execute(
            """
            INSERT INTO user_settings (
                user_id, location_json, calculation_method, timezone, prayer_offsets
            )
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                location_json = excluded.location_json,
                calculation_method = excluded.calculation_method,
                timezone = excluded.timezone,
                prayer_offsets = excluded.prayer_offsets,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                settings.user_id,
                location_json,
                settings.calculation_method,
                settings.timezone,
                prayer_offsets_json,
            ),
        )
        await self.conn.commit()
        logger.info(f"Saved settings for user {settings.user_id}")

    async def get_all_subscribed_guilds(self) -> list[int]:
        """Get all guild IDs with active subscriptions."""
        cursor = await self.conn.execute(
            """
            SELECT guild_id
            FROM guild_settings
            WHERE subscribed_channel_id IS NOT NULL
            """
        )
        rows = await cursor.fetchall()
        return [row[0] for row in rows]

    async def mark_prayer_sent(self, guild_id: int, prayer: str, date: str):
        """Mark a scheduled prayer as sent."""
        await self.conn.execute(
            """
            UPDATE scheduled_prayers
            SET sent = 1
            WHERE guild_id = ? AND prayer = ? AND date = ?
            """,
            (guild_id, prayer, date),
        )
        await self.conn.commit()

    async def is_prayer_sent(self, guild_id: int, prayer: str, date: str) -> bool:
        """Check if prayer notification was already sent."""
        cursor = await self.conn.execute(
            """
            SELECT sent
            FROM scheduled_prayers
            WHERE guild_id = ? AND prayer = ? AND date = ?
            """,
            (guild_id, prayer, date),
        )
        row = await cursor.fetchone()
        return bool(row and row[0])

    async def record_scheduled_prayer(
        self, guild_id: int, prayer: str, scheduled_time: str, date: str
    ):
        """Record a scheduled prayer for deduplication."""
        await self.conn.execute(
            """
            INSERT OR IGNORE INTO scheduled_prayers
                (guild_id, prayer, scheduled_time, date)
            VALUES (?, ?, ?, ?)
            """,
            (guild_id, prayer, scheduled_time, date),
        )
        await self.conn.commit()
