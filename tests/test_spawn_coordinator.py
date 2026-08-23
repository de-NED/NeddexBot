from datetime import datetime, timedelta
import random

from src.core.activity import ActivityTracker
from src.core.servers import ServerEligibility
from src.core.spawning import (
    SpawnCandidate,
    SpawnCoordinator,
    SpawnEngine,
)


BASE_TIME = datetime(2026, 1, 1, 12, 0, 0)


class FakeModelSource:
    def __init__(self) -> None:
        self.candidates = [
            SpawnCandidate("bmw-m4", 1.0),
        ]

    def get_spawn_candidates(self) -> list[SpawnCandidate]:
        return list(self.candidates)


def make_coordinator(
    *,
    main_server_id: int | None = None,
    required_activity: int = 1,
) -> SpawnCoordinator:
    eligibility = ServerEligibility(
        main_server_id=main_server_id,
    )

    activity = ActivityTracker(
        rng=random.Random(1),
    )

    activity.required_activity = required_activity

    engine = SpawnEngine(
        FakeModelSource(),
        spawn_cooldown=timedelta(minutes=30),
        catch_window=timedelta(minutes=2),
        rng=random.Random(1),
    )

    return SpawnCoordinator(
        eligibility=eligibility,
        activity=activity,
        engine=engine,
    )


def test_ineligible_server_activity_is_ignored():
    coordinator = make_coordinator()

    result = coordinator.process_message(
        server_id=1,
        human_member_count=19,
        user_id=10,
        created_at=BASE_TIME,
    )

    assert result.counted is False
    assert result.spawned is None


def test_eligible_server_counts_human_activity():
    coordinator = make_coordinator(
        required_activity=2,
    )

    result = coordinator.process_message(
        server_id=1,
        human_member_count=20,
        user_id=10,
        created_at=BASE_TIME,
    )

    assert result.counted is True
    assert result.ready is False
    assert result.spawned is None


def test_required_activity_creates_spawn():
    coordinator = make_coordinator(
        required_activity=2,
    )

    first = coordinator.process_message(
        server_id=1,
        human_member_count=20,
        user_id=10,
        created_at=BASE_TIME,
    )

    second = coordinator.process_message(
        server_id=1,
        human_member_count=20,
        user_id=11,
        created_at=BASE_TIME,
    )

    assert first.spawned is None
    assert second.ready is True
    assert second.spawned is not None
    assert second.spawned.model_id == "bmw-m4"


def test_activity_resets_after_successful_spawn():
    coordinator = make_coordinator(
        required_activity=1,
    )

    result = coordinator.process_message(
        server_id=1,
        human_member_count=20,
        user_id=10,
        created_at=BASE_TIME,
    )

    assert result.spawned is not None
    assert coordinator.activity.activity_count == 0


def test_bot_activity_does_not_count():
    coordinator = make_coordinator(
        required_activity=1,
    )

    result = coordinator.process_message(
        server_id=1,
        human_member_count=20,
        user_id=10,
        created_at=BASE_TIME,
        is_bot=True,
    )

    assert result.counted is False
    assert result.spawned is None


def test_webhook_activity_does_not_count():
    coordinator = make_coordinator(
        required_activity=1,
    )

    result = coordinator.process_message(
        server_id=1,
        human_member_count=20,
        user_id=10,
        created_at=BASE_TIME,
        is_webhook=True,
    )

    assert result.counted is False
    assert result.spawned is None


def test_command_activity_does_not_count():
    coordinator = make_coordinator(
        required_activity=1,
    )

    result = coordinator.process_message(
        server_id=1,
        human_member_count=20,
        user_id=10,
        created_at=BASE_TIME,
        is_command=True,
    )

    assert result.counted is False
    assert result.spawned is None


def test_main_server_bypasses_member_requirement():
    coordinator = make_coordinator(
        main_server_id=123,
        required_activity=1,
    )

    result = coordinator.process_message(
        server_id=123,
        human_member_count=0,
        user_id=10,
        created_at=BASE_TIME,
    )

    assert result.spawned is not None


def test_activity_does_not_accumulate_while_spawn_is_active():
    coordinator = make_coordinator(
        required_activity=1,
    )

    first = coordinator.process_message(
        server_id=1,
        human_member_count=20,
        user_id=10,
        created_at=BASE_TIME,
    )

    second = coordinator.process_message(
        server_id=1,
        human_member_count=20,
        user_id=11,
        created_at=BASE_TIME + timedelta(seconds=20),
    )

    assert first.spawned is not None
    assert second.counted is False
    assert second.spawned is None
    assert coordinator.activity.activity_count == 0


def test_expired_spawn_allows_new_activity():
    coordinator = make_coordinator(
        required_activity=1,
    )

    first = coordinator.process_message(
        server_id=1,
        human_member_count=20,
        user_id=10,
        created_at=BASE_TIME,
    )

    assert first.spawned is not None

    second = coordinator.process_message(
        server_id=1,
        human_member_count=20,
        user_id=11,
        created_at=BASE_TIME + timedelta(minutes=2),
    )

    assert second.counted is True
    assert second.spawned is None


def test_expire_spawn_delegates_to_engine():
    coordinator = make_coordinator(
        required_activity=1,
    )

    result = coordinator.process_message(
        server_id=1,
        human_member_count=20,
        user_id=10,
        created_at=BASE_TIME,
    )

    assert result.spawned is not None

    expired = coordinator.expire_spawn(
        BASE_TIME + timedelta(minutes=2),
    )

    assert expired is True
    assert coordinator.engine.active_spawn is None