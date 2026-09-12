import sqlite3

from .models import ServerConfig


class ServerConfigRepository:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS server_configs (
                    server_id INTEGER PRIMARY KEY,
                    spawn_channel_id INTEGER,
                    spawning_enabled INTEGER NOT NULL DEFAULT 0
                )
                """
            )
            connection.commit()

    def get(self, server_id: int) -> ServerConfig:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT server_id, spawn_channel_id, spawning_enabled
                FROM server_configs
                WHERE server_id = ?
                """,
                (server_id,),
            ).fetchone()

        if row is None:
            return ServerConfig(
                server_id=server_id,
                spawn_channel_id=None,
                spawning_enabled=False,
            )

        return ServerConfig(
            server_id=row["server_id"],
            spawn_channel_id=row["spawn_channel_id"],
            spawning_enabled=bool(row["spawning_enabled"]),
        )

    def upsert(
        self,
        *,
        server_id: int,
        spawn_channel_id: int | None,
        spawning_enabled: bool,
    ) -> ServerConfig:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO server_configs (
                    server_id,
                    spawn_channel_id,
                    spawning_enabled
                )
                VALUES (?, ?, ?)
                ON CONFLICT(server_id)
                DO UPDATE SET
                    spawn_channel_id = excluded.spawn_channel_id,
                    spawning_enabled = excluded.spawning_enabled
                """,
                (
                    server_id,
                    spawn_channel_id,
                    int(spawning_enabled),
                ),
            )
            connection.commit()

        return self.get(server_id)