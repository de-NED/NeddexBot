from pydantic import BaseModel


class VehicleModelResponse(BaseModel):
    id: int
    manufacturer: str
    model_name: str
    year: int | None
    rarity_weight: float
    spawn_image: str | None
    card_image: str | None
    enabled: bool
    spawn_eligible: bool
    limited: bool
    mint_limit: int | None
    highest_mint: int