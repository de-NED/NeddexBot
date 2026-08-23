from datetime import datetime, timedelta
import random

from src.core.servers import ServerEligibility
from src.core.spawning import (
    SpawnCandidate,
    SpawnManager,
)


BASE_TIME = datetime(2026, 1, 1, 12, 0, 0)


class FakeModelSource:
    def get_spawn_candidates(self) -> list[SpawnCandidate]:
        return [
            SpawnCandidate("bmw-m4", 1.0),
        ]


def make_manager() -> SpawnManager:
    return SpawnManager(
        eligibility=ServerEligibility(),
        model_source=FakeModelSource(),
        spawn_cooldown=timedelta(minutes=30),
        catch_window=timedelta(minutes=2),
        rng=random.Random(1),
    )


def prepare_server_for_one_message(
    manager: SpawnManager,
    server_id: int,
) -> None:
    """
    Make the test server require exactly one qualifying message.

    Production behavior remains random between 1 and 3.
    """
    state = manager.get_state(server_id)
    state.activity.required_activity = 1


def test_servers_have_independent_state():
    manager = make_manager()

    server_a = manager.get_state(100)
    server_b = manager.get_state(200)

    assert server_a is not server_b
    assert server_a.activity is not server_b.activity
    assert server_a.engine is not server_b.engine


def test_same_server_reuses_state():
    manager = make_manager()

    first = manager.get_state(100)
    second = manager.get_state(100)

    assert first is second


def test_activity_does_not_cross_servers():
    manager = make_manager()

    prepare_server_for_one_message(manager, 100)
    prepare_server_for_one_message(manager, 200)

    result_a = manager.process_message(
        server_id=100,
        human_member_count=20,
        user_id=1,
        created_at=BASE_TIME,
    )

    result_b = manager.process_message(
        server_id=200,
        human_member_count=20,
        user_id=2,
        created_at=BASE_TIME,
    )

    assert result_a.spawned is not None
    assert result_b.spawned is not None


def test_active_spawns_are_independent():
    manager = make_manager()

    prepare_server_for_one_message(manager, 100)
    prepare_server_for_one_message(manager, 200)

    first = manager.process_message(
        server_id=100,
        human_member_count=20,
        user_id=1,
        created_at=BASE_TIME,
    )

    second = manager.process_message(
        server_id=200,
        human_member_count=20,
        user_id=2,
        created_at=BASE_TIME,
    )

    assert first.spawned is not None
    assert second.spawned is not None

    assert manager.get_active_spawn(100) is not None
    assert manager.get_active_spawn(200) is not None


def test_cooldown_does_not_cross_servers():
    manager = make_manager()

    prepare_server_for_one_message(manager, 100)
    prepare_server_for_one_message(manager, 200)

    first = manager.process_message(
        server_id=100,
        human_member_count=20,
        user_id=1,
        created_at=BASE_TIME,
    )

    second = manager.process_message(
        server_id=200,
        human_member_count=20,
        user_id=2,
        created_at=BASE_TIME,
    )

    assert first.spawned is not None
    assert second.spawned is not None


def test_catch_is_limited_to_correct_server():
    manager = make_manager()

    prepare_server_for_one_message(manager, 100)

    first = manager.process_message(
        server_id=100,
        human_member_count=20,
        user_id=1,
        created_at=BASE_TIME,
    )

    assert first.spawned is not None

    assert (
        manager.resolve_catch(
            server_id=200,
            model_id="bmw-m4",
            now=BASE_TIME,
        )
        is False
    )

    assert (
        manager.resolve_catch(
            server_id=100,
            model_id="bmw-m4",
            now=BASE_TIME,
        )
        is True
    )


def test_expiring_one_server_does_not_expire_another():
    manager = make_manager()

    prepare_server_for_one_message(manager, 100)
    prepare_server_for_one_message(manager, 200)

    first = manager.process_message(
        server_id=100,
        human_member_count=20,
        user_id=1,
        created_at=BASE_TIME,
    )

    second = manager.process_message(
        server_id=200,
        human_member_count=20,
        user_id=2,
        created_at=BASE_TIME,
    )

    assert first.spawned is not None
    assert second.spawned is not None

    expired = manager.expire_spawn(
        server_id=100,
        now=BASE_TIME + timedelta(minutes=2),
    )

    assert expired is True
    assert manager.get_active_spawn(100) is None
    assert manager.get_active_spawn(200) is not None