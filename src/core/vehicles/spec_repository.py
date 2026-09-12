from __future__ import annotations

import sqlite3
from pathlib import Path

from .specs import VehicleSpec


class VehicleSpecRepository:
    """
    Database access for Vehicle Specs.

    A spec is the collectible unit.

    Example:
    BMW M4 Competition CSL
    """

    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute(
            "PRAGMA foreign_keys = ON"
        )
        return connection

    def initialize(self) -> None:
        """
        Create vehicle_specs table.
        """

        self.database_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS vehicle_specs (

                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    vehicle_model_id INTEGER NOT NULL,

                    name TEXT NOT NULL,

                    rarity_weight REAL NOT NULL
                        CHECK(rarity_weight > 0),

                    spawn_image TEXT,

                    card_id INTEGER,

                    enabled INTEGER NOT NULL DEFAULT 1,

                    spawn_eligible INTEGER NOT NULL DEFAULT 1,

                    limited INTEGER NOT NULL DEFAULT 0,

                    mint_limit INTEGER,

                    highest_mint INTEGER NOT NULL DEFAULT 0,

                    CHECK(
                        (limited = 0 AND mint_limit IS NULL)
                        OR
                        (limited = 1
                        AND mint_limit IS NOT NULL
                        AND mint_limit > 0)
                    ),

                    CHECK(
                        highest_mint >= 0
                    ),

                    CHECK(
                        mint_limit IS NULL
                        OR highest_mint <= mint_limit
                    ),

                    FOREIGN KEY(vehicle_model_id)
                    REFERENCES vehicle_models(id)
                    ON DELETE RESTRICT

                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_vehicle_specs_spawn
                ON vehicle_specs(spawn_eligible)
                """
            )

            connection.commit()

    def create(
        self,
        *,
        vehicle_model_id: int,
        name: str,
        rarity_weight: float,
        spawn_image: str | None,
        card_id: int | None,
        enabled: bool = True,
        spawn_eligible: bool = True,
        limited: bool = False,
        mint_limit: int | None = None,
    ) -> VehicleSpec:
        """
        Create a new vehicle spec.
        """

        name = name.strip()

        if vehicle_model_id <= 0:
            raise ValueError(
                "vehicle_model_id must be positive"
            )

        if not name:
            raise ValueError(
                "Spec name cannot be empty."
            )

        if rarity_weight <= 0:
            raise ValueError(
                "rarity_weight must be positive"
            )

        if limited:
            if mint_limit is None or mint_limit <= 0:
                raise ValueError(
                    "limited specs must have a positive mint_limit"
                )
        else:
            mint_limit = None

        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO vehicle_specs (
                    vehicle_model_id,
                    name,
                    rarity_weight,
                    spawn_image,
                    card_id,
                    enabled,
                    spawn_eligible,
                    limited,
                    mint_limit,
                    highest_mint
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                """,
                (
                    vehicle_model_id,
                    name,
                    rarity_weight,
                    spawn_image,
                    card_id,
                    int(enabled),
                    int(spawn_eligible),
                    int(limited),
                    mint_limit,
                ),
            )

            spec_id = cursor.lastrowid

            if spec_id is None:
                raise RuntimeError(
                    "Failed to create Vehicle Spec."
                )

            connection.commit()

        return VehicleSpec(
            id=spec_id,
            vehicle_model_id=vehicle_model_id,
            name=name,
            rarity_weight=rarity_weight,
            spawn_image=spawn_image,
            card_id=card_id,
            enabled=enabled,
            spawn_eligible=spawn_eligible,
            limited=limited,
            mint_limit=mint_limit,
            highest_mint=0,
        )

    def get_spawn_eligible_specs(self) -> list[VehicleSpec]:
        """
        Return Vehicle Specs currently allowed in the spawn pool.
        """

        with self._connect() as connection:
            rows = connection.execute(
               """
                SELECT
                    id,
                    vehicle_model_id,
                    name,
                    rarity_weight,
                    spawn_image,
                    card_id,
                    enabled,
                    spawn_eligible,
                    limited,
                    mint_limit,
                    highest_mint
                FROM vehicle_specs
                WHERE enabled = 1
                  AND spawn_eligible = 1
                  AND rarity_weight > 0
                  AND (
                        limited = 0
                        OR highest_mint < mint_limit
                  )
                ORDER BY id
                """
            ).fetchall()

        return [
            VehicleSpec(
                id=row["id"],
                vehicle_model_id=row["vehicle_model_id"],
                name=row["name"],
                rarity_weight=row["rarity_weight"],
                spawn_image=row["spawn_image"],
                card_id=row["card_id"],
                enabled=bool(row["enabled"]),
                spawn_eligible=bool(row["spawn_eligible"]),
                limited=bool(row["limited"]),
                mint_limit=row["mint_limit"],
                highest_mint=row["highest_mint"],
            )
            for row in rows
        ]