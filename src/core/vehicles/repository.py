from __future__ import annotations

import sqlite3
from pathlib import Path

from .models import VehicleModel


class VehicleModelRepository:
    """Database access for Vehicle Model entities."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize(self) -> None:
        """Create the Vehicle Model tables if they do not exist."""

        self.database_path.parent.mkdir(parents=True, exist_ok=True)

        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS vehicle_models (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    manufacturer TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    year INTEGER,
                    rarity_weight REAL NOT NULL CHECK (rarity_weight > 0),
                    spawn_image TEXT,
                    card_image TEXT,
                    enabled INTEGER NOT NULL DEFAULT 1,
                    spawn_eligible INTEGER NOT NULL DEFAULT 1,
                    limited INTEGER NOT NULL DEFAULT 0,
                    mint_limit INTEGER,
                    highest_mint INTEGER NOT NULL DEFAULT 0,
                    CHECK (
                        (limited = 0 AND mint_limit IS NULL)
                        OR
                        (limited = 1 AND mint_limit IS NOT NULL AND mint_limit > 0)
                    ),
                    CHECK (
                        highest_mint >= 0
                    ),
                    CHECK (
                        mint_limit IS NULL OR highest_mint <= mint_limit
                    )
                )
                """
            )

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS vehicle_model_catch_names (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vehicle_model_id INTEGER NOT NULL,
                    catch_name TEXT NOT NULL,
                    normalized_name TEXT NOT NULL,
                    FOREIGN KEY (vehicle_model_id)
                        REFERENCES vehicle_models(id)
                        ON DELETE CASCADE
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_vehicle_model_catch_names_lookup
                ON vehicle_model_catch_names(normalized_name)
                """
            )

            connection.commit()

    def create(
        self,
        manufacturer: str,
        model_name: str,
        year: int | None,
        rarity_weight: float,
        spawn_image: str | None,
        card_image: str | None,
        enabled: bool,
        spawn_eligible: bool,
        limited: bool,
        mint_limit: int | None,
        catch_names: str,
    ) -> VehicleModel:
        """Create a Vehicle Model and its catch names."""

        manufacturer = manufacturer.strip()
        model_name = model_name.strip()

        if not manufacturer:
            raise ValueError("Manufacturer cannot be empty.")

        if not model_name:
            raise ValueError("Model name cannot be empty.")

        if rarity_weight <= 0:
            raise ValueError("Rarity weight must be greater than zero.")

        if limited:
            if mint_limit is None or mint_limit <= 0:
                raise ValueError(
                    "A limited vehicle model requires a positive mint limit."
                )
        else:
            mint_limit = None

        parsed_catch_names = self._parse_catch_names(catch_names)

        if not parsed_catch_names:
            raise ValueError("At least one catch name is required.")

        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO vehicle_models (
                    manufacturer,
                    model_name,
                    year,
                    rarity_weight,
                    spawn_image,
                    card_image,
                    enabled,
                    spawn_eligible,
                    limited,
                    mint_limit,
                    highest_mint
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                """,
                (
                    manufacturer,
                    model_name,
                    year,
                    rarity_weight,
                    spawn_image,
                    card_image,
                    int(enabled),
                    int(spawn_eligible),
                    int(limited),
                    mint_limit,
                ),
            )

            vehicle_model_id = cursor.lastrowid

            if vehicle_model_id is None:
                raise RuntimeError("Failed to create Vehicle Model.")

            for catch_name in parsed_catch_names:
                connection.execute(
                    """
                    INSERT INTO vehicle_model_catch_names (
                        vehicle_model_id,
                        catch_name,
                        normalized_name
                    )
                    VALUES (?, ?, ?)
                    """,
                    (
                        vehicle_model_id,
                        catch_name,
                        self._normalize_catch_name(catch_name),
                    ),
                )

            connection.commit()

        return self.get(vehicle_model_id)

    def update(
        self,
        vehicle_model_id: int,
        manufacturer: str,
        model_name: str,
        year: int | None,
        rarity_weight: float,
        spawn_image: str | None,
        card_image: str | None,
        enabled: bool,
        spawn_eligible: bool,
        limited: bool,
        mint_limit: int | None,
        catch_names: str,
    ) -> VehicleModel:
        """Update a Vehicle Model and its catch names."""

        manufacturer = manufacturer.strip()
        model_name = model_name.strip()

        if not manufacturer:
            raise ValueError("Manufacturer cannot be empty.")

        if not model_name:
            raise ValueError("Model name cannot be empty.")

        if rarity_weight <= 0:
            raise ValueError("Rarity weight must be greater than zero.")

        if limited:
            if mint_limit is None or mint_limit <= 0:
                raise ValueError(
                    "A limited vehicle model requires a positive mint limit."
                )
        else:
            mint_limit = None

        parsed_catch_names = self._parse_catch_names(catch_names)

        if not parsed_catch_names:
            raise ValueError("At least one catch name is required.")

        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT highest_mint
                FROM vehicle_models
                WHERE id = ?
                """,
                (vehicle_model_id,),
            ).fetchone()

            if row is None:
                raise LookupError(
                    f"Vehicle Model {vehicle_model_id} does not exist."
                )

            highest_mint = row["highest_mint"]

            if mint_limit is not None and highest_mint > mint_limit:
                raise ValueError(
                    "Mint limit cannot be lower than the current highest mint."
                )

            connection.execute(
                """
                UPDATE vehicle_models
                SET
                    manufacturer = ?,
                    model_name = ?,
                    year = ?,
                    rarity_weight = ?,
                    spawn_image = ?,
                    card_image = ?,
                    enabled = ?,
                    spawn_eligible = ?,
                    limited = ?,
                    mint_limit = ?
                WHERE id = ?
                """,
                (
                    manufacturer,
                    model_name,
                    year,
                    rarity_weight,
                    spawn_image,
                    card_image,
                    int(enabled),
                    int(spawn_eligible),
                    int(limited),
                    mint_limit,
                    vehicle_model_id,
                ),
            )

            connection.execute(
                """
                DELETE FROM vehicle_model_catch_names
                WHERE vehicle_model_id = ?
                """,
                (vehicle_model_id,),
            )

            for catch_name in parsed_catch_names:
                connection.execute(
                    """
                    INSERT INTO vehicle_model_catch_names (
                        vehicle_model_id,
                        catch_name,
                        normalized_name
                    )
                    VALUES (?, ?, ?)
                    """,
                    (
                        vehicle_model_id,
                        catch_name,
                        self._normalize_catch_name(catch_name),
                    ),
                )

            connection.commit()

        return self.get(vehicle_model_id)

    def get(self, vehicle_model_id: int) -> VehicleModel:
        """Retrieve a Vehicle Model by its internal ID."""

        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    id,
                    manufacturer,
                    model_name,
                    year,
                    rarity_weight,
                    spawn_image,
                    card_image,
                    enabled,
                    spawn_eligible,
                    limited,
                    mint_limit,
                    highest_mint
                FROM vehicle_models
                WHERE id = ?
                """,
                (vehicle_model_id,),
            ).fetchone()

        if row is None:
            raise LookupError(
                f"Vehicle Model {vehicle_model_id} does not exist."
            )

        return VehicleModel(
            id=row["id"],
            manufacturer=row["manufacturer"],
            model_name=row["model_name"],
            year=row["year"],
            rarity_weight=row["rarity_weight"],
            spawn_image=row["spawn_image"],
            card_image=row["card_image"],
            enabled=bool(row["enabled"]),
            spawn_eligible=bool(row["spawn_eligible"]),
            limited=bool(row["limited"]),
            mint_limit=row["mint_limit"],
            highest_mint=row["highest_mint"],
        )


    def delete(self, vehicle_model_id: int) -> None:
        """Delete a Vehicle Model if it has no minted instances."""

        with self._connect() as connection:
            try:
                cursor = connection.execute(
                    """
                    DELETE FROM vehicle_models
                    WHERE id = ?
                    """,
                    (vehicle_model_id,),
                )

                if cursor.rowcount == 0:
                    raise LookupError(
                        f"Vehicle Model {vehicle_model_id} does not exist."
                    )

                connection.commit()

            except sqlite3.IntegrityError as exc:
                connection.rollback()
                raise ValueError(
                    f"Vehicle Model {vehicle_model_id} cannot be deleted "
                    "because it has minted vehicle instances."
                ) from exc

    def list_all(self) -> list[VehicleModel]:
        """Return all Vehicle Models for administrative use."""

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    id,
                    manufacturer,
                    model_name,
                    year,
                    rarity_weight,
                    spawn_image,
                    card_image,
                    enabled,
                    spawn_eligible,
                    limited,
                    mint_limit,
                    highest_mint
                FROM vehicle_models
                ORDER BY id
                """
            ).fetchall()

        return [
            VehicleModel(
                id=row["id"],
                manufacturer=row["manufacturer"],
                model_name=row["model_name"],
                year=row["year"],
                rarity_weight=row["rarity_weight"],
                spawn_image=row["spawn_image"],
                card_image=row["card_image"],
                enabled=bool(row["enabled"]),
                spawn_eligible=bool(row["spawn_eligible"]),
                limited=bool(row["limited"]),
                mint_limit=row["mint_limit"],
                highest_mint=row["highest_mint"],
            )
            for row in rows
        ]

    def list_page(
        self,
        *,
        limit: int,
        offset: int,
        search: str | None = None,
        enabled: bool | None = None,
        spawn_eligible: bool | None = None,
    ) -> tuple[list[VehicleModel], int]:
        """Return a filtered page of Vehicle Models and total match count."""

        if limit < 1:
            raise ValueError("Limit must be greater than zero.")

        if offset < 0:
            raise ValueError("Offset cannot be negative.")

        normalized_search = search.strip().casefold() if search else None

        where_clauses: list[str] = []
        parameters: list[object] = []

        if normalized_search:
            where_clauses.append(
                """
                lower(manufacturer || ' ' || model_name) LIKE ?
                """
            )
            parameters.append(f"%{normalized_search}%")

        if enabled is not None:
            where_clauses.append("enabled = ?")
            parameters.append(int(enabled))

        if spawn_eligible is not None:
            where_clauses.append("spawn_eligible = ?")
            parameters.append(int(spawn_eligible))

        where_sql = ""

        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)

        with self._connect() as connection:
            total = connection.execute(
                f"""
                SELECT COUNT(*)
                FROM vehicle_models
                {where_sql}
                """,
                parameters,
            ).fetchone()[0]

            rows = connection.execute(
                f"""
                SELECT
                    id,
                    manufacturer,
                    model_name,
                    year,
                    rarity_weight,
                    spawn_image,
                    card_image,
                    enabled,
                    spawn_eligible,
                    limited,
                    mint_limit,
                    highest_mint
                FROM vehicle_models
                {where_sql}
                ORDER BY id
                LIMIT ? OFFSET ?
                """,
                [*parameters, limit, offset],
            ).fetchall()

        vehicles = [
            VehicleModel(
                id=row["id"],
                manufacturer=row["manufacturer"],
                model_name=row["model_name"],
                year=row["year"],
                rarity_weight=row["rarity_weight"],
                spawn_image=row["spawn_image"],
                card_image=row["card_image"],
                enabled=bool(row["enabled"]),
                spawn_eligible=bool(row["spawn_eligible"]),
                limited=bool(row["limited"]),
                mint_limit=row["mint_limit"],
                highest_mint=row["highest_mint"],
            )
            for row in rows
        ]

        return vehicles, total

    def find_by_catch_name(
        self,
        submitted_name: str,
    ) -> VehicleModel | None:
        """Find a model using an exact, case-insensitive catch name."""

        normalized_name = self._normalize_catch_name(submitted_name)

        if not normalized_name:
            return None

        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    vehicle_models.id
                FROM vehicle_model_catch_names
                INNER JOIN vehicle_models
                    ON vehicle_models.id =
                       vehicle_model_catch_names.vehicle_model_id
                WHERE vehicle_model_catch_names.normalized_name = ?
                  AND vehicle_models.enabled = 1
                LIMIT 1
                """,
                (normalized_name,),
            ).fetchone()

        if row is None:
            return None

        return self.get(row["id"])

    def set_highest_mint(
        self,
        vehicle_model_id: int,
        highest_mint: int,
    ) -> VehicleModel:
        """
        Set the highest assigned mint for a Vehicle Model.

        This is intentionally validated against the model's mint limit.
        """

        if highest_mint < 0:
            raise ValueError("Highest mint cannot be negative.")

        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT mint_limit
                FROM vehicle_models
                WHERE id = ?
                """,
                (vehicle_model_id,),
            ).fetchone()

            if row is None:
                raise LookupError(
                    f"Vehicle Model {vehicle_model_id} does not exist."
                )

            mint_limit = row["mint_limit"]

            if mint_limit is not None and highest_mint > mint_limit:
                raise ValueError(
                    "Highest mint cannot exceed the model's mint limit."
                )

            connection.execute(
                """
                UPDATE vehicle_models
                SET highest_mint = ?
                WHERE id = ?
                """,
                (
                    highest_mint,
                    vehicle_model_id,
                ),
            )

            connection.commit()

        return self.get(vehicle_model_id)

    def get_spawn_eligible_models(self) -> list[VehicleModel]:
        """
        Return Vehicle Models that are currently allowed to participate
        in the global spawn pool.

        Disabled models, manually excluded models, and exhausted limited
        models are excluded.
        """

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    id,
                    manufacturer,
                    model_name,
                    year,
                    rarity_weight,
                    spawn_image,
                    card_image,
                    enabled,
                    spawn_eligible,
                    limited,
                    mint_limit,
                    highest_mint
                FROM vehicle_models
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
            VehicleModel(
                id=row["id"],
                manufacturer=row["manufacturer"],
                model_name=row["model_name"],
                year=row["year"],
                rarity_weight=row["rarity_weight"],
                spawn_image=row["spawn_image"],
                card_image=row["card_image"],
                enabled=bool(row["enabled"]),
                spawn_eligible=bool(row["spawn_eligible"]),
                limited=bool(row["limited"]),
                mint_limit=row["mint_limit"],
                highest_mint=row["highest_mint"],
            )
            for row in rows
        ]

    @staticmethod
    def _parse_catch_names(catch_names: str) -> list[str]:
        """Split the admin catch-name field into individual names."""

        names: list[str] = []

        for raw_name in catch_names.split(";"):
            name = raw_name.strip()

            if name:
                names.append(name)

        return names

    @staticmethod
    def _normalize_catch_name(catch_name: str) -> str:
        """Normalize only what the Core has explicitly agreed to normalize."""

        return catch_name.strip().casefold()