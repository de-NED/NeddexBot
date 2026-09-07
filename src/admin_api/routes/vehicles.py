from math import ceil

from fastapi import APIRouter, Query, Request
from fastapi import APIRouter, HTTPException, Query, Request

from src.admin_api.schemas import (
    VehicleModelCreateRequest,
    VehicleModelListResponse,
    VehicleModelResponse,
    VehicleModelUpdateRequest,
)

from src.application import NeddexApplication


router = APIRouter(
    prefix="/admin/vehicles",
    tags=["vehicles"],
)

@router.post("", response_model=VehicleModelResponse, status_code=201)
async def create_vehicle(
    payload: VehicleModelCreateRequest,
    request: Request,
) -> VehicleModelResponse:
    application = get_application(request)

    vehicle = application.vehicle_models.create(
        manufacturer=payload.manufacturer,
        model_name=payload.model_name,
        year=payload.year,
        rarity_weight=payload.rarity_weight,
        spawn_image=payload.spawn_image,
        card_image=payload.card_image,
        enabled=payload.enabled,
        spawn_eligible=payload.spawn_eligible,
        limited=payload.limited,
        mint_limit=payload.mint_limit,
        catch_names=payload.catch_names,
    )

    return VehicleModelResponse(
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

@router.put(
    "/{vehicle_model_id}",
    response_model=VehicleModelResponse,
)
async def update_vehicle(
    vehicle_model_id: int,
    payload: VehicleModelUpdateRequest,
    request: Request,
) -> VehicleModelResponse:
    application = get_application(request)

    vehicle = application.vehicle_models.update(
        vehicle_model_id=vehicle_model_id,
        manufacturer=payload.manufacturer,
        model_name=payload.model_name,
        year=payload.year,
        rarity_weight=payload.rarity_weight,
        spawn_image=payload.spawn_image,
        card_image=payload.card_image,
        enabled=payload.enabled,
        spawn_eligible=payload.spawn_eligible,
        limited=payload.limited,
        mint_limit=payload.mint_limit,
        catch_names=payload.catch_names,
    )

    return VehicleModelResponse(
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

def get_application(request: Request) -> NeddexApplication:
    application = getattr(request.app.state, "neddex_application", None)

    if application is None:
        raise RuntimeError("Neddex application is not configured.")

    return application

@router.delete("/{vehicle_model_id}", status_code=204)
async def delete_vehicle(
    vehicle_model_id: int,
    request: Request,
) -> None:
    application = get_application(request)

    try:
        application.vehicle_models.delete(vehicle_model_id)
    except LookupError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

@router.get("", response_model=VehicleModelListResponse)
async def list_vehicles(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: str | None = Query(None, max_length=100),
    enabled: bool | None = None,
    spawn_eligible: bool | None = None,
) -> VehicleModelListResponse:
    application = get_application(request)

    offset = (page - 1) * page_size

    vehicles, total = application.vehicle_models.list_page(
        limit=page_size,
        offset=offset,
        search=search,
        enabled=enabled,
        spawn_eligible=spawn_eligible,
    )

    total_pages = ceil(total / page_size) if total else 0

    return VehicleModelListResponse(
        items=[
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
            for vehicle in vehicles
        ],
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
    )