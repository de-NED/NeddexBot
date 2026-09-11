from datetime import datetime, timezone
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
        catch_names="m4",
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
                "catch_names": "m4",
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


def test_list_vehicles_supports_search(tmp_path: Path) -> None:
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


def test_list_vehicles_supports_enabled_filter(tmp_path: Path) -> None:
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


def test_update_vehicle(tmp_path: Path) -> None:
    database_path = tmp_path / "test.db"
    app = create_app(database_path)
    application = app.state.neddex_application

    vehicle = application.vehicle_models.create(
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
        catch_names="m4,bmw m4",
    )

    client = TestClient(app)

    response = client.put(
        f"/admin/vehicles/{vehicle.id}",
        json={
            "manufacturer": "BMW",
            "model_name": "M4 Competition",
            "year": 2025,
            "rarity_weight": 2.0,
            "spawn_image": None,
            "card_image": None,
            "enabled": False,
            "spawn_eligible": True,
            "limited": True,
            "mint_limit": 100,
            "catch_names": "m4 competition; m4 comp",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == vehicle.id
    assert data["manufacturer"] == "BMW"
    assert data["model_name"] == "M4 Competition"
    assert data["year"] == 2025
    assert data["rarity_weight"] == 2.0
    assert data["enabled"] is False
    assert data["spawn_eligible"] is True
    assert data["limited"] is True
    assert data["mint_limit"] == 100
    assert data["catch_names"] == "m4 competition; m4 comp"


def test_delete_vehicle_removes_vehicle_model(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "test.db"
    app = create_app(database_path)
    application = app.state.neddex_application

    vehicle = application.vehicle_models.create(
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

    response = client.delete(
        f"/admin/vehicles/{vehicle.id}"
    )

    assert response.status_code == 204
    assert application.vehicle_models.list_all() == []


def test_delete_vehicle_returns_404_for_missing_vehicle(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "test.db"
    app = create_app(database_path)

    client = TestClient(app)

    response = client.delete("/admin/vehicles/999")

    assert response.status_code == 404


def test_delete_vehicle_returns_409_when_vehicle_has_minted_instance(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "test.db"
    app = create_app(database_path)
    application = app.state.neddex_application

    vehicle = application.vehicle_models.create(
        manufacturer="BMW",
        model_name="M4",
        year=2024,
        rarity_weight=1.0,
        spawn_image=None,
        card_image=None,
        enabled=True,
        spawn_eligible=True,
        limited=False,
        mint_limit=10,
        catch_names="M4",
    )

    application.vehicle_instances.create(
        vehicle_model_id=vehicle.id,
        owner_user_id=123456789,
        acquired_at=datetime.now(timezone.utc),
    )

    client = TestClient(app)

    response = client.delete(
        f"/admin/vehicles/{vehicle.id}"
    )

    assert response.status_code == 409
    assert application.vehicle_models.get(vehicle.id).id == vehicle.id
