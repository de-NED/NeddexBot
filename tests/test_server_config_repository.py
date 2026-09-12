from src.core.servers.repository import ServerConfigRepository


def test_missing_server_has_safe_defaults(tmp_path):
    repository = ServerConfigRepository(str(tmp_path / "test.db"))

    config = repository.get(123)

    assert config.server_id == 123
    assert config.spawn_channel_id is None
    assert config.spawning_enabled is False


def test_server_config_persists(tmp_path):
    db_path = tmp_path / "test.db"

    repository = ServerConfigRepository(str(db_path))

    saved = repository.upsert(
        server_id=123,
        spawn_channel_id=456,
        spawning_enabled=True,
    )

    assert saved.server_id == 123
    assert saved.spawn_channel_id == 456
    assert saved.spawning_enabled is True

    new_repository = ServerConfigRepository(str(db_path))
    loaded = new_repository.get(123)

    assert loaded.server_id == 123
    assert loaded.spawn_channel_id == 456
    assert loaded.spawning_enabled is True


def test_server_config_can_be_disabled(tmp_path):
    repository = ServerConfigRepository(str(tmp_path / "test.db"))

    repository.upsert(
        server_id=123,
        spawn_channel_id=456,
        spawning_enabled=True,
    )

    config = repository.upsert(
        server_id=123,
        spawn_channel_id=789,
        spawning_enabled=False,
    )

    assert config.spawn_channel_id == 789
    assert config.spawning_enabled is False