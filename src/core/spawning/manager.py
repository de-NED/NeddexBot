from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import random

from src.core.activity import ActivityTracker
from src.core.servers import ServerEligibility

from .coordinator import SpawnActivityResult, SpawnCoordinator
from .engine import ActiveSpawn, SpawnEngine, SpawnModelSource


@dataclass(slots=True)
class ServerSpawnState:
    """All mutable spawn state belonging to one Discord server."""

    activity: ActivityTracker
    engine: SpawnEngine


class SpawnManager:
    """
    Owns independent spawn state for every Discord server.

    No activity, cooldown, or active spawn is shared between servers.
    """

    def __init__(
        self,
        *,
        eligibility: ServerEligibility,
        model_source: SpawnModelSource,
        activity_cooldown: timedelta = timedelta(seconds=10),
        spawn_cooldown: timedelta = timedelta(minutes=30),
        catch_window: timedelta = timedelta(minutes=2),
        rng: random.Random | None = None,
    ) -> None:
        self.eligibility = eligibility
        self.model_source = model_source
        self.activity_cooldown = activity_cooldown
        self.spawn_cooldown = spawn_cooldown
        self.catch_window = catch_window
        self.rng = rng or random.Random()

        self._states: dict[int, ServerSpawnState] = {}

    def _create_state(self) -> ServerSpawnState:
        """Create completely independent state for one server."""

        state_rng = random.Random(self.rng.getrandbits(64))

        activity = ActivityTracker(
            activity_cooldown=self.activity_cooldown,
            rng=random.Random(state_rng.getrandbits(64)),
        )

        engine = SpawnEngine(
            self.model_source,
            spawn_cooldown=self.spawn_cooldown,
            catch_window=self.catch_window,
            rng=random.Random(state_rng.getrandbits(64)),
        )

        return ServerSpawnState(
            activity=activity,
            engine=engine,
        )

    def get_state(self, server_id: int) -> ServerSpawnState:
        """Return the persistent state for a server."""

        if server_id not in self._states:
            self._states[server_id] = self._create_state()

        return self._states[server_id]

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
    ) -> SpawnActivityResult:
        """Process activity using only this server's state."""

        state = self.get_state(server_id)

        coordinator = SpawnCoordinator(
            eligibility=self.eligibility,
            activity=state.activity,
            engine=state.engine,
        )

        return coordinator.process_message(
            server_id=server_id,
            human_member_count=human_member_count,
            user_id=user_id,
            created_at=created_at,
            is_bot=is_bot,
            is_webhook=is_webhook,
            is_command=is_command,
        )

    def get_active_spawn(self, server_id: int) -> ActiveSpawn | None:
        """Return the active spawn for one server, if any."""

        return self.get_state(server_id).engine.active_spawn

    def expire_spawn(
        self,
        *,
        server_id: int,
        now: datetime,
    ) -> bool:
        """Expire the active spawn for one server."""

        return self.get_state(server_id).engine.expire_if_needed(now)

    def resolve_catch(
        self,
        *,
        server_id: int,
        model_id: str,
        now: datetime,
    ) -> bool:
        """Resolve a catch against this server's active spawn."""

        return self.get_state(server_id).engine.resolve_catch(
            model_id=model_id,
            now=now,
        )