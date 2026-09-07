from pathlib import Path

from fastapi.testclient import TestClient

from src.admin_api.app import create_app


def test_list_vehicles_returns_vehicle_models(tmp_path: Path) -> None:
    database_path = tmp_path / "test.db"
    app = create_app(database_path)
    application = app.state.neddex_application

    application.vehicle_models.create(
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
        catch_names="M4",
    )

    client = TestClient(app)
    response = client.get("/admin/vehicles")

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "id": 1,
                "manufacturer": "BMW",
                "model_name": "M4",
                "year": 2024,
                "rarity_weight": 1.0,
                "spawn_image": None,
                "card_image": None,
                "enabled": True,
                "spawn_eligible": True,
                "limited": False,
                "mint_limit": None,
                "highest_mint": 0,
            }
        ],
        "page": 1,
        "page_size": 50,
        "total": 1,
        "total_pages": 1,
    }


def test_list_vehicles_supports_pagination(tmp_path: Path) -> None:
    database_path = tmp_path / "test.db"
    app = create_app(database_path)
    application = app.state.neddex_application

    for index in range(5):
        application.vehicle_models.create(
            manufacturer="BMW",
            model_name=f"M{index + 1}",
            year=2024,
            rarity_weight=1.0,
            spawn_image=None,
            card_image=None,
            enabled=True,
            spawn_eligible=True,
            limited=False,
            mint_limit=None,
            catch_names=f"M{index + 1}",
        )

    client = TestClient(app)

    response = client.get(
        "/admin/vehicles?page=2&page_size=2"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["page"] == 2
    assert data["page_size"] == 2
    assert data["total"] == 5
    assert data["total_pages"] == 3

    assert [vehicle["id"] for vehicle in data["items"]] == [3, 4]


def test_list_vehicles_supports_search(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "test.db"
    app = create_app(database_path)
    application = app.state.neddex_application

    application.vehicle_models.create(
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
        catch_names="M4",
    )

    application.vehicle_models.create(
        manufacturer="Toyota",
        model_name="Supra",
        year=2023,
        rarity_weight=1.0,
        spawn_image=None,
        card_image=None,
        enabled=True,
        spawn_eligible=True,
        limited=False,
        mint_limit=None,
        catch_names="Supra",
    )

    client = TestClient(app)

    response = client.get("/admin/vehicles?search=bmw")

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["total_pages"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["manufacturer"] == "BMW"


def test_list_vehicles_supports_enabled_filter(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "test.db"
    app = create_app(database_path)
    application = app.state.neddex_application

    application.vehicle_models.create(
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
        catch_names="M4",
    )

    application.vehicle_models.create(
        manufacturer="BMW",
        model_name="M3",
        year=2023,
        rarity_weight=1.0,
        spawn_image=None,
        card_image=None,
        enabled=False,
        spawn_eligible=True,
        limited=False,
        mint_limit=None,
        catch_names="M3",
    )

    client = TestClient(app)

    response = client.get("/admin/vehicles?enabled=false")

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["model_name"] == "M3"


def test_list_vehicles_supports_spawn_eligible_filter(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "test.db"
    app = create_app(database_path)
    application = app.state.neddex_application

    application.vehicle_models.create(
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
        catch_names="M4",
    )

    application.vehicle_models.create(
        manufacturer="BMW",
        model_name="M3",
        year=2023,
        rarity_weight=1.0,
        spawn_image=None,
        card_image=None,
        enabled=True,
        spawn_eligible=False,
        limited=False,
        mint_limit=None,
        catch_names="M3",
    )

    client = TestClient(app)

    response = client.get(
        "/admin/vehicles?spawn_eligible=false"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["model_name"] == "M3"