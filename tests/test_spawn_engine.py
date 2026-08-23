from datetime import datetime, timedelta
import random

from src.core.spawning import SpawnCandidate, SpawnEngine


BASE_TIME = datetime(2026, 1, 1, 12, 0, 0)


class FakeModelSource:
    def __init__(self, candidates: list[SpawnCandidate]) -> None:
        self.candidates = candidates

    def get_spawn_candidates(self) -> list[SpawnCandidate]:
        return list(self.candidates)


def make_engine(
    candidates: list[SpawnCandidate] | None = None,
    *,
    cooldown: timedelta = timedelta(minutes=30),
    catch_window: timedelta = timedelta(minutes=2),
    seed: int = 1,
) -> SpawnEngine:
    if candidates is None:
        candidates = [
            SpawnCandidate("bmw-m4", 1.0),
            SpawnCandidate("bmw-m5", 1.0),
        ]
 
    source = FakeModelSource(candidates)
                 

    return SpawnEngine(
        source,
        spawn_cooldown=cooldown,
        catch_window=catch_window,
        rng=random.Random(seed),
    )


def test_first_spawn_is_allowed():
    engine = make_engine()

    assert engine.can_spawn(BASE_TIME) is True


def test_spawn_creates_active_spawn():
    engine = make_engine()

    spawn = engine.create_spawn(BASE_TIME)

    assert spawn is not None
    assert engine.active_spawn == spawn
    assert spawn.created_at == BASE_TIME
    assert spawn.expires_at == BASE_TIME + timedelta(minutes=2)


def test_second_spawn_is_blocked_while_active():
    engine = make_engine()

    engine.create_spawn(BASE_TIME)

    assert engine.create_spawn(
        BASE_TIME + timedelta(seconds=30)
    ) is None


def test_spawn_cannot_happen_during_cooldown():
    engine = make_engine()

    engine.create_spawn(BASE_TIME)

    engine.active_spawn = None

    assert engine.create_spawn(
        BASE_TIME + timedelta(minutes=29)
    ) is None


def test_spawn_allowed_after_cooldown():
    engine = make_engine()

    engine.create_spawn(BASE_TIME)

    engine.active_spawn = None

    spawn = engine.create_spawn(
        BASE_TIME + timedelta(minutes=30)
    )

    assert spawn is not None


def test_no_candidates_means_no_spawn():
    engine = make_engine([])

    assert engine.create_spawn(BASE_TIME) is None
    assert engine.active_spawn is None


def test_zero_weight_candidates_are_ignored():
    engine = make_engine(
        [
            SpawnCandidate("disabled-car", 0.0),
            SpawnCandidate("bmw-m4", 1.0),
        ]
    )

    spawn = engine.create_spawn(BASE_TIME)

    assert spawn is not None
    assert spawn.model_id == "bmw-m4"


def test_negative_weight_candidates_are_ignored():
    engine = make_engine(
        [
            SpawnCandidate("invalid-car", -10.0),
            SpawnCandidate("bmw-m4", 1.0),
        ]
    )

    spawn = engine.create_spawn(BASE_TIME)

    assert spawn is not None
    assert spawn.model_id == "bmw-m4"


def test_expired_spawn_is_detected():
    engine = make_engine()

    engine.create_spawn(BASE_TIME)

    assert engine.is_expired(
        BASE_TIME + timedelta(minutes=2)
    ) is True


def test_unexpired_spawn_is_not_expired():
    engine = make_engine()

    engine.create_spawn(BASE_TIME)

    assert engine.is_expired(
        BASE_TIME + timedelta(seconds=30)
    ) is False


def test_expired_spawn_is_removed():
    engine = make_engine()

    engine.create_spawn(BASE_TIME)

    expired = engine.expire_if_needed(
        BASE_TIME + timedelta(minutes=2)
    )

    assert expired is True
    assert engine.active_spawn is None


def test_unexpired_spawn_is_not_removed():
    engine = make_engine()

    engine.create_spawn(BASE_TIME)

    expired = engine.expire_if_needed(
        BASE_TIME + timedelta(seconds=30)
    )

    assert expired is False
    assert engine.active_spawn is not None


def test_correct_model_can_be_caught():
    engine = make_engine(
        [SpawnCandidate("bmw-m4", 1.0)]
    )

    engine.create_spawn(BASE_TIME)

    result = engine.resolve_catch(
        model_id="bmw-m4",
        now=BASE_TIME + timedelta(seconds=10),
    )

    assert result is True
    assert engine.active_spawn is None


def test_wrong_model_cannot_be_caught():
    engine = make_engine(
        [SpawnCandidate("bmw-m4", 1.0)]
    )

    engine.create_spawn(BASE_TIME)

    result = engine.resolve_catch(
        model_id="bmw-m5",
        now=BASE_TIME + timedelta(seconds=10),
    )

    assert result is False
    assert engine.active_spawn is not None


def test_catch_at_exact_expiration_is_rejected():
    engine = make_engine(
        [SpawnCandidate("bmw-m4", 1.0)]
    )

    engine.create_spawn(BASE_TIME)

    result = engine.resolve_catch(
        model_id="bmw-m4",
        now=BASE_TIME + timedelta(minutes=2),
    )

    assert result is False
    assert engine.active_spawn is None


def test_catch_before_expiration_is_accepted():
    engine = make_engine(
        [SpawnCandidate("bmw-m4", 1.0)]
    )

    engine.create_spawn(BASE_TIME)

    result = engine.resolve_catch(
        model_id="bmw-m4",
        now=BASE_TIME + timedelta(minutes=1, seconds=59),
    )

    assert result is True


def test_wrong_catch_does_not_consume_spawn():
    engine = make_engine(
        [SpawnCandidate("bmw-m4", 1.0)]
    )

    engine.create_spawn(BASE_TIME)

    result = engine.resolve_catch(
        model_id="bmw-m5",
        now=BASE_TIME + timedelta(seconds=30),
    )

    assert result is False
    assert engine.active_spawn is not None


def test_spawn_id_is_unique_for_sequential_spawns():
    engine = make_engine(
        [SpawnCandidate("bmw-m4", 1.0)],
        cooldown=timedelta(0),
    )

    first = engine.create_spawn(BASE_TIME)

    engine.active_spawn = None

    second = engine.create_spawn(
        BASE_TIME + timedelta(minutes=1)
    )

    assert first is not None
    assert second is not None
    assert first.spawn_id != second.spawn_id