from __future__ import annotations

from datetime import datetime, timezone

import discord


class CatchModal(discord.ui.Modal):
    """Collects the vehicle name after pressing Catch."""

    def __init__(
        self,
        *,
        catch_service,
    ) -> None:
        super().__init__(title="Catch Vehicle")

        self.catch_service = catch_service

        self.vehicle_name = discord.ui.TextInput(
            label="Vehicle name",
            placeholder="Example: BMW M4",
            max_length=100,
            required=True,
        )

        self.add_item(self.vehicle_name)

    async def on_submit(
        self,
        interaction: discord.Interaction,
    ) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                "You can only catch vehicles inside a server.",
                ephemeral=True,
            )
            return

        result = self.catch_service.catch(
            server_id=interaction.guild.id,
            user_id=interaction.user.id,
            submitted_name=self.vehicle_name.value,
            now=datetime.now(timezone.utc),
        )

        messages = {
            "caught": "Vehicle caught successfully.",
            "no_active_spawn": "There is no active vehicle to catch.",
            "spawn_expired": "That vehicle has already escaped.",
            "unknown_vehicle": "I don't recognize that vehicle.",
            "wrong_vehicle": "That's not the vehicle that spawned.",
            "spawn_already_claimed": "Someone else caught that vehicle first.",
            "invalid_spawn_model": "That spawn is invalid.",
        }

        message = messages.get(
            result.reason,
            "Something went wrong while catching that vehicle.",
        )

        await interaction.response.send_message(
            message,
            ephemeral=True,
        )