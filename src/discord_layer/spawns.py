from __future__ import annotations

from pathlib import Path

import discord

from .views import SpawnCatchView


async def send_spawn_message(
    *,
    channel: discord.TextChannel,
    image_path: str,
    catch_service,
) -> discord.Message:
    """
    Sends the raw spawn image with the catch button.

    Discord layer only.
    Core already decided what spawned.
    """

    view = SpawnCatchView(
        catch_service=catch_service,
    )

    image_file = Path(image_path)

    if not image_file.exists():
        raise FileNotFoundError(
            f"Spawn image does not exist: {image_file}"
        )

    file = discord.File(
        image_file,
        filename=image_file.name,
    )

    embed = discord.Embed(
        title="A vehicle has appeared!",
        description="Press Catch to attempt ownership.",
    )

    embed.set_image(
        url=f"attachment://{image_file.name}"
    )

    return await channel.send(
        embed=embed,
        file=file,
        view=view,
    )