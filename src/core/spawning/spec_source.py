from __future__ import annotations

from .engine import SpawnCandidate
from src.core.vehicles import VehicleSpecRepository


class VehicleSpecSpawnSource:
    """
    Provides eligible Vehicle Specs for spawning.

    Spawn system only sees:
    - spec id
    - spawn weight

    It does not know:
    - manufacturer
    - model name
    - images
    - cards
    """

    def __init__(
        self,
        repository: VehicleSpecRepository,
    ) -> None:
        self.repository = repository

    def get_spawn_candidates(self) -> list[SpawnCandidate]:
        specs = self.repository.get_spawn_eligible_specs()

        return [
            SpawnCandidate(
                model_id=str(spec.id),
                weight=spec.rarity_weight,
            )
            for spec in specs
        ]