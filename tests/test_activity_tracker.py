from __future__ import annotations

from datetime import datetime, timedelta
import random

from src.core.activity import ActivityTracker


BASE_TIME = datetime(2026, 1, 1, 12, 0, 0)


def make_tracker(seed: int = 1) -> ActivityTracker:
    return ActivityTracker(rng=random.Random(seed))


def test_requirement_is_between_one_and_three():
    for seed in range(100):
        tracker = make_tracker(seed)

        assert 1 <= tracker.required_activity <= 3


def test_human_message_counts():
    tracker = make_tracker()

    counted = tracker.record_message(
        user_id=1,
        created_at=BASE_TIME,
    )

    assert counted is True
    assert tracker.activity_count == 1


def test_bot_message_does_not_count():
    tracker = make_tracker()

    counted = tracker.record_message(
        user_id=1,
        created_at=BASE_TIME,
        is_bot=True,
    )

    assert counted is False
    assert tracker.activity_count == 0


def test_webhook_does_not_count():
    tracker = make_tracker()

    counted = tracker.record_message(
        user_id=1,
        created_at=BASE_TIME,
        is_webhook=True,
    )

    assert counted is False
    assert tracker.activity_count == 0


def test_command_does_not_count():
    tracker = make_tracker()

    counted = tracker.record_message(
        user_id=1,
        created_at=BASE_TIME,
        is_command=True,
    )

    assert counted is False
    assert tracker.activity_count == 0


def test_same_user_is_throttled_for_ten_seconds():
    tracker = make_tracker()

    first = tracker.record_message(
        user_id=1,
        created_at=BASE_TIME,
    )

    second = tracker.record_message(
        user_id=1,
        created_at=BASE_TIME + timedelta(seconds=5),
    )

    assert first is True
    assert second is False
    assert tracker.activity_count == 1


def test_same_user_can_count_after_ten_seconds():
    tracker = make_tracker()

    first = tracker.record_message(
        user_id=1,
        created_at=BASE_TIME,
    )

    second = tracker.record_message(
        user_id=1,
        created_at=BASE_TIME + timedelta(seconds=10),
    )

    assert first is True
    assert second is True
    assert tracker.activity_count == 2


def test_different_users_can_count_immediately():
    tracker = make_tracker()

    first = tracker.record_message(
        user_id=1,
        created_at=BASE_TIME,
    )

    second = tracker.record_message(
        user_id=2,
        created_at=BASE_TIME,
    )

    assert first is True
    assert second is True
    assert tracker.activity_count == 2


def test_tracker_becomes_ready():
    tracker = make_tracker(seed=5)

    required = tracker.required_activity

    for user_id in range(required):
        tracker.record_message(
            user_id=user_id,
            created_at=BASE_TIME,
        )

    assert tracker.is_ready() is True


def test_tracker_is_not_ready_before_requirement():
    tracker = make_tracker(seed=5)

    required = tracker.required_activity

    if required == 1:
        return

    tracker.record_message(
        user_id=1,
        created_at=BASE_TIME,
    )

    assert tracker.is_ready() is False


def test_reset_starts_new_activity_window():
    tracker = make_tracker()

    tracker.record_message(
        user_id=1,
        created_at=BASE_TIME,
    )

    tracker.reset()

    assert tracker.activity_count == 0
    assert 1 <= tracker.required_activity <= 3
    assert tracker.last_activity_by_user == {}