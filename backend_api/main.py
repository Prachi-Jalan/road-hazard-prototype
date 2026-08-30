from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import Base, engine, get_db
from models import Hazard
from schemas import DetectionCreate, HazardResponse

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Smart Road Hazard Detection API",
    version="1.0.0"
)


@app.get("/")
def health_check():
    return {
        "status": "ok",
        "service": "road-hazard-api"
    }


@app.post("/api/detections", response_model=HazardResponse)
def create_detection(
    detection: DetectionCreate,
    db: Session = Depends(get_db)
):
    hazard = Hazard(
        hazard_type=detection.hazard_type,
        latitude=detection.latitude,
        longitude=detection.longitude,
        confidence=detection.confidence,
        severity=detection.severity,
        timestamp=detection.frame_timestamp,
        observation_count=1,
        verification_status="unverified",
        distance_m=detection.distance_m,
        ahead=detection.ahead,
        on_route=detection.on_route,
        location=f"SRID=4326;POINT({detection.longitude} {detection.latitude})"
    )

    db.add(hazard)
    db.commit()
    db.refresh(hazard)

    return hazard


@app.get("/api/hazards/nearby", response_model=list[HazardResponse])
def get_nearby_hazards(
    lat: float,
    lon: float,
    radius_m: float = 500,
    db: Session = Depends(get_db)
):
    point = func.ST_SetSRID(
        func.ST_MakePoint(lon, lat),
        4326
    )

    distance = func.ST_Distance(
        Hazard.location,
        func.Geography(point)
    ).label("calculated_distance")

    hazards = (
        db.query(Hazard, distance)
        .filter(
            func.ST_DWithin(
                Hazard.location,
                func.Geography(point),
                radius_m
            )
        )
        .order_by(distance)
        .all()
    )

    results = []

    for hazard, calculated_distance in hazards:
        hazard.distance_m = calculated_distance
        results.append(hazard)

    return results

@app.patch(
    "/api/hazards/{hazard_id}/verify",
    response_model=HazardResponse
)
def verify_hazard(
    hazard_id: int,
    db: Session = Depends(get_db)
):
    hazard = (
        db.query(Hazard)
        .filter(Hazard.hazard_id == hazard_id)
        .first()
    )

    if hazard is None:
        raise HTTPException(
            status_code=404,
            detail="Hazard not found"
        )

    hazard.verification_status = "verified"

    db.commit()
    db.refresh(hazard)

    return hazard
