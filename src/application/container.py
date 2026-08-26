from __future__ import annotations

from pathlib import Path

from src.core.collections import VehicleInstanceRepository
from src.core.servers import ServerEligibility
from src.core.spawning import (
    CatchService,
    SpawnManager,
    VehicleModelSpawnSource,
)
from src.core.vehicles import VehicleModelRepository

from src.discord_layer.coordinator import DiscordSpawnAdapter
from src.discord_layer.spawns import send_spawn_message


class NeddexApplication:
    """Application dependency container."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

        self.vehicle_models = VehicleModelRepository(
            database_path
        )

        self.vehicle_instances = VehicleInstanceRepository(
            database_path
        )

        self.spawn_manager: SpawnManager | None = None
        self.catch_service: CatchService | None = None
        self.discord_spawn_adapter: DiscordSpawnAdapter | None = None

    def initialize(self) -> None:
        self.vehicle_models.initialize()
        self.vehicle_instances.initialize()

        eligibility = ServerEligibility()

        model_source = VehicleModelSpawnSource(
            self.vehicle_models
        )

        self.spawn_manager = SpawnManager(
            eligibility=eligibility,
            model_source=model_source,
        )

        self.catch_service = CatchService(
            spawn_manager=self.spawn_manager,
            vehicle_repository=self.vehicle_models,
            instance_repository=self.vehicle_instances,
        )

        self.discord_spawn_adapter = DiscordSpawnAdapter(
            send_spawn_message=send_spawn_message,
            vehicle_repository=self.vehicle_models,
        )