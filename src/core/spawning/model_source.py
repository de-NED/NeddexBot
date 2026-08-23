from __future__ import annotations

from src.core.vehicles import VehicleModelRepository

from .engine import SpawnCandidate


class VehicleModelSpawnSource:
    """
    Adapts VehicleModelRepository to the SpawnEngine.

    The SpawnEngine only knows about SpawnCandidate objects.
    The repository remains responsible for vehicle-model data
    and eligibility rules.
    """

    def __init__(self, repository: VehicleModelRepository) -> None:
        self.repository = repository

    def get_spawn_candidates(self) -> list[SpawnCandidate]:
        """Return the current global vehicle spawn pool."""

        models = self.repository.get_spawn_eligible_models()

        return [
            SpawnCandidate(
                model_id=str(model.id),
                weight=model.rarity_weight,
            )
            for model in models
        ]