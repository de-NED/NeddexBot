from __future__ import annotations
from src.core.vehicles import VehicleModelRepository

import logging
import os
import sqlite3
from pathlib import Path

import discord
from dotenv import load_dotenv


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATABASE_PATH = DATA_DIR / "neddex.db"


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger("neddex")


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

def load_config() -> str:
    """Load and validate the Discord bot token."""

    load_dotenv(PROJECT_ROOT / ".env")

    token = os.getenv("DISCORD_TOKEN")

    if not token:
        raise RuntimeError(
            "DISCORD_TOKEN is missing. "
            "Create a .env file in the project root and add "
            "DISCORD_TOKEN=your_bot_token."
        )

    return token


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

def initialize_database() -> None:
    """Create the Core database if it does not already exist."""

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute("PRAGMA foreign_keys = ON")

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS system_metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )

        connection.commit()

    logger.info("Database initialized: %s", DATABASE_PATH)


# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------

class NeddexCore:
    """Minimal Core bootstrap."""

    def __init__(self) -> None:
        self.vehicle_models = VehicleModelRepository(DATABASE_PATH)

    def initialize(self) -> None:
        self.vehicle_models.initialize()
        logger.info("Neddex Core initialized.")

# ---------------------------------------------------------------------------
# Discord Bot
# ---------------------------------------------------------------------------

class NeddexBot(discord.Client):
    """Neddex Discord client."""

    def __init__(self) -> None:
        intents = discord.Intents.none()
        intents.guilds = True

        super().__init__(intents=intents)

        self.core = NeddexCore()

    async def setup_hook(self) -> None:
        """Initialize Neddex before the bot becomes ready."""

        initialize_database()
        self.core.initialize()

    async def on_ready(self) -> None:
        """Report successful Discord connection."""

        if self.user is None:
            logger.error("Discord connected, but bot user information is unavailable.")
            return

        logger.info(
            "Neddex is online as %s (ID: %s)",
            self.user,
            self.user.id,
        )


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

def main() -> None:
    token = load_config()
    bot = NeddexBot()

    try:
        bot.run(token)
    except discord.LoginFailure as exc:
        logger.error(
            "Discord authentication failed. "
            "Check the DISCORD_TOKEN in .env."
        )
        raise RuntimeError("Invalid Discord bot token.") from exc
    except Exception:
        logger.exception("Neddex stopped because of an unexpected error.")
        raise


if __name__ == "__main__":
    main()