from datetime import datetime

from pydantic import BaseModel, Field


class BBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float


class DetectionCreate(BaseModel):
    hazard_type: str
    confidence: float = Field(ge=0, le=1)
    bbox: BBox
    frame_timestamp: datetime

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)

    distance_m: float | None = None
    ahead: bool | None = None
    on_route: bool | None = None

    severity: str = "Unknown"


class HazardResponse(BaseModel):
    hazard_id: int
    hazard_type: str
    latitude: float
    longitude: float
    confidence: float
    severity: str
    timestamp: datetime
    observation_count: int
    verification_status: str
    distance_m: float | None = None
    ahead: bool | None = None
    on_route: bool | None = None

    model_config = {"from_attributes": True}
