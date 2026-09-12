from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from src.core.activity import ActivityTracker
from src.core.servers import ServerConfig, ServerEligibility

from .engine import ActiveSpawn, SpawnEngine


@dataclass(frozen=True, slots=True)
class SpawnActivityResult:
    """Result of processing one Discord activity event."""

    counted: bool
    ready: bool
    spawned: ActiveSpawn | None


class SpawnCoordinator:
    """
    Coordinates server eligibility, human activity, and the SpawnEngine.

    The coordinator does not know anything about Discord UI, images,
    vehicle cards, ownership, or vehicle instances.
    """

    def __init__(
        self,
        *,
        eligibility: ServerEligibility,
        activity: ActivityTracker,
        engine: SpawnEngine,
    ) -> None:
        self.eligibility = eligibility
        self.activity = activity
        self.engine = engine

    def process_message(
        self,
        *,
        server_id: int,
        human_member_count: int,
        user_id: int,
        created_at: datetime,
        is_bot: bool = False,
        is_webhook: bool = False,
        is_command: bool = False,
        server_config: ServerConfig | None = None,
    ) -> SpawnActivityResult:
        """
        Process one Discord activity event.

        Activity only contributes toward a new spawn when there is
        currently no active spawn.
        """

        if not self.eligibility.is_eligible(
            server_id=server_id,
            human_member_count=human_member_count,
            server_config=server_config,
        ):
            return SpawnActivityResult(
                counted=False,
                ready=False,
                spawned=None,
            )

        if self.engine.active_spawn is not None:
            if created_at < self.engine.active_spawn.expires_at:
                return SpawnActivityResult(
                    counted=False,
                    ready=False,
                    spawned=None,
                )

            self.engine.expire_if_needed(created_at)

        counted = self.activity.record_message(
            user_id=user_id,
            created_at=created_at,
            is_bot=is_bot,
            is_webhook=is_webhook,
            is_command=is_command,
        )

        if not counted:
            return SpawnActivityResult(
                counted=False,
                ready=self.activity.is_ready(),
                spawned=None,
            )

        if not self.activity.is_ready():
            return SpawnActivityResult(
                counted=True,
                ready=False,
                spawned=None,
            )

        spawn = self.engine.create_spawn(created_at)

        if spawn is None:
            return SpawnActivityResult(
                counted=True,
                ready=True,
                spawned=None,
            )

        self.activity.reset()

        return SpawnActivityResult(
            counted=True,
            ready=True,
            spawned=spawn,
        )

    def expire_spawn(self, now: datetime) -> bool:
        """Expire the active spawn when its catch window has ended."""

        return self.engine.expire_if_needed(now)