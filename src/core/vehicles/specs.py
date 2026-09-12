from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class VehicleSpec:
    """
    A specific version of a vehicle.

    Example:
    BMW M4
    ├── Base
    ├── Competition
    └── CSL

    Each spec is independently spawnable and collectible.
    """

    id: int
    vehicle_model_id: int

    name: str

    rarity_weight: float

    spawn_image: str | None

    card_id: int | None

    enabled: bool
    spawn_eligible: bool

    limited: bool
    mint_limit: int | None
    highest_mint: int