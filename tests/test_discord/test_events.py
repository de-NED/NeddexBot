from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from src.discord_layer.events import handle_message


def make_message(
    *,
    bot: bool = False,
    guild=True,
    content: str = "hello",
    user_id: int = 123,
    guild_id: int = 456,
    human_members: int = 5,
):
    author = SimpleNamespace(
        bot=bot,
        id=user_id,
    )

    if guild:
        members = [
            SimpleNamespace(bot=False)
            for _ in range(human_members)
        ]

        members.append(
            SimpleNamespace(bot=True)
        )

        guild_object = SimpleNamespace(
            id=guild_id,
            members=members,
        )
    else:
        guild_object = None

    return SimpleNamespace(
        author=author,
        guild=guild_object,
        content=content,
        channel=AsyncMock(),
    )


def make_bot(
    *,
    spawn_manager,
    catch_service,
    discord_spawn_adapter,
):
    return SimpleNamespace(
        application=SimpleNamespace(
            spawn_manager=spawn_manager,
            catch_service=catch_service,
            discord_spawn_adapter=discord_spawn_adapter,
        )
    )


@pytest.mark.asyncio
async def test_bot_message_is_ignored():
    spawn_manager = Mock()
    adapter = AsyncMock()

    bot = make_bot(
        spawn_manager=spawn_manager,
        catch_service=object(),
        discord_spawn_adapter=adapter,
    )

    message = make_message(bot=True)

    await handle_message(bot, message)

    spawn_manager.process_message.assert_not_called()
    adapter.handle_spawn_result.assert_not_awaited()


@pytest.mark.asyncio
async def test_direct_message_is_ignored():
    spawn_manager = Mock()
    adapter = AsyncMock()

    bot = make_bot(
        spawn_manager=spawn_manager,
        catch_service=object(),
        discord_spawn_adapter=adapter,
    )

    message = make_message(guild=False)

    await handle_message(bot, message)

    spawn_manager.process_message.assert_not_called()
    adapter.handle_spawn_result.assert_not_awaited()


@pytest.mark.asyncio
async def test_command_message_is_ignored():
    spawn_manager = Mock()
    adapter = AsyncMock()

    bot = make_bot(
        spawn_manager=spawn_manager,
        catch_service=object(),
        discord_spawn_adapter=adapter,
    )

    message = make_message(content="!spawn")

    await handle_message(bot, message)

    spawn_manager.process_message.assert_not_called()
    adapter.handle_spawn_result.assert_not_awaited()


@pytest.mark.asyncio
async def test_normal_message_is_sent_to_spawn_manager():
    spawn_manager = Mock()

    spawn_manager.process_message.return_value = SimpleNamespace(
        spawned=None,
    )

    adapter = AsyncMock()

    bot = make_bot(
        spawn_manager=spawn_manager,
        catch_service=object(),
        discord_spawn_adapter=adapter,
    )

    message = make_message(
        user_id=123,
        guild_id=456,
        human_members=7,
    )

    await handle_message(bot, message)

    spawn_manager.process_message.assert_called_once()

    kwargs = spawn_manager.process_message.call_args.kwargs

    assert kwargs["server_id"] == 456
    assert kwargs["human_member_count"] == 7
    assert kwargs["user_id"] == 123

    assert isinstance(kwargs["created_at"], datetime)
    assert kwargs["created_at"].tzinfo is not None

    adapter.handle_spawn_result.assert_not_awaited()


@pytest.mark.asyncio
async def test_spawn_result_is_sent_to_discord_adapter():
    spawn_manager = Mock()

    spawn_result = SimpleNamespace(
        spawned=SimpleNamespace(
            model_id="42",
        ),
    )

    spawn_manager.process_message.return_value = spawn_result

    catch_service = object()
    adapter = AsyncMock()

    bot = make_bot(
        spawn_manager=spawn_manager,
        catch_service=catch_service,
        discord_spawn_adapter=adapter,
    )

    message = make_message()

    await handle_message(bot, message)

    adapter.handle_spawn_result.assert_awaited_once_with(
        result=spawn_result,
        channel=message.channel,
        catch_service=catch_service,
    )


@pytest.mark.asyncio
async def test_no_spawn_does_not_call_discord_adapter():
    spawn_manager = Mock()

    spawn_manager.process_message.return_value = SimpleNamespace(
        spawned=None,
    )

    adapter = AsyncMock()

    bot = make_bot(
        spawn_manager=spawn_manager,
        catch_service=object(),
        discord_spawn_adapter=adapter,
    )

    message = make_message()

    await handle_message(bot, message)

    adapter.handle_spawn_result.assert_not_awaited()


@pytest.mark.asyncio
async def test_missing_spawn_manager_is_safe():
    adapter = AsyncMock()

    bot = make_bot(
        spawn_manager=None,
        catch_service=object(),
        discord_spawn_adapter=adapter,
    )

    message = make_message()

    await handle_message(bot, message)

    adapter.handle_spawn_result.assert_not_awaited()


@pytest.mark.asyncio
async def test_missing_catch_service_is_safe():
    spawn_manager = Mock()

    spawn_result = SimpleNamespace(
        spawned=SimpleNamespace(
            model_id="42",
        ),
    )

    spawn_manager.process_message.return_value = spawn_result

    adapter = AsyncMock()

    bot = make_bot(
        spawn_manager=spawn_manager,
        catch_service=None,
        discord_spawn_adapter=adapter,
    )

    message = make_message()

    await handle_message(bot, message)

    adapter.handle_spawn_result.assert_not_awaited()


@pytest.mark.asyncio
async def test_missing_discord_adapter_is_safe():
    spawn_manager = Mock()

    spawn_result = SimpleNamespace(
        spawned=SimpleNamespace(
            model_id="42",
        ),
    )

    spawn_manager.process_message.return_value = spawn_result

    bot = make_bot(
        spawn_manager=spawn_manager,
        catch_service=object(),
        discord_spawn_adapter=None,
    )

    message = make_message()

    await handle_message(bot, message)