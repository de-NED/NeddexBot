from src.core.spawning import VehicleModelSpawnSource
from src.core.vehicles import VehicleModelRepository


def test_model_source_returns_eligible_models(tmp_path):
    repository = VehicleModelRepository(
        tmp_path / "test.db"
    )
    repository.initialize()

    m4 = repository.create(
        manufacturer="BMW",
        model_name="M4",
        year=2024,
        rarity_weight=0.5,
        spawn_image=None,
        card_image=None,
        enabled=True,
        spawn_eligible=True,
        limited=False,
        mint_limit=None,
        catch_names="BMW M4",
    )

    source = VehicleModelSpawnSource(repository)

    candidates = source.get_spawn_candidates()

    assert len(candidates) == 1
    assert candidates[0].model_id == str(m4.id)
    assert candidates[0].weight == 0.5


def test_model_source_excludes_disabled_models(tmp_path):
    repository = VehicleModelRepository(
        tmp_path / "test.db"
    )
    repository.initialize()

    repository.create(
        manufacturer="BMW",
        model_name="M4",
        year=2024,
        rarity_weight=0.5,
        spawn_image=None,
        card_image=None,
        enabled=False,
        spawn_eligible=True,
        limited=False,
        mint_limit=None,
        catch_names="BMW M4",
    )

    source = VehicleModelSpawnSource(repository)

    assert source.get_spawn_candidates() == []


def test_model_source_excludes_spawn_ineligible_models(tmp_path):
    repository = VehicleModelRepository(
        tmp_path / "test.db"
    )
    repository.initialize()

    repository.create(
        manufacturer="BMW",
        model_name="M4",
        year=2024,
        rarity_weight=0.5,
        spawn_image=None,
        card_image=None,
        enabled=True,
        spawn_eligible=False,
        limited=False,
        mint_limit=None,
        catch_names="BMW M4",
    )

    source = VehicleModelSpawnSource(repository)

    assert source.get_spawn_candidates() == []


def test_model_source_excludes_exhausted_limited_models(tmp_path):
    repository = VehicleModelRepository(
        tmp_path / "test.db"
    )
    repository.initialize()

    m4 = repository.create(
        manufacturer="BMW",
        model_name="M4",
        year=2024,
        rarity_weight=0.5,
        spawn_image=None,
        card_image=None,
        enabled=True,
        spawn_eligible=True,
        limited=True,
        mint_limit=100,
        catch_names="BMW M4",
    )

    repository.set_highest_mint(m4.id, 100)

    source = VehicleModelSpawnSource(repository)

    assert source.get_spawn_candidates() == []


def test_model_source_preserves_rarity_weight(tmp_path):
    repository = VehicleModelRepository(
        tmp_path / "test.db"
    )
    repository.initialize()

    m4 = repository.create(
        manufacturer="BMW",
        model_name="M4",
        year=2024,
        rarity_weight=0.25,
        spawn_image=None,
        card_image=None,
        enabled=True,
        spawn_eligible=True,
        limited=False,
        mint_limit=None,
        catch_names="BMW M4",
    )

    source = VehicleModelSpawnSource(repository)

    candidates = source.get_spawn_candidates()

    assert candidates[0].weight == 0.25