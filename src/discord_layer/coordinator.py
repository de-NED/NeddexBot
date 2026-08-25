from __future__ import annotations

from src.core.spawning import SpawnActivityResult


class DiscordSpawnAdapter:
    """
    Converts Core spawn results into Discord messages.

    Core decides WHAT spawned.
    Discord decides HOW it is displayed.
    """

    def __init__(
        self,
        *,
        send_spawn_message,
        vehicle_repository,
    ) -> None:
        self.send_spawn_message = send_spawn_message
        self.vehicle_repository = vehicle_repository

    async def handle_spawn_result(
        self,
        *,
        result: SpawnActivityResult,
        channel,
        catch_service,
    ) -> None:
        if result.spawned is None:
            return

        vehicle = self.vehicle_repository.get(
            int(result.spawned.model_id)
        )

        if vehicle.spawn_image is None:
            return

        await self.send_spawn_message(
            channel=channel,
            image_path=vehicle.spawn_image,
            catch_service=catch_service,
        )