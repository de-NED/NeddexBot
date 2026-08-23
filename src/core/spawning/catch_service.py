from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from src.core.vehicles import VehicleModelRepository

from .manager import SpawnManager


@dataclass(frozen=True, slots=True)
class CatchResult:
    """Result of attempting to catch the active vehicle spawn."""

    success: bool
    model_id: int | None
    spawn_id: str | None
    reason: str


class CatchService:
    """
    Handles vehicle catch validation.

    Responsibilities:
    - find the submitted catch name
    - verify the server has an active spawn
    - verify the submitted vehicle matches the active spawn
    - resolve the spawn on success

    It does NOT:
    - create inventory
    - create profiles
    - create vehicle instances
    - assign ownership
    - create mints
    - send Discord messages
    """

    def __init__(
        self,
        *,
        spawn_manager: SpawnManager,
        vehicle_repository: VehicleModelRepository,
    ) -> None:
        self.spawn_manager = spawn_manager
        self.vehicle_repository = vehicle_repository

    def catch(
        self,
        *,
        server_id: int,
        user_id: int,
        submitted_name: str,
        now: datetime,
    ) -> CatchResult:
        """
        Attempt to catch the active vehicle for one server.

        The user ID is intentionally accepted by the Core boundary even
        though ownership is not created yet. This keeps the operation
        ready for the later ownership layer without coupling it now.
        """

        del user_id

        active_spawn = self.spawn_manager.get_active_spawn(server_id)

        if active_spawn is None:
            return CatchResult(
                success=False,
                model_id=None,
                spawn_id=None,
                reason="no_active_spawn",
            )

        vehicle = self.vehicle_repository.find_by_catch_name(
            submitted_name
        )

        if vehicle is None:
            return CatchResult(
                success=False,
                model_id=None,
                spawn_id=active_spawn.spawn_id,
                reason="unknown_vehicle",
            )

        try:
            spawned_model_id = int(active_spawn.model_id)
        except ValueError:
            return CatchResult(
                success=False,
                model_id=None,
                spawn_id=active_spawn.spawn_id,
                reason="invalid_spawn_model",
            )

        if vehicle.id != spawned_model_id:
            return CatchResult(
                success=False,
                model_id=vehicle.id,
                spawn_id=active_spawn.spawn_id,
                reason="wrong_vehicle",
            )

        resolved = self.spawn_manager.resolve_catch(
            server_id=server_id,
            model_id=active_spawn.model_id,
            now=now,
        )

        if not resolved:
            return CatchResult(
                success=False,
                model_id=vehicle.id,
                spawn_id=active_spawn.spawn_id,
                reason="spawn_expired",
            )

        return CatchResult(
            success=True,
            model_id=vehicle.id,
            spawn_id=active_spawn.spawn_id,
            reason="caught",
        )