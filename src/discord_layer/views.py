from __future__ import annotations
from .modals import CatchModal

import discord
import discord.ui

class SpawnCatchView(discord.ui.View):
    """
    Discord button attached to a vehicle spawn image.
    """

    def __init__(
        self,
        *,
        catch_service,
        timeout: float = 120,
    )-> None:
        super().__init__(timeout=timeout)
        self.catch_service = catch_service

    @discord.ui.button(
        label="Catch",
        style=discord.ButtonStyle.green,
        custom_id="neddex_spawn_catch",
    )
    async def catch_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        
        await interaction.response.send_modal(
            CatchModal(
                catch_service=self.catch_service
            )
        )