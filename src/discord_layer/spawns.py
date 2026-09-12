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
    """Send the raw spawn image with the Catch button."""

    view = SpawnCatchView(
        catch_service=catch_service,
    )

    image_file = Path(image_path)

    if not image_file.is_absolute():
        image_file = Path.cwd() / "data" / image_file

    if not image_file.exists():
        raise FileNotFoundError(
            f"Spawn image does not exist: {image_file}"
        )

    file = discord.File(
        image_file,
        filename=image_file.name,
    )

    return await channel.send(
        file=file,
        view=view,
    )