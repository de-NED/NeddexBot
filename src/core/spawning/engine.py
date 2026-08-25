from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import random
from typing import Protocol


@dataclass(frozen=True, slots=True)
class SpawnCandidate:
    """A vehicle model that can currently participate in spawning."""

    model_id: str
    weight: float


@dataclass(frozen=True, slots=True)
class ActiveSpawn:
    """Represents one currently active vehicle spawn."""

    spawn_id: str
    model_id: str
    created_at: datetime
    expires_at: datetime


class SpawnModelSource(Protocol):
    """Interface required by the SpawnEngine to obtain eligible models."""

    def get_spawn_candidates(self) -> list[SpawnCandidate]:
        ...


class SpawnEngine:
    """
    Pure Core spawn engine.

    Responsibilities:
    - enforce the spawn cooldown
    - maintain one active spawn
    - select an eligible vehicle model
    - create an active spawn
    - determine whether a spawn has expired
    - resolve successful catches
    - claim and restore catches safely

    It does NOT:
    - inspect Discord messages
    - inspect server membership
    - manage images
    - manage vehicle instances
    - assign ownership
    - create mints
    """

    def __init__(
        self,
        model_source: SpawnModelSource,
        *,
        spawn_cooldown: timedelta = timedelta(minutes=30),
        catch_window: timedelta = timedelta(minutes=2),
        rng: random.Random | None = None,
    ) -> None:
        if spawn_cooldown < timedelta(0):
            raise ValueError("spawn_cooldown cannot be negative")

        if catch_window <= timedelta(0):
            raise ValueError("catch_window must be greater than zero")

        self.model_source = model_source
        self.spawn_cooldown = spawn_cooldown
        self.catch_window = catch_window
        self.rng = rng or random.Random()

        self.active_spawn: ActiveSpawn | None = None
        self.last_spawn_at: datetime | None = None

    def can_spawn(self, now: datetime) -> bool:
        """
        Return whether a new spawn can currently be created.
        """

        if self.active_spawn is not None:
            if now < self.active_spawn.expires_at:
                return False

            self.active_spawn = None

        if self.last_spawn_at is None:
            return True

        return now >= self.last_spawn_at + self.spawn_cooldown

    def create_spawn(self, now: datetime) -> ActiveSpawn | None:
        """
        Create a new spawn if the engine is ready.

        Returns None when spawning is currently unavailable or no eligible
        vehicle models exist.
        """

        if not self.can_spawn(now):
            return None

        candidates = [
            candidate
            for candidate in self.model_source.get_spawn_candidates()
            if candidate.weight > 0
        ]

        if not candidates:
            return None

        selected = self._weighted_choice(candidates)

        spawn = ActiveSpawn(
            spawn_id=self._create_spawn_id(),
            model_id=selected.model_id,
            created_at=now,
            expires_at=now + self.catch_window,
        )

        self.active_spawn = spawn
        self.last_spawn_at = now

        return spawn

    def is_expired(self, now: datetime) -> bool:
        """Return whether the current spawn has expired."""

        if self.active_spawn is None:
            return False

        return now >= self.active_spawn.expires_at

    def expire_if_needed(self, now: datetime) -> bool:
        """
        Expire the active spawn if its catch window has ended.

        Returns True if a spawn was expired.
        """

        if not self.is_expired(now):
            return False

        self.active_spawn = None
        return True

    def resolve_catch(
        self,
        *,
        model_id: str,
        now: datetime,
    ) -> bool:
        """
        Resolve a valid catch against the active spawn.

        Returns True only when the supplied model matches the active spawn
        and the catch occurs before expiration.

        Deprecated in favor of claim_catch() for catch flows that need
        recovery if vehicle minting fails.
        """

        claimed = self.claim_catch(
            model_id=model_id,
            now=now,
        )

        return claimed is not None

    def claim_catch(
        self,
        *,
        model_id: str,
        now: datetime,
    ) -> ActiveSpawn | None:
        """
        Claim and remove a valid active spawn.

        Returns the claimed spawn when successful.
        Returns None when no valid matching spawn exists.
        """

        if self.active_spawn is None:
            return None

        if now >= self.active_spawn.expires_at:
            self.active_spawn = None
            return None

        if model_id != self.active_spawn.model_id:
            return None

        claimed = self.active_spawn
        self.active_spawn = None

        return claimed

    def restore_spawn(
        self,
        spawn: ActiveSpawn,
    ) -> None:
        """
        Restore a previously claimed spawn.

        A restore is only valid when there is currently no active spawn.
        """

        if self.active_spawn is not None:
            raise RuntimeError(
                "Cannot restore spawn while another spawn is active."
            )

        self.active_spawn = spawn

    def _weighted_choice(
        self,
        candidates: list[SpawnCandidate],
    ) -> SpawnCandidate:
        total_weight = sum(candidate.weight for candidate in candidates)

        if total_weight <= 0:
            raise ValueError("Total spawn weight must be greater than zero")

        target = self.rng.uniform(0, total_weight)
        cumulative = 0.0

        for candidate in candidates:
            cumulative += candidate.weight

            if target <= cumulative:
                return candidate

        return candidates[-1]

    def _create_spawn_id(self) -> str:
        return f"spawn-{self.rng.getrandbits(64):016x}"
