from datetime import datetime, timedelta
import random

from src.core.collections import VehicleInstanceRepository
from src.core.servers import ServerEligibility
from src.core.spawning import (
    CatchService,
    SpawnCandidate,
    SpawnManager,
)
from src.core.vehicles import VehicleModelRepository


BASE_TIME = datetime(2026, 1, 1, 12, 0, 0)


class FakeModelSource:
    def __init__(self, model_id: str) -> None:
        self.model_id = model_id

    def get_spawn_candidates(self) -> list[SpawnCandidate]:
        return [
            SpawnCandidate(
                model_id=self.model_id,
                weight=1.0,
            )
        ]


def make_system(tmp_path):
    database_path = tmp_path / "test.db"

    vehicle_repository = VehicleModelRepository(database_path)
    vehicle_repository.initialize()

    instance_repository = VehicleInstanceRepository(database_path)
    instance_repository.initialize()

    vehicle = vehicle_repository.create(
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

    manager = SpawnManager(
        eligibility=ServerEligibility(),
        model_source=FakeModelSource(str(vehicle.id)),
        spawn_cooldown=timedelta(minutes=30),
        catch_window=timedelta(minutes=2),
        rng=random.Random(1),
    )

    state = manager.get_state(100)
    state.activity.required_activity = 1

    service = CatchService(
        spawn_manager=manager,
        vehicle_repository=vehicle_repository,
        instance_repository=instance_repository,
    )

    return (
        vehicle_repository,
        instance_repository,
        manager,
        service,
        vehicle,
    )


def create_spawn(manager: SpawnManager):
    result = manager.process_message(
        server_id=100,
        human_member_count=20,
        user_id=50,
        created_at=BASE_TIME,
    )

    assert result.spawned is not None

    return result.spawned


def test_successful_catch_creates_instance(tmp_path):
    _, instances, manager, service, vehicle = make_system(tmp_path)

    spawn = create_spawn(manager)

    result = service.catch(
        server_id=100,
        user_id=123,
        submitted_name="BMW M4",
        now=BASE_TIME,
    )

    assert result.success is True
    assert result.reason == "caught"
    assert result.model_id == vehicle.id
    assert result.spawn_id == spawn.spawn_id

    assert result.vehicle_instance is not None
    assert result.vehicle_instance.vehicle_model_id == vehicle.id
    assert result.vehicle_instance.owner_user_id == 123
    assert result.vehicle_instance.mint_number == 1

    owned = instances.list_for_owner(123)

    assert len(owned) == 1


def test_successful_catch_consumes_spawn(tmp_path):
    _, _, manager, service, _ = make_system(tmp_path)

    create_spawn(manager)

    result = service.catch(
        server_id=100,
        user_id=123,
        submitted_name="M4",
        now=BASE_TIME,
    )

    assert result.success is True
    assert manager.get_active_spawn(100) is None


def test_second_catch_cannot_mint_again(tmp_path):
    _, instances, manager, service, _ = make_system(tmp_path)

    create_spawn(manager)

    first = service.catch(
        server_id=100,
        user_id=123,
        submitted_name="M4",
        now=BASE_TIME,
    )

    second = service.catch(
        server_id=100,
        user_id=456,
        submitted_name="M4",
        now=BASE_TIME,
    )

    assert first.success is True
    assert second.success is False
    assert second.reason == "no_active_spawn"

    assert len(instances.list_for_owner(123)) == 1
    assert len(instances.list_for_owner(456)) == 0


def test_unknown_vehicle_does_not_consume_spawn(tmp_path):
    _, instances, manager, service, _ = make_system(tmp_path)

    create_spawn(manager)

    result = service.catch(
        server_id=100,
        user_id=123,
        submitted_name="Ferrari",
        now=BASE_TIME,
    )

    assert result.success is False
    assert result.reason == "unknown_vehicle"
    assert result.vehicle_instance is None

    assert instances.list_for_owner(123) == []
    assert manager.get_active_spawn(100) is not None


def test_wrong_vehicle_does_not_consume_spawn(tmp_path):
    repository, instances, manager, service, _ = make_system(tmp_path)

    repository.create(
        manufacturer="Porsche",
        model_name="911",
        year=2024,
        rarity_weight=1.0,
        spawn_image=None,
        card_image=None,
        enabled=True,
        spawn_eligible=True,
        limited=False,
        mint_limit=None,
        catch_names="porsche 911",
    )

    create_spawn(manager)

    result = service.catch(
        server_id=100,
        user_id=123,
        submitted_name="porsche 911",
        now=BASE_TIME,
    )

    assert result.success is False
    assert result.reason == "wrong_vehicle"
    assert result.vehicle_instance is None

    assert instances.list_for_owner(123) == []
    assert manager.get_active_spawn(100) is not None


def test_expired_spawn_does_not_create_instance(tmp_path):
    _, instances, manager, service, _ = make_system(tmp_path)

    create_spawn(manager)

    result = service.catch(
        server_id=100,
        user_id=123,
        submitted_name="BMW M4",
        now=BASE_TIME + timedelta(minutes=2),
    )

    assert result.success is False
    assert result.reason == "spawn_expired"
    assert result.vehicle_instance is None

    assert instances.list_for_owner(123) == []
    assert manager.get_active_spawn(100) is None


def test_wrong_server_cannot_catch(tmp_path):
    _, instances, manager, service, _ = make_system(tmp_path)

    create_spawn(manager)

    result = service.catch(
        server_id=200,
        user_id=123,
        submitted_name="BMW M4",
        now=BASE_TIME,
    )

    assert result.success is False
    assert result.reason == "no_active_spawn"
    assert result.vehicle_instance is None

    assert instances.list_for_owner(123) == []
    assert manager.get_active_spawn(100) is not None


def test_catch_name_is_case_insensitive(tmp_path):
    _, instances, manager, service, vehicle = make_system(tmp_path)

    create_spawn(manager)

    result = service.catch(
        server_id=100,
        user_id=123,
        submitted_name="bMw M4",
        now=BASE_TIME,
    )

    assert result.success is True
    assert result.model_id == vehicle.id
    assert len(instances.list_for_owner(123)) == 1


def test_successful_catch_assigns_correct_owner(tmp_path):
    _, instances, manager, service, vehicle = make_system(tmp_path)

    create_spawn(manager)

    result = service.catch(
        server_id=100,
        user_id=987654,
        submitted_name="M4",
        now=BASE_TIME,
    )

    assert result.success is True
    assert result.vehicle_instance is not None
    assert result.vehicle_instance.owner_user_id == 987654
    assert result.vehicle_instance.vehicle_model_id == vehicle.id

    assert len(instances.list_for_owner(987654)) == 1


def test_failed_mint_restores_claimed_spawn(tmp_path):
    _, instances, manager, service, _ = make_system(tmp_path)

    spawn = create_spawn(manager)

    def failed_create(**kwargs):
        raise RuntimeError("database failure")

    service.instance_repository.create = failed_create

    try:
        service.catch(
            server_id=100,
            user_id=123,
            submitted_name="M4",
            now=BASE_TIME,
        )
    except RuntimeError as exc:
        assert str(exc) == "database failure"
    else:
        raise AssertionError(
            "CatchService should raise when vehicle minting fails."
        )

    restored_spawn = manager.get_active_spawn(100)

    assert restored_spawn is not None
    assert restored_spawn.spawn_id == spawn.spawn_id
    assert restored_spawn.model_id == spawn.model_id

    assert instances.list_for_owner(123) == []


def test_expired_catch_never_mints(tmp_path):
    _, instances, manager, service, _ = make_system(tmp_path)

    create_spawn(manager)

    result = service.catch(
        server_id=100,
        user_id=123,
        submitted_name="M4",
        now=BASE_TIME + timedelta(minutes=2),
    )

    assert result.success is False
    assert result.reason == "spawn_expired"
    assert result.vehicle_instance is None
    assert instances.list_for_owner(123) == []


def test_successful_claim_prevents_second_claim(tmp_path):
    _, instances, manager, service, _ = make_system(tmp_path)

    create_spawn(manager)

    first = service.catch(
        server_id=100,
        user_id=123,
        submitted_name="M4",
        now=BASE_TIME,
    )

    second = service.catch(
        server_id=100,
        user_id=456,
        submitted_name="M4",
        now=BASE_TIME,
    )

    assert first.success is True
    assert second.success is False

    assert len(instances.list_for_owner(123)) == 1
    assert instances.list_for_owner(456) == []
    assert manager.get_active_spawn(100) is None