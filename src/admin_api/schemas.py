from pydantic import BaseModel


class VehicleModelCreateRequest(BaseModel):
    manufacturer: str
    model_name: str
    year: int | None = None
    rarity_weight: float
    spawn_image: str | None = None
    card_image: str | None = None
    enabled: bool = True
    spawn_eligible: bool = True
    limited: bool = False
    mint_limit: int | None = None
    catch_names: str

class VehicleModelUpdateRequest(BaseModel):
    manufacturer: str
    model_name: str
    year: int | None = None
    rarity_weight: float
    spawn_image: str | None = None
    card_image: str | None = None
    enabled: bool = True
    spawn_eligible: bool = True
    limited: bool = False
    mint_limit: int | None = None
    catch_names: str
    
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


class VehicleModelListResponse(BaseModel):
    items: list[VehicleModelResponse]
    page: int
    page_size: int
    total: int
    total_pages: int