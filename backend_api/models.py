from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from geoalchemy2 import Geography

from database import Base


class Hazard(Base):
    __tablename__ = "hazards"

    hazard_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    hazard_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    latitude: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    longitude: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )

    observation_count: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False
    )

    verification_status: Mapped[str] = mapped_column(
        String(20),
        default="unverified",
        nullable=False
    )

    distance_m: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    ahead: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True
    )

    on_route: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True
    )

    location = mapped_column(
        Geography(geometry_type="POINT", srid=4326),
        nullable=False
    )
