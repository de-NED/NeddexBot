from __future__ import annotations

from datetime import datetime

import discord

from src.application import NeddexApplication


async def handle_message(
    bot: discord.Client,
    message: discord.Message,
) -> None:
    """
    Convert Discord messages into Core activity.

    Catching is handled by the button + modal flow.
    """

    if message.author.bot:
        return

    if message.guild is None:
        return

    if message.content.startswith("!"):
        return

    application: NeddexApplication = bot.application

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
        created_at=datetime.utcnow(),
    )

    if result.spawned is None:
        return

    if application.catch_service is None:
        return

    vehicle = application.vehicle_models.get(
        int(result.spawned.model_id)
    )

    if vehicle.spawn_image is None:
        return

    from .spawns import send_spawn_message

    await send_spawn_message(
        channel=message.channel,
        image_path=vehicle.spawn_image,
        catch_service=application.catch_service,
    )