from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from src.core.collections import VehicleInstance, VehicleInstanceRepository
from src.core.vehicles import VehicleModelRepository

from .manager import SpawnManager


@dataclass(frozen=True, slots=True)
class CatchResult:
    """Result of attempting to catch the active vehicle spawn."""

    success: bool
    model_id: int | None
    spawn_id: str | None
    vehicle_instance: VehicleInstance | None
    reason: str


class CatchService:
    """
    Handles vehicle catch validation and successful ownership creation.

    Responsibilities:
    - find the submitted catch name
    - verify the server has an active spawn
    - verify the submitted vehicle matches the active spawn
    - create the vehicle instance
    - consume the spawn after successful mint

    It does NOT:
    - send Discord messages
    - render cards
    - manage Discord UI
    - manage garage capacity
    - manage trading
    """

    def __init__(
        self,
        *,
        spawn_manager: SpawnManager,
        vehicle_repository: VehicleModelRepository,
        instance_repository: VehicleInstanceRepository,
    ) -> None:
        self.spawn_manager = spawn_manager
        self.vehicle_repository = vehicle_repository
        self.instance_repository = instance_repository

    def catch(
        self,
        *,
        server_id: int,
        user_id: int,
        submitted_name: str,
        now: datetime,
    ) -> CatchResult:
        """Attempt to catch the active vehicle."""

        active_spawn = self.spawn_manager.get_active_spawn(server_id)

        if active_spawn is None:
            return CatchResult(
                success=False,
                model_id=None,
                spawn_id=None,
                vehicle_instance=None,
                reason="no_active_spawn",
            )

        if now >= active_spawn.expires_at:
            self.spawn_manager.expire_spawn(
                server_id=server_id,
                now=now,
            )

            return CatchResult(
                success=False,
                model_id=None,
                spawn_id=active_spawn.spawn_id,
                vehicle_instance=None,
                reason="spawn_expired",
            )

        vehicle = self.vehicle_repository.find_by_catch_name(
            submitted_name
        )

        if vehicle is None:
            return CatchResult(
                success=False,
                model_id=None,
                spawn_id=active_spawn.spawn_id,
                vehicle_instance=None,
                reason="unknown_vehicle",
            )

        try:
            spawned_model_id = int(active_spawn.model_id)
        except ValueError:
            return CatchResult(
                success=False,
                model_id=None,
                spawn_id=active_spawn.spawn_id,
                vehicle_instance=None,
                reason="invalid_spawn_model",
            )

        if vehicle.id != spawned_model_id:
            return CatchResult(
                success=False,
                model_id=vehicle.id,
                spawn_id=active_spawn.spawn_id,
                vehicle_instance=None,
                reason="wrong_vehicle",
            )

        instance = self.instance_repository.create(
            vehicle_model_id=vehicle.id,
            owner_user_id=user_id,
            acquired_at=now,
        )

        resolved = self.spawn_manager.resolve_catch(
            server_id=server_id,
            model_id=active_spawn.model_id,
            now=now,
        )

        if not resolved:
            raise RuntimeError(
                "Spawn was lost after successful mint."
            )

        return CatchResult(
            success=True,
            model_id=vehicle.id,
            spawn_id=active_spawn.spawn_id,
            vehicle_instance=instance,
            reason="caught",
        )