from __future__ import annotations

from pathlib import Path

import discord

from src.application import NeddexApplication

from .events import handle_message


class NeddexBot(discord.Client):
    """
    Discord client entry point.
    """

    def __init__(
        self,
        *,
        database_path: Path,
    ) -> None:
        intents = discord.Intents.none()

        intents.guilds = True
        intents.members = True
        intents.message_content = True

        super().__init__(intents=intents)

        self.neddex_application = NeddexApplication(
            database_path
        )

    async def setup_hook(self) -> None:
        self.neddex_application.initialize()

    async def on_message(
        self,
        message: discord.Message,
    ) -> None:
        print(
            "ON_MESSAGE",
            message.author,
            message.content,
        )
        await handle_message(
            self,
            message,
        )

    async def on_ready(self) -> None:
        if self.user is None:
            return

        print(
            f"Neddex online as {self.user} "
            f"({self.user.id})"
        )