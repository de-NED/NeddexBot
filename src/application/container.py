from __future__ import annotations

from pathlib import Path
from datetime import timedelta
import random

from src.core.collections import VehicleInstanceRepository
from src.core.servers import ServerEligibility
from src.core.spawning import (
    CatchService,
    SpawnManager,
    VehicleModelSpawnSource,
)
from src.core.vehicles import VehicleModelRepository


class NeddexApplication:
    """
    Connects infrastructure and Core services.

    Discord does not own game logic.
    It only calls this container.
    """

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

    def initialize(self) -> None:
        self.vehicle_models.initialize()
        self.vehicle_instances.initialize()

        model_source = VehicleModelSpawnSource(
            self.vehicle_models
        )

        eligibility = ServerEligibility()

        self.spawn_manager = SpawnManager(
            eligibility=eligibility,
            model_source=model_source,
            spawn_cooldown=timedelta(minutes=30),
            catch_window=timedelta(minutes=2),
            rng=random.Random(),
        )

        self.catch_service = CatchService(
            spawn_manager=self.spawn_manager,
            vehicle_repository=self.vehicle_models,
            instance_repository=self.vehicle_instances,
        )