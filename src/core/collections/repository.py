from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from .models import VehicleInstance


class VehicleInstanceRepository:
    """Database access for individually owned vehicle instances."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize(self) -> None:
        """Create the vehicle instance table."""

        self.database_path.parent.mkdir(parents=True, exist_ok=True)

        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS vehicle_instances (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vehicle_model_id INTEGER NOT NULL,
                    owner_user_id INTEGER NOT NULL,
                    mint_number INTEGER NOT NULL,
                    acquired_at TEXT NOT NULL,
                    UNIQUE(vehicle_model_id, mint_number),
                    FOREIGN KEY (vehicle_model_id)
                        REFERENCES vehicle_models(id)
                        ON DELETE RESTRICT
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_vehicle_instances_owner
                ON vehicle_instances(owner_user_id)
                """
            )

            connection.commit()

    def create(
        self,
        *,
        vehicle_model_id: int,
        owner_user_id: int,
        acquired_at: datetime,
    ) -> VehicleInstance:
        """
        Mint one vehicle instance.

        The model's highest_mint is advanced in the same transaction
        as the instance creation.
        """

        if owner_user_id <= 0:
            raise ValueError("owner_user_id must be positive")

        with self._connect() as connection:
            model = connection.execute(
                """
                SELECT
                    id,
                    limited,
                    mint_limit,
                    highest_mint
                FROM vehicle_models
                WHERE id = ?
                """,
                (vehicle_model_id,),
            ).fetchone()

            if model is None:
                raise LookupError(
                    f"Vehicle Model {vehicle_model_id} does not exist."
                )

            if model["limited"] and model["highest_mint"] >= model["mint_limit"]:
                raise ValueError("Vehicle Model mint supply is exhausted.")

            next_mint = model["highest_mint"] + 1

            connection.execute(
                """
                UPDATE vehicle_models
                SET highest_mint = ?
                WHERE id = ?
                """,
                (next_mint, vehicle_model_id),
            )

            cursor = connection.execute(
                """
                INSERT INTO vehicle_instances (
                    vehicle_model_id,
                    owner_user_id,
                    mint_number,
                    acquired_at
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    vehicle_model_id,
                    owner_user_id,
                    next_mint,
                    acquired_at.isoformat(),
                ),
            )

            instance_id = cursor.lastrowid

            if instance_id is None:
                raise RuntimeError(
                    "Failed to create Vehicle Instance."
                )

            connection.commit()

        return self.get(instance_id)

    def get(self, instance_id: int) -> VehicleInstance:
        """Retrieve one vehicle instance."""

        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    id,
                    vehicle_model_id,
                    owner_user_id,
                    mint_number,
                    acquired_at
                FROM vehicle_instances
                WHERE id = ?
                """,
                (instance_id,),
            ).fetchone()

        if row is None:
            raise LookupError(
                f"Vehicle Instance {instance_id} does not exist."
            )

        return VehicleInstance(
            id=row["id"],
            vehicle_model_id=row["vehicle_model_id"],
            owner_user_id=row["owner_user_id"],
            mint_number=row["mint_number"],
            acquired_at=datetime.fromisoformat(row["acquired_at"]),
        )

    def list_for_owner(
        self,
        owner_user_id: int,
    ) -> list[VehicleInstance]:
        """Return all vehicle instances owned by one user."""

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    id,
                    vehicle_model_id,
                    owner_user_id,
                    mint_number,
                    acquired_at
                FROM vehicle_instances
                WHERE owner_user_id = ?
                ORDER BY id
                """,
                (owner_user_id,),
            ).fetchall()

        return [
            VehicleInstance(
                id=row["id"],
                vehicle_model_id=row["vehicle_model_id"],
                owner_user_id=row["owner_user_id"],
                mint_number=row["mint_number"],
                acquired_at=datetime.fromisoformat(row["acquired_at"]),
            )
            for row in rows
        ]