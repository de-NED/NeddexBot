from fastapi import APIRouter, Request

from src.application import NeddexApplication

from src.admin_api.schemas import VehicleModelResponse


router = APIRouter(
    prefix="/admin/vehicles",
    tags=["vehicles"],
)


def get_application(request: Request) -> NeddexApplication:
    application = getattr(request.app.state, "neddex_application", None)

    if application is None:
        raise RuntimeError("Neddex application is not configured.")

    return application


@router.get("", response_model=list[VehicleModelResponse])
async def list_vehicles(request: Request) -> list[VehicleModelResponse]:
    application = get_application(request)

    return [
        VehicleModelResponse(
            id=vehicle.id,
            manufacturer=vehicle.manufacturer,
            model_name=vehicle.model_name,
            year=vehicle.year,
            rarity_weight=vehicle.rarity_weight,
            spawn_image=vehicle.spawn_image,
            card_image=vehicle.card_image,
            enabled=vehicle.enabled,
            spawn_eligible=vehicle.spawn_eligible,
            limited=vehicle.limited,
            mint_limit=vehicle.mint_limit,
            highest_mint=vehicle.highest_mint,
        )
        for vehicle in application.vehicle_models.list_all()
    ]