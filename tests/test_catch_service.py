from datetime import datetime, timedelta
import random

from src.core.servers import ServerEligibility
from src.core.spawning import (
    SpawnCandidate,
    SpawnManager,
)
from src.core.spawning.catch_service import CatchService
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
    repository = VehicleModelRepository(
        tmp_path / "test.db"
    )
    repository.initialize()

    vehicle = repository.create(
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

    manager.get_state(100).activity.required_activity = 1

    service = CatchService(
        spawn_manager=manager,
        vehicle_repository=repository,
    )

    return repository, manager, service, vehicle


def create_spawn(manager: SpawnManager):
    result = manager.process_message(
        server_id=100,
        human_member_count=20,
        user_id=50,
        created_at=BASE_TIME,
    )

    assert result.spawned is not None

    return result.spawned


def test_successful_catch(tmp_path):
    repository, manager, service, vehicle = make_system(tmp_path)

    spawn = create_spawn(manager)

    result = service.catch(
        server_id=100,
        user_id=123,
        submitted_name="BMW M4",
        now=BASE_TIME,
    )

    assert result.success is True
    assert result.model_id == vehicle.id
    assert result.spawn_id == spawn.spawn_id
    assert result.reason == "caught"

    assert manager.get_active_spawn(100) is None


def test_catch_name_is_case_insensitive(tmp_path):
    repository, manager, service, vehicle = make_system(tmp_path)

    create_spawn(manager)

    result = service.catch(
        server_id=100,
        user_id=123,
        submitted_name="bMw m4",
        now=BASE_TIME,
    )

    assert result.success is True
    assert result.model_id == vehicle.id


def test_alias_can_be_used(tmp_path):
    repository, manager, service, vehicle = make_system(tmp_path)

    create_spawn(manager)

    result = service.catch(
        server_id=100,
        user_id=123,
        submitted_name="m4",
        now=BASE_TIME,
    )

    assert result.success is True
    assert result.model_id == vehicle.id


def test_unknown_vehicle_does_not_consume_spawn(tmp_path):
    repository, manager, service, vehicle = make_system(tmp_path)

    spawn = create_spawn(manager)

    result = service.catch(
        server_id=100,
        user_id=123,
        submitted_name="Ferrari",
        now=BASE_TIME,
    )

    assert result.success is False
    assert result.model_id is None
    assert result.spawn_id == spawn.spawn_id
    assert result.reason == "unknown_vehicle"

    assert manager.get_active_spawn(100) is not None


def test_wrong_vehicle_does_not_consume_spawn(tmp_path):
    repository, manager, service, vehicle = make_system(tmp_path)

    porsche = repository.create(
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

    spawn = create_spawn(manager)

    result = service.catch(
        server_id=100,
        user_id=123,
        submitted_name="porsche 911",
        now=BASE_TIME,
    )

    assert result.success is False
    assert result.model_id == porsche.id
    assert result.spawn_id == spawn.spawn_id
    assert result.reason == "wrong_vehicle"

    assert manager.get_active_spawn(100) is not None


def test_no_active_spawn_fails(tmp_path):
    repository, manager, service, vehicle = make_system(tmp_path)

    result = service.catch(
        server_id=100,
        user_id=123,
        submitted_name="BMW M4",
        now=BASE_TIME,
    )

    assert result.success is False
    assert result.model_id is None
    assert result.spawn_id is None
    assert result.reason == "no_active_spawn"


def test_expired_spawn_fails(tmp_path):
    repository, manager, service, vehicle = make_system(tmp_path)

    spawn = create_spawn(manager)

    result = service.catch(
        server_id=100,
        user_id=123,
        submitted_name="BMW M4",
        now=BASE_TIME + timedelta(minutes=2),
    )

    assert result.success is False
    assert result.model_id == vehicle.id
    assert result.spawn_id == spawn.spawn_id
    assert result.reason == "spawn_expired"

    assert manager.get_active_spawn(100) is None


def test_catch_cannot_cross_servers(tmp_path):
    repository, manager, service, vehicle = make_system(tmp_path)

    create_spawn(manager)

    result = service.catch(
        server_id=200,
        user_id=123,
        submitted_name="BMW M4",
        now=BASE_TIME,
    )

    assert result.success is False
    assert result.model_id is None
    assert result.spawn_id is None
    assert result.reason == "no_active_spawn"

    assert manager.get_active_spawn(100) is not None