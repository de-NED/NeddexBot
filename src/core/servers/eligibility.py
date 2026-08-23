from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ServerEligibility:
    """
    Determines whether a Discord server is eligible for Neddex spawning.

    This component does not inspect activity and does not start spawns.
    """

    minimum_human_members: int = 20
    main_server_id: int | None = None

    def is_eligible(
        self,
        *,
        server_id: int,
        human_member_count: int,
    ) -> bool:
        """
        Return whether the server can use the Neddex spawn system.
        """

        if self.main_server_id is not None and server_id == self.main_server_id:
            return True

        return human_member_count >= self.minimum_human_members