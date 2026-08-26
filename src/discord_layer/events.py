from __future__ import annotations

from datetime import datetime, timezone
import logging

import discord

from src.application import NeddexApplication

logger = logging.getLogger("neddex")


async def handle_message(
    bot: discord.Client,
    message: discord.Message,
) -> None:
    """
    Convert Discord messages into Core activity.

    Core decides whether a spawn occurs.
    DiscordSpawnAdapter handles presenting the spawn.
    Catching is handled by the button + modal flow.
    """

    logger.info(
        "Received message from %s in %s: %s",
        message.author,
        message.guild,
        message.content,
    )

    if message.author.bot:
        return

    if message.guild is None:
        return

    if message.content.startswith("!"):
        return

    application: NeddexApplication = bot.neddex_application

    if application.spawn_manager is None:
        return

    result = application.spawn_manager.process_message(
        server_id=message.guild.id,
        human_member_count=sum(
            1
            for member in message.guild.members
            if not member.bot
        ),
        user_id=message.author.id,
        created_at=datetime.now(timezone.utc),
    )

    if result.spawned is None:
        return

    if application.catch_service is None:
        return

    if application.discord_spawn_adapter is None:
        return

    await application.discord_spawn_adapter.handle_spawn_result(
        result=result,
        channel=message.channel,
        catch_service=application.catch_service,
    )