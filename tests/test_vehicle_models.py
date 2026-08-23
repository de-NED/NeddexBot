from __future__ import annotations

import sqlite3

import pytest

from src.core.vehicles import VehicleModelRepository


@pytest.fixture
def repository(tmp_path):
    database_path = tmp_path / "test.db"

    repository = VehicleModelRepository(database_path)
    repository.initialize()

    return repository


def test_create_vehicle_model(repository):
    vehicle = repository.create(
        manufacturer="BMW",
        model_name="M4",
        year=2021,
        rarity_weight=0.01,
        spawn_image="https://example.com/m4-spawn.png",
        card_image="https://example.com/m4-card.png",
        enabled=True,
        spawn_eligible=True,
        limited=False,
        mint_limit=None,
        catch_names="bmw m4;m4",
    )

    assert vehicle.id == 1
    assert vehicle.manufacturer == "BMW"
    assert vehicle.model_name == "M4"
    assert vehicle.year == 2021
    assert vehicle.rarity_weight == 0.01
    assert vehicle.limited is False
    assert vehicle.mint_limit is None
    assert vehicle.highest_mint == 0


def test_catch_names_are_case_insensitive(repository):
    repository.create(
        manufacturer="BMW",
        model_name="M4",
        year=2021,
        rarity_weight=0.01,
        spawn_image=None,
        card_image=None,
        enabled=True,
        spawn_eligible=True,
        limited=False,
        mint_limit=None,
        catch_names="bmw m4;m4",
    )

    assert repository.find_by_catch_name("bmw m4") is not None
    assert repository.find_by_catch_name("BMW M4") is not None
    assert repository.find_by_catch_name("M4") is not None
    assert repository.find_by_catch_name("m4") is not None


def test_catch_names_are_exact(repository):
    repository.create(
        manufacturer="BMW",
        model_name="M4",
        year=2021,
        rarity_weight=0.01,
        spawn_image=None,
        card_image=None,
        enabled=True,
        spawn_eligible=True,
        limited=False,
        mint_limit=None,
        catch_names="bmw m4;m4",
    )

    assert repository.find_by_catch_name("bmw") is None
    assert repository.find_by_catch_name("bmw m4 competition") is None
    assert repository.find_by_catch_name("m-4") is None


def test_duplicate_catch_names_are_harmless(repository):
    vehicle = repository.create(
        manufacturer="BMW",
        model_name="M4",
        year=2021,
        rarity_weight=0.01,
        spawn_image=None,
        card_image=None,
        enabled=True,
        spawn_eligible=True,
        limited=False,
        mint_limit=None,
        catch_names="m4;m4;M4",
    )

    assert repository.find_by_catch_name("m4").id == vehicle.id


def test_whitespace_around_aliases_is_ignored(repository):
    vehicle = repository.create(
        manufacturer="BMW",
        model_name="M4",
        year=2021,
        rarity_weight=0.01,
        spawn_image=None,
        card_image=None,
        enabled=True,
        spawn_eligible=True,
        limited=False,
        mint_limit=None,
        catch_names=" bmw m4 ; m4 ",
    )

    assert repository.find_by_catch_name("BMW M4").id == vehicle.id
    assert repository.find_by_catch_name(" M4 ").id == vehicle.id


def test_disabled_model_cannot_be_caught(repository):
    repository.create(
        manufacturer="BMW",
        model_name="M4",
        year=2021,
        rarity_weight=0.01,
        spawn_image=None,
        card_image=None,
        enabled=False,
        spawn_eligible=True,
        limited=False,
        mint_limit=None,
        catch_names="bmw m4;m4",
    )

    assert repository.find_by_catch_name("m4") is None


def test_limited_model_requires_positive_supply(repository):
    with pytest.raises(ValueError):
        repository.create(
            manufacturer="BMW",
            model_name="M4",
            year=2021,
            rarity_weight=0.01,
            spawn_image=None,
            card_image=None,
            enabled=True,
            spawn_eligible=True,
            limited=True,
            mint_limit=None,
            catch_names="m4",
        )


def test_database_foreign_key_cascade(repository):
    vehicle = repository.create(
        manufacturer="BMW",
        model_name="M4",
        year=2021,
        rarity_weight=0.01,
        spawn_image=None,
        card_image=None,
        enabled=True,
        spawn_eligible=True,
        limited=False,
        mint_limit=None,
        catch_names="m4",
    )

    with sqlite3.connect(repository.database_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")

        connection.execute(
            "DELETE FROM vehicle_models WHERE id = ?",
            (vehicle.id,),
        )

        connection.commit()

        remaining = connection.execute(
            """
            SELECT COUNT(*)
            FROM vehicle_model_catch_names
            WHERE vehicle_model_id = ?
            """,
            (vehicle.id,),
        ).fetchone()[0]

    assert remaining == 0