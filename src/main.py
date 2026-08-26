from __future__ import annotations

import logging
import os
from pathlib import Path

import discord
from dotenv import load_dotenv

from src.discord_layer.bot import NeddexBot


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "data" / "neddex.db"


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger("neddex")


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


def main() -> None:
    token = load_config()

    bot = NeddexBot(
        database_path=DATABASE_PATH,
    )

    try:
        bot.run(token)
    except discord.LoginFailure as exc:
        logger.error(
            "Discord authentication failed. "
            "Check the DISCORD_TOKEN in .env."
        )
        raise RuntimeError(
            "Invalid Discord bot token."
        ) from exc
    except Exception:
        logger.exception(
            "Neddex stopped because of an unexpected error."
        )
        raise


if __name__ == "__main__":
    main()