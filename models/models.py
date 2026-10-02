from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from database.database import Base


class Restaurant(Base):
    """A restaurant that can have multiple inspection records."""

    __tablename__ = "restaurants"
    __table_args__ = (UniqueConstraint("code", name="uq_restaurants_code"),)

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    location = Column(String(500), nullable=False)
    code = Column(String(32), nullable=False, index=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    inspections = relationship("Inspection", back_populates="restaurant")


class Inspection(Base):
    __tablename__ = "inspections"
    __table_args__ = (UniqueConstraint("inspection_code", name="uq_inspections_code"),)

    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(
        Integer,
        ForeignKey("restaurants.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    inspection_code = Column(String(64), nullable=False, index=True)
    score = Column(Integer, nullable=False, default=100, server_default="100")
    restaurantName = Column(String(255), nullable=False)
    location = Column(String(500), nullable=False)
    email = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(100), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    restaurant = relationship("Restaurant", back_populates="inspections")

    related_records = relationship(
        "InspectionRelated",
        back_populates="inspection",
        cascade="all, delete-orphan"
    )


class InspectionRelated(Base):
    __tablename__ = "inspection_related"

    id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(
        Integer,
        ForeignKey("inspections.id"),
        nullable=False,
        index=True
    )
    note = Column(String(255), nullable=False)

    inspection = relationship(
        "Inspection",
        back_populates="related_records"
    )


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)


class Session(Base):
    __tablename__ = "sessions"

    id = Column(String(255), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
