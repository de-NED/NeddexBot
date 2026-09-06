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
    assert response.json() == [
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
    ]