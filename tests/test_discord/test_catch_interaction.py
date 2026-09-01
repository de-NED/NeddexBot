from unittest.mock import ANY, AsyncMock, Mock

import discord
import pytest

from src.discord_layer.views import SpawnCatchView
from src.discord_layer.modals import CatchModal


def test_spawn_view_has_catch_button():
    catch_service = object()

    view = SpawnCatchView(
        catch_service=catch_service,
    )

    assert len(view.children) == 1

    button = view.children[0]

    assert isinstance(button, discord.ui.Button)
    assert button.label == "Catch"
    assert button.custom_id == "neddex_spawn_catch"


@pytest.mark.asyncio
async def test_catch_button_opens_modal():
    catch_service = object()

    view = SpawnCatchView(
        catch_service=catch_service,
    )

    interaction = AsyncMock()

    button = view.children[0]

    await button.callback(interaction)

    interaction.response.send_modal.assert_awaited_once()

    modal = interaction.response.send_modal.await_args.args[0]

    assert isinstance(modal, CatchModal)
    assert modal.catch_service is catch_service


@pytest.mark.asyncio
async def test_catch_modal_submits_to_service():
    catch_service = Mock()

    catch_service.catch.return_value = type(
        "CatchResult",
        (),
        {"reason": "caught"},
    )()

    modal = CatchModal(
        catch_service=catch_service,
    )

    modal.vehicle_name._value = "BMW M4"

    interaction = AsyncMock()
    interaction.guild.id = 123
    interaction.user.id = 456

    await modal.on_submit(interaction)

    catch_service.catch.assert_called_once_with(
        server_id=123,
        user_id=456,
        submitted_name="BMW M4",
        now=ANY,
    )

    interaction.response.send_message.assert_awaited_once_with(
        "Vehicle caught successfully.",
        ephemeral=True,
    )

@pytest.mark.asyncio
async def test_catch_modal_rejects_dm():
    catch_service = Mock()

    modal = CatchModal(
        catch_service=catch_service,
    )

    interaction = AsyncMock()
    interaction.guild = None

    await modal.on_submit(interaction)

    catch_service.catch.assert_not_called()

    interaction.response.send_message.assert_awaited_once_with(
        "You can only catch vehicles inside a server.",
        ephemeral=True,
    )


@pytest.mark.asyncio
async def test_catch_modal_maps_unknown_vehicle():
    catch_service = Mock()

    catch_service.catch.return_value = type(
        "CatchResult",
        (),
        {"reason": "unknown_vehicle"},
    )()

    modal = CatchModal(
        catch_service=catch_service,
    )

    modal.vehicle_name._value = "Ferrari"

    interaction = AsyncMock()
    interaction.guild.id = 123
    interaction.user.id = 456

    await modal.on_submit(interaction)

    interaction.response.send_message.assert_awaited_once_with(
        "I don't recognize that vehicle.",
        ephemeral=True,
    )