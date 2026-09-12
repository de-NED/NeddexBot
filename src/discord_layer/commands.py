from __future__ import annotations

from datetime import datetime, timezone

import discord
from discord import app_commands


def register_commands(
    tree: app_commands.CommandTree,
    bot: discord.Client,
) -> None:
    @tree.command(
        name="config",
        description="Configure Neddex for this server.",
    )
    @app_commands.describe(
        spawn_channel="Channel where Neddex spawns vehicles.",
        spawning_enabled="Enable or disable Neddex spawning.",
    )
    @app_commands.default_permissions(administrator=True)
    @app_commands.guild_only()
    async def config(
        interaction: discord.Interaction,
        spawn_channel: discord.TextChannel | None = None,
        spawning_enabled: bool | None = None,
    ) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.",
                ephemeral=True,
            )
            return

        application = getattr(bot, "neddex_application", None)

        if application is None:
            await interaction.response.send_message(
                "Neddex application is not initialized.",
                ephemeral=True,
            )
            return

        repository = application.server_configs

        current = repository.get(interaction.guild.id)

        new_spawn_channel_id = (
            spawn_channel.id
            if spawn_channel is not None
            else current.spawn_channel_id
        )

        new_spawning_enabled = (
            spawning_enabled
            if spawning_enabled is not None
            else current.spawning_enabled
        )

        if (
            spawn_channel is None
            and spawning_enabled is None
        ):
            if current.spawn_channel_id is None:
                channel_text = "Not configured"
            else:
                channel = interaction.guild.get_channel(
                    current.spawn_channel_id
                )

                if channel is None:
                    channel_text = (
                        f"<#{current.spawn_channel_id}>"
                    )
                else:
                    channel_text = channel.mention

            status = "Enabled" if current.spawning_enabled else "Disabled"

            await interaction.response.send_message(
                (
                    "**Neddex Configuration**\n"
                    f"Spawn channel: {channel_text}\n"
                    f"Spawning: {status}"
                ),
                ephemeral=True,
            )
            return

        saved = repository.upsert(
            server_id=interaction.guild.id,
            spawn_channel_id=new_spawn_channel_id,
            spawning_enabled=new_spawning_enabled,
        )

        if saved.spawn_channel_id is None:
            channel_text = "Not configured"
        else:
            channel_text = f"<#{saved.spawn_channel_id}>"

        status = "Enabled" if saved.spawning_enabled else "Disabled"

        await interaction.response.send_message(
            (
                "**Neddex Configuration Updated**\n"
                f"Spawn channel: {channel_text}\n"
                f"Spawning: {status}"
            ),
            ephemeral=True,
        )

    admin = app_commands.Group(
        name="admin",
        description="Neddex development and administration commands.",
    )

    @admin.command(
        name="spawn",
        description="Force a vehicle spawn for development testing.",
    )
    @app_commands.default_permissions(administrator=True)
    @app_commands.guild_only()
    async def admin_spawn(
        interaction: discord.Interaction,
    ) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.",
                ephemeral=True,
            )
            return

        application = getattr(bot, "neddex_application", None)

        if application is None:
            await interaction.response.send_message(
                "Neddex application is not initialized.",
                ephemeral=True,
            )
            return

        if application.spawn_manager is None:
            await interaction.response.send_message(
                "Neddex spawn manager is not initialized.",
                ephemeral=True,
            )
            return

        if application.catch_service is None:
            await interaction.response.send_message(
                "Neddex catch service is not initialized.",
                ephemeral=True,
            )
            return

        if application.discord_spawn_adapter is None:
            await interaction.response.send_message(
                "Neddex Discord spawn adapter is not initialized.",
                ephemeral=True,
            )
            return

        config = application.server_configs.get(
            interaction.guild.id
        )

        if config.spawn_channel_id is None:
            await interaction.response.send_message(
                "No spawn channel is configured. Use `/config` first.",
                ephemeral=True,
            )
            return

        channel = interaction.guild.get_channel(
            config.spawn_channel_id
        )

        if channel is None:
            await interaction.response.send_message(
                "The configured spawn channel could not be found.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)

        result = application.spawn_manager.force_spawn(
            server_id=interaction.guild.id,
            now=datetime.now(timezone.utc),
        )

        if result.spawned is None:
            await interaction.followup.send(
                "No vehicle could be spawned. Check that at least one "
                "eligible vehicle has a positive rarity weight.",
                ephemeral=True,
            )
            return

        await application.discord_spawn_adapter.handle_spawn_result(
            result=result,
            channel=channel,
            catch_service=application.catch_service,
        )

        await interaction.followup.send(
            "Manual spawn triggered.",
            ephemeral=True,
        )

    tree.add_command(admin)