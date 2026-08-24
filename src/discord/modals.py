from __future__ import annotations

from datetime import datetime

import discord


class CatchModal(discord.ui.Modal):
    """
    Collects the vehicle name after pressing Catch.
    """

    def __init__(
        self,
        *,
        catch_service,
    ) -> None:
        super().__init__(
            title="Catch Vehicle"
        )

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
        result = self.catch_service.catch(
            server_id=interaction.guild.id,
            user_id=interaction.user.id,
            submitted_name=self.vehicle_name.value,
            now=datetime.utcnow(),
        )

        await interaction.response.send_message(
            result.reason,
            ephemeral=True,
        )