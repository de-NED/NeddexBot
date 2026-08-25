from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from src.discord_layer.spawns import send_spawn_message


@pytest.mark.asyncio
async def test_spawn_message_sends_raw_image_with_view(tmp_path: Path):
    image = tmp_path / "bmw_m4.png"
    image.write_bytes(b"fake-image")

    channel = AsyncMock()

    await send_spawn_message(
        channel=channel,
        image_path=str(image),
        catch_service=object(),
    )

    channel.send.assert_awaited_once()

    kwargs = channel.send.await_args.kwargs

    assert "file" in kwargs
    assert "view" in kwargs
    assert kwargs["file"].filename == "bmw_m4.png"