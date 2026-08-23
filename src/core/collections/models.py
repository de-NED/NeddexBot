from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class VehicleInstance:
    """One individually owned vehicle."""

    id: int
    vehicle_model_id: int
    owner_user_id: int
    mint_number: int
    acquired_at: datetime