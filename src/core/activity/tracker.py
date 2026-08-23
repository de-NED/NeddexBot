from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
import random


@dataclass(slots=True)
class ActivityTracker:
    """
    Tracks legitimate human activity for the Neddex spawn system.

    The tracker does not know anything about vehicles or spawning.
    It only determines when enough qualifying activity has occurred.
    """

    activity_cooldown: timedelta = timedelta(seconds=10)
    rng: random.Random = field(default_factory=random.Random)

    required_activity: int = field(init=False)
    activity_count: int = field(default=0, init=False)
    last_activity_by_user: dict[int, datetime] = field(
        default_factory=dict,
        init=False,
    )

    def __post_init__(self) -> None:
        self.required_activity = self._random_requirement()

    def record_message(
        self,
        *,
        user_id: int,
        created_at: datetime,
        is_bot: bool = False,
        is_webhook: bool = False,
        is_command: bool = False,
    ) -> bool:
        """
        Record a qualifying human message.

        Returns True when the message contributed activity.
        """

        if is_bot or is_webhook or is_command:
            return False

        last_activity = self.last_activity_by_user.get(user_id)

        if last_activity is not None:
            if created_at - last_activity < self.activity_cooldown:
                return False

        self.last_activity_by_user[user_id] = created_at
        self.activity_count += 1

        return True

    def is_ready(self) -> bool:
        """Return whether enough activity has accumulated."""

        return self.activity_count >= self.required_activity

    def reset(self) -> None:
        """Reset activity tracking for a new spawn opportunity."""

        self.activity_count = 0
        self.required_activity = self._random_requirement()
        self.last_activity_by_user.clear()

    def _random_requirement(self) -> int:
        """Choose the next activity requirement between 1 and 3."""

        return self.rng.randint(1, 3)