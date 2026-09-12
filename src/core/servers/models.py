from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ServerConfig:
    server_id: int
    spawn_channel_id: int | None
    spawning_enabled: bool