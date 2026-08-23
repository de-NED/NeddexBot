from datetime import datetime

import pytest

from src.core.collections import VehicleInstanceRepository
from src.core.vehicles import VehicleModelRepository


BASE_TIME = datetime(2026, 1, 1, 12, 0, 0)


@pytest.fixture
def repositories(tmp_path):
    database_path = tmp_path / "test.db"

    models = VehicleModelRepository(database_path)
    models.initialize()

    instances = VehicleInstanceRepository(database_path)
    instances.initialize()

    return models, instances


def create_unlimited_model(models):
    return models.create(
        manufacturer="BMW",
        model_name="M4",
        year=2024,
        rarity_weight=1.0,
        spawn_image=None,
        card_image=None,
        enabled=True,
        spawn_eligible=True,
        limited=False,
        mint_limit=None,
        catch_names="bmw m4;m4",
    )


def create_limited_model(models, mint_limit=2):
    return models.create(
        manufacturer="Porsche",
        model_name="911",
        year=2024,
        rarity_weight=1.0,
        spawn_image=None,
        card_image=None,
        enabled=True,
        spawn_eligible=True,
        limited=True,
        mint_limit=mint_limit,
        catch_names="porsche 911;911",
    )


def test_create_vehicle_instance(repositories):
    models, instances = repositories
    model = create_unlimited_model(models)

    vehicle = instances.create(
        vehicle_model_id=model.id,
        owner_user_id=123,
        acquired_at=BASE_TIME,
    )

    assert vehicle.id == 1
    assert vehicle.vehicle_model_id == model.id
    assert vehicle.owner_user_id == 123
    assert vehicle.mint_number == 1
    assert vehicle.acquired_at == BASE_TIME


def test_first_mint_is_one(repositories):
    models, instances = repositories
    model = create_unlimited_model(models)

    vehicle = instances.create(
        vehicle_model_id=model.id,
        owner_user_id=123,
        acquired_at=BASE_TIME,
    )

    assert vehicle.mint_number == 1
    assert models.get(model.id).highest_mint == 1


def test_mints_increment(repositories):
    models, instances = repositories
    model = create_unlimited_model(models)

    first = instances.create(
        vehicle_model_id=model.id,
        owner_user_id=123,
        acquired_at=BASE_TIME,
    )

    second = instances.create(
        vehicle_model_id=model.id,
        owner_user_id=456,
        acquired_at=BASE_TIME,
    )

    assert first.mint_number == 1
    assert second.mint_number == 2
    assert models.get(model.id).highest_mint == 2


def test_limited_supply_is_enforced(repositories):
    models, instances = repositories
    model = create_limited_model(models, mint_limit=2)

    instances.create(
        vehicle_model_id=model.id,
        owner_user_id=123,
        acquired_at=BASE_TIME,
    )

    instances.create(
        vehicle_model_id=model.id,
        owner_user_id=456,
        acquired_at=BASE_TIME,
    )

    with pytest.raises(ValueError, match="exhausted"):
        instances.create(
            vehicle_model_id=model.id,
            owner_user_id=789,
            acquired_at=BASE_TIME,
        )


def test_unlimited_model_has_no_supply_limit(repositories):
    models, instances = repositories
    model = create_unlimited_model(models)

    for user_id in range(1, 6):
        instances.create(
            vehicle_model_id=model.id,
            owner_user_id=user_id,
            acquired_at=BASE_TIME,
        )

    assert models.get(model.id).highest_mint == 5


def test_same_model_can_be_owned_by_multiple_users(repositories):
    models, instances = repositories
    model = create_unlimited_model(models)

    first = instances.create(
        vehicle_model_id=model.id,
        owner_user_id=100,
        acquired_at=BASE_TIME,
    )

    second = instances.create(
        vehicle_model_id=model.id,
        owner_user_id=200,
        acquired_at=BASE_TIME,
    )

    assert first.owner_user_id == 100
    assert second.owner_user_id == 200
    assert first.mint_number != second.mint_number


def test_list_for_owner(repositories):
    models, instances = repositories
    model = create_unlimited_model(models)

    instances.create(
        vehicle_model_id=model.id,
        owner_user_id=100,
        acquired_at=BASE_TIME,
    )

    instances.create(
        vehicle_model_id=model.id,
        owner_user_id=100,
        acquired_at=BASE_TIME,
    )

    instances.create(
        vehicle_model_id=model.id,
        owner_user_id=200,
        acquired_at=BASE_TIME,
    )

    owned = instances.list_for_owner(100)

    assert len(owned) == 2
    assert [vehicle.owner_user_id for vehicle in owned] == [100, 100]
    assert [vehicle.mint_number for vehicle in owned] == [1, 2]


def test_unknown_model_cannot_be_minted(repositories):
    models, instances = repositories

    with pytest.raises(LookupError):
        instances.create(
            vehicle_model_id=999,
            owner_user_id=123,
            acquired_at=BASE_TIME,
        )


def test_invalid_owner_is_rejected(repositories):
    models, instances = repositories
    model = create_unlimited_model(models)

    with pytest.raises(ValueError, match="owner_user_id"):
        instances.create(
            vehicle_model_id=model.id,
            owner_user_id=0,
            acquired_at=BASE_TIME,
        )