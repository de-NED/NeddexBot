from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest

from src.core.spawning import ActiveSpawn, SpawnActivityResult
from src.discord_layer.coordinator import DiscordSpawnAdapter
from src.discord_layer.spawns import send_spawn_message


BASE_TIME = datetime(2026, 1, 1, tzinfo=timezone.utc)


@pytest.mark.asyncio
async def test_spawn_message_sends_raw_image_with_view(
    tmp_path: Path,
):
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


@pytest.mark.asyncio
async def test_spawn_adapter_sends_spawn_image(tmp_path: Path):
    image = tmp_path / "bmw_m4.png"
    image.write_bytes(b"fake-image")

    channel = AsyncMock()
    send_spawn_message_mock = AsyncMock()

    vehicle = Mock()
    vehicle.spawn_image = str(image)

    vehicle_repository = Mock()
    vehicle_repository.get.return_value = vehicle

    adapter = DiscordSpawnAdapter(
        send_spawn_message=send_spawn_message_mock,
        vehicle_repository=vehicle_repository,
    )

    spawn = ActiveSpawn(
        spawn_id="spawn-test",
        model_id="1",
        created_at=BASE_TIME,
        expires_at=BASE_TIME + timedelta(minutes=2),
    )

    result = SpawnActivityResult(
        counted=True,
        ready=True,
        spawned=spawn,
    )

    catch_service = object()

    await adapter.handle_spawn_result(
        result=result,
        channel=channel,
        catch_service=catch_service,
    )

    vehicle_repository.get.assert_called_once_with(1)

    send_spawn_message_mock.assert_awaited_once_with(
        channel=channel,
        image_path=str(image),
        catch_service=catch_service,
    )


@pytest.mark.asyncio
async def test_spawn_adapter_does_nothing_without_spawn():
    channel = AsyncMock()
    send_spawn_message_mock = AsyncMock()
    vehicle_repository = Mock()

    adapter = DiscordSpawnAdapter(
        send_spawn_message=send_spawn_message_mock,
        vehicle_repository=vehicle_repository,
    )

    result = SpawnActivityResult(
        counted=True,
        ready=True,
        spawned=None,
    )

    await adapter.handle_spawn_result(
        result=result,
        channel=channel,
        catch_service=object(),
    )

    vehicle_repository.get.assert_not_called()
    send_spawn_message_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_spawn_adapter_does_not_send_without_spawn_image():
    channel = AsyncMock()
    send_spawn_message_mock = AsyncMock()

    vehicle = Mock()
    vehicle.spawn_image = None

    vehicle_repository = Mock()
    vehicle_repository.get.return_value = vehicle

    adapter = DiscordSpawnAdapter(
        send_spawn_message=send_spawn_message_mock,
        vehicle_repository=vehicle_repository,
    )

    spawn = ActiveSpawn(
        spawn_id="spawn-test",
        model_id="1",
        created_at=BASE_TIME,
        expires_at=BASE_TIME + timedelta(minutes=2),
    )

    result = SpawnActivityResult(
        counted=True,
        ready=True,
        spawned=spawn,
    )

    await adapter.handle_spawn_result(
        result=result,
        channel=channel,
        catch_service=object(),
    )

    vehicle_repository.get.assert_called_once_with(1)
    send_spawn_message_mock.assert_not_awaited()